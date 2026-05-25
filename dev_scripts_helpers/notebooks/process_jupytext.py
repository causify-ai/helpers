#!/usr/bin/env python

"""
Automate some common workflows with jupytext.

> find . -name "*.ipynb" | grep -v ipynb_checkpoints | head -3 | xargs -t -L 1 process_jupytext.py --action sync --file

# Pair
> process_jupytext.py -f vendors/kibot/data_exploratory_analysis.ipynb --action pair

# Test
> process_jupytext.py -f vendors/kibot/data_exploratory_analysis.ipynb --action test
> process_jupytext.py -f vendors/kibot/data_exploratory_analysis.ipynb --action test_strict

# Sync
> process_jupytext.py -f vendors/kibot/data_exploratory_analysis.ipynb --action sync

# Diff (compare notebook with paired Python file using vimdiff)
> process_jupytext.py -f vendors/kibot/data_exploratory_analysis.ipynb --action diff
> process_jupytext.py -f vendors/kibot/data_exploratory_analysis.py --action diff

Import as:

import dev_scripts_helpers.notebooks.process_jupytext as dshnprju
"""

import argparse
import datetime
import logging
import os
import re

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hsystem as hsystem
import linters.utils as liutils

_LOG = logging.getLogger(__name__)

# #############################################################################

_EXECUTABLE = "jupytext"


def _pair(file_name: str) -> None:
    hdbg.dassert(
        liutils.is_ipynb_file(file_name),
        "'%s' has no .ipynb extension",
        file_name,
    )
    if liutils.is_paired_jupytext_file(file_name):
        _LOG.warning("The file '%s' seems already paired", file_name)
    # It is a ipynb and it is unpaired: create the python file.
    msg = f"There was no paired notebook for '{file_name}': created and added to git"
    _LOG.warning(msg)
    # Convert a notebook into jupytext.
    cmd = []
    cmd.append(_EXECUTABLE)
    cmd.append("--update-metadata")
    cmd.append("""'{"jupytext":{"formats":"ipynb,py:percent"}}'""")
    cmd.append(file_name)
    cmd = " ".join(cmd)
    hsystem.system(cmd)
    # Test the ipynb -> py:percent -> ipynb round trip conversion.
    cmd = _EXECUTABLE + f" --test --stop --to py:percent {file_name}"
    hsystem.system(cmd)
    # Add the .py file.
    cmd = _EXECUTABLE + f" --to py:percent {file_name}"
    hsystem.system(cmd)
    # Add to git.
    py_file_name = liutils.from_ipynb_to_python_file(file_name)
    cmd = f"git add {py_file_name}"
    hsystem.system(cmd)


def _sync(file_name: str) -> None:
    if liutils.is_paired_jupytext_file(file_name):
        if liutils.is_py_file(file_name):
            # Based on the `jupytext` documentation, the `--sync` command should be
            # enough to update the `.ipynb` file based on the updated paired `.py`
            # file. But for some reason these changes are not saved automatically
            # and have to be followed up by manually opening the notebook in Jupyter
            # and saving it. For this reason, we force updating and autosaving the
            # files with `--update`.
            cmd_update = _EXECUTABLE + f" --to ipynb --update {file_name}"
        else:
            cmd_update = _EXECUTABLE + f" --to py {file_name}"
        hsystem.system(cmd_update)
        cmd_sync = _EXECUTABLE + f" --sync {file_name}"
        hsystem.system(cmd_sync)
    else:
        _LOG.warning("The file '%s' is not paired: run --pair", file_name)


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


def _test(file_name: str, action: str) -> None:
    if action == "test":
        opts = "--test"
    elif action == "test_strict":
        opts = "--test-strict"
    else:
        raise ValueError(f"Invalid action='{action}'")
    cmd = [_EXECUTABLE, opts, f"--stop --to py:percent {file_name}"]
    cmd = " ".join(cmd)
    _LOG.debug("cmd=%s", cmd)
    rc, txt = hsystem.system_to_string(cmd, abort_on_error=False)
    if rc != 0:
        # Here we handle special cases that must be escaped.
        _LOG.debug("rc=%s, txt=\n'%s'", rc, txt)
        if _is_jupytext_version_different(txt):
            _LOG.warning(
                "'%s': PASSED (with jupytext version mismatch, which is ignored)",
                file_name,
            )
        else:
            _LOG.error("'%s': FAILED", file_name)
            raise RuntimeError(txt)
    else:
        _LOG.info("'%s': PASSED", file_name)


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
    _LOG.info("%s", cmd)
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


def _diff(file_name: str) -> None:
    """
    Compare a notebook with its paired Python file using vimdiff.

    :param file_name: Path to .ipynb or .py file
    """
    _LOG.info("Processing file: %s", file_name)
    # Find paired file.
    paired_file = _find_paired_file(file_name)
    _LOG.info("Found paired file: %s", paired_file)
    # Report which file is newer.
    _report_newer_file(file_name, paired_file)
    # Determine which is the notebook file.
    if file_name.endswith(".ipynb"):
        ipynb_file = file_name
        py_file = paired_file
    else:
        ipynb_file = paired_file
        py_file = file_name
    # Check sync status.
    _check_sync_status(ipynb_file)
    # Extract Python from notebook.
    tmp_py_file = _extract_python_from_notebook(ipynb_file)
    # Run vimdiff.
    _LOG.info("Running vimdiff between %s and %s", py_file, tmp_py_file)
    _run_vimdiff(py_file, tmp_py_file)


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-f",
        "--file",
        action="store",
        type=str,
        required=True,
        help="File to process",
    )
    parser.add_argument(
        "--action",
        action="store",
        choices=["pair", "test", "test_strict", "sync", "diff"],
        required=True,
        help="Action to perform",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level)
    #
    file_name = args.file
    hdbg.dassert_path_exists(file_name)
    if args.action == "pair":
        _pair(file_name)
    elif args.action == "sync":
        _sync(file_name)
    elif args.action in ("test", "test_strict"):
        _test(file_name, args.action)
    elif args.action == "diff":
        _diff(file_name)
    else:
        raise ValueError(f"Invalid action '{args.action}'")


if __name__ == "__main__":
    _main(_parse())
