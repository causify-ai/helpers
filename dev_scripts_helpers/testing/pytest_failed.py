#!/usr/bin/env python

"""
Parse the failed tests out of a pytest log, print them, save a repro script,
and copy the test names to the clipboard.

Examples

# Parse failed tests from `tmp.pytest_log.txt`.
> pytest_failed.py

# Parse failed tests from a specific log file, keeping only the file names.
> pytest_failed.py --input tmp.log --only_file

Creates the following files:
- tmp.pytest_failed.sh: script to rerun failed tests
- tmp.pytest_failed.classes.sh: script to rerun failed test classes
- tmp.pytest_failed.files.sh: script to rerun failed test files
- tmp.pytest_failed.failed_tests.txt: list of failed tests
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
import helpers.hprint as hprint
import helpers.hpytest as hpytest

_LOG = logging.getLogger(__name__)


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-i",
        "--input",
        action="store",
        default=None,
        help="Pytest log file to parse for failed tests",
    )
    group.add_argument(
        "--files",
        nargs="+",
        default=None,
        help="Multiple pytest log files to parse (space-separated)",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _process_single_file(file_path: str) -> dict:
    """
    Process a single pytest log file and return summary info.
    """
    _LOG.info("Reading '%s'", file_path)
    txt = hio.from_file(file_path)
    _LOG.info("Parsing '%s'", file_path)
    lines = txt.split("\n")
    info = hpytest.parse_failed_tests(lines)
    # Print the results.
    print(hpytest.info_to_str(info))
    # Write the repro scripts.
    failed_tests = info["log_failed_tests"]
    hpytest.write_repro_script(
        failed_tests,
        "Repro script for the failed tests",
        "tmp.pytest_failed.repro.sh",
    )
    #
    failed_classes = hpytest.filter_failed_tests(
        failed_tests, only_file=False, only_class=True
    )
    hpytest.write_repro_script(
        failed_classes,
        "Repro script for the classes containing failed tests",
        "tmp.pytest_failed.repro_classes.sh",
    )
    #
    failed_files = hpytest.filter_failed_tests(
        failed_tests, only_file=True, only_class=False
    )
    hpytest.write_repro_script(
        failed_files,
        "Repro script for the files containing failed tests",
        "tmp.pytest_failed.repro_files.sh",
    )
    # Write the reports.
    print(hprint.frame("Failed tests"))
    print("\n".join(failed_tests))
    #
    print(hprint.frame("Test info"))
    passed_tests_file = "tmp.pytest_failed.passed_tests.txt"
    hpytest.write_passed_tests(info, passed_tests_file)
    _LOG.info("Created '%s'", passed_tests_file)
    #
    failed_tests_file = "tmp.pytest_failed.failed_tests.txt"
    hpytest.write_failed_tests(info, failed_tests_file)
    _LOG.info("Created '%s'", failed_tests_file)
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
    # Extract summary info.
    num_passed = len(info["log_passed_tests"]) if info["log_passed_tests"] else 0
    num_skipped = len(info["log_skipped_tests"]) if info["log_skipped_tests"] else 0
    num_failed = len(info["log_failed_tests"]) if info["log_failed_tests"] else 0
    num_total = num_passed + num_skipped + num_failed
    passed = "PASS" if num_failed == 0 else "FAIL"
    return {
        "build": file_path,
        "passed": passed,
        "num_passed": num_passed,
        "num_skipped": num_skipped,
        "num_failed": num_failed,
        "num_total": num_total,
    }


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Determine input files.
    files = []
    if args.files:
        files = args.files
    elif args.input:
        files = [args.input]
    else:
        files = ["tmp.pytest_log.txt"]
    # Process each file and collect summary info.
    summary = []
    for file_path in files:
        summary.append(_process_single_file(file_path))
    # Print summary table.
    if len(files) > 1:
        print(hprint.frame("Summary"))
        print(f"{'Build':<50} {'Status':<6} {'Passed':<8} {'Skipped':<8} {'Failed':<8} {'Total':<8}")
        print("-" * 88)
        for row in summary:
            print(
                f"{row['build']:<50} {row['passed']:<6} "
                f"{row['num_passed']:<8} {row['num_skipped']:<8} "
                f"{row['num_failed']:<8} {row['num_total']:<8}"
            )


if __name__ == "__main__":
    _main(_parse())
