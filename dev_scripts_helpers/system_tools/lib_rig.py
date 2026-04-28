#!/usr/bin/env python
"""
Ripgrep wrapper utility with file type filtering support.
"""

import argparse
import logging
import subprocess
from typing import List, Optional

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)


def _build_ripgrep_command(
    *,
    pattern: str,
    directory: str,
    extensions: Optional[List[str]],
    rg_opts: List[str],
) -> List[str]:
    """
    Build ripgrep command with given parameters.

    :param pattern: Search pattern (supports regex)
    :param directory: Directory to search in
    :param extensions: File extensions to search (without dot), optional list
    :param rg_opts: Additional ripgrep options
    :return: Command list ready for subprocess
    """
    cmd = ["rg"]
    if extensions:
        for ext in extensions:
            cmd.extend(["-g", f"*.{ext}"])
    cmd.append(pattern)
    cmd.append(directory)
    cmd.extend(rg_opts)
    return cmd


def _get_default_rg_opts() -> List[str]:
    """
    Get default ripgrep options.

    :return: List of default options
    """
    return ["-n", "--no-heading", "--color=never"]


def parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments for rig utility.

    Supports:
    - Search mode: pattern [directory] [extensions]
    - Help mode: --help or -h

    :return: ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "positional", nargs="*", help="Positional arguments for search"
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _parse_arguments(parsed: argparse.Namespace) -> argparse.Namespace:
    """
    Process parsed command-line arguments into a structured result.

    :param parsed: Raw parsed arguments from ArgumentParser
    :return: Processed arguments namespace
    """
    result = argparse.Namespace()
    result.pattern = None
    result.directory = "."
    result.extensions = None
    if parsed.positional:
        result.pattern = parsed.positional[0]
    if len(parsed.positional) > 1:
        result.directory = parsed.positional[1]
    if len(parsed.positional) > 2:
        result.extensions = [ext.strip() for ext in parsed.positional[2].split(",")]
        # Assert that none of the extensions start with a dot
        for ext in result.extensions:
            hdbg.dassert(
                not ext.startswith("."),
                f"Extension '{ext}' should not start with a dot",
            )
    return result


def main(parser: argparse.ArgumentParser) -> int:
    """
    Main entry point for rig utility.

    :param parser: ArgumentParser instance
    :return: Exit code (0 for success, 1 for error)
    """
    parsed = parser.parse_args()
    hdbg.init_logger(
        verbosity=parsed.log_level,
        use_exec_path=True,
        report_command_line=False,
        log_filename="",
    )
    _LOG.debug(hprint.func_signature_to_str())
    parsed = _parse_arguments(parsed)
    if not parsed.pattern:
        parser.print_help()
        return 0
    # Validate that the directory exists.
    hdbg.dassert_dir_exists(parsed.directory)
    rg_opts = _get_default_rg_opts()
    cmd = _build_ripgrep_command(
        pattern=parsed.pattern,
        directory=parsed.directory,
        extensions=parsed.extensions,
        rg_opts=rg_opts,
    )
    _LOG.debug("> %s", cmd)
    _LOG.debug("> %s", " ".join(cmd))
    subprocess.run(cmd)
    return 0
