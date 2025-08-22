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

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hmkdocs as hmkdocs
import helpers.hparser as hparser
import helpers.hsystem as hsystem

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
        os.path.exists(input_dir),
        f"Input directory '{input_dir}' does not exist",
    )
    # Remove output directory if it exists and create fresh one.
    if os.path.exists(output_dir):
        cmd = f"rm -rf {output_dir}/*"
        hsystem.system(cmd)
    else:
        cmd = f"mkdir {output_dir}"
        hsystem.system(cmd)
    # Copy the entire directory tree.
    cmd = f"cp -r {input_dir}/* {output_dir}"
    hsystem.system(cmd)
    _LOG.info(f"Copied directory from '{input_dir}' to '{output_dir}'")


def _process_markdown_files(directory: str) -> None:
    """
    Process all markdown files in the given directory recursively.

    :param directory: Directory to process
    """
    directories = sorted(os.walk(directory))
    _LOG.info(f"Processing {len(directories)} markdown files")
    for root, dirs, files in directories:
        _ = dirs
        files = sorted(files)
        _LOG.info(f"Processing {len(files)} markdown files in '{root}'")
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                _LOG.info(f"Processing markdown file: {file_path}")
                # Read the file.
                content = hio.from_file(file_path)
                # Apply preprocessing.
                processed_content = hmkdocs.preprocess_mkdocs_markdown(content)
                # Write back to the same file.
                hio.to_file(file_path, processed_content)
                _LOG.debug(f"Successfully processed: {file_path}")


def _copy_assets_and_styles(input_dir: str, output_dir: str) -> None:
    """
    Copy assets and styles from the input directory to the output directory.
    """
    # Find the assets and styles directories.
    mkdocs_html_dir = os.path.join(input_dir, "mkdocs_html")
    hdbg.dassert_dir_exists(mkdocs_html_dir)
    cmd = f"cp -r {mkdocs_html_dir}/* {output_dir}"
    hsystem.system(cmd)
    # Copy the mkdocs.yml file.
    mkdocs_yml_file = os.path.join(input_dir, "mkdocs.yml")
    hdbg.dassert_file_exists(mkdocs_yml_file)
    cmd = f"cp {mkdocs_yml_file} {output_dir}"
    hsystem.system(cmd)


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    input_dir = args.input_dir
    output_dir = args.output_dir
    # If the output directory is a subdirectory of the input directory, then
    # we process the files in the output directory from previous runs.
    hdbg.dassert(
        not hio.is_subdir(output_dir, input_dir),
            "Output directory '%s' can't be a subdirectory of input directory '%s'",
            output_dir,
            input_dir,
        )
    # TODO(ai): Do not f-string.
    _LOG.info(
        f"Starting mkdocs preprocessing from '{input_dir}' to '{output_dir}'"
    )
    # Copy all files from input to output directory.
    _copy_directory(input_dir, output_dir)
    # Process markdown files in place in the output directory.
    _process_markdown_files(output_dir)
    # Copy assets and styles.
    #_copy_assets_and_styles(input_dir, output_dir)
    _LOG.info("Mkdocs preprocessing completed successfully")


if __name__ == "__main__":
    _main(_parse())
