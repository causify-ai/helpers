#!/usr/bin/env python

"""
Split a file into multiple files based on tags.

Reads a file containing special tags and splits it into separate output files.
After splitting, the input file is modified to remove content between tags,
keeping only the tags themselves and any untagged content.

Tags format:
- <start_common> - Optional section copied to all output files
- <start:filename> - Start of a new file section

Features:
- Multiple chunks can use the same filename - they will be concatenated
- Can append to existing files instead of overwriting them
- Common section is prepended only once per file (first chunk)

Example:
# Split a file with tags into separate files:
> split_in_files.py --input_file input.txt

# Split with custom output directory:
> split_in_files.py --input_file input.txt --output_dir ./output

# Preview what would be done without writing files:
> split_in_files.py --input_file input.txt --dry_run

# Keep the input file unchanged after splitting:
> split_in_files.py --input_file input.txt --preserve_input

# Append to existing files instead of overwriting:
> split_in_files.py --input_file input.txt --append

# Skip content verification for faster processing:
> split_in_files.py --input_file input.txt --skip_verify

# Use multiple chunks with same filename (concatenated into one file):
# Input file:
#   <start:output.txt>
#   First chunk
#   <start:output.txt>
#   Second chunk
# Result: output.txt contains "First chunk\nSecond chunk"

Import as:

import split_in_files as splinfi
"""

import argparse
import logging
import os
import re

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

# #############################################################################


def _get_line_number(content: str, position: int) -> int:
    """
    Get line number for a character position in content.

    :param content: the file content
    :param position: character position in content
    :return: line number (1-indexed)
    """
    return content[:position].count("\n") + 1


def _parse_file_content(content: str) -> tuple:
    """
    Parse file content and extract sections based on tags.

    Supports multiple chunks for the same filename - they will be collected
    in order and can be concatenated or appended to the same file.

    :param content: the content of the input file
    :return: tuple of (common_section, sections_dict, line_ranges) where:
        - sections_dict maps filename to list of content chunks
        - line_ranges maps filename to list of (start_line, end_line) tuples
    """
    # Find all tags in the content.
    tag_pattern = r"<start(?::([^>]+)|_common)>"
    matches = list(re.finditer(tag_pattern, content))
    hdbg.dassert_lt(
        0,
        len(matches),
        "No tags found in input file. Expected tags like <start:filename> or <start_common>.",
    )
    _LOG.debug("Found %d tags in input file", len(matches))
    # Extract common section if present.
    common_section = ""
    common_line_range = None
    sections = {}
    line_ranges = {}
    start_idx = 0
    # Check if first tag is <start_common>.
    if matches:
        first_match = matches[0]
        if first_match.group(0) == "<start_common>":
            _LOG.debug("Found <start_common> section")
            # Find where common section ends.
            if len(matches) > 1:
                common_end_idx = matches[1].start()
            else:
                common_end_idx = len(content)
            # Extract common section (excluding the tag itself).
            common_section = content[first_match.end() : common_end_idx]
            # Calculate line range for common section.
            start_line = _get_line_number(content, first_match.end())
            end_line = _get_line_number(content, common_end_idx)
            common_line_range = (start_line, end_line)
            start_idx = 1
    # Extract file sections - support multiple chunks per filename.
    for i in range(start_idx, len(matches)):
        match = matches[i]
        filename = match.group(1)
        hdbg.dassert_is_not(
            filename,
            None,
            "Tag at position %s is not a valid <start:filename> tag",
            match.start(),
        )
        _LOG.debug("Processing section for file '%s'", filename)
        # Find where this section ends.
        if i + 1 < len(matches):
            section_end_idx = matches[i + 1].start()
        else:
            section_end_idx = len(content)
        # Extract section content (excluding the tag itself).
        section_content = content[match.end() : section_end_idx]
        # Calculate line range for this section.
        start_line = _get_line_number(content, match.end())
        end_line = _get_line_number(content, section_end_idx)
        # Support multiple chunks for the same filename.
        if filename not in sections:
            sections[filename] = []
            line_ranges[filename] = []
        sections[filename].append(section_content)
        line_ranges[filename].append((start_line, end_line))
    hdbg.dassert_lt(
        0,
        len(sections),
        "No file sections found. Expected at least one <start:filename> tag.",
    )
    _LOG.debug("Extracted %d unique files", len(sections))
    # Log if any files have multiple chunks.
    for filename, chunks in sections.items():
        if len(chunks) > 1:
            _LOG.info("File '%s' has %d chunks", filename, len(chunks))
    return common_section, sections, line_ranges, common_line_range


def _display_dry_run(
    *,
    line_ranges: dict,
    common_line_range: tuple,
    output_dir: str,
) -> None:
    """
    Display what would be written in dry run mode.

    :param line_ranges: dict mapping filename to list of (start_line, end_line) tuples
    :param common_line_range: tuple of (start_line, end_line) for common section
    :param output_dir: output directory path
    """
    _LOG.info("Dry run mode: showing what would be written")
    _LOG.info("Output directory: %s", output_dir)
    # Display common section if present.
    if common_line_range:
        start_line, end_line = common_line_range
        _LOG.info(
            "Common section (will be copied to all files): line_%d:line_%d",
            start_line,
            end_line,
        )
    # Display file sections.
    for filename, line_range_list in line_ranges.items():
        output_path = os.path.join(output_dir, filename)
        # Handle multiple chunks for the same file.
        for chunk_idx, (start_line, end_line) in enumerate(line_range_list):
            if len(line_range_list) > 1:
                chunk_label = f" [chunk {chunk_idx + 1}/{len(line_range_list)}]"
            else:
                chunk_label = ""
            if common_line_range:
                common_start, common_end = common_line_range
                if chunk_idx == 0:
                    _LOG.info(
                        "line_%d:line_%d + line_%d:line_%d -> %s%s",
                        common_start,
                        common_end,
                        start_line,
                        end_line,
                        output_path,
                        chunk_label,
                    )
                else:
                    _LOG.info(
                        "line_%d:line_%d -> %s%s (append)",
                        start_line,
                        end_line,
                        output_path,
                        chunk_label,
                    )
            else:
                if chunk_idx == 0:
                    _LOG.info(
                        "line_%d:line_%d -> %s%s",
                        start_line,
                        end_line,
                        output_path,
                        chunk_label,
                    )
                else:
                    _LOG.info(
                        "line_%d:line_%d -> %s%s (append)",
                        start_line,
                        end_line,
                        output_path,
                        chunk_label,
                    )


def _remove_content_from_input_file(input_file: str, content: str) -> None:
    """
    Remove content between tags from input file, keeping tags and untagged content.

    :param input_file: path to the input file
    :param content: the original file content
    """
    # Find all tags in the content.
    tag_pattern = r"<start(?::([^>]+)|_common)>"
    matches = list(re.finditer(tag_pattern, content))
    # Build new content with tags but without content between them.
    new_content_parts = []
    last_pos = 0
    for i, match in enumerate(matches):
        # Keep everything before this tag (untagged content).
        new_content_parts.append(content[last_pos : match.start()])
        # Keep the tag itself.
        new_content_parts.append(match.group(0))
        new_content_parts.append("\n")
        # Skip content until next tag or end of file.
        if i + 1 < len(matches):
            last_pos = matches[i + 1].start()
        else:
            last_pos = len(content)
    # Add any trailing untagged content.
    if last_pos < len(content):
        trailing = content[last_pos:]
        # Only add if it's not just whitespace.
        if trailing.strip():
            new_content_parts.append(trailing)
    new_content = "".join(new_content_parts)
    # Write back to input file.
    hio.to_file(input_file, new_content)
    _LOG.info(
        "Removed content from input file, keeping tags and untagged sections"
    )


def _split_file(
    input_file: str,
    *,
    output_dir: str,
    dry_run: bool,
    skip_verify: bool,
    preserve_input: bool,
    append: bool,
) -> None:
    """
    Split input file into multiple files based on tags.

    Supports multiple chunks for the same filename - chunks can be concatenated
    into a single file or appended to existing files.

    :param input_file: path to the input file
    :param output_dir: directory where output files will be written
    :param dry_run: if True, show what would be done without writing files
    :param skip_verify: if True, skip verification that all content is saved
    :param preserve_input: if True, keep input file unchanged after splitting
    :param append: if True, append to existing files instead of overwriting
    """
    hdbg.dassert(
        os.path.exists(input_file),
        "Input file does not exist:",
        input_file,
    )
    _LOG.info("Reading input file: %s", input_file)
    # Read the input file.
    content = hio.from_file(input_file)
    # Parse the content.
    common_section, sections, line_ranges, common_line_range = (
        _parse_file_content(content)
    )
    # If dry run, display what would be done and return.
    if dry_run:
        _display_dry_run(
            line_ranges=line_ranges,
            common_line_range=common_line_range,
            output_dir=output_dir,
        )
        return
    # Create output directory if it doesn't exist.
    hio.create_dir(output_dir, incremental=True)
    _LOG.info("Writing output files to: %s", output_dir)
    # Write each section to a file, handling multiple chunks per filename.
    total_files = 0
    for filename, chunk_list in sections.items():
        output_path = os.path.join(output_dir, filename)
        file_exists = os.path.exists(output_path)
        # Process each chunk for this filename.
        for chunk_idx, chunk_content in enumerate(chunk_list):
            is_first_chunk = chunk_idx == 0
            # Determine write mode.
            if is_first_chunk and not append:
                # First chunk, not in append mode: create/overwrite file.
                mode = "write"
                final_content = common_section + chunk_content
            elif is_first_chunk and append and file_exists:
                # First chunk, append mode, file exists: append to file.
                mode = "append"
                final_content = chunk_content
            elif is_first_chunk and append and not file_exists:
                # First chunk, append mode, file doesn't exist: create file.
                mode = "write"
                final_content = common_section + chunk_content
            else:
                # Subsequent chunks: always append.
                mode = "append"
                final_content = chunk_content
            # Write or append the content.
            if mode == "write":
                hio.to_file(output_path, final_content)
                action = "Created" if not file_exists else "Overwrote"
            else:
                # Append to file.
                existing_content = hio.from_file(output_path)
                hio.to_file(output_path, existing_content + final_content)
                action = "Appended to"
            # Log the action.
            if len(chunk_list) > 1:
                _LOG.info(
                    "%s file: %s [chunk %d/%d] (%d bytes)",
                    action,
                    output_path,
                    chunk_idx + 1,
                    len(chunk_list),
                    len(final_content),
                )
            else:
                _LOG.info(
                    "%s file: %s (%d bytes)",
                    action,
                    output_path,
                    len(final_content),
                )
            # Update file_exists for next iteration.
            file_exists = True
        total_files += 1
    _LOG.info("Successfully split file into %d output files", total_files)
    # Remove content from input file unless preserve_input is True.
    if not preserve_input:
        _remove_content_from_input_file(input_file, content)


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input_file",
        action="store",
        required=True,
        help="Path to input file to split",
    )
    parser.add_argument(
        "--output_dir",
        action="store",
        help="Output directory for split files (default: same as input file)",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Show what would be done without writing files",
    )
    parser.add_argument(
        "--skip_verify",
        action="store_true",
        help="Skip verification that all content is saved",
    )
    parser.add_argument(
        "--preserve_input",
        action="store_true",
        help="Keep input file unchanged (default: remove content, keep tags)",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to existing files instead of overwriting them",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Determine output directory.
    if args.output_dir:
        output_dir = args.output_dir
    else:
        # Use same directory as input file.
        output_dir = os.path.dirname(os.path.abspath(args.input_file))
    _LOG.debug("Output directory: %s", output_dir)
    # Split the file.
    _split_file(
        args.input_file,
        output_dir=output_dir,
        dry_run=args.dry_run,
        skip_verify=args.skip_verify,
        preserve_input=args.preserve_input,
        append=args.append,
    )


if __name__ == "__main__":
    _main(_parse())
