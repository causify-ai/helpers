#!/usr/bin/env python

"""
Reorganize Python code from a single file into multiple files based on a map.

This script reads a markdown map file that specifies how to organize functions
from an input Python file into multiple target files. It performs text-based
manipulation to extract, reorder, and organize functions according to the map.

Example usage:
> reorder_python_code.py \
    --input_file helpers/hpandas.py \
    --map_file hpandas_map.md

The map file uses markdown structure:
- Level 1 headers (#) specify target file names
- Level 2 headers (##) specify section dividers
- Bullet lists specify function names to include

Import as:

import dev_scripts_helpers.coding_tools.reorder_python_code as dscctoreco
"""

import argparse
import logging
import os
import re
from typing import Dict, List, Tuple

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


# #############################################################################
# Parse map file
# #############################################################################


def _parse_map_file(
    map_file_path: str,
) -> Dict[str, List[Tuple[str, List[str]]]]:
    """
    Parse the markdown map file to extract file structure.

    The map file format:
    - H1 headers (# filename.py) define target files
    - H2 headers (## Section Name) define section comments
    - Bullet points list function names for each section

    :param map_file_path: path to the markdown map file
    :return: dictionary mapping target filenames to list of (section, functions)
        tuples
    """
    hdbg.dassert(
        os.path.exists(map_file_path),
        "Map file does not exist:",
        map_file_path,
    )
    _LOG.info("Parsing map file: %s", map_file_path)
    # Read the map file.
    content = hio.from_file(map_file_path)
    lines = content.split("\n")
    # Parse the structure.
    file_mapping: Dict[str, List[Tuple[str, List[str]]]] = {}
    current_file = None
    current_section = None
    current_functions: List[str] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Check for H1 header (target file).
        if line.startswith("# ") and not line.startswith("## "):
            # Save previous section if exists.
            if current_file and current_section:
                if current_file not in file_mapping:
                    file_mapping[current_file] = []
                file_mapping[current_file].append(
                    (current_section, current_functions)
                )
                current_functions = []
            # Save functions without section (if file has no section headers).
            elif current_file and current_functions:
                if current_file not in file_mapping:
                    file_mapping[current_file] = []
                # Use filename as default section name.
                file_mapping[current_file].append(
                    ("Functions", current_functions)
                )
                current_functions = []
            # Extract filename.
            current_file = line[2:].strip()
            current_section = None
            _LOG.debug("Found target file: %s", current_file)
        # Check for H2 header (section name).
        elif line.startswith("## "):
            # Save previous section if exists.
            if current_file and current_section:
                if current_file not in file_mapping:
                    file_mapping[current_file] = []
                file_mapping[current_file].append(
                    (current_section, current_functions)
                )
                current_functions = []
            # Save functions without section (if switching to new section).
            elif current_file and current_functions:
                if current_file not in file_mapping:
                    file_mapping[current_file] = []
                file_mapping[current_file].append(
                    ("Functions", current_functions)
                )
                current_functions = []
            # Extract section name.
            current_section = line[3:].strip()
            _LOG.debug("Found section: %s", current_section)
        # Check for bullet point (function name).
        elif line.startswith("- "):
            # If no section is set, use default.
            if current_file and not current_section:
                current_section = "Functions"
            # Extract function name (remove parentheses if present).
            func_name = line[2:].strip()
            func_name = func_name.replace("()", "")
            current_functions.append(func_name)
            _LOG.debug("Found function: %s", func_name)
    # Save last section.
    if current_file and (current_section or current_functions):
        if current_file not in file_mapping:
            file_mapping[current_file] = []
        section_name = current_section if current_section else "Functions"
        file_mapping[current_file].append((section_name, current_functions))
    _LOG.info("Parsed %d target files from map", len(file_mapping))
    return file_mapping


# #############################################################################
# Extract functions using text parsing
# #############################################################################


def _find_function_boundaries(
    lines: List[str], function_name: str, start_search_idx: int = 0
) -> Tuple[int, int]:
    """
    Find the start and end line indices for a function or class definition.

    Uses text-based parsing to locate function boundaries by finding the
    function definition and the next function or class definition at the
    same or lower indentation level.

    :param lines: list of code lines
    :param function_name: name of the function or class to find
    :param start_search_idx: line index to start searching from
    :return: tuple of (start_line_idx, end_line_idx)
    """
    _LOG.debug("Searching for function: %s", function_name)
    # Pattern to match function or class definition.
    func_pattern = re.compile(r"^(\s*)(def|class)\s+(\w+)")
    # Find the start of the target function.
    start_idx = None
    start_indent = None
    for i in range(start_search_idx, len(lines)):
        line = lines[i]
        match = func_pattern.match(line)
        if match and match.group(3) == function_name:
            start_idx = i
            start_indent = len(match.group(1))
            _LOG.debug("Found function %s at line %d", function_name, i)
            break
    hdbg.dassert_is_not(
        start_idx,
        None,
        "Function not found in input file: %s",
        function_name,
    )
    # Find the end of the function (next function/class at same or lower indent).
    end_idx = len(lines)
    for i in range(start_idx + 1, len(lines)):
        line = lines[i]
        # Skip empty lines.
        if not line.strip():
            continue
        # Check if we found another function/class at same or lower indent.
        match = func_pattern.match(line)
        if match:
            current_indent = len(match.group(1))
            if current_indent <= start_indent:
                end_idx = i
                _LOG.debug("Function %s ends at line %d", function_name, i)
                break
    return start_idx, end_idx


def _extract_functions_from_source(
    source_file_path: str,
) -> Dict[str, Tuple[int, int]]:
    """
    Extract function definitions and their line ranges from source file.

    Uses text-based parsing with regular expressions to find function
    and class definitions. Only extracts top-level functions and
    classes, not nested ones.

    :param source_file_path: path to the Python source file
    :return: dictionary mapping function names to (start_line, end_line)
        tuples
    """
    hdbg.dassert(
        os.path.exists(source_file_path),
        "Source file does not exist:",
        source_file_path,
    )
    _LOG.info("Extracting functions from: %s", source_file_path)
    # Read the source file.
    content = hio.from_file(source_file_path)
    lines = content.split("\n")
    # Pattern to match function or class definition (only top-level, no indent).
    func_pattern = re.compile(r"^(def|class)\s+(\w+)")
    # Extract all top-level function and class names first.
    function_names = []
    for i, line in enumerate(lines):
        match = func_pattern.match(line)
        if match:
            func_name = match.group(2)
            function_names.append(func_name)
            _LOG.debug("Found %s: %s at line %d", match.group(1), func_name, i)
    # Now extract boundaries for each function.
    functions: Dict[str, Tuple[int, int]] = {}
    search_idx = 0
    for func_name in function_names:
        start_line, end_line = _find_function_boundaries(
            lines, func_name, search_idx
        )
        functions[func_name] = (
            start_line + 1,
            end_line,
        )  # Convert to 1-indexed.
        search_idx = end_line
    _LOG.info("Extracted %d functions/classes from source", len(functions))
    return functions


def _find_module_header_end(lines: List[str]) -> int:
    """
    Find the end of the module header (imports and docstrings).

    The module header includes:
    - Module docstring
    - Import statements
    - Module-level constants and variables defined before first function

    :param lines: list of source file lines
    :return: line index where the module header ends
    """
    # Pattern to match function or class definition.
    func_pattern = re.compile(r"^(def|class)\s+\w+")
    # Find the first top-level function or class definition.
    first_def_line = None
    for i, line in enumerate(lines):
        # Skip lines that are indented (not top-level).
        if line and line[0] in (" ", "\t"):
            continue
        # Check if this is a function or class definition.
        if func_pattern.match(line):
            first_def_line = i
            break
    # If no functions found, return end of file.
    if first_def_line is None:
        return len(lines)
    # Look backwards from first function to skip empty lines and comments.
    header_end = first_def_line
    while header_end > 0:
        line = lines[header_end - 1].strip()
        # Stop if we find a non-empty, non-comment line.
        if line and not line.startswith("#"):
            break
        header_end -= 1
    _LOG.debug("Module header ends at line %d", header_end)
    return header_end


# #############################################################################
# Create target files
# #############################################################################


def _remove_trailing_section_headers(lines: List[str]) -> List[str]:
    """
    Remove trailing section headers and excessive blank lines from extracted
    code.

    Section headers follow the pattern:
    # #############################################################################
    # Section Name
    # #############################################################################

    :param lines: list of code lines
    :return: cleaned list of lines
    """
    if not lines:
        return lines
    # Pattern to match section header border (77 or more #).
    header_border_pattern = re.compile(r"^#\s*#{77,}\s*$")
    # Work backwards to find where actual code ends.
    end_idx = len(lines)
    i = len(lines) - 1
    while i >= 0:
        line = lines[i].rstrip()
        # Skip trailing blank lines.
        if not line:
            i -= 1
            continue
        # Check if this is a section header border.
        if header_border_pattern.match(line):
            # This might be the end of a section header block.
            # Check if we have a 3-line section header pattern.
            if i >= 2:
                line_minus_1 = lines[i - 1].strip()
                line_minus_2 = lines[i - 2].rstrip()
                # Check if lines i-2 and i are borders and i-1 is a comment.
                if (
                    header_border_pattern.match(line_minus_2)
                    and line_minus_1.startswith("#")
                    and not header_border_pattern.match(line_minus_1)
                ):
                    # Found a section header, remove it.
                    i -= 3
                    continue
        # Found non-header, non-blank line - this is the end of actual code.
        end_idx = i + 1
        break
    # Return lines up to end_idx, preserving at most 2 trailing blank lines.
    result = lines[:end_idx]
    # Add back up to 2 trailing blank lines if they existed.
    blank_count = 0
    for i in range(end_idx, len(lines)):
        if not lines[i].strip():
            blank_count += 1
            if blank_count <= 2:
                result.append(lines[i])
        else:
            break
    return result


def _create_section_comment(section_name: str) -> str:
    """
    Create a formatted section comment block.

    :param section_name: name of the section
    :return: formatted comment string
    """
    comment = f"# {'#' * 77}\n# {section_name}\n# {'#' * 77}\n"
    return comment


def _create_target_file(
    source_file_path: str,
    target_file_path: str,
    sections: List[Tuple[str, List[str]]],
    source_functions: Dict[str, Tuple[int, int]],
) -> None:
    """
    Create a target file with only the specified functions.

    :param source_file_path: path to source Python file
    :param target_file_path: path to target Python file
    :param sections: list of (section_name, function_names) tuples
    :param source_functions: dictionary mapping function names to line
        ranges
    """
    _LOG.info("Creating target file: %s", target_file_path)
    # Read source file.
    content = hio.from_file(source_file_path)
    lines = content.split("\n")
    # Find where module header ends.
    header_end = _find_module_header_end(lines)
    # Start with module header.
    output_lines: List[str] = lines[:header_end]
    # Process each section.
    for section_name, function_names in sections:
        _LOG.debug(
            "Processing section: %s with %d functions",
            section_name,
            len(function_names),
        )
        # Add blank lines before section.
        output_lines.append("")
        # Add section comment.
        output_lines.append(_create_section_comment(section_name))
        output_lines.append("")
        # Add each function.
        for func_name in function_names:
            if func_name not in source_functions:
                _LOG.warning("Function %s not found in source file", func_name)
                continue
            # Get function line range.
            start_line, end_line = source_functions[func_name]
            # Extract function code (convert to 0-indexed).
            func_lines = lines[start_line - 1 : end_line]
            # Remove trailing section headers from the original file.
            func_lines = _remove_trailing_section_headers(func_lines)
            # Add function to output.
            output_lines.extend(func_lines)
            output_lines.append("")  # Add blank line after function.
            _LOG.debug(
                "Added function %s (%d lines)", func_name, len(func_lines)
            )
    # Write output file.
    output_content = "\n".join(output_lines)
    hio.to_file(target_file_path, output_content)
    _LOG.info("Created target file with %d lines", len(output_lines))


def _reorder_python_code(*, input_file: str, map_file: str) -> None:
    """
    Reorganize Python code based on mapping file.

    :param input_file: path to source Python file
    :param map_file: path to markdown map file
    """
    _LOG.info("Starting code reorganization")
    _LOG.info("Input file: %s", input_file)
    _LOG.info("Map file: %s", map_file)
    # Step 1: Parse the map file.
    file_mapping = _parse_map_file(map_file)
    # Step 2: Extract functions from source file.
    source_functions = _extract_functions_from_source(input_file)
    # Get the directory of the input file.
    input_dir = os.path.dirname(input_file)
    # Step 3-6: Create each target file.
    for target_filename, sections in file_mapping.items():
        # Build target file path.
        target_file_path = os.path.join(input_dir, target_filename)
        _LOG.info("Processing target file: %s", target_file_path)
        # Create the target file.
        _create_target_file(
            input_file, target_file_path, sections, source_functions
        )
    _LOG.info("Code reorganization completed")


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input_file",
        action="store",
        required=True,
        help="Path to the input Python file to reorganize",
    )
    parser.add_argument(
        "--map_file",
        action="store",
        required=True,
        help="Path to the markdown map file defining the reorganization",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Reorganize the code.
    _reorder_python_code(input_file=args.input_file, map_file=args.map_file)


if __name__ == "__main__":
    _main(_parse())
