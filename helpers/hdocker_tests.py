"""
Utilities for running docker tests.

Import as:

import helpers.hdocker_tests as hdtests
"""

import glob
import logging
import os
from typing import List

import helpers.hdbg as hdbg
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# #############################################################################
# Constants
# #############################################################################


# Pattern for docker test files.
DOCKER_TEST_PATTERN = "docker_test_*.py"


# #############################################################################
# Helper functions
# #############################################################################


def get_docker_test_files(test_dir: str) -> List[str]:
    """
    Find all docker test files in the specified directory.

    :param test_dir: directory to search for test files
    :return: sorted list of test file paths
    """
    pattern = os.path.join(test_dir, DOCKER_TEST_PATTERN)
    files = sorted(glob.glob(pattern))
    _LOG.info("Found %d docker test files", len(files))
    for file in files:
        _LOG.debug("  - %s", file)
    return files


def _run_docker_pytest_cmd(
    test_file: str, *, docker_cmd_script: str = "./docker_cmd.sh"
) -> int:
    """
    Run a test file through docker_cmd.sh with pytest.

    :param test_file: path to the test file
    :param docker_cmd_script: path to docker_cmd.sh script
    :return: return code from the command
    """
    hdbg.dassert_file_exists(test_file)
    hdbg.dassert_file_exists(docker_cmd_script)
    cmd = f'{docker_cmd_script} "pytest {test_file}"'
    _LOG.info("Running: %s", cmd)
    rc = hsystem.system(cmd, abort_on_error=False)
    return rc


def run_all_tests(
    test_dir: str, *, docker_cmd_script: str = "./docker_cmd.sh"
) -> int:
    """
    Find and run all docker test files in the directory.

    :param test_dir: directory containing test files
    :param docker_cmd_script: path to docker_cmd.sh script
    :return: 0 if all tests passed, non-zero otherwise
    """
    test_files = get_docker_test_files(test_dir)
    if not test_files:
        _LOG.warning("No docker test files found in %s", test_dir)
        return 0
    failed_tests = []
    for test_file in test_files:
        return_code = _run_docker_pytest_cmd(
            test_file, docker_cmd_script=docker_cmd_script
        )
        if return_code != 0:
            failed_tests.append(test_file)
    if failed_tests:
        _LOG.error("Failed tests: %s", failed_tests)
        return 1
    _LOG.info("All tests passed")
    return 0


def run_docker_build(script_dir: str) -> None:
    """
    Build the Docker image by running docker_build.sh in script_dir.

    :param script_dir: directory containing docker_build.sh
    """
    docker_build_script = os.path.join(script_dir, "docker_build.sh")
    hdbg.dassert_file_exists(docker_build_script)
    cmd = f"cd {script_dir} && bash {docker_build_script}"
    hsystem.system(cmd)


def run_docker_cmd(
    script_dir: str, *, shell_cmd: str = "ls /curr_dir"
) -> None:
    """
    Run an arbitrary shell command inside Docker via docker_cmd.sh.

    :param script_dir: directory containing docker_cmd.sh
    :param shell_cmd: shell command to run inside the container
    """
    docker_cmd_script = os.path.join(script_dir, "docker_cmd.sh")
    hdbg.dassert_file_exists(docker_cmd_script)
    # cd into script_dir so docker_cmd.sh mounts the right directory.
    cmd = f"cd {script_dir} && bash {docker_cmd_script} '{shell_cmd}'"
    hsystem.system(cmd)


def run_notebook_in_docker(notebook_name: str, script_dir: str) -> None:
    """
    Run a notebook inside Docker via docker_cmd.sh using jupyter nbconvert.

    :param notebook_name: notebook filename relative to script_dir (e.g.,
        template.example.ipynb)
    :param script_dir: directory containing docker_cmd.sh and the notebook
    """
    docker_cmd_script = os.path.join(script_dir, "docker_cmd.sh")
    notebook_path = os.path.join(script_dir, notebook_name)
    hdbg.dassert_file_exists(notebook_path)
    # cd into script_dir so docker_cmd.sh mounts the right directory.
    # Inside the container the notebooks are at /curr_dir/<notebook_name>.
    cmd = (
        f"cd {script_dir} && "
        f"bash {docker_cmd_script} "
        f"'jupyter nbconvert --execute --to html "
        f"--ExecutePreprocessor.timeout=-1 /curr_dir/{notebook_name}'"
    )
    hsystem.system(cmd)
