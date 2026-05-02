#!/usr/bin/env python

"""
Wrap pyright to output diagnostics in cfile-compatible format.
"""

import argparse
import json
import logging
import sys
from typing import List

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# #############################################################################


def _process_message(message: str) -> str:
    """
    Process diagnostic message by converting newlines and truncating.

    :param message: Raw diagnostic message
    :return: Processed message with newlines converted to commas and truncated
    """
    # Convert newlines to commas
    processed = message.replace("\n", ", ")
    # Truncate if longer than 100 characters
    if len(processed) > 100:
        processed = processed[:97] + "..."
    return processed


def _transform_pyright_output(json_output: str) -> str:
    """
    Transform pyright JSON output to cfile-compatible format.

    :param json_output: JSON output from pyright with --outputjson flag
    :return: cfile-compatible formatted diagnostics with summary
    """
    data = json.loads(json_output)
    _LOG.debug("data=%s", data)
    lines: List[str] = []
    for diagnostic in data.get("generalDiagnostics", []):
        file_path = diagnostic.get("file", "")
        message = diagnostic.get("message", "")
        message = _process_message(message)
        range_info = diagnostic.get("range", {})
        start = range_info.get("start", {})
        line = start.get("line", 0) + 1
        character = start.get("character", 0) + 1
        lines.append(f"{file_path}:{line}:{character}: {message}")
    # Parse and format summary.
    summary = data.get("summary", {})
    if summary:
        error_count = summary.get("errorCount", 0)
        warning_count = summary.get("warningCount", 0)
        information_count = summary.get("informationCount", 0)
        time_in_sec = summary.get("timeInSec", 0)
        summary_line = (
            f"{error_count} errors, {warning_count} warnings, "
            f"{information_count} informations, time_in_sec={time_in_sec}"
        )
        lines.append(summary_line)
    return "\n".join(lines)


# #############################################################################
# Main
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        add_help=True,
    )
    hparser.add_verbosity_arg(parser, log_level="INFO")
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Run pyright with --outputjson and transform output to cfile format.
    """
    args, remaining = parser.parse_known_args()
    hparser.parse_verbosity_args(args)
    # Parse remaining arguments.
    cmd_args = list(remaining)
    hdbg.dassert_isinstance(cmd_args, list, "Command arguments must be a list")
    if "-h" in cmd_args or "--help" in cmd_args:
        hsystem.system(f"pyright {' '.join(cmd_args)}", abort_on_error=False)
        sys.exit(0)
    if "--outputjson" not in cmd_args:
        cmd_args.append("--outputjson")
    # Run pyright.
    _LOG.debug("Running pyright")
    cmd = f"pyright {' '.join(cmd_args)} > tmp.pyright.txt"
    hsystem.system(cmd, abort_on_error=False)
    # Parse output of pyright.
    _LOG.debug("Reading output from file 'tmp.pyright.txt'")
    output = hio.from_file("tmp.pyright.txt")
    # Transform output to cfile format.
    _LOG.debug("Transforming output to cfile format")
    cfile_output = _transform_pyright_output(output)
    # Print cfile output.
    _LOG.debug("Printing cfile output")
    if cfile_output:
        print(cfile_output)


if __name__ == "__main__":
    parser = _parse()
    _main(parser)
