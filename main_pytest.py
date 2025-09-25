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

import junitparser

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hparser as hparser
import helpers.hpytest as hpytest
import helpers.lib_tasks_docker as hlitadoc
import helpers.lib_tasks_utils as hlitauti
import helpers.repo_config_utils as hrecouti

_LOG = logging.getLogger(__name__)


def _get_docker_image_for_runnable_dir(
    runnable_dir: str, stage: str = "dev", version: str = ""
) -> str:
    """
    Get the Docker image name that would be used for the given runnable directory.

    :param runnable_dir: path to the runnable directory
    :param stage: Docker stage (dev, prod, local)
    :param version: Docker version
    :return: full Docker image name
    """
    # Build the path to the repo_config.yml file in the runnable directory.
    repo_config_file = os.path.join(runnable_dir, "repo_config.yml")
    hdbg.dassert_path_exists(
        repo_config_file, "repo_config.yml not found in %s", runnable_dir
    )
    # Load the repo config for the specific runnable directory.
    repo_config = hrecouti.RepoConfig.from_file(repo_config_file)
    # Build the full base image path.
    container_registry_base_path = hlitauti.get_default_param("CSFY_ECR_BASE_PATH")
    base_image_name = repo_config.get_docker_base_image_name()
    base_image = f"{container_registry_base_path}/{base_image_name}"
    # Use the get_image function to build the full image name.
    image_name = hlitadoc.get_image(base_image, stage, version)
    return image_name


def _add_common_test_arguments(parser: argparse.ArgumentParser) -> None:
    """
    Add common arguments shared by all test commands.

    :param parser: The parser to add arguments to
    """
    parser.add_argument(
        "--dir",
        action="store",
        required=False,
        type=str,
        help="Name of runnable dir",
    )
    parser.add_argument(
        "--purge-docker-images",
        action="store_true",
        help="Purge all Docker images after running tests",
    )


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
    _add_common_test_arguments(run_fast_tests_parser)
    # Add command for running slow tests.
    run_slow_tests_parser = subparsers.add_parser(
        "run_slow_tests", help="Run slow tests"
    )
    _add_common_test_arguments(run_slow_tests_parser)
    # Add command for running superslow tests.
    run_superslow_tests_parser = subparsers.add_parser(
        "run_superslow_tests", help="Run superslow tests"
    )
    _add_common_test_arguments(run_superslow_tests_parser)
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
        _LOG.warning("%s is not a runnable directory", runnable_dir)
        return False
    return True


def _run_test(
    runnable_dir: str, command: str, purge_docker_images: bool = False
) -> bool:
    """
    Run test in for specified runnable directory.

    :param runnable_dir: directory to run tests in
    :param command: command to run tests (e.g. run_fast_tests,
        run_slow_tests, run_superslow_tests)
    :param purge_docker_images: whether to purge Docker images after
        test
    :return: True if the tests were run successfully, False otherwise
    """
    is_runnable_dir = _is_runnable_dir(runnable_dir)
    hdbg.dassert(is_runnable_dir, "%s is not a runnable dir.", runnable_dir)
    _LOG.info("Running tests in %s", runnable_dir)

    # Get the Docker image that will be used for this test run.
    docker_image = None
    if purge_docker_images:
        # Get the image name that would be used by the test command for this specific runnable directory.
        # We use default stage and version as they match the invoke commands.
        docker_image = _get_docker_image_for_runnable_dir(
            runnable_dir, stage="dev", version=""
        )
        _LOG.info("Will clean up Docker image after test: %s", docker_image)

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
    # Clean up the specific Docker image used in the test run if requested.
    if purge_docker_images and docker_image:
        _LOG.info("Cleaning up Docker image: %s", docker_image)
        hlitadoc.docker_image_delete(docker_image)
    # pytest returns:
    # - 0 if all tests passed
    # - 5 if no tests are collected
    if result.returncode in [0, 5]:
        return True
    return False


def _run_tests(
    runnable_dirs: List[str], command: str, purge_docker_images: bool = False
) -> bool:
    """
    Run tests for all runnable directories.

    :param runnable_dirs: list of runnable directories
    :param command: command to run tests (e.g. `run_fast_tests`,
        `run_slow_tests`, `run_superslow_tests`)
    :param purge_docker_images: whether to purge Docker images after each test
    :return: True if all tests for all runnable directories passed, False otherwise
    """
    results = []
    for runnable_dir in runnable_dirs:
        res = _run_test(runnable_dir, command, purge_docker_images)
        results.append(res)
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
    purge_docker_images = getattr(args, "purge_docker_images", False)
    all_tests_passed = False
    try:
        if runnable_dir:
            # If a runnable directory is specified, run tests for it.
            runnable_dirs = [runnable_dir]
        else:
            # If no runnable directory is specified, run tests for all runnable directories.
            runnable_dirs = _find_runnable_dirs()
        # Run tests.
        if command == "run_fast_tests":
            all_tests_passed = _run_tests(
                runnable_dirs=runnable_dirs,
                command=command,
                purge_docker_images=purge_docker_images,
            )
        elif command == "run_slow_tests":
            all_tests_passed = _run_tests(
                runnable_dirs=runnable_dirs,
                command=command,
                purge_docker_images=purge_docker_images,
            )
        elif command == "run_superslow_tests":
            all_tests_passed = _run_tests(
                runnable_dirs=runnable_dirs,
                command=command,
                purge_docker_images=purge_docker_images,
            )
        else:
            _LOG.error("Invalid command.")
        # Search for junit xml report files.
        junit_xml_files = glob.glob("**/tmp.junit.xml", recursive=True)
        # Combine the junit xml files into a single file.
        combined_junit_xml = junitparser.JUnitXml()
        for junit_xml_file in junit_xml_files:
            _LOG.debug("Processing %s.", junit_xml_file)
            junit_xml = junitparser.JUnitXml.fromfile(junit_xml_file)
            combined_junit_xml += junit_xml
        combined_junit_xml_file = "tmp.combined_junit.xml"
        combined_junit_xml.write(combined_junit_xml_file)
        # Print report based on the combined junit xml file.
        reporter = hpytest.JUnitReporter(combined_junit_xml_file)
        reporter.parse()
        reporter.print_summary()
    except Exception as e:
        _LOG.error("Error: %s", e)
        sys.exit(1)
    finally:
        if not all_tests_passed:
            # Error code is not propagated upward to the parent process causing the
            # GH actions to not fail the pipeline (See CmampTask11449).
            # We need to explicitly exit to fail the pipeline.
            sys.exit(1)


if __name__ == "__main__":
    _main(_parse())
