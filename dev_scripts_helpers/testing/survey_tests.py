#!/usr/bin/env python

"""
Survey test files in a codebase to map test classes and methods with skip
status.

This script recursively searches for test directories and analyzes Python test
files to create a comprehensive mapping of test classes, methods, and their skip
status.

Examples:
# Survey current directory
> survey_tests.py -dir .

# Survey specific directory
> survey_tests.py -dir /path/to/project

# Survey with verbose output
> survey_tests.py --dir /path/to/project --log_level DEBUG

Import as:

import survey_tests as surtes
"""

import argparse
import json
import logging
import pprint

import dev_scripts_helpers.testing.survey_tests_lib as dshtsteli
import helpers.hdbg as hdbg
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-d",
        "--dir",
        nargs="?",
        default=".",
        help="Root directory to search for tests (default: current directory)",
    )
    parser.add_argument(
        "--output_format",
        choices=["pretty", "json"],
        default="pretty",
        help="Output format for results (default: pretty)",
    )
    parser.add_argument(
        "--output_file", help="Output file to write results (default: stdout)"
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _format_results(test_map: dshtsteli.TestFileMap, format_type: str) -> str:
    """
    Format the test survey results for output.

    :param test_map: the test file mapping results
    :param format_type: format type ("pretty" or "json")
    :return: formatted string representation
    """
    if format_type == "json":
        # Convert tuples to lists for JSON serialization
        json_map = {}
        for file_path, classes in test_map.items():
            json_map[file_path] = {}
            for (class_skipped, class_name), methods in classes.items():
                class_key = f"{class_name} (skipped: {class_skipped})"
                json_map[file_path][class_key] = [
                    {"name": method_name, "skipped": method_skipped}
                    for method_skipped, method_name in methods
                ]
        return json.dumps(json_map, indent=2)
    else:
        # Pretty print format
        return pprint.pformat(test_map, width=100)


def _print_summary(test_map: dshtsteli.TestFileMap) -> None:
    """
    Print a summary of the survey results.

    :param test_map: the test file mapping results
    """
    total_files = len(test_map)
    total_classes = sum(len(classes) for classes in test_map.values())
    total_methods = sum(
        len(methods)
        for classes in test_map.values()
        for methods in classes.values()
    )
    skipped_classes = sum(
        1
        for classes in test_map.values()
        for (class_skipped, _), _ in classes.items()
        if class_skipped
    )
    skipped_methods = sum(
        sum(1 for method_skipped, _ in methods if method_skipped)
        for classes in test_map.values()
        for methods in classes.values()
    )
    _LOG.info("=== Test Survey Summary ===")
    _LOG.info(f"Total test files: {total_files}")
    _LOG.info(
        f"Total test classes: {total_classes} (skipped: {skipped_classes})"
    )
    _LOG.info(
        f"Total test methods: {total_methods} (skipped: {skipped_methods})"
    )
    _LOG.info("=" * 27)


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    _LOG.info(f"Starting test survey in directory: {args.root_dir}")
    # Survey the tests
    test_map = dshtsteli.survey_tests(args.root_dir)
    # Print summary
    _print_summary(test_map)
    # Format and output results
    formatted_results = _format_results(test_map, args.output_format)
    if args.output_file:
        _LOG.info(f"Writing results to: {args.output_file}")
        with open(args.output_file, "w") as f:
            f.write(formatted_results)
    else:
        print(formatted_results)
    _LOG.info("Test survey completed successfully")


if __name__ == "__main__":
    _main(_parse())
