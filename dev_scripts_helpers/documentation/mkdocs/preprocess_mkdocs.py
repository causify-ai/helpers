#!/usr/bin/env python

"""
Preprocess markdown files for mkdocs.

This script takes markdown files from an input directory and processes them
for mkdocs by:
1. Copying all files from input to output directory
2. Running a series of markdown transformations
    - Removing table of contents between <!-- toc --> and <!-- tocstop -->
    - Dedenting Python code blocks so they are aligned
    - Replacing 2 spaces indentation with 4 spaces

Example usage:
> preprocess_mkdocs.py --input_dir docs --output_dir tmp.mkdocs

Import as:

import preprocess_mkdocs as premkdo
"""

import argparse
import logging
import os
import shutil

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hmkdocs as hmkdocs
import helpers.hgit as hgit
import helpers.hsystem as hsystem
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input_dir",
        action="store",
        required=True,
        help="Input directory containing markdown files",
    )
    parser.add_argument(
        "--output_dir",
        action="store",
        required=True,
        help="Output directory for processed files",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _copy_directory(input_dir: str, output_dir: str) -> None:
    """
    Copy all files from input directory to output directory.

    :param input_dir: Source directory path
    :param output_dir: Destination directory path
    """
    # TODO(ai): Use dassert_dir_exists().
    hdbg.dassert(
        os.path.exists(input_dir), f"Input directory '{input_dir}' does not exist"
    )
    # Remove output directory if it exists and create fresh one.
    if os.path.exists(output_dir):
        hio.safe_rm_file(output_dir)
    # Copy the entire directory tree.
    # TODO(ai): Use hsystem("cp -r ...")
    shutil.copytree(input_dir, output_dir)
    _LOG.info(f"Copied directory from '{input_dir}' to '{output_dir}'")


def _process_markdown_files(directory: str) -> None:
    """
    Process all markdown files in the given directory recursively.

    :param directory: Directory to process
    """
    for root, dirs, files in os.walk(directory):
        _ = dirs
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                _LOG.info(f"Processing markdown file: {file_path}")
                # Read the file.
                content = hio.from_file(file_path)
                # Apply preprocessing
                processed_content = hmkdocs.preprocess_mkdocs_markdown(content)
                # Write back to the same file
                hio.to_file(file_path, processed_content)
                _LOG.debug(f"Successfully processed: {file_path}")


def _copy_assets_and_styles(directory: str) -> None:
    """
    Copy assets and styles from the input directory to the output directory.
    """
    # Find the assets and styles directories.
    mkdocs_html_dir = hgit.find_file("mkdocs_html")
    cmd = f"cp -r {mkdocs_html_dir}/* {directory}"
    hsystem.system(cmd)


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    input_dir = args.input_dir
    output_dir = args.output_dir
    _LOG.info(
        f"Starting mkdocs preprocessing from '{input_dir}' to '{output_dir}'"
    )
    # Copy all files from input to output directory.
    _copy_directory(input_dir, output_dir)
    # Process markdown files in place in the output directory.
    _process_markdown_files(output_dir)
    # Copy assets and styles.
    _copy_assets_and_styles(output_dir)
    _LOG.info("Mkdocs preprocessing completed successfully")


if __name__ == "__main__":
    _main(_parse())
