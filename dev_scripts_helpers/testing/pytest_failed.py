#!/usr/bin/env python

"""
Parse the failed tests out of a pytest log, print them, save a repro script,
and copy the test names to the clipboard.

Examples

# Parse failed tests from `tmp.pytest_script.txt`.
> pytest_failed.py

# Parse failed tests from a specific log file, keeping only the file names.
> pytest_failed.py --file_name tmp.log --only_file
"""

import argparse
import logging
import pprint
from typing import List

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hpytest as hpytest
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-i", "--input",
        action="store",
        # This is the output from pytest_log.
        default="tmp.pytest_script.txt",
        help="Pytest log file to parse for failed tests",
    )
    parser.add_argument(
        "--only_file",
        action="store_true",
        help="Return only the file name for each failed test",
    )
    parser.add_argument(
        "--only_class",
        action="store_true",
        help="Return only the class name for each failed test",
    )
    parser.add_argument(
        "--print_tests",
        action="store_true",
        help="Print the list of failed tests",
    )
    parser.add_argument(
        "--pbcopy",
        action="store_true",
        help="Copy the list of failed tests to the system clipboard",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _write_repro_script(file_name: str, tests: List[str]) -> None:
    """
    Write an executable script that reruns `tests` via `pytest_log`.

    :param file_name: name of the script to create
    :param tests: tests, classes, or files to pass to `pytest_log`
    """
    repro_txt = "pytest_log " + " ".join(tests) + " $*"
    hio.create_executable_script(file_name, repro_txt)
    _LOG.info("Created '%s'", file_name)


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Read file.
    _LOG.info("Reading '%s'", args.input)
    txt = hio.from_file(args.input)
    # Extract info, always keeping the full test names so the classes/files
    # repro scripts can be derived from them.
    _LOG.info("Parsing '%s'", args.input)
    info = hpytest.parse_failed_tests(txt, only_file=False, only_class=False)
    failed_tests = info["failed_tests"]
    print(hprint.frame("Results"))
    info_to_print = {k: v for k, v in info.items() if k != "failed_tests"}
    print(pprint.pformat(info_to_print))
    # Write the repro scripts.
    _write_repro_script("tmp.pytest_failed.sh", failed_tests)
    failed_classes = hpytest.filter_failed_tests(
        failed_tests, only_file=False, only_class=True
    )
    _write_repro_script("tmp.pytest_failed.classes.sh", failed_classes)
    failed_files = hpytest.filter_failed_tests(
        failed_tests, only_file=True, only_class=False
    )
    _write_repro_script("tmp.pytest_failed.files.sh", failed_files)
    # Select the tests to print/copy based on `--only_file`/`--only_class`.
    if args.only_file:
        selected_tests = failed_files
    elif args.only_class:
        selected_tests = failed_classes
    else:
        selected_tests = failed_tests
    if args.print_tests:
        print("\n".join(selected_tests))
    # Save to clipboard.
    if args.pbcopy:
        txt = " ".join(selected_tests)
        hsystem.to_pbcopy(txt, pbcopy=True)


if __name__ == "__main__":
    _main(_parse())
