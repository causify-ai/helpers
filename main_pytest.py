#!/usr/bin/env python

"""
Main script used for running tests in runnable directories.
"""

import argparse
import glob
import logging
import os
import subprocess
import sys
from typing import List

from junitparser import JUnitXml

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hparser as hparser
import helpers.hpytest as hpytest

_LOG = logging.getLogger(__name__)


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Sub-command help")
    # Add command for running fast tests.
    run_fast_tests_parser = subparsers.add_parser(
        "run_fast_tests", help="Run fast tests"
    )
    run_fast_tests_parser.add_argument(
        "--dir",
        action="store",
        required=False,
        type=str,
        help="Name of runnable dir",
    )
    # Add command for running slow tests.
    run_slow_tests_parser = subparsers.add_parser(
        "run_slow_tests", help="Run slow tests"
    )
    run_slow_tests_parser.add_argument(
        "--dir",
        action="store",
        required=False,
        type=str,
        help="Name of runnable dir",
    )
    # Add command for running superslow tests.
    run_superslow_tests_parser = subparsers.add_parser(
        "run_superslow_tests", help="Run superslow tests"
    )
    run_superslow_tests_parser.add_argument(
        "--dir",
        action="store",
        required=False,
        type=str,
        help="Name of runnable dir",
    )
    parser = hparser.add_verbosity_arg(parser)
    return parser


def _is_runnable_dir(runnable_dir: str) -> bool:
    """
    Check if the specified directory is a runnable directory.

    Each directory that is runnable contains the files:
    - changelog.txt: store the changelog
    - devops: dir with all the Docker files needed to build and run a container

    :param runnable_dir: nme of the runnable directory
    :return: True if the directory is a runnable directory, False otherwise
    """
    changelog_path = os.path.join(runnable_dir, "changelog.txt")
    devops_path = os.path.join(runnable_dir, "devops")
    if not os.path.exists(changelog_path) or not os.path.isdir(devops_path):
        _LOG.warning(f"{runnable_dir} is not a runnable directory")
        return False
    return True


def _run_test(runnable_dir: str, command: str) -> bool:
    """
    Run test in for specified runnable directory.

    :param runnable_dir: directory to run tests in
    :param command: command to run tests (e.g. run_fast_tests,
        run_slow_tests, run_superslow_tests)
    :return: True if the tests were run successfully, False otherwise
    """
    is_runnable_dir = _is_runnable_dir(runnable_dir)
    hdbg.dassert(is_runnable_dir, f"{runnable_dir} is not a runnable dir.")
    _LOG.info(f"Running tests in {runnable_dir}")
    # Make sure the `invoke` command is referencing to the correct
    # devops and helpers directory.
    env = os.environ.copy()
    env["HELPERS_ROOT_DIR"] = os.path.join(os.getcwd(), "helpers_root")
    # Give priority to the current runnable directory over helpers.
    env["PYTHONPATH"] = (
        f"{os.path.join(os.getcwd(), runnable_dir)}:{env['HELPERS_ROOT_DIR']}"
    )
    # TODO(heanh): Use hsystem.
    # We cannot use `hsystem.system` because it does not support passing of env
    # variables yet.
    result = subprocess.run(
        f"invoke {command}", shell=True, env=env, cwd=runnable_dir
    )
    # pytest returns 5 if no tests are collected.
    if result.returncode in [0, 5]:
        return True
    return False


def _run_tests(runnable_dirs: List[str], command: str) -> bool:
    """
    Run tests for all runnable directories.

    :param runnable_dirs: list of runnable directories
    :param command: command to run tests (e.g. run_fast_tests,
        run_slow_tests, run_superslow_tests)
    :return: True if the tests were run successfully, False otherwise
    """
    results = []
    for runnable_dir in runnable_dirs:
        res = _run_test(runnable_dir, command)
        results.append(res)
    # If any of the item is False, return False.
    return all(results)


def _find_runnable_dirs() -> List[str]:
    """
    Find all the runnable directories in the current repo.

    We use the `runnable_dir` file as a marker to identify runnable directories.

    :return: list of runnable directories
    """
    runnable_dirs = []
    root = hgit.find_git_root()
    for dir_path, _, file_names in os.walk(root):
        if "runnable_dir" in file_names:
            relative_path = os.path.relpath(dir_path, root)
            runnable_dirs.append(relative_path)
    return runnable_dirs


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    command = args.command
    runnable_dir = args.dir
    if runnable_dir:
        # Run tests for the specified runnable directory.
        runnable_dirs = [runnable_dir]
    else:
        # Run tests for all runnable directories.
        runnable_dirs = _find_runnable_dirs()
    # Run tests.
    if command == "run_fast_tests":
        res = _run_tests(runnable_dirs=runnable_dirs, command=command)
    elif command == "run_slow_tests":
        res = _run_tests(runnable_dirs=runnable_dirs, command=command)
    elif command == "run_superslow_tests":
        res = _run_tests(runnable_dirs=runnable_dirs, command=command)
    else:
        _LOG.error("Invalid command.")
    # Search for junit xml report files.
    junit_xml_files = glob.glob("**/junit.xml", recursive=True)
    # Combine the junit xml files into a single file.
    combined_junit_xml = JUnitXml()
    for junit_xml_file in junit_xml_files:
        _LOG.debug(f"Processing {junit_xml_file}.")
        junit_xml = JUnitXml.fromfile(junit_xml_file)
        combined_junit_xml += junit_xml
    combined_junit_xml_file = "tmp.combined_junit.xml"
    # Save the combined junit xml file.
    combined_junit_xml.write(combined_junit_xml_file)
    # Print report.
    reporter = hpytest.JUnitReporter(combined_junit_xml_file)
    reporter.parse()
    reporter.print_summary()
    if not res:
        # Error code is not propagated upward to the parent process causing the
        # GH actions to not fail the pipeline (See CmampTask11449).
        # We need to explicitly exit to fail the pipeline.
        sys.exit(1)


if __name__ == "__main__":
    _main(_parse())
