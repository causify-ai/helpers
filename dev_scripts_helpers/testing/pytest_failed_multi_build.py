#!/usr/bin/env python

"""
Consolidate failed tests across multiple build configurations.

For architecture overview, see pytest_testing_system.README.md

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
import dev_scripts_helpers.testing.pytest_utils as putils

_LOG = logging.getLogger(__name__)


# #############################################################################
# File reading helpers
# #############################################################################


def _read_failed_tests(build_name: str) -> List[str]:
    """
    Read failed tests from a single build.

    :param build_name: Build name (e.g., 'docker', 'apple', 'dev_container')
    :return: List of failed test names
    """
    failed_file = f"tmp.pytest_failed.{build_name}.failed_tests.txt"
    hdbg.dassert_file_exists(failed_file)
    txt = hio.from_file(failed_file)
    lines = [line.strip() for line in txt.split("\n") if line.strip()]
    return lines


def _read_repro_script(build_name: str) -> str:
    """
    Read repro script from a single build.

    :param build_name: Build name (e.g., 'docker', 'apple', 'dev_container')
    :return: Content of repro script
    """
    repro_file = f"tmp.pytest_failed.{build_name}.repro.sh"
    hdbg.dassert_file_exists(repro_file)
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
            docker_engine, use_docker_cmd = putils.BUILD_CONFIG.get(
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


def _summary_to_str(
    build_names: List[str], test_to_builds: Dict[str, Set[str]]
) -> str:
    """
    Create summary of failing tests across builds.

    :param build_names: List of build names
    :param test_to_builds: Dict mapping test name to set of builds where it failed
    :return: Summary string
    """
    lines = [hprint.frame("Failed Tests Summary")]
    lines.append(f"{'Test Name':<70} {'Builds':<30}")
    lines.append("-" * 100)
    for test_name in sorted(test_to_builds.keys()):
        builds = ", ".join(sorted(test_to_builds[test_name]))
        lines.append(f"{test_name:<70} {builds:<30}")
    lines.append(f"\nTotal failing tests: {len(test_to_builds)}")
    lines.append(f"Across builds: {', '.join(build_names)}")
    # Count tests failing in multiple builds.
    multi_build_failures = sum(
        1 for builds in test_to_builds.values() if len(builds) > 1
    )
    lines.append(f"Tests failing in multiple builds: {multi_build_failures}")
    return "\n".join(lines)


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
    summary = _summary_to_str(build_names, test_to_builds)
    print(summary)
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
