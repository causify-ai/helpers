#!/usr/bin/env -S uv run

# /// script
# dependencies = []
# ///

"""
Wrap pyright to output diagnostics in cfile-compatible format.

Import as:

import dev_scripts_helpers.pyright_cfile as dpycfile
"""

import argparse
import json
import logging
from typing import List

import helpers.hdbg as hdbg
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# #############################################################################
# Transform
# #############################################################################


def _transform_pyright_output(json_output: str) -> str:
    """
    Transform pyright JSON output to cfile-compatible format.

    :param json_output: JSON output from pyright with --outputjson flag
    :return: cfile-compatible formatted diagnostics
    """
    data = json.loads(json_output)
    lines: List[str] = []
    for diagnostic in data.get("generalDiagnostics", []):
        file_path = diagnostic.get("file", "")
        message = diagnostic.get("message", "")
        range_info = diagnostic.get("range", {})
        start = range_info.get("start", {})
        line = start.get("line", 0) + 1
        character = start.get("character", 0) + 1
        lines.append(f"{file_path}:{line}:{character}: {message}")
    return "\n".join(lines)


# #############################################################################
# Main
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Wrap pyright to output diagnostics in cfile format",
        add_help=False,
    )
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Run pyright with --outputjson and transform output to cfile format.
    """
    _, remaining = parser.parse_known_args()
    cmd_args = list(remaining)
    hdbg.dassert_isinstance(cmd_args, list, "Command arguments must be a list")
    if "--outputjson" not in cmd_args:
        cmd_args.append("--outputjson")
    cmd = f"pyright {' '.join(cmd_args)}"
    _LOG.debug("Running command: %s", cmd)
    _, output = hsystem.system_to_string(
        cmd, suppress_output=False, abort_on_error=False
    )
    cfile_output = _transform_pyright_output(output)
    if cfile_output:
        print(cfile_output)


if __name__ == "__main__":
    parser = _parse()
    _main(parser)
