#!/usr/bin/env python

"""
Consolidate failed tests across multiple build configurations.

- Read output from multiple builds from `pytest_failed.py`
- Create a summary of tests failing across the builds
- Consolidate all repro commands in a single one

For architecture overview, see `pytest_testing_system.README.md`.

Examples:
> pytest_failed_multi_build.py

> pytest_failed_multi_build.py --build_names docker apple dev_container
"""

import argparse
import logging
import os
import subprocess
import sys
from typing import Any, Dict, List, Set

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint
import dev_scripts_helpers.testing.pytest_utils as dshtpyut

_LOG = logging.getLogger(__name__)


# #############################################################################
# Generate intermediate files by calling pytest_failed.py
# #############################################################################


def _extract_build_stats(build_name: str) -> Dict[str, Any]:
    """
    Extract build statistics from JSON info file.

    :param build_name: Build name (e.g., 'docker', 'apple', 'dev_container')
    :return: Dict with build stats
    """
    # Read file.
    info_file = dshtpyut.get_output_file_path("info.json", build_name=build_name)
    hdbg.dassert_file_exists(info_file)
    info = hio.from_json(info_file)
    # Extract info.
    num_passed = info.get("log_num_passed", 0) or 0
    num_failed = info.get("log_num_failed", 0) or 0
    num_skipped = info.get("log_num_skipped", 0) or 0
    num_total = num_passed + num_failed + num_skipped
    duration = f"{info['pytest_duration_in_secs']}s"
    # Assemble result.
    res = {
        "build": build_name,
        "passed": num_passed,
        "skipped": num_skipped,
        "failed": num_failed,
        "total": num_total,
        "duration": duration,
    }
    return res


def _generate_build_files(build_names: List[str]) -> List[Dict[str, Any]]:
    """
    Generate pytest_failed output files for each build by calling pytest_failed.py.

    :param build_names: List of build names (e.g., ['docker', 'apple', 'dev_container'])
    :return: List of build statistics dicts
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pytest_failed_script = os.path.join(script_dir, "pytest_failed.py")
    hdbg.dassert_file_exists(pytest_failed_script)

    build_stats = []
    for build_name in build_names:
        input_file = f"tmp.pytest_multi_build.{build_name}.txt"
        if not os.path.exists(input_file):
            _LOG.warning(
                "Input file not found: %s (skipping %s)", input_file, build_name
            )
            continue

        _LOG.info("Processing %s from %s", build_name, input_file)
        cmd = [
            sys.executable,
            pytest_failed_script,
            "--input",
            input_file,
            "--build_name",
            build_name,
        ]
        # TODO(ai_gp): Use hsystem.system
        result = subprocess.run(cmd, capture_output=False)
        if result.returncode != 0:
            _LOG.error("Failed to process %s", build_name)
            sys.exit(1)

        stats = _extract_build_stats(build_name)
        build_stats.append(stats)

    return build_stats


# #############################################################################
# File reading helpers
# #############################################################################


def _read_failed_tests(build_name: str) -> List[str]:
    """
    Read failed tests from a single build.

    :param build_name: Build name (e.g., 'docker', 'apple', 'dev_container')
    :return: List of failed test names
    """
    failed_file = dshtpyut.get_output_file_path(
        "failed_tests.txt", build_name=build_name
    )
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
    repro_file = dshtpyut.get_output_file_path("repro.sh", build_name=build_name)
    hdbg.dassert_file_exists(repro_file)
    return hio.from_file(repro_file)


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


def _extract_tests_from_repro(repro_content: str) -> List[str]:
    """
    Extract test names from repro script.

    :param repro_content: Content of repro script
    :return: List of test names
    """
    lines = repro_content.split("\n")
    for line in lines:
        line = line.strip()
        if line.startswith("pytest_log"):
            # Extract everything after "pytest_log "
            # Format: pytest_log test1 test2 test3 ... $*
            parts = line.split()
            if len(parts) > 1:
                # Remove "pytest_log" and "$*" from the end
                tests = parts[1:]
                if tests and tests[-1] == "$*":
                    tests = tests[:-1]
                return tests
    return []


def _create_consolidated_repro(build_names: List[str]) -> str:
    """
    Create consolidated repro script from multiple builds.

    :param build_names: List of build names
    :return: Consolidated repro script content
    """
    header = "#!/bin/bash\n"
    header += "# Consolidated repro script for multiple builds.\n\n"
    content = header
    for build_name in build_names:
        repro_file = dshtpyut.get_output_file_path(
            "repro.sh", build_name=build_name
        )
        if os.path.exists(repro_file):
            repro_content = _read_repro_script(build_name)
            tests = _extract_tests_from_repro(repro_content)

            if tests:
                content += f"# Build: {build_name}\n"
                cmd = dshtpyut.get_build_command(tests, build_name)
                content += f"{cmd}\n"
                content += "\n"
    return content


def _build_stats_to_str(build_stats: List[Dict[str, Any]]) -> str:
    """
    Format build statistics as a table.

    :param build_stats: List of build statistics dicts
    :return: Formatted table string
    """
    lines = [hprint.frame("Build Statistics")]
    lines.append(
        f"{'Build':<20} {'Passed':>8} {'Skipped':>8} {'Failed':>8} {'Total':>8} {'Duration':>10}"
    )
    lines.append("-" * 70)
    for stats in build_stats:
        lines.append(
            f"{stats['build']:<20} {stats['passed']:>8} {stats['skipped']:>8} "
            f"{stats['failed']:>8} {stats['total']:>8} {str(stats['duration']):>10}"
        )
    return "\n".join(lines)


def _failed_tests_table_to_str(test_to_builds: Dict[str, Set[str]]) -> str:
    """
    Create formatted table of failing tests for file output.

    :param test_to_builds: Dict mapping test name to set of builds where it failed
    :return: Formatted table string
    """
    lines = []
    lines.append(f"{'Test Name':<70} {'Builds':<30}")
    lines.append("-" * 100)
    for test_name in sorted(test_to_builds.keys()):
        builds = ", ".join(sorted(test_to_builds[test_name]))
        lines.append(f"{test_name:<70} {builds:<30}")
    return "\n".join(lines)


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
    lines.append(_failed_tests_table_to_str(test_to_builds))
    lines.append(f"\nTotal failing tests: {len(test_to_builds)}")
    lines.append(f"Across builds: {', '.join(build_names)}")
    # Count tests failing in multiple builds.
    multi_build_failures = sum(
        1 for builds in test_to_builds.values() if len(builds) > 1
    )
    lines.append(f"Tests failing in multiple builds: {multi_build_failures}")
    return "\n".join(lines)


# #############################################################################
# CLI
# #############################################################################


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
    _LOG.info(
        "Consolidating failed tests for builds: %s", ", ".join(build_names)
    )
    # Generate pytest_failed output files for each build.
    _LOG.info("Generating intermediate files by calling pytest_failed.py...")
    build_stats = _generate_build_files(build_names)
    # Print build statistics.
    stats_summary = _build_stats_to_str(build_stats)
    print(stats_summary)
    # Consolidate failed tests.
    test_to_builds = _consolidate_failed_tests(build_names)
    # Print summary.
    summary = _summary_to_str(build_names, test_to_builds)
    print(summary)
    # Create consolidated repro script.
    repro_content = _create_consolidated_repro(build_names)
    repro_file = "tmp.pytest_failed_multi_build.repro.sh"
    hio.create_executable_script(repro_file, repro_content)
    _LOG.info("Created consolidated repro script: %s", repro_file)
    # Create consolidated failed tests file with formatted table.
    failed_table = _failed_tests_table_to_str(test_to_builds)
    failed_file = "tmp.pytest_failed_multi_build.failed_tests.txt"
    hio.to_file(failed_file, failed_table)
    _LOG.info("Created consolidated failed tests file: %s", failed_file)


if __name__ == "__main__":
    _main(_parse())
