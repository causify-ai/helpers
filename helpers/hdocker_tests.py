"""
Utilities for running docker tests.

Import as:

import helpers.hdocker_tests as hdoctest
"""

import glob
import logging
import os
from typing import List

import pytest

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

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


# #############################################################################



# #############################################################################
# DockerTestCase
# #############################################################################


class DockerTestCase(hunitest.TestCase):
    """
    Base test class for Docker tests.

    Subclasses must set `_test_file = __file__` and may add notebook test
    methods that call `self._helper(notebook_name)`.
    """

    _test_file: str = ""

    # TODO(ai_gp): Add test_docker_build_from_scratch marked as superslow
    # to build the container from scratch.

    @pytest.mark.slow
    def test_docker_build(self) -> None:
        """
        Test that docker_build.sh runs without error.
        """
        # Prepare inputs.
        script_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(self._test_file))
        )
        docker_build_script = os.path.join(script_dir, "docker_build.sh")
        hdbg.dassert_file_exists(docker_build_script)
        # Run test.
        cmd = f"cd {script_dir} && bash {docker_build_script}"
        hsystem.system(cmd)

    @pytest.mark.slow
    def test_docker_cmd(self) -> None:
        """
        Test that docker_cmd.sh 'ls /git_root' runs without error.
        """
        # Prepare inputs.
        script_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(self._test_file))
        )
        docker_cmd_script = os.path.join(script_dir, "docker_cmd.sh")
        hdbg.dassert_file_exists(docker_cmd_script)
        # Run test.
        cmd = f"cd {script_dir} && bash {docker_cmd_script} 'ls /git_root'"
        hsystem.system(cmd)

    def test_docker_bash(self) -> None:
        """
        Test that docker_bash.sh runs 'ls /git_root' and exits without error.
        """
        # Prepare inputs.
        script_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(self._test_file))
        )
        docker_bash_script = os.path.join(script_dir, "docker_bash.sh")
        if not os.path.exists(docker_bash_script):
            pytest.skip("docker_bash.sh not found in " + script_dir)
        # Run test.
        shell_cmd = "ls /git_root"
        cmd = f"echo '{shell_cmd}' | bash {docker_bash_script}"
        hsystem.system(cmd)

    def _run_notebook(self, notebook_name: str) -> None:
        """
        Run a single notebook inside Docker.

        :param notebook_name: notebook filename relative to the project dir
        """
        # Prepare inputs.
        script_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(self._test_file))
        )
        docker_cmd_script = os.path.join(script_dir, "docker_cmd.sh")
        notebook_path = os.path.join(script_dir, notebook_name)
        hdbg.dassert_file_exists(notebook_path)
        # Compute the notebook path inside the container via /git_root.
        git_root = hgit.find_git_root(script_dir)
        rel_path = os.path.relpath(script_dir, git_root)
        container_notebook_path = f"/git_root/{rel_path}/{notebook_name}"
        cmd = (
            f"cd {script_dir} && "
            f"bash {docker_cmd_script} "
            f"'jupyter nbconvert --execute --to html "
            f"--ExecutePreprocessor.timeout=-1 {container_notebook_path}'"
        )
        hsystem.system(cmd)
