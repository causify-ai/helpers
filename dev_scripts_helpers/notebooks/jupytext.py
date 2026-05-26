#!/usr/bin/env python

"""
Automate some common workflows with jupytext.

# Pair
> jupytext.py --action pair --files <notebook.ipynb> [<notebook2.ipynb> ...]
> jupytext.py --action pair --all
> jupytext.py --action pair --modified
> jupytext.py --action pair --branch

# Test
> jupytext.py --action test --files <notebook.{py,ipynb}> [<notebook2.{py,ipynb}> ...]
> jupytext.py --action test --all
> jupytext.py --action test --modified

# Sync
> jupytext.py --action sync --files <notebook.{py,ipynb}> [<notebook2.{py,ipynb}> ...]
> jupytext.py --action sync --all
> jupytext.py --action sync --modified

# Diff (compare notebook with paired Python file using vimdiff)
> jupytext.py --action diff --files <notebook.{py,ipynb}> [<notebook2.{py,ipynb}> ...]

Import as:

import dev_scripts_helpers.notebooks.jupytext as dshnprju
"""

import argparse
import datetime
import logging
import os
import re
import sys
from typing import Tuple

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hsystem as hsystem
import linters.utils as liutils

_LOG = logging.getLogger(__name__)

# #############################################################################
# Pair
# #############################################################################

def _pair(file_name: str) -> None:
    """
    Create a paired Python file for an ipynb notebook using jupytext.

    :param file_name: Path to .ipynb file to pair
    """
    hdbg.dassert(
        liutils.is_ipynb_file(file_name),
        "'%s' has no .ipynb extension",
        file_name,
    )
    if liutils.is_paired_jupytext_file(file_name):
        _LOG.warning("The file '%s' seems already paired", file_name)
    # Create a paired Python file for the notebook to enable editing in IDE.
    msg = f"There was no paired notebook for '{file_name}': created and added to git"
    _LOG.warning(msg)
    # Configure jupytext metadata to use ipynb and py:percent formats.
    cmd = []
    cmd.append("jupytext")
    cmd.append("--update-metadata")
    cmd.append("""'{"jupytext":{"formats":"ipynb,py:percent"}}'""")
    cmd.append(file_name)
    cmd = " ".join(cmd)
    _LOG.info("Execute '%s'", cmd)
    hsystem.system(cmd)
    # Validate the round-trip conversion: ipynb -> py:percent -> ipynb.
    cmd = "jupytext" + f" --test --stop --to py:percent {file_name}"
    _LOG.info("Execute '%s'", cmd)
    hsystem.system(cmd)
    # Generate the paired Python file in py:percent format.
    cmd = "jupytext" + f" --to py:percent {file_name}"
    _LOG.info("Execute '%s'", cmd)
    hsystem.system(cmd)
    # Track the paired Python file in git for version control.
    py_file_name = liutils.from_ipynb_to_python_file(file_name)
    cmd = f"git add {py_file_name}"
    _LOG.info("Execute '%s'", cmd)
    hsystem.system(cmd)

# #############################################################################
# Sync
# #############################################################################

def _sync(file_name: str) -> None:
    """
    Synchronize paired .ipynb and .py files to keep them in sync.

    :param file_name: Path to .ipynb or .py file to synchronize
    """
    if liutils.is_paired_jupytext_file(file_name):
        if liutils.is_py_file(file_name):
            # Jupytext's `--sync` alone doesn't persist changes to `.ipynb` due to
            # automatic notebook metadata serialization; use `--update` to force
            # autosave the `.ipynb` file with changes from the paired `.py` file.
            cmd_update = "jupytext" + f" --to ipynb --update {file_name}"
        else:
            cmd_update = "jupytext" + f" --to py {file_name}"
        _LOG.info("Execute '%s'", cmd_update)
        hsystem.system(cmd_update)
        cmd_sync = "jupytext" + f" --sync {file_name}"
        _LOG.info("Execute '%s'", cmd_sync)
        hsystem.system(cmd_sync)
    else:
        _LOG.warning("The file '%s' is not paired: run --pair", file_name)

# #############################################################################
# Test
# #############################################################################

def _is_jupytext_version_different(output_txt: str) -> bool:
    """
    Return True if there is a difference in jupytext_version.

    Workaround for https://github.com/mwouts/jupytext/issues/414 to avoid
    report an error due to jupytext version mismatch.

    [jupytext] Reading nlp/notebooks/PTask1081_RP_small_test.py
    nlp/notebooks/PTask1081_RP_small_test.py:
    --- expected
    +++ actual
    @@ -5,7 +5,7 @@
     #       extension: .py
     #       format_name: percent
     #       format_version: '1.3'
    -#       jupytext_version: 1.3.3
    +#       jupytext_version: 1.3.0
     #   kernelspec:
     #     display_name: Python [conda env:.conda-amp_develop] *
     #     language: python
    """
    ret = False
    regex = r"jupytext_version: \d.*"
    m = re.findall(regex, output_txt, re.MULTILINE)
    _LOG.debug("Regex search result: %s", m)
    if m:
        if len(m) == 2:
            ret = True
            _LOG.warning(
                "There is a mismatch of jupytext version: '%s' vs '%s': skipping",
                m[0],
                m[1],
            )
    return ret


def _test(file_name: str, action: str) -> bool:
    """
    Test if notebook and paired Python file are in sync.

    :param file_name: Path to .ipynb or .py file to test
    :param action: Action type (not currently used)
    :return: True if files are in sync, False otherwise
    """
    if liutils.is_ipynb_file(file_name):
        ipynb_file = file_name
    else:
        ipynb_file = liutils.from_python_to_ipynb_file(file_name)
    in_sync, _ = _is_notebook_in_sync(ipynb_file)
    if not in_sync:
        _LOG.warning(
            "Notebook '%s' and paired .py file are NOT in sync",
            ipynb_file,
        )
    return in_sync


# #############################################################################
# Diff
# #############################################################################


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
        # Unreachable, but needed for type checker.
        paired_file = ""
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


def _is_notebook_in_sync(ipynb_file: str) -> Tuple[bool, str]:
    """
    Check if notebook and paired Python file are in sync.

    Extracts Python from the notebook and compares with the paired Python file
    using `diff`.

    :param ipynb_file: Path to .ipynb file
    :return: Tuple of (is_in_sync, tmp_py_file_path)
        - is_in_sync: True if files are identical, False if they differ
        - tmp_py_file_path: Path to the temporary Python file extracted from notebook
    """
    _LOG.info("Checking sync status...")
    paired_py_file = _find_paired_file(ipynb_file)
    tmp_py_file = _extract_python_from_notebook(ipynb_file)
    cmd = f"diff {paired_py_file} {tmp_py_file}"
    _LOG.info("Execute '%s'", cmd)
    rc, _ = hsystem.system_to_string(cmd, abort_on_error=False)
    in_sync = rc == 0
    if in_sync:
        _LOG.info("Files are in sync")
    else:
        _LOG.warning("Files are NOT in sync - there are differences")
    return in_sync, tmp_py_file


def _extract_python_from_notebook(ipynb_file: str) -> str:
    """
    Extract Python code from notebook to temporary file.

    :param ipynb_file: Path to .ipynb file
    :return: Path to temporary Python file
    """
    # Generate a descriptive temp file name to aid debugging.
    base_name = os.path.basename(ipynb_file)
    tmp_file = f"tmp.jupytext_diff.{base_name[:-6]}.py"
    # Convert notebook to py:percent format for comparison with paired .py file.
    cmd = f"jupytext --to py:percent {ipynb_file} -o {tmp_file}"
    _LOG.info("Execute '%s'", cmd)
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
    _LOG.info("Execute '%s'", cmd)
    os.system(cmd)


def _diff(file_name: str) -> None:
    """
    Compare a notebook with its paired Python file using vimdiff.

    :param file_name: Path to .ipynb or .py file
    """
    _LOG.info("Processing file: %s", file_name)
    paired_file = _find_paired_file(file_name)
    _LOG.info("Found paired file: %s", paired_file)
    _report_newer_file(file_name, paired_file)
    if file_name.endswith(".ipynb"):
        ipynb_file = file_name
        py_file = paired_file
    else:
        ipynb_file = paired_file
        py_file = file_name
    _, tmp_py_file = _is_notebook_in_sync(ipynb_file)
    _LOG.info("Running vimdiff between %s and %s", py_file, tmp_py_file)
    _run_vimdiff(py_file, tmp_py_file)


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments for jupytext operations.

    :return: Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--action",
        action="store",
        choices=["pair", "test", "sync", "diff"],
        required=True,
        help="Action to perform",
    )
    hparser.add_file_selection_args(parser)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main entry point for jupytext automation script.

    :param parser: Argument parser with parsed command-line arguments
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level)
    files = hparser.parse_file_selection_args(args)
    hdbg.dassert(
        len(files) > 0,
        "No files selected; use --all, --files, --modified, --branch, --last_commit, or --from_file",
    )
    rc = 0
    for file_name in files:
        _LOG.info("Processing file: %s", file_name)
        hdbg.dassert_path_exists(file_name)
        if args.action == "pair":
            _pair(file_name)
        elif args.action == "sync":
            _sync(file_name)
        elif args.action in ("test", "test_strict"):
            if not _test(file_name, args.action):
                rc = 1
        elif args.action == "diff":
            _diff(file_name)
        else:
            raise ValueError(f"Invalid action '{args.action}'")
    sys.exit(rc)


if __name__ == "__main__":
    _main(_parse())
