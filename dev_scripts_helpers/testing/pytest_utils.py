"""
Shared utilities for pytest testing scripts.

For architecture overview, see pytest_testing_system.README.md

Import as:

import dev_scripts_helpers.testing.pytest_utils as dshtpyut
"""

import os
from typing import Dict, List, Tuple

import helpers.hdbg as hdbg
import helpers.hio as hio

# Build configurations: name -> (docker_engine, use_docker_cmd).
BUILD_CONFIG: Dict[str, Tuple[str, bool]] = {
    "docker": ("docker", False),
    "apple": ("apple", False),
    "dev_container": ("docker", True),
}


# #############################################################################
# Path management
# #############################################################################


def get_output_file_path(basename: str, *, build_name: str = "") -> str:
    """
    Get output file path with optional build_name encoding in directory structure.

    Creates directory `tmp.pytest_failed.{build_name}/` and stores file inside.
    For example:
    - basename='duration_stats.txt', build_name='apple'
    - Returns: 'tmp.pytest_failed.apple/duration_stats.txt'

    :param basename: Filename (e.g., 'duration_stats.txt')
    :param build_name: Optional build name to create directory
    :return: Full file path
    """
    if build_name:
        dir_name = f"tmp.pytest_failed.{build_name}"
        if not os.path.exists(dir_name):
            hio.create_dir(dir_name, incremental=True)
        return os.path.join(dir_name, basename)
    return basename


# #############################################################################
# Command generation
# #############################################################################


def get_build_command(
    tests: List[str], build_name: str
) -> str:
    """
    Generate pytest command for a given build and test list.

    :param tests: List of test names to run
    :param build_name: Build name (e.g., 'docker', 'apple', 'dev_container')
    :return: Complete shell command to run tests
    """
    hdbg.dassert_in(build_name, BUILD_CONFIG, "Unknown build name")
    tests_str = " ".join(tests)
    docker_engine, use_docker_cmd = BUILD_CONFIG[build_name]
    if use_docker_cmd:
        cmd = f'invoke docker_cmd --stage=local -v 1.6.0 --cmd "pytest_log {tests_str} $*"'
    else:
        cmd = f"export CSFY_DOCKER_ENGINE='{docker_engine}'; pytest_log {tests_str} $*"
    return cmd
