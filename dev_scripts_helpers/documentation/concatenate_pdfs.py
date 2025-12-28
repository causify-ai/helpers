#!/usr/bin/env -S uv run --script

"""
Concatenate multiple PDF files into a single PDF file.

The script takes a list of PDF files (or glob patterns) and merges them
into a single output PDF file. Files are sorted alphabetically before
concatenation.

Usage examples:

# Concatenate all PDF files in current directory.
> concatenate_pdfs.py --input_files "*.pdf" --output_file combined.pdf

# Concatenate specific lesson PDFs in sorted order.
> concatenate_pdfs.py --input_files "data605/book/Lesson*.pdf" --output_file data605_lessons.pdf

# Dry run to see which files will be concatenated.
> concatenate_pdfs.py --input_files "*.pdf" --output_file combined.pdf --dry_run

# Concatenate specific files.
> concatenate_pdfs.py --input_files "file1.pdf file2.pdf file3.pdf" --output_file output.pdf

Import as:

import dev_scripts_helpers.documentation.concatenate_pdfs as dsdocopr
"""

# /// script
# dependencies = ["pypdf", "pyyaml"]
# ///

import argparse
import glob
import logging
from pathlib import Path
from typing import List

from pypdf import PdfWriter

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

# #############################################################################


def _expand_and_sort_files(input_files: str) -> List[str]:
    """
    Expand glob patterns and sort the resulting file list.

    :param input_files: Space-separated list of file paths or glob patterns
    :return: Sorted list of resolved file paths
    """
    _LOG.debug("Expanding input files: '%s'", input_files)
    # Split the input string into individual patterns.
    patterns = input_files.split()
    # Expand each pattern and collect all matching files.
    all_files = []
    for pattern in patterns:
        matched_files = glob.glob(pattern)
        if not matched_files:
            _LOG.warning("Pattern '%s' matched no files", pattern)
        else:
            _LOG.debug("Pattern '%s' matched %d files", pattern, len(matched_files))
        all_files.extend(matched_files)
    # Remove duplicates while preserving order, then sort.
    unique_files = list(dict.fromkeys(all_files))
    sorted_files = sorted(unique_files)
    _LOG.info("Found %d files to process", len(sorted_files))
    return sorted_files


def _validate_pdf_files(files: List[str]) -> None:
    """
    Validate that all files exist and are PDF files.

    :param files: List of file paths to validate
    """
    hdbg.dassert_lt(0, len(files), "No files to concatenate")
    for file_path in files:
        hdbg.dassert(
            Path(file_path).exists(),
            "File does not exist: %s",
            file_path,
        )
        hdbg.dassert(
            file_path.lower().endswith(".pdf"),
            "File is not a PDF: %s",
            file_path,
        )


def _concatenate_pdfs(
    input_files: List[str],
    *,
    output_file: str,
    dry_run: bool,
) -> None:
    """
    Concatenate multiple PDF files into a single PDF.

    :param input_files: List of PDF file paths to concatenate
    :param output_file: Path to the output PDF file
    :param dry_run: If True, only print which files would be concatenated
    """
    _LOG.info("Starting PDF concatenation")
    # Validate input files.
    _validate_pdf_files(input_files)
    # Report what will be done.
    _LOG.info("Files to concatenate (%d total):", len(input_files))
    for idx, file_path in enumerate(input_files, 1):
        file_size = Path(file_path).stat().st_size
        _LOG.info("  %d. %s (%d bytes)", idx, file_path, file_size)
    _LOG.info("Output file: %s", output_file)
    # If dry run, stop here.
    if dry_run:
        _LOG.info("Dry run mode: no files will be concatenated")
        return
    # Create output directory if it doesn't exist.
    output_path = Path(output_file)
    if output_path.parent != Path("."):
        hio.create_dir(str(output_path.parent), incremental=True)
    # Merge PDFs.
    _LOG.info("Merging PDF files...")
    writer = PdfWriter()
    for file_path in input_files:
        _LOG.debug("Adding file: %s", file_path)
        writer.append(file_path)
    # Write the output file.
    _LOG.info("Writing output file: %s", output_file)
    with open(output_file, "wb") as output_stream:
        writer.write(output_stream)
    # Report success.
    output_size = Path(output_file).stat().st_size
    total_pages = len(writer.pages)
    _LOG.info(
        "Successfully created %s (%d bytes, %d files, %d pages)",
        output_file,
        output_size,
        len(input_files),
        total_pages,
    )


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input_files",
        action="store",
        required=True,
        help="Space-separated list of input PDF files or glob patterns (e.g., '*.pdf' or 'Lesson*.pdf')",
    )
    parser.add_argument(
        "--output_file",
        action="store",
        required=True,
        help="Path to the output PDF file",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Print which files will be concatenated without actually doing it",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Expand and sort input files.
    input_files = _expand_and_sort_files(args.input_files)
    # Concatenate PDFs.
    _concatenate_pdfs(
        input_files,
        output_file=args.output_file,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    _main(_parse())
