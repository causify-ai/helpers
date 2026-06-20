#!/usr/bin/env python

"""
Standardize book filenames to a consistent format.

> standardize_book_filename.py --input INPUT_FILE [--mv]
"""

import argparse
import logging
import os
import shutil

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hprint as hprint
import dev_scripts_helpers.documentation.documentation_utils as dshddout

_LOG = logging.getLogger(__name__)


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        type=str,
        help="File path to rename",
    )
    parser.add_argument(
        "--mv",
        action="store_true",
        help="Execute the move; without this flag only shows what would be renamed (dry run)",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main function to standardize book filenames.
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    input_file = args.input
    _LOG.info("Processing file: %s", input_file)
    hdbg.dassert_file_exists(input_file, "Input file does not exist")
    # Get the directory and filename.
    dir_path = os.path.dirname(input_file)
    if not dir_path:
        dir_path = "."
    filename = os.path.basename(input_file)
    # Standardize the filename.
    standardized = dshddout.standardize_book_filename(filename)
    output_file = os.path.join(dir_path, standardized)
    # Print the rename operation.
    print(hprint.frame("Rename"))
    print(f"Dir   : {dir_path}")
    print(f"Before: {filename}")
    print(f"After : {standardized}")
    # Rename the file if --mv is specified.
    if args.mv:
        _LOG.info("Renaming: %s -> %s", input_file, output_file)
        shutil.move(input_file, output_file)
    else:
        _LOG.info("Dry run: would rename %s -> %s", input_file, output_file)


if __name__ == "__main__":
    parser = _parse()
    _main(parser)
