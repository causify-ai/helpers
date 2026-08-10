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
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Helper functions
# #############################################################################


def get_docker_test_files(test_dir: str) -> List[str]:
    """
    Find all docker test files in the `test_dir` directory.

    :param test_dir: directory to search for test files
    :return: sorted list of test file paths
    """
    # Pattern for docker test files.
    docker_test_pattern = "docker_test_*.py"
    pattern = os.path.join(test_dir, docker_test_pattern)
    files = sorted(glob.glob(pattern))
    _LOG.info("Found %d docker test files", len(files))
    for file in files:
        _LOG.debug("  - %s", file)
    return files


# TODO(gp): Consider making docker_cmd_script mandatory.
def _run_docker_pytest_cmd(
    test_file: str, *, docker_cmd_script: str = "./docker_cmd.sh"
) -> int:
    """
    Run a test file through `docker_cmd.sh` with pytest.

    :param test_file: path to the test file
    :param docker_cmd_script: path to `docker_cmd.sh` script
    :return: return code from the command
    """
    hdbg.dassert_file_exists(test_file)
    hdbg.dassert_file_exists(docker_cmd_script)
    #
    cmd = f'{docker_cmd_script} "pytest {test_file}"'
    # TODO(gp): Why abort_on_error?
    rc = hsystem.system(cmd, abort_on_error=False)
    return rc


# TODO(gp): Consider making shell_cmd mandatory.
def run_docker_cmd(docker_script_dir: str, *, shell_cmd: str = "ls /git_root") -> None:
    """
    Run an arbitrary shell command inside Docker via `docker_cmd.sh`.

    :param docker_script_dir: directory containing docker_cmd.sh
    :param shell_cmd: shell command to run inside the container
    """
    hdbg.dassert_path_exists(docker_script_dir)
    # Look for `docker_cmd.sh`
    docker_cmd_script = os.path.join(docker_script_dir, "docker_cmd.sh")
    hdbg.dassert_file_exists(docker_cmd_script)
    #
    cmd = f"cd {docker_script_dir} && bash {docker_cmd_script} '{shell_cmd}'"
    hsystem.system(cmd)


# TODO(gp): Consider making docker_cmd_script mandatory.
def run_all_tests(
    test_dir: str, *, docker_cmd_script: str = "./docker_cmd.sh"
) -> int:
    """
    Find and run all docker test files in the directory.

    :param test_dir: directory containing test files
    :param docker_cmd_script: path to docker_cmd.sh script
    :return: 0 if all tests passed, non-zero otherwise
    """
    # Find the docker tests to run.
    test_files = get_docker_test_files(test_dir)
    if not test_files:
        _LOG.warning("No docker test files found in %s", test_dir)
        return 0
    # Run one test at the time.
    failed_tests = []
    for test_file in test_files:
        return_code = _run_docker_pytest_cmd(
            test_file, docker_cmd_script=docker_cmd_script
        )
        if return_code != 0:
            failed_tests.append(test_file)
    # Report result.
    if failed_tests:
        _LOG.error("Failed tests: %s", failed_tests)
        return 1
    _LOG.info("All tests passed")
    return 0


# #############################################################################
# DockerTestCase
# #############################################################################


# TODO(gp): Can this be used for run_dockerized_* tests?
class DockerTestCase(hunitest.TestCase):
    """
    Base test class for Docker tests.

    Subclasses must set `_test_file = __file__` and may add notebook test
    methods that call `self.helper(notebook_name)`.
    """

    # Assigned by subclasses.
    _test_file: str = ""

    def _get_docker_docker_script_dir(self) -> str:
        """
        Compute the project directory containing the Docker scripts.

        - `self._test_file` is the path of the test file, which lives in a
          `test/` subdirectory of the project
            - E.g., `.../my_project/test/test_docker_all.py`
        - Going up two directory levels from the test file yields the project
          directory that contains `docker_build.sh`, `docker_cmd.sh`, and
          `docker_bash.sh`.

        :return: absolute path to the project directory
        """
        docker_script_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(self._test_file))
        )
        return docker_script_dir

    @pytest.mark.order(1)
    @pytest.mark.slow
    def test_docker_build(self) -> None:
        """
        Test that `docker_build.sh` runs without error.
        """
        # Prepare inputs.
        docker_script_dir = self._get_docker_docker_script_dir()
        docker_build_script = os.path.join(docker_script_dir, "docker_build.sh")
        hdbg.dassert_file_exists(docker_build_script)
        # Run test.
        cmd = f"cd {docker_script_dir} && bash {docker_build_script}"
        hsystem.system(cmd)

    @pytest.mark.order(2)
    @pytest.mark.slow
    def test_docker_cmd(self) -> None:
        """
        Test that `docker_cmd.sh 'ls /git_root'` runs without error.
        """
        # Prepare inputs.
        docker_script_dir = self._get_docker_docker_script_dir()
        docker_cmd_script = os.path.join(docker_script_dir, "docker_cmd.sh")
        hdbg.dassert_file_exists(docker_cmd_script)
        # Run test.
        cmd = f"cd {docker_script_dir} && bash {docker_cmd_script} 'ls /git_root'"
        hsystem.system(cmd)

    @pytest.mark.order(3)
    def test_docker_bash(self) -> None:
        """
        Test that `docker_bash.sh` runs 'ls /git_root' without error.
        """
        # Prepare inputs.
        docker_script_dir = self._get_docker_docker_script_dir()
        docker_bash_script = os.path.join(docker_script_dir, "docker_bash.sh")
        if not os.path.exists(docker_bash_script):
            pytest.skip("docker_bash.sh not found in " + docker_script_dir)
        # Run test.
        shell_cmd = "ls /git_root"
        cmd = f"echo '{shell_cmd}' | bash {docker_bash_script}"
        hsystem.system(cmd)

    def helper(self, notebook_name: str) -> None:
        """
        Run a single notebook inside Docker.

        :param notebook_name: notebook filename relative to the project dir
        """
        # Prepare inputs.
        docker_script_dir = self._get_docker_docker_script_dir()
        docker_cmd_script = os.path.join(docker_script_dir, "docker_cmd.sh")
        _LOG.debug(hprint.to_str("docker_cmd_script"))
        # Notebook path.
        notebook_path = os.path.join(docker_script_dir, notebook_name)
        hdbg.dassert_file_exists(notebook_path)
        _LOG.debug(hprint.to_str("notebook_path"))
        # Compute the notebook path inside the container via /git_root.
        git_root = hgit.find_git_root(docker_script_dir)
        rel_path = os.path.relpath(docker_script_dir, git_root)
        container_notebook_path = f"/git_root/{rel_path}/{notebook_name}"
        _LOG.debug(hprint.to_str("container_notebook_path"))
        # Run command.
        cmd = (
            f"cd {docker_script_dir} && "
            f"bash {docker_cmd_script} "
            f"'jupyter nbconvert --execute --to html "
            f"--ExecutePreprocessor.timeout=-1 {container_notebook_path}'"
        )
        hsystem.system(cmd)
