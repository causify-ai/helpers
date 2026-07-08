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
- tmp.pytest_failed.updated_tests.txt: list of tests whose golden outcome was updated
- tmp.pytest_failed.tests_by_duration.txt: tests ordered by duration
- tmp.pytest_failed.duration_stats.txt: duration statistics by file and class
- tmp.pytest_failed.stacktraces.txt: failure reason for each failed test
"""

import argparse
import logging

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hpytest as hpytest

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
    hparser.add_verbosity_arg(parser)
    return parser


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
    hpytest.write_repro_script(failed_tests, "tmp.pytest_failed.sh")
    #
    failed_classes = hpytest.filter_failed_tests(
        failed_tests, only_file=False, only_class=True
    )
    hpytest.write_repro_script(failed_classes, "tmp.pytest_failed.classes.sh")
    #
    failed_files = hpytest.filter_failed_tests(
        failed_tests, only_file=True, only_class=False
    )
    hpytest.write_repro_script(failed_files, "tmp.pytest_failed.files.sh")
    # Write the reports.
    passed_tests_file = "tmp.pytest_failed.passed_tests.txt"
    hpytest.write_passed_tests(info, passed_tests_file)
    _LOG.info("Created '%s'", passed_tests_file)
    #
    skipped_tests_file = "tmp.pytest_failed.skipped_tests.txt"
    hpytest.write_skipped_tests(info, skipped_tests_file)
    _LOG.info("Created '%s'", skipped_tests_file)
    #
    updated_tests_file = "tmp.pytest_failed.updated_tests.txt"
    hpytest.write_updated_tests(info, updated_tests_file)
    _LOG.info("Created '%s'", updated_tests_file)
    #
    tests_by_duration_file = "tmp.pytest_failed.tests_by_duration.txt"
    hpytest.write_tests_by_duration(info, tests_by_duration_file)
    _LOG.info("Created '%s'", tests_by_duration_file)
    #
    duration_stats_file = "tmp.pytest_failed.duration_stats.txt"
    hpytest.write_duration_stats(info, duration_stats_file)
    _LOG.info("Created '%s'", duration_stats_file)
    #
    stacktraces_file = "tmp.pytest_failed.stacktraces.txt"
    hpytest.write_test_stacktraces(info, stacktraces_file)
    _LOG.info("Created '%s'", stacktraces_file)


if __name__ == "__main__":
    _main(_parse())
