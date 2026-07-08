#!/usr/bin/env python

"""
Parse the failed tests out of a pytest log, print them, save a repro script,
and copy the test names to the clipboard.

Examples

# Parse failed tests from `tmp.pytest_script.txt`.
> pytest_failed.py

# Parse failed tests from a specific log file, keeping only the file names.
> pytest_failed.py --input tmp.log --only_file

Creates the following files:
- tmp.pytest_failed.sh: script to rerun failed tests
- tmp.pytest_failed.classes.sh: script to rerun failed test classes
- tmp.pytest_failed.files.sh: script to rerun failed test files
- tmp.pytest_failed.passed_tests.txt: list of passed tests
- tmp.pytest_failed.skipped_tests.txt: list of skipped tests
- tmp.pytest_failed.tests_by_duration.txt: tests ordered by duration
- tmp.pytest_failed.duration_stats.txt: duration statistics by file and class
"""

import argparse
import logging
from typing import List

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
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
        "-i",
        "--input",
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
    lines = txt.split("\n")
    info = hpytest.parse_failed_tests(lines)
    # Print the results.
    print(hpytest.info_to_str(info))
    # Write the repro scripts.
    failed_tests = info["log_failed_tests"]
    _write_repro_script("tmp.pytest_failed.sh", failed_tests)
    failed_classes = hpytest.filter_failed_tests(
        failed_tests, only_file=False, only_class=True
    )
    _write_repro_script("tmp.pytest_failed.classes.sh", failed_classes)
    failed_files = hpytest.filter_failed_tests(
        failed_tests, only_file=True, only_class=False
    )
    _write_repro_script("tmp.pytest_failed.files.sh", failed_files)
    # Write the reports.
    passed_tests_file = "tmp.pytest_failed.passed_tests.txt"
    hpytest.write_passed_tests(info, passed_tests_file)
    _LOG.info("Created '%s'", passed_tests_file)
    #
    skipped_tests_file = "tmp.pytest_failed.skipped_tests.txt"
    hpytest.write_skipped_tests(info, skipped_tests_file)
    _LOG.info("Created '%s'", skipped_tests_file)
    #
    tests_by_duration_file = "tmp.pytest_failed.tests_by_duration.txt"
    hpytest.write_tests_by_duration(info, tests_by_duration_file)
    _LOG.info("Created '%s'", tests_by_duration_file)
    #
    duration_stats_file = "tmp.pytest_failed.duration_stats.txt"
    hpytest.write_duration_stats(info, duration_stats_file)
    _LOG.info("Created '%s'", duration_stats_file)
    # Select the tests to print/copy based on `--only_file`/`--only_class`.
    if args.only_file:
        selected_tests = failed_files
    elif args.only_class:
        selected_tests = failed_classes
    else:
        selected_tests = failed_tests
    # Save selected tests to a file.
    selected_tests_file = "tmp.pytest_failed.selected_tests.txt"
    hio.to_file(selected_tests_file, "\n".join(selected_tests))
    _LOG.info("Created '%s'", selected_tests_file)
    if args.print_tests:
        print("\n".join(selected_tests))
    # Save to clipboard.
    if args.pbcopy:
        txt = " ".join(selected_tests)
        hsystem.to_pbcopy(txt, pbcopy=True)


if __name__ == "__main__":
    _main(_parse())
