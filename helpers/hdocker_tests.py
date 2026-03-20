"""
Utilities for running docker tests.

Import as:

import helpers.hdocker_tests as hdtests
"""

import glob
import logging
import os
import subprocess
from typing import List

import helpers.hdbg as hdbg

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


def run_docker_cmd(test_file: str, *, docker_cmd_script: str = "./docker_cmd.sh") -> int:
  """
  Run a test file through docker_cmd.sh with pytest.

  :param test_file: path to the test file
  :param docker_cmd_script: path to docker_cmd.sh script
  :return: return code from the command
  """
  hdbg.dassert_file_exists(test_file, "Test file does not exist")
  hdbg.dassert_file_exists(docker_cmd_script, "docker_cmd.sh does not exist")
  cmd = f'{docker_cmd_script} "pytest {test_file}"'
  _LOG.info("Running: %s", cmd)
  result = subprocess.run(cmd, shell=True)
  return result.returncode


def run_all_tests(test_dir: str, *, docker_cmd_script: str = "./docker_cmd.sh") -> int:
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
    return_code = run_docker_cmd(test_file, docker_cmd_script=docker_cmd_script)
    if return_code != 0:
      failed_tests.append(test_file)
  if failed_tests:
    _LOG.error("Failed tests: %s", failed_tests)
    return 1
  _LOG.info("All tests passed")
  return 0
