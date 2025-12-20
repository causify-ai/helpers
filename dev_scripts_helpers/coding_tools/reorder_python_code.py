#!/usr/bin/env python

"""
Reorganize functions from a monolithic Python file into multiple smaller files
based on a markdown mapping file.

The script parses a markdown map file that organizes functions by category and
creates separate Python files for each category, copying only the relevant
functions from the source file.

Example usage:
    python reorder_python_code.py \\
        --input_file helpers/hpandas.py \\
        --map_file hpandas_map.md

Import as:

import dev_scripts_helpers.coding_tools.reorder_python_code as dscctoreco
"""

import argparse
import ast
import logging
import os
import re
from typing import Dict, List, Tuple

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


# #############################################################################
# Helper functions
# #############################################################################


def _parse_map_file(map_file_path: str) -> Dict[str, List[Tuple[str, List[str]]]]:
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
    hdbg.dassert(os.path.exists(map_file_path), "Map file does not exist: %s", map_file_path)
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
                file_mapping[current_file].append((current_section, current_functions))
                current_functions = []
            # Save functions without section (if file has no section headers).
            elif current_file and current_functions:
                if current_file not in file_mapping:
                    file_mapping[current_file] = []
                # Use filename as default section name.
                file_mapping[current_file].append(("Functions", current_functions))
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
                file_mapping[current_file].append((current_section, current_functions))
                current_functions = []
            # Save functions without section (if switching to new section).
            elif current_file and current_functions:
                if current_file not in file_mapping:
                    file_mapping[current_file] = []
                file_mapping[current_file].append(("Functions", current_functions))
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


def _extract_functions_from_source(
    source_file_path: str,
) -> Dict[str, Tuple[int, int]]:
    """
    Extract function definitions and their line ranges from source file.

    :param source_file_path: path to the Python source file
    :return: dictionary mapping function names to (start_line, end_line) tuples
    """
    hdbg.dassert(os.path.exists(source_file_path), "Source file does not exist: %s", source_file_path)
    _LOG.info("Extracting functions from: %s", source_file_path)
    # Read and parse the source file.
    content = hio.from_file(source_file_path)
    tree = ast.parse(content)
    # Extract function definitions.
    functions: Dict[str, Tuple[int, int]] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Get function name and line numbers.
            func_name = node.name
            start_line = node.lineno
            # Find end line by looking at the last statement.
            end_line = node.end_lineno
            functions[func_name] = (start_line, end_line)
            _LOG.debug("Found function %s at lines %d-%d", func_name, start_line, end_line)
        # Also handle class definitions to capture class methods.
        elif isinstance(node, ast.ClassDef):
            class_name = node.name
            start_line = node.lineno
            end_line = node.end_lineno
            functions[class_name] = (start_line, end_line)
            _LOG.debug("Found class %s at lines %d-%d", class_name, start_line, end_line)
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
    # Parse the source to find where functions start.
    content = "\n".join(lines)
    tree = ast.parse(content)
    # Find the first top-level function or class definition.
    # We only look at module.body to get top-level definitions, not nested ones.
    first_def_line = float("inf")
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.lineno < first_def_line:
                first_def_line = node.lineno
    # If no functions found, return end of file.
    if first_def_line == float("inf"):
        return len(lines)
    # Look backwards from first function to find last import or constant.
    header_end = first_def_line - 1
    # Check if there are section comments just before the first function.
    while header_end > 0:
        line = lines[header_end - 1].strip()
        # Stop if we find a non-empty, non-comment line.
        if line and not line.startswith("#"):
            break
        header_end -= 1
    _LOG.debug("Module header ends at line %d", header_end)
    return header_end


def _create_section_comment(section_name: str) -> str:
    """
    Create a formatted section comment block.

    :param section_name: name of the section
    :return: formatted comment string
    """
    comment = f"\n\n# {'#' * 77}\n# {section_name}\n# {'#' * 77}\n\n"
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
    :param source_functions: dictionary mapping function names to line ranges
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
        _LOG.debug("Processing section: %s with %d functions", section_name, len(function_names))
        # Add section comment.
        output_lines.append(_create_section_comment(section_name))
        # Add each function.
        for func_name in function_names:
            if func_name not in source_functions:
                _LOG.warning("Function %s not found in source file", func_name)
                continue
            # Get function line range.
            start_line, end_line = source_functions[func_name]
            # Extract function code (convert to 0-indexed).
            func_lines = lines[start_line - 1 : end_line]
            # Add function to output.
            output_lines.extend(func_lines)
            output_lines.append("")  # Add blank line after function.
            _LOG.debug("Added function %s (%d lines)", func_name, len(func_lines))
    # Write output file.
    output_content = "\n".join(output_lines)
    hio.to_file(target_file_path, output_content)
    _LOG.info("Created target file with %d lines", len(output_lines))


def _reorder_python_code(input_file: str, map_file: str) -> None:
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
    # Step 3 & 4: Create each target file.
    for target_filename, sections in file_mapping.items():
        # Build target file path.
        target_file_path = os.path.join(input_dir, target_filename)
        _LOG.info("Processing target file: %s", target_file_path)
        # Create the target file.
        _create_target_file(input_file, target_file_path, sections, source_functions)
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
    _reorder_python_code(args.input_file, args.map_file)


if __name__ == "__main__":
    _main(_parse())
