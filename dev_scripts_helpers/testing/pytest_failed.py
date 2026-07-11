#!/usr/bin/env python

"""
Parse the failed tests out of a pytest log, print them, save a repro script,
and copy the test names to the clipboard.

Examples

# Parse failed tests from `tmp.pytest_log.txt`.
> pytest_failed.py

# Parse failed tests from a specific log file, keeping only the file names.
> pytest_failed.py --input tmp.log --only_file

Creates the following files:
- tmp.pytest_failed.repro.sh: script to rerun failed tests
- tmp.pytest_failed.repro_classes.sh: script to rerun failed test classes
- tmp.pytest_failed.repro_files.sh: script to rerun failed test files
- tmp.pytest_failed.failed_tests.txt: list of failed tests
- tmp.pytest_failed.passed_tests.txt: list of passed tests
- tmp.pytest_failed.skipped_tests.txt: list of skipped tests
- tmp.pytest_failed.updated_tests.txt: list of tests whose golden outcome was updated
- tmp.pytest_failed.tests_by_duration.txt: tests ordered by duration
- tmp.pytest_failed.duration_stats.txt: duration statistics by file and class
- tmp.pytest_failed.stacktraces.txt: failure reason for each failed test
"""

import argparse
import logging
import os
from typing import Dict, Tuple

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hpytest as hpytest

_LOG = logging.getLogger(__name__)

# Build configurations: name -> (docker_engine, use_docker_cmd)
_BUILD_CONFIG: Dict[str, Tuple[str, bool]] = {
    "docker": ("docker", False),
    "apple": ("apple", False),
    "dev_container": ("docker", True),
}


# #############################################################################
# Build environment helpers
# #############################################################################


def _add_build_env_to_repro(repro_file: str, build_name: str) -> None:
    """
    Add build-specific environment setup to repro script.

    :param repro_file: Path to the repro script file
    :param build_name: Build name (e.g., 'docker', 'apple', 'dev_container')
    """
    # TODO(ai_gp): Use hdassert_in
    if build_name not in _BUILD_CONFIG:
        _LOG.warning("Unknown build name: %s", build_name)
        return
    docker_engine, use_docker_cmd = _BUILD_CONFIG[build_name]
    # Read existing repro script.
    # TODO(ai_gp): Use hdassert_file_exists
    if not os.path.exists(repro_file):
        _LOG.warning("Repro file does not exist: %s", repro_file)
        return
    content = hio.from_file(repro_file)
    # Prepend environment setup.
    # TODO(ai_gp): Use """ and hprint.dedent
    header = f"#!/bin/bash\n# Repro script for build: {build_name}\nexport CSFY_DOCKER_ENGINE='{docker_engine}'\n"
    # TODO(ai_gp): Add the invoke ... around each commands
    if use_docker_cmd:
        header += "# Note: This build requires docker_cmd wrapper\n"
        header += "# Run commands with: invoke docker_cmd --stage=local -v 1.6.0 --cmd \"<command>\"\n"
    header += "\n"
    # Remove shebang from existing content if present.
    if content.startswith("#!/bin/bash"):
        content = content[len("#!/bin/bash\n"):]
    updated_content = header + content
    hio.to_file(repro_file, updated_content)
    _LOG.info("Updated repro script: %s", repro_file)


# #############################################################################
# Parsing
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-i",
        "--input",
        action="store",
        default=None,
        help="Pytest log file to parse for failed tests",
    )
    # TODO(ai_gp): Remove this.
    group.add_argument(
        "--files",
        nargs="+",
        default=None,
        help="Multiple pytest log files to parse (space-separated)",
    )
    parser.add_argument(
        "--build_name",
        action="store",
        default="",
        help="Build name for output file naming (e.g., 'docker', 'apple', 'dev_container')",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _get_output_filename(base: str, *, build_name: str = "") -> str:
    """
    Get output filename with optional build_name encoding.

    :param base: Base filename (e.g., 'tmp.pytest_failed')
    :param build_name: Optional build name to encode in filename
    :return: Full filename
    """
    if build_name:
        # Insert build_name after the base: tmp.pytest_failed.docker.ext
        parts = base.rsplit(".", 1)
        if len(parts) == 2:
            return f"{parts[0]}.{build_name}.{parts[1]}"
        return f"{base}.{build_name}"
    return base


def _process_single_file(file_path: str, *, build_name: str = "") -> Dict[str, str]:
    """
    Process a single pytest log file and return summary info.

    :param file_path: Path to pytest log file
    :param build_name: Build name for output file naming (e.g., 'docker', 'apple', 'dev_container')
    """
    _LOG.info("Reading '%s'", file_path)
    txt = hio.from_file(file_path)
    _LOG.info("Parsing '%s'", file_path)
    lines = txt.split("\n")
    info = hpytest.parse_failed_tests(lines)
    # Print the results.
    print(hpytest.info_to_str(info))
    # Write the repro scripts with build-specific naming if provided.
    failed_tests = info["log_failed_tests"]
    repro_file = _get_output_filename("tmp.pytest_failed.repro.sh", build_name)
    hpytest.write_repro_script(
        failed_tests,
        "Repro script for the failed tests",
        repro_file,
    )
    # Add environment setup to the repro script if build_name is provided.
    if build_name:
        _add_build_env_to_repro(repro_file, build_name)
    #
    failed_classes = hpytest.filter_failed_tests(
        failed_tests, only_file=False, only_class=True
    )
    repro_classes_file = _get_output_filename("tmp.pytest_failed.repro_classes.sh", build_name)
    hpytest.write_repro_script(
        failed_classes,
        "Repro script for the classes containing failed tests",
        repro_classes_file,
    )
    #
    failed_files = hpytest.filter_failed_tests(
        failed_tests, only_file=True, only_class=False
    )
    repro_files_file = _get_output_filename("tmp.pytest_failed.repro_files.sh", build_name)
    hpytest.write_repro_script(
        failed_files,
        "Repro script for the files containing failed tests",
        repro_files_file,
    )
    # Write the reports.
    print(hprint.frame("Failed tests"))
    print("\n".join(failed_tests))
    #
    print(hprint.frame("Test info"))
    passed_tests_file = _get_output_filename("tmp.pytest_failed.passed_tests.txt", build_name)
    hpytest.write_passed_tests(info, passed_tests_file)
    _LOG.info("Created '%s'", passed_tests_file)
    #
    failed_tests_file = _get_output_filename("tmp.pytest_failed.failed_tests.txt", build_name)
    hpytest.write_failed_tests(info, failed_tests_file)
    _LOG.info("Created '%s'", failed_tests_file)
    #
    skipped_tests_file = _get_output_filename("tmp.pytest_failed.skipped_tests.txt", build_name)
    hpytest.write_skipped_tests(info, skipped_tests_file)
    _LOG.info("Created '%s'", skipped_tests_file)
    #
    updated_tests_file = _get_output_filename("tmp.pytest_failed.updated_tests.txt", build_name)
    hpytest.write_updated_tests(info, updated_tests_file)
    _LOG.info("Created '%s'", updated_tests_file)
    #
    tests_by_duration_file = _get_output_filename("tmp.pytest_failed.tests_by_duration.txt", build_name)
    hpytest.write_tests_by_duration(info, tests_by_duration_file)
    _LOG.info("Created '%s'", tests_by_duration_file)
    #
    duration_stats_file = _get_output_filename("tmp.pytest_failed.duration_stats.txt", build_name)
    hpytest.write_duration_stats(info, duration_stats_file)
    _LOG.info("Created '%s'", duration_stats_file)
    #
    stacktraces_file = _get_output_filename("tmp.pytest_failed.stacktraces.txt", build_name)
    hpytest.write_test_stacktraces(info, stacktraces_file)
    _LOG.info("Created '%s'", stacktraces_file)
    # Extract summary info.
    num_passed = len(info["log_passed_tests"]) if info["log_passed_tests"] else 0
    num_skipped = (
        len(info["log_skipped_tests"]) if info["log_skipped_tests"] else 0
    )
    num_failed = len(info["log_failed_tests"]) if info["log_failed_tests"] else 0
    num_total = num_passed + num_skipped + num_failed
    passed = "PASS" if num_failed == 0 else "FAIL"
    return {
        "build": file_path,
        "passed": passed,
        "num_passed": num_passed,
        "num_skipped": num_skipped,
        "num_failed": num_failed,
        "num_total": num_total,
    }


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Determine input files.
    # TODO(ai_gp): Remove the iteration around args.files.
    files = []
    if args.files:
        files = args.files
    elif args.input:
        files = [args.input]
    else:
        files = ["tmp.pytest_log.txt"]
    # Process each file and collect summary info.
    summary = []
    for file_path in files:
        summary.append(_process_single_file(file_path, args.build_name))
    # Print summary table.
    # TODO(ai_gp): Remove this since there is a single build.
    if len(files) > 1:
        print(hprint.frame("Summary"))
        print(
            f"{'Build':<50} {'Status':<6} {'Passed':<8} {'Skipped':<8} {'Failed':<8} {'Total':<8}"
        )
        print("-" * 88)
        for row in summary:
            print(
                f"{row['build']:<50} {row['passed']:<6} "
                f"{row['num_passed']:<8} {row['num_skipped']:<8} "
                f"{row['num_failed']:<8} {row['num_total']:<8}"
            )


if __name__ == "__main__":
    _main(_parse())
