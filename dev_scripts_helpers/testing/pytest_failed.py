#!/usr/bin/env python

"""
Parse the failed tests out of a pytest log, print them, save a repro script,
and copy the test names to the clipboard.

For architecture overview, see `pytest_testing_system.README.md`.

Examples

# Parse failed tests from `tmp.pytest_log.txt`.
> pytest_failed.py

# Parse failed tests from a specific log file, keeping only the file names.
> pytest_failed.py --input tmp.log --only_file

# Parse failed tests from a specific log with build name.
> pytest_failed.py --input tmp.log --build_name apple

Creates the following files (with optional `build_name` subdirectory):
- tmp.pytest_failed.{build_name}/repro.sh: script to rerun failed tests
- tmp.pytest_failed.{build_name}/repro_classes.sh: script to rerun failed test
  classes
- tmp.pytest_failed.{build_name}/repro_files.sh: script to rerun failed test
  files
- tmp.pytest_failed.{build_name}/failed_tests.txt: list of failed tests
- tmp.pytest_failed.{build_name}/passed_tests.txt: list of passed tests
- tmp.pytest_failed.{build_name}/skipped_tests.txt: list of skipped tests
- tmp.pytest_failed.{build_name}/updated_tests.txt: list of tests whose golden
  outcome was updated
- tmp.pytest_failed.{build_name}/tests_by_duration.txt: tests ordered by
  duration
- tmp.pytest_failed.{build_name}/duration_stats.txt: duration statistics by
  file and class
- tmp.pytest_failed.{build_name}/stacktraces.txt: failure reason for each
  failed test
- tmp.pytest_failed.{build_name}/info.json: parsed test info from
  hpytest.parse_failed_tests()

When build_name is not provided, files are created in the current directory.
"""

import argparse
import logging
from typing import Any, Dict

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hpytest as hpytest
import helpers.htable as htable

_LOG = logging.getLogger(__name__)


# #############################################################################
# Build environment helpers
# #############################################################################


def _add_build_env_to_repro(content: str, build_name: str) -> str:
    """
    Add build-specific environment setup to repro script content.

    :param content: Script content to enhance
    :param build_name: Build name (e.g., 'docker', 'apple', 'dev_container')
    :return: Updated script content with build-specific environment setup
    """
    _LOG.debug(hprint.to_str("build_name"))
    hdbg.dassert_in(build_name, hpytest.BUILD_CONFIG)
    docker_engine, use_docker_cmd = hpytest.BUILD_CONFIG[build_name]
    # Prepend environment setup specific to the build configuration.
    header_parts = [
        "#!/bin/bash",
        f"# Repro script for build: {build_name}",
        f"export CSFY_DOCKER_ENGINE='{docker_engine}'",
    ]
    if use_docker_cmd:
        header_parts.extend(
            [
                "# Note: This build requires docker_cmd wrapper",
                '# Run commands with: invoke docker_cmd --stage=local -v 1.6.0 --cmd "<command>"',
            ]
        )
    header = "\n".join(header_parts) + "\n\n"
    # Remove shebang from existing content to avoid duplication when prepending header.
    if content.startswith("#!/bin/bash"):
        first_newline = content.find("\n")
        if first_newline != -1:
            content = content[first_newline + 1 :]
    updated_content = header + content
    _LOG.debug("return=%s bytes", len(updated_content))
    return updated_content


# #############################################################################
# Parsing
# #############################################################################


def _format_outcome_table(result: Dict[str, Any]) -> str:
    """
    Format test outcome results as a table.

    :param result: Result dict from _process_single_file
    :return: Formatted table string
    """
    _LOG.debug("result keys=%s", list(result.keys()))
    lines = [hprint.frame("Test Outcome Summary")]
    # Convert result dict to table row with test counts and status.
    table_data = [
        [
            result["build"],
            result["passed"],
            str(result["num_passed"]),
            str(result["num_skipped"]),
            str(result["num_failed"]),
            str(result["num_total"]),
            f"{result['duration']:.2f}s" if "duration" in result else "N/A",
        ]
    ]
    # Create and format table.
    table_obj = htable.Table(
        table_data,
        ["Build", "Status", "Passed", "Skipped", "Failed", "Total", "Duration"],
    )
    lines.append(str(table_obj))
    result_str = "\n".join(lines)
    _LOG.debug("return=%s bytes", len(result_str))
    return result_str


def _process_single_file(
    file_path: str, *, build_name: str = ""
) -> Dict[str, Any]:
    """
    Process a single pytest log file and return summary info.

    :param file_path: Path to pytest log file
    :param build_name: Build name for output file naming
        - E.g., 'docker', 'apple', 'dev_container'
    """
    _LOG.debug(hprint.to_str("file_path build_name"))
    _LOG.info("Reading '%s'", file_path)
    txt = hio.from_file(file_path)
    _LOG.info("Parsing '%s'", file_path)
    lines = txt.split("\n")
    info = hpytest.parse_failed_tests(lines)
    # Print parsed test results summary.
    print(hpytest.info_to_str(info))
    # Write main repro script for failed tests.
    failed_tests = info["log_failed_tests"]
    repro_file = hpytest.get_output_file_path("repro.sh", build_name=build_name)
    hpytest.write_repro_script(
        failed_tests,
        "Repro script for the failed tests",
        repro_file,
    )
    if build_name:
        content = hio.from_file(repro_file)
        updated_content = _add_build_env_to_repro(content, build_name)
        hio.to_file(repro_file, updated_content)
        _LOG.info("Updated repro script: %s", repro_file)
    # Write repro script for failed test classes.
    failed_classes = hpytest.filter_failed_tests(
        failed_tests, only_file=False, only_class=True
    )
    repro_classes_file = hpytest.get_output_file_path(
        "repro_classes.sh", build_name=build_name
    )
    hpytest.write_repro_script(
        failed_classes,
        "Repro script for the classes containing failed tests",
        repro_classes_file,
    )
    # Write repro script for failed test files.
    failed_files = hpytest.filter_failed_tests(
        failed_tests, only_file=True, only_class=False
    )
    repro_files_file = hpytest.get_output_file_path(
        "repro_files.sh", build_name=build_name
    )
    hpytest.write_repro_script(
        failed_files,
        "Repro script for the files containing failed tests",
        repro_files_file,
    )
    # Print failed tests to console.
    print(hprint.frame("Failed tests"))
    print("\n".join(failed_tests))
    # - Write test result files (passed, failed, skipped, updated).
    # Passed.
    passed_tests_file = hpytest.get_output_file_path(
        "passed_tests.txt", build_name=build_name
    )
    hpytest.write_passed_tests(info, passed_tests_file)
    _LOG.info("Created '%s'", passed_tests_file)
    # Failed.
    failed_tests_file = hpytest.get_output_file_path(
        "failed_tests.txt", build_name=build_name
    )
    hpytest.write_failed_tests(info, failed_tests_file)
    _LOG.info("Created '%s'", failed_tests_file)
    # Skipped.
    skipped_tests_file = hpytest.get_output_file_path(
        "skipped_tests.txt", build_name=build_name
    )
    hpytest.write_skipped_tests(info, skipped_tests_file)
    _LOG.info("Created '%s'", skipped_tests_file)
    # Updated.
    updated_tests_file = hpytest.get_output_file_path(
        "updated_tests.txt", build_name=build_name
    )
    hpytest.write_updated_tests(info, updated_tests_file)
    _LOG.info("Created '%s'", updated_tests_file)
    # - Write analysis files (duration, stacktraces, json info).
    # By duration.
    tests_by_duration_file = hpytest.get_output_file_path(
        "tests_by_duration.txt", build_name=build_name
    )
    hpytest.write_tests_by_duration(info, tests_by_duration_file)
    _LOG.info("Created '%s'", tests_by_duration_file)
    # Stats.
    duration_stats_file = hpytest.get_output_file_path(
        "duration_stats.txt", build_name=build_name
    )
    hpytest.write_duration_stats(info, duration_stats_file)
    _LOG.info("Created '%s'", duration_stats_file)
    # Stacktraces.
    stacktraces_file = hpytest.get_output_file_path(
        "stacktraces.txt", build_name=build_name
    )
    hpytest.write_test_stacktraces(info, stacktraces_file)
    _LOG.info("Created '%s'", stacktraces_file)
    # Info.
    info_json_file = hpytest.get_output_file_path(
        "info.json", build_name=build_name
    )
    hio.to_json(info_json_file, info)
    _LOG.info("Created '%s'", info_json_file)
    # Extract summary statistics from parsed info.
    num_passed = len(info["log_passed_tests"]) if info["log_passed_tests"] else 0
    num_skipped = (
        len(info["log_skipped_tests"]) if info["log_skipped_tests"] else 0
    )
    num_failed = len(info["log_failed_tests"]) if info["log_failed_tests"] else 0
    num_total = num_passed + num_skipped + num_failed
    passed = "PASS" if num_failed == 0 else "FAIL"
    # Prefer the final summary line's duration; fall back to summing per-test
    # durations when the run didn't complete before printing the final summary.
    total_duration = info.get("pytest_duration_in_secs") or 0.0
    # TODO(ai_gp): Make this part of info.
    if total_duration == 0.0:
        total_duration = sum((info.get("log_test_durations") or {}).values())
    result = {
        "build": file_path,
        "passed": passed,
        "num_passed": num_passed,
        "num_skipped": num_skipped,
        "num_failed": num_failed,
        "num_total": num_total,
        "duration": total_duration,
    }
    _LOG.debug("return=%s", result)
    return result


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-i",
        "--input",
        action="store",
        default="tmp.pytest_log.txt",
        help="Pytest log file to parse for failed tests",
    )
    parser.add_argument(
        "--build_name",
        action="store",
        default="",
        help="Build name for output file naming (e.g., 'docker', 'apple', 'dev_container')",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    _LOG.debug("_main called")
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Process the pytest log file to extract and organize failed tests.
    result = _process_single_file(args.input, build_name=args.build_name)
    # Print outcome summary table with test counts and overall status.
    print("\n" + _format_outcome_table(result))


if __name__ == "__main__":
    _main(_parse())
