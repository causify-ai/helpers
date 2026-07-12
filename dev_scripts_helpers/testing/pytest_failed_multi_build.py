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
import sys
from typing import Any, Dict, List, Set

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.htable as htable
import helpers.hpytest as hpytest

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
    _LOG.debug(hprint.to_str("build_name"))
    info_file = hpytest.get_output_file_path("info.json", build_name=build_name)
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
    _LOG.debug("return=%s", res)
    return res


def _generate_build_files(build_names: List[str]) -> List[Dict[str, Any]]:
    """
    Generate output files for each build by calling `pytest_failed.py`.

    :param build_names: List of build names
        - E.g., ['docker', 'apple', 'dev_container']
    :return: List of build statistics dicts
    """
    _LOG.debug(hprint.to_str("build_names"))
    # Locate `pytest_failed.py` script in the same directory.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pytest_failed_script = os.path.join(script_dir, "pytest_failed.py")
    hdbg.dassert_file_exists(pytest_failed_script)
    # Execute pytest_failed.py for each build configuration.
    build_stats = []
    for build_name in build_names:
        input_file = f"tmp.pytest_multi_build.{build_name}.txt"
        hdbg.dassert_file_exists(input_file)
        _LOG.info("Processing %s from %s", build_name, input_file)
        # Build command to execute `pytest_failed.py` for this build.
        cmd = " ".join(
            [
                sys.executable,
                pytest_failed_script,
                "--input",
                input_file,
                "--build_name",
                build_name,
            ]
        )
        hsystem.system(cmd)
        # Extract build statistics from generated output.
        stats = _extract_build_stats(build_name)
        build_stats.append(stats)
    _LOG.debug("return=%s items", len(build_stats))
    return build_stats


# #############################################################################
# Consolidate failed tests.
# #############################################################################


def _read_failed_tests(build_name: str) -> List[str]:
    """
    Read failed tests from a single build.

    :param build_name: Build name
    :return: List of failed test names
    """
    _LOG.debug(hprint.to_str("build_name"))
    failed_file = hpytest.get_output_file_path(
        "failed_tests.txt", build_name=build_name
    )
    hdbg.dassert_file_exists(failed_file)
    txt = hio.from_file(failed_file)
    # Parse file content into list of non-empty test names.
    lines = [line.strip() for line in txt.split("\n") if line.strip()]
    _LOG.debug("return=%s tests", len(lines))
    return lines


def _consolidate_failed_tests(build_names: List[str]) -> Dict[str, Set[str]]:
    """
    Consolidate failed tests across multiple builds.

    :param build_names: List of build names
    :return: Dict mapping test name to set of builds where it failed
    """
    _LOG.debug(hprint.to_str("build_names"))
    test_to_builds: Dict[str, Set[str]] = {}
    # Read failed tests from each build and build a mapping of test -> builds.
    for build_name in build_names:
        failed_tests = _read_failed_tests(build_name)
        for test_name in failed_tests:
            if test_name not in test_to_builds:
                test_to_builds[test_name] = set()
            test_to_builds[test_name].add(build_name)
    _LOG.debug(
        "return=%s tests across %d builds", len(test_to_builds), len(build_names)
    )
    return test_to_builds


# #############################################################################
# Consolidate repro script.
# #############################################################################


def _read_repro_script(build_name: str) -> str:
    """
    Read repro script from a single build.

    :param build_name: Build name
    :return: Content of repro script
    """
    _LOG.debug(hprint.to_str("build_name"))
    repro_file = hpytest.get_output_file_path("repro.sh", build_name=build_name)
    hdbg.dassert_file_exists(repro_file)
    content = hio.from_file(repro_file)
    _LOG.debug("return=%s bytes", len(content))
    return content


# TODO(gp): Consider simplifying the parsing logic: the function extracts test
# names from repro scripts but could potentially concatenate all scripts
# instead of parsing each one individually.
def _extract_tests_from_repro(repro_content: str) -> List[str]:
    """
    Extract test names from repro script.

    :param repro_content: Content of repro script
    :return: List of test names
    """
    _LOG.debug("repro_content len=%s", len(repro_content))
    lines = repro_content.split("\n")
    # Parse the pytest_log line to extract all test names.
    for line in lines:
        line = line.strip()
        if line.startswith("pytest_log"):
            # Extract test names from: pytest_log test1 test2 test3 ... $*
            parts = line.split()
            if len(parts) > 1:
                tests = parts[1:]
                # Remove trailing $* placeholder if present.
                if tests and tests[-1] == "$*":
                    tests = tests[:-1]
                _LOG.debug("return=%s tests", len(tests))
                return tests
    _LOG.debug("return=no tests found")
    return []


def _create_consolidated_repro(build_names: List[str]) -> str:
    """
    Create consolidated repro script from multiple builds.

    :param build_names: List of build names
        - Example: `['docker', 'apple', 'dev_container']`
    :return: Consolidated repro script content, e.g.,
        ```
        #!/bin/bash
        # Consolidated repro script for multiple builds.

        # Build: docker
        pytest tests/test_module.py::TestClass::test_method1 ...

        # Build: apple
        pytest tests/test_module.py::TestClass::test_method2 ...
        ```
    """
    _LOG.debug(hprint.to_str("build_names"))
    header = "#!/bin/bash\n"
    header += "# Consolidated repro script for multiple builds.\n\n"
    content = header
    # Merge repro scripts from each build, extracting test names and rebuilding commands.
    for build_name in build_names:
        repro_file = hpytest.get_output_file_path(
            "repro.sh", build_name=build_name
        )
        hdbg.dassert_file_exists(repro_file)
        repro_content = _read_repro_script(build_name)
        tests = _extract_tests_from_repro(repro_content)
        if tests:
            content += f"# Build: {build_name}\n"
            cmd = hpytest.get_build_command(tests, build_name)
            content += f"{cmd}\n"
            content += "\n"
    _LOG.debug("return=%s bytes", len(content))
    return content


def _build_stats_to_str(build_stats: List[Dict[str, Any]]) -> str:
    """
    Format build statistics as a table.

    :param build_stats: List of build statistics dicts
    :return: Formatted table string, e.g.,
        ```
        Build          Status   Passed   Skipped   Failed   Total   Duration
        -----------------------------------------------------------------------
        docker         PASS      1234        0       10      1244       45.2s
        apple          FAIL      1230        2       12      1244       52.1s
        dev_container  PASS      1232        1       11      1244       48.5s
        ```
    """
    _LOG.debug("build_stats=%s items", len(build_stats))
    lines = [hprint.frame("Build Statistics")]
    # Convert each build stat dict to table row with pass/fail status.
    table_data = []
    for stats in build_stats:
        status = "PASS" if stats["failed"] == 0 else "FAIL"
        table_data.append(
            [
                stats["build"],
                status,
                str(stats["passed"]),
                str(stats["skipped"]),
                str(stats["failed"]),
                str(stats["total"]),
                str(stats["duration"]),
            ]
        )
    # Create and format table.
    table_obj = htable.Table(
        table_data,
        ["Build", "Status", "Passed", "Skipped", "Failed", "Total", "Duration"],
    )
    lines.append(str(table_obj))
    result = "\n".join(lines)
    _LOG.debug("return=%s bytes", len(result))
    return result


def _failed_tests_table_to_str(test_to_builds: Dict[str, Set[str]]) -> str:
    """
    Create formatted table of failing tests for file output.

    :param test_to_builds: Dict mapping test name to set of builds where it failed
        - Example: `{'test1': {'docker', 'apple'}, 'test2': {'docker'}}`
    :return: Formatted table string, e.g.,
        ```
        Test Name              Builds
        -------------------------------------------
        tests/test_module.py::test1   docker, apple
        tests/test_module.py::test2   docker
        ```
    """
    _LOG.debug("test_to_builds=%s tests", len(test_to_builds))
    # Build table with test names and the builds where they failed.
    table_data = []
    for test_name in sorted(test_to_builds.keys()):
        builds = ", ".join(sorted(test_to_builds[test_name]))
        table_data.append([test_name, builds])
    # Create and format table.
    table_obj = htable.Table(table_data, ["Test Name", "Builds"])
    result = str(table_obj)
    _LOG.debug("return=%s bytes", len(result))
    return result


def _summary_to_str(
    build_names: List[str], test_to_builds: Dict[str, Set[str]]
) -> str:
    """
    Create summary of failing tests across builds.

    :param build_names: List of build names
    :param test_to_builds: Dict mapping test name to set of builds where it failed
    :return: Summary string, e.g.,
        ```
        Test Name                                              Builds
        -----------------------------------------------------------------------------
        tests/core/test_module.py::TestClass::test_method1      docker, apple
        tests/core/test_module.py::TestClass::test_method2      docker
        tests/data/test_pipeline.py::TestPipeline::test_run     apple, dev_container

        Total failing tests: 3
        Across builds: docker, apple, dev_container
        Tests failing in multiple builds: 1
        ```
    """
    _LOG.debug(hprint.to_str("build_names"))
    lines = [hprint.frame("Failed Tests Summary")]
    lines.append(_failed_tests_table_to_str(test_to_builds))
    lines.append(f"\nTotal failing tests: {len(test_to_builds)}")
    lines.append(f"Across builds: {', '.join(build_names)}")
    # Count tests that fail across multiple builds (likely infrastructure
    # issues).
    multi_build_failures = sum(
        1 for builds in test_to_builds.values() if len(builds) > 1
    )
    lines.append(f"Tests failing in multiple builds: {multi_build_failures}")
    result = "\n".join(lines)
    _LOG.debug("return=%s bytes", len(result))
    return result


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
    _LOG.debug("_main called")
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    build_names = args.build_names
    _LOG.info(
        "Consolidating failed tests for builds: %s", ", ".join(build_names)
    )
    # Generate pytest_failed output files for each build by invoking
    # `pytest_failed.py`.
    _LOG.info("Generating intermediate files by calling pytest_failed.py...")
    build_stats = _generate_build_files(build_names)
    # Print build statistics summary.
    stats_summary = _build_stats_to_str(build_stats)
    print(stats_summary)
    # Consolidate failed tests across all builds to identify common failures.
    test_to_builds = _consolidate_failed_tests(build_names)
    # Print summary of failures.
    summary = _summary_to_str(build_names, test_to_builds)
    print(summary)
    # Create consolidated repro script combining tests from all builds.
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
