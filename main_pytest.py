#!/usr/bin/env python

"""
Main script used for running tests in runnable directories.
"""

import argparse
import logging
import os
import subprocess
import sys

import helpers.hdbg as hdbg
import helpers.hparser as hparser

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


def _run_test(runnable_dir: str, command: str) -> None:
    """
    Run test in for specified runnable directory.

    :param runnable_dir: directory to run tests in
    :param command: command to run tests (e.g. run_fast_tests,
        run_slow_tests, run_superslow_tests)
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
    # Error code is not propagated upward to the parent process causing the
    # GH actions to not fail the pipeline (See CmampTask11449).
    # We need to explicitly exit with the return code of the subprocess.
    if result.returncode != 0:
        sys.exit(result.returncode)


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    command = args.command
    runnable_dirs = [
        "ck.infra",
    ]
    if command == "run_fast_tests":
        runnable_dir = args.dir
        if runnable_dir:
            # Run tests for the specified runnable directory.
            _run_test(runnable_dir, command)
        else:
            # Run tests for all runnable directories.
            _LOG.info("Running fast tests for all runnable directories.")
            for runnable_dir in runnable_dirs:
                _run_test(runnable_dir, command)
    elif command == "run_slow_tests":
        runnable_dir = args.dir
        if runnable_dir:
            # Run tests for the specified runnable directory.
            _run_test(runnable_dir, command)
        else:
            # Run tests for all runnable directories.
            _LOG.info("Running slow tests for all runnable directories.")
            for runnable_dir in runnable_dirs:
                _run_test(runnable_dir, command)
    elif command == "run_superslow_tests":
        runnable_dir = args.dir
        if runnable_dir:
            # Run tests for the specified runnable directory.
            _run_test(runnable_dir, command)
        else:
            # Run tests for all runnable directories.
            _LOG.info("Running superslow tests for all runnable directories.")
            for runnable_dir in runnable_dirs:
                _run_test(runnable_dir, command)
    else:
        _LOG.error("Invalid command.")


if __name__ == "__main__":
    _main(_parse())
