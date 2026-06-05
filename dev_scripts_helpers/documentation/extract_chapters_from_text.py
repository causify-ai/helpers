#!/usr/bin/env python

"""
Split a markdown file into individual chapters based on level-1 headers.

Each chapter is saved to a separate file in the output directory with a
filename derived from the chapter title (with special characters removed).

Usage:
> extract_chapters_from_text.py -i book.md -o book_chapters
> extract_chapters_from_text.py -i book.md -o book_chapters --add_numbers
> extract_chapters_from_text.py -i book.md -o book_chapters --overwrite
"""

import argparse
import logging
import os
import re
import shutil
import unicodedata
from typing import Dict, List, Tuple

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


def _extract_chapters(content: str) -> List[Tuple[str, str]]:
    """
    Extract chapters from markdown content based on level-1 headers.

    Each chapter consists of a title (from the header) and its content
    (from the header until the next level-1 header or end of file).

    :param content: markdown file content
    :return: list of (chapter_title, chapter_content) tuples
    """
    chapters: List[Tuple[str, str]] = []
    # Split by level-1 headers: lines starting with "# ".
    lines = content.split("\n")
    current_chapter_title = None
    current_chapter_lines = []
    for line in lines:
        # Check if this is a level-1 header.
        if re.match(r"^# ", line):
            # Save previous chapter if it exists.
            if current_chapter_title is not None:
                chapter_content = "\n".join(current_chapter_lines)
                chapters.append((current_chapter_title, chapter_content))
            # Start new chapter.
            current_chapter_title = line[2:].strip()
            current_chapter_lines = [line]
        elif current_chapter_title is not None:
            # Add line to current chapter.
            current_chapter_lines.append(line)
    # Save final chapter.
    if current_chapter_title is not None:
        chapter_content = "\n".join(current_chapter_lines)
        chapters.append((current_chapter_title, chapter_content))
    return chapters


def _sanitize_chapter_title(title: str) -> str:
    """
    Sanitize a chapter title to create a valid filename.

    Uses `hio.purify_file_name()` to remove non-Linux friendly characters,
    then replaces spaces with underscores.

    :param title: chapter title to sanitize
    :return: sanitized filename (without extension)
    """
    hdbg.dassert_ne(
        title.strip(),
        "",
        "Chapter title cannot be empty or all spaces",
    )
    # Normalize Unicode characters: NFKD converts curly quotes, etc. to ASCII
    # equivalents, then remove any remaining non-ASCII characters.
    normalized = unicodedata.normalize("NFKD", title)
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    # Replace spaces with underscores for better readability.
    sanitized = normalized.replace(" ", "_")
    # Use purify_file_name to remove other non-friendly characters.
    sanitized = hio.purify_file_name(sanitized)
    # Remove the directory part if present (purify_file_name returns basename).
    sanitized = os.path.basename(sanitized)
    return sanitized


def _validate_chapters(chapters: List[Tuple[str, str]]) -> None:
    """
    Validate that chapters have valid titles and unique filenames.

    Ensures:
    - No empty chapter titles or titles with only whitespace
    - All chapters have unique sanitized filenames

    :param chapters: list of (chapter_title, chapter_content) tuples
    """
    if not chapters:
        return
    # Validate chapter titles and collect sanitized names.
    sanitized_names: Dict[str, str] = {}
    for chapter_title, _ in chapters:
        hdbg.dassert_ne(
            chapter_title.strip(),
            "",
            "Chapter title cannot be empty or all spaces",
        )
        sanitized_name = _sanitize_chapter_title(chapter_title)
        # Check for duplicates.
        if sanitized_name in sanitized_names:
            raise ValueError(
                f"Duplicate chapter filename after sanitization: '{sanitized_name}' "
                f"(from titles '{chapter_title}' and '{sanitized_names[sanitized_name]}')"
            )
        sanitized_names[sanitized_name] = chapter_title


def _check_output_files_exist(
    chapters: List[Tuple[str, str]],
    output_dir: str,
    add_numbers: bool,
) -> bool:
    """
    Check if any output files already exist.

    :param chapters: list of chapters
    :param output_dir: output directory path
    :param add_numbers: whether chapter numbers are being added
    :return: True if any output files exist, False otherwise
    """
    for idx, (chapter_title, _) in enumerate(chapters):
        sanitized_name = _sanitize_chapter_title(chapter_title)
        # Construct filename with optional numbering.
        if add_numbers:
            filename = f"{idx + 1}_{sanitized_name}.md"
        else:
            filename = f"{sanitized_name}.md"
        output_file = os.path.join(output_dir, filename)
        if os.path.exists(output_file):
            return True
    return False


def _write_chapters(
    chapters: List[Tuple[str, str]],
    output_dir: str,
    add_numbers: bool,
) -> None:
    """
    Write chapters to separate files in the output directory.

    :param chapters: list of (chapter_title, chapter_content) tuples
    :param output_dir: output directory path
    :param add_numbers: whether to add chapter numbers to filenames
    """
    _LOG.info("Writing %d chapters to %s", len(chapters), output_dir)
    hio.create_dir(output_dir, incremental=True)
    for idx, (chapter_title, chapter_content) in enumerate(chapters):
        sanitized_name = _sanitize_chapter_title(chapter_title)
        # Construct filename with optional numbering.
        if add_numbers:
            filename = f"{idx + 1}_{sanitized_name}.md"
        else:
            filename = f"{sanitized_name}.md"
        output_file = os.path.join(output_dir, filename)
        _LOG.info("Writing chapter %d: %s", idx + 1, filename)
        hio.to_file(output_file, chapter_content)
    _LOG.info("All chapters written successfully")


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments.

    :return: configured argument parser
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input",
        "-i",
        action="store",
        required=True,
        type=str,
        help="Input markdown file containing chapters",
    )
    parser.add_argument(
        "--output",
        "-o",
        action="store",
        required=True,
        type=str,
        help="Output directory where chapter files will be saved",
    )
    parser.add_argument(
        "--add_numbers",
        action="store_true",
        help="Add chapter numbers as prefix to filenames (e.g., 1_Chapter_Name.md)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Delete existing chapter files if they already exist",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main function to split markdown file into chapters.

    :param parser: argument parser with user inputs
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Validate input file exists.
    input_file = args.input
    hdbg.dassert_file_exists(input_file, "Input file does not exist")
    _LOG.info("Reading input file: %s", input_file)
    # Read input content.
    content = hio.from_file(input_file)
    # Extract chapters from markdown.
    chapters = _extract_chapters(content)
    _LOG.info("Extracted %d chapters from input file", len(chapters))
    hdbg.dassert_lt(
        0,
        len(chapters),
        "No chapters found in input file (no level-1 headers starting with '# ')",
    )
    # Validate chapters.
    _validate_chapters(chapters)
    output_dir = args.output
    # Check for existing output files.
    files_exist = _check_output_files_exist(
        chapters, output_dir, args.add_numbers
    )
    if files_exist and not args.overwrite:
        raise ValueError(
            f"Output directory already contains chapter files: {output_dir} "
            "(use --overwrite to replace)"
        )
    if files_exist and args.overwrite:
        _LOG.info("Removing existing chapter files in %s", output_dir)
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
    # Write chapters to output directory.
    _write_chapters(chapters, output_dir, args.add_numbers)


if __name__ == "__main__":
    _main(_parse())
