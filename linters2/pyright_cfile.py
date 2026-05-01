#!/usr/bin/env python

"""
Wrap pyright to output diagnostics in cfile-compatible format.
"""

import argparse
import json
import logging
from typing import List

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# #############################################################################


def _transform_pyright_output(json_output: str) -> str:
    """
    Transform pyright JSON output to cfile-compatible format.

    :param json_output: JSON output from pyright with --outputjson flag
    :return: cfile-compatible formatted diagnostics
    """
    data = json.loads(json_output)
    _LOG.debug("data=%s", data)
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
        description=__doc__,
        add_help=False,
    )
    hparser.add_verbosity_arg(parser, log_level="INFO")
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Run pyright with --outputjson and transform output to cfile format.
    """
    args, remaining = parser.parse_known_args()
    hparser.parse_verbosity_args(args)
    #
    cmd_args = list(remaining)
    hdbg.dassert_isinstance(cmd_args, list, "Command arguments must be a list")
    if "-h" in cmd_args or "--help" in cmd_args:
        hsystem.system(f"pyright {' '.join(cmd_args)}")
        return
    if "--outputjson" not in cmd_args:
        cmd_args.append("--outputjson")
    #
    _LOG.debug("Running pyright")
    cmd = f"pyright {' '.join(cmd_args)} > tmp.pyright.txt"
    hsystem.system(cmd, abort_on_error=False)
    #
    _LOG.debug("Reading output from file 'tmp.pyright.txt'")
    output = hio.from_file("tmp.pyright.txt")
    _LOG.debug("Transforming output to cfile format")
    cfile_output = _transform_pyright_output(output)
    _LOG.debug("Printing cfile output")
    if cfile_output:
        print(cfile_output)


if __name__ == "__main__":
    parser = _parse()
    _main(parser)
