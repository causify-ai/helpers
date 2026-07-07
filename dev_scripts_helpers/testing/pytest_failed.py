#!/usr/bin/env python

"""
Parse the failed tests out of a pytest log, print them, save a repro script,
and copy the test names to the clipboard.

Examples

# Parse failed tests from `tmp.pytest_script.txt`.
> pytest_failed.py

# Parse failed tests from a specific log file, keeping only the file names.
> pytest_failed.py --file_name tmp.log --only_file

# Also write passed/skipped tests, tests by duration, and duration stats.
> pytest_failed.py \
    --passed_tests_file tmp.passed.txt \
    --skipped_tests_file tmp.skipped.txt \
    --tests_by_duration_file tmp.by_duration.txt \
    --duration_stats_file tmp.duration_stats.txt
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
    parser.add_argument(
        "--passed_tests_file",
        action="store",
        default="",
        help="File to write the list of passed tests to",
    )
    parser.add_argument(
        "--skipped_tests_file",
        action="store",
        default="",
        help="File to write the list of skipped tests to",
    )
    parser.add_argument(
        "--tests_by_duration_file",
        action="store",
        default="",
        help="File to write all timed tests ordered by duration to",
    )
    parser.add_argument(
        "--duration_stats_file",
        action="store",
        default="",
        help="File to write test duration statistics by file and class to",
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
    # Write the optional reports.
    if args.passed_tests_file:
        hpytest.write_passed_tests(info, args.passed_tests_file)
        _LOG.info("Created '%s'", args.passed_tests_file)
    if args.skipped_tests_file:
        hpytest.write_skipped_tests(info, args.skipped_tests_file)
        _LOG.info("Created '%s'", args.skipped_tests_file)
    if args.tests_by_duration_file:
        hpytest.write_tests_by_duration(info, args.tests_by_duration_file)
        _LOG.info("Created '%s'", args.tests_by_duration_file)
    if args.duration_stats_file:
        hpytest.write_duration_stats(info, args.duration_stats_file)
        _LOG.info("Created '%s'", args.duration_stats_file)
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
