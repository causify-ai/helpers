#!/usr/bin/env python

"""
Consolidate failed tests across multiple build configurations.

Reads pytest_failed.py output from multiple builds and creates a summary of
tests failing across the builds, consolidating all repro commands.

Examples:

> pytest_failed_multi_build.py
> pytest_failed_multi_build.py --build_names docker apple dev_container
"""

import argparse
import logging
import os
from typing import Dict, List, Set

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)

# Build configurations: name -> (docker_engine, use_docker_cmd)
_BUILD_CONFIG: Dict[str, tuple] = {
    "docker": ("docker", False),
    "apple": ("apple", False),
    "dev_container": ("docker", True),
}


# #############################################################################
# File reading helpers
# #############################################################################


def _read_failed_tests(build_name: str) -> Set[str]:
    """
    Read failed tests from a single build.

    :param build_name: Build name (e.g., 'docker', 'apple', 'dev_container')
    :return: Set of failed test names
    """
    failed_file = f"tmp.pytest_failed.{build_name}.failed_tests.txt"
    # TODO(ai_gp): Use dassert_file_exists
    if not os.path.exists(failed_file):
        _LOG.warning("Failed tests file not found: %s", failed_file)
        return set()
    txt = hio.from_file(failed_file)
    lines = [line.strip() for line in txt.split("\n") if line.strip()]
    # TODO(ai_gp): Return List
    return set(lines)


def _read_repro_script(build_name: str) -> str:
    """
    Read repro script from a single build.

    :param build_name: Build name (e.g., 'docker', 'apple', 'dev_container')
    :return: Content of repro script
    """
    repro_file = f"tmp.pytest_failed.{build_name}.repro.sh"
    # TODO(ai_gp): Use dassert_file_exists
    if not os.path.exists(repro_file):
        _LOG.warning("Repro script not found: %s", repro_file)
        return ""
    return hio.from_file(repro_file)


def _extract_pytest_cmd(repro_content: str) -> str:
    """
    Extract pytest command from repro script.

    :param repro_content: Content of repro script
    :return: pytest command line
    """
    lines = repro_content.split("\n")
    for line in lines:
        line = line.strip()
        if line.startswith("pytest") or line.startswith("pytest_log"):
            return line
    return ""


# #############################################################################
# Consolidation logic
# #############################################################################


def _consolidate_failed_tests(build_names: List[str]) -> Dict[str, Set[str]]:
    """
    Consolidate failed tests across multiple builds.

    :param build_names: List of build names
    :return: Dict mapping test name to set of builds where it failed
    """
    test_to_builds: Dict[str, Set[str]] = {}
    for build_name in build_names:
        failed_tests = _read_failed_tests(build_name)
        for test_name in failed_tests:
            if test_name not in test_to_builds:
                test_to_builds[test_name] = set()
            test_to_builds[test_name].add(build_name)
    return test_to_builds


def _create_consolidated_repro(build_names: List[str]) -> str:
    """
    Create consolidated repro script from multiple builds.

    :param build_names: List of build names
    :return: Consolidated repro script content
    """
    header = "#!/bin/bash\n"
    header += "# Consolidated repro script for multiple builds\n"
    header += "# Run individual build repro scripts:\n\n"
    content = header
    for build_name in build_names:
        repro_file = f"tmp.pytest_failed.{build_name}.repro.sh"
        if os.path.exists(repro_file):
            docker_engine, use_docker_cmd = _BUILD_CONFIG.get(
                build_name, ("", False)
            )
            content += f"# Build: {build_name} (CSFY_DOCKER_ENGINE={docker_engine})\n"
            content += f"# bash {repro_file}\n"
            pytest_cmd = _extract_pytest_cmd(_read_repro_script(build_name))
            if pytest_cmd:
                if use_docker_cmd:
                    content += f"# invoke docker_cmd --stage=local -v 1.6.0 --cmd \"{pytest_cmd}\"\n"
                else:
                    content += f"# export CSFY_DOCKER_ENGINE='{docker_engine}'; {pytest_cmd}\n"
            content += "\n"
    return content


# TODO(ai_gp): _summary_to_str and then print
def _print_summary(
    build_names: List[str], test_to_builds: Dict[str, Set[str]]
) -> None:
    """
    Print summary of failing tests across builds.

    :param build_names: List of build names
    :param test_to_builds: Dict mapping test name to set of builds where it failed
    """
    # TODO(ai_gp): Create a str with all the results and return it
    print(hprint.frame("Failed Tests Summary"))
    print(
        f"{'Test Name':<70} {'Builds':<30}"
    )
    print("-" * 100)
    for test_name in sorted(test_to_builds.keys()):
        builds = ", ".join(sorted(test_to_builds[test_name]))
        print(f"{test_name:<70} {builds:<30}")
    print(f"\nTotal failing tests: {len(test_to_builds)}")
    print(f"Across builds: {', '.join(build_names)}")
    # Count tests failing in multiple builds.
    multi_build_failures = sum(
        1 for builds in test_to_builds.values() if len(builds) > 1
    )
    print(f"Tests failing in multiple builds: {multi_build_failures}")


def _parse() -> argparse.ArgumentParser:
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--build_names",
        nargs="+",
        default=["docker", "apple", "dev_container"],
        help="Build names to consolidate (default: docker apple dev_container)",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Execute consolidation of failed tests across multiple builds.
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    build_names = args.build_names
    _LOG.info("Consolidating failed tests for builds: %s", ", ".join(build_names))
    # Consolidate failed tests.
    test_to_builds = _consolidate_failed_tests(build_names)
    # Print summary.
    _print_summary(build_names, test_to_builds)
    # Create consolidated repro script.
    repro_content = _create_consolidated_repro(build_names)
    repro_file = "tmp.pytest_failed_multi_build.repro.sh"
    hio.to_file(repro_file, repro_content)
    _LOG.info("Created consolidated repro script: %s", repro_file)
    # Create consolidated failed tests file.
    all_failed_tests = sorted(test_to_builds.keys())
    failed_file = "tmp.pytest_failed_multi_build.failed_tests.txt"
    hio.to_file(failed_file, "\n".join(all_failed_tests))
    _LOG.info("Created consolidated failed tests file: %s", failed_file)


if __name__ == "__main__":
    _main(_parse())
