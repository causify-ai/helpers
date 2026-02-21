#!/usr/bin/env python

"""
Compare a Jupyter notebook with its paired Python file using jupytext.

Given a file (.ipynb or .py), this script:
- Finds the paired file (.py for .ipynb, .ipynb for .py)
- Reports which file is newer
- Checks if the files are in sync using jupytext --test
- Extracts Python code from the .ipynb file to a temporary file
- Prints the vimdiff command to compare the Python file and extracted code

Usage examples:
  ./jupytext_diff.py notebook.ipynb
  ./jupytext_diff.py script.py

Import as:

import dev_scripts_helpers.jupytext_diff as dscjudi
"""

import argparse
import logging
import os

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("file", help="Input file (.ipynb or .py)")
    hparser.add_verbosity_arg(parser)
    return parser


def _find_paired_file(file_path: str) -> str:
    """
    Find the paired file for the given file.

    :param file_path: Path to .ipynb or .py file
    :return: Path to paired file
    """
    hdbg.dassert(
        os.path.exists(file_path), "Input file does not exist:", file_path
    )
    if file_path.endswith(".ipynb"):
        paired_file = file_path[:-6] + ".py"
    elif file_path.endswith(".py"):
        paired_file = file_path[:-3] + ".ipynb"
    else:
        hdbg.dfatal("File must end with .ipynb or .py:", file_path)
    hdbg.dassert(
        os.path.exists(paired_file), "Paired file does not exist:", paired_file
    )
    return paired_file


def _report_newer_file(file1: str, file2: str) -> None:
    """
    Report which file is newer based on modification time.

    :param file1: First file path
    :param file2: Second file path
    """
    import datetime

    mtime1 = os.path.getmtime(file1)
    mtime2 = os.path.getmtime(file2)
    timestamp1 = datetime.datetime.fromtimestamp(mtime1).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    timestamp2 = datetime.datetime.fromtimestamp(mtime2).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    _LOG.info("File: %s - Modified: %s", file1, timestamp1)
    _LOG.info("File: %s - Modified: %s", file2, timestamp2)
    if mtime1 > mtime2:
        _LOG.info("Newer file: %s", file1)
    elif mtime2 > mtime1:
        _LOG.info("Newer file: %s", file2)
    else:
        _LOG.info("Files have the same modification time")


def _check_sync_status(ipynb_file: str) -> None:
    """
    Check if notebook and paired file are in sync using jupytext.

    Exit codes:
    - 0: Files already in sync (no diff)
    - 1: Files differ
    - 2: Error

    :param ipynb_file: Path to .ipynb file
    """
    cmd = f"jupytext --diff {ipynb_file} > /dev/null 2>&1"
    _LOG.info("Checking sync status...")
    exit_code = os.system(cmd)
    # os.system returns the exit code shifted left by 8 bits on Unix
    exit_code = exit_code >> 8
    if exit_code == 0:
        _LOG.info("Files already in sync")
    elif exit_code == 1:
        _LOG.warning("Files are NOT in sync - there are differences")
    else:
        _LOG.error("Error checking sync status (exit code: %d)", exit_code)


def _extract_python_from_notebook(ipynb_file: str) -> str:
    """
    Extract Python code from notebook to temporary file.

    :param ipynb_file: Path to .ipynb file
    :return: Path to temporary Python file
    """
    # Create temp file name.
    base_name = os.path.basename(ipynb_file)
    tmp_file = f"tmp.jupytext_diff.{base_name[:-6]}.py"
    # Extract using jupytext.
    cmd = f"jupytext --to py:percent {ipynb_file} -o {tmp_file}"
    hsystem.system(cmd)
    _LOG.info("Extracted Python code to: %s", tmp_file)
    return tmp_file


def _run_vimdiff(file1: str, file2: str) -> None:
    """
    Run vimdiff between two files.

    :param file1: First file path
    :param file2: Second file path
    """
    cmd = f"vimdiff {file1} {file2}"
    _LOG.info("To compare files, run: %s", cmd)
    os.system(cmd)


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Get input file.
    input_file = args.file
    _LOG.info("Processing file: %s", input_file)
    # Find paired file.
    paired_file = _find_paired_file(input_file)
    _LOG.info("Found paired file: %s", paired_file)
    # Report which file is newer.
    _report_newer_file(input_file, paired_file)
    # Determine which is the notebook file.
    if input_file.endswith(".ipynb"):
        ipynb_file = input_file
        py_file = paired_file
    else:
        ipynb_file = paired_file
        py_file = input_file
    # Check sync status.
    _check_sync_status(ipynb_file)
    # Extract Python from notebook.
    tmp_py_file = _extract_python_from_notebook(ipynb_file)
    # Run vimdiff.
    _LOG.info("Running vimdiff between %s and %s", py_file, tmp_py_file)
    _run_vimdiff(py_file, tmp_py_file)


if __name__ == "__main__":
    _main(_parse())
