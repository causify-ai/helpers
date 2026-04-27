#!/usr/bin/env python

import argparse
import subprocess
from typing import List, Optional


def _build_ripgrep_command(
    *,
    pattern: str,
    directory: str,
    extension: Optional[str],
    rg_opts: List[str],
) -> List[str]:
    """
    Build ripgrep command with given parameters.

    :param pattern: Search pattern (supports regex)
    :param directory: Directory to search in
    :param extension: File extension filter (without dot), optional
    :param rg_opts: Additional ripgrep options
    :return: Command list ready for subprocess
    """
    cmd = ["rg"]
    if extension:
        cmd.extend(["-g", f"*.{extension}"])
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


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments for rig utility.

    Supports:
    - Search mode: pattern [directory] [extension] [rg_opts]
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
    result.extension = None
    if parsed.positional:
        result.pattern = parsed.positional[0]
    if len(parsed.positional) > 1:
        result.directory = parsed.positional[1]
    if len(parsed.positional) > 2:
        result.extension = parsed.positional[2]
    return result


def _main(parser: argparse.ArgumentParser) -> int:
    """
    Main entry point for rig utility.

    :param parser: ArgumentParser instance
    :return: Exit code (0 for success, 1 for error)
    """
    parsed = parser.parse_args()
    parsed = _parse_arguments(parsed)
    if not parsed.pattern:
        parser.print_help()
        return 0
    rg_opts = _get_default_rg_opts()
    cmd = _build_ripgrep_command(
        pattern=parsed.pattern,
        directory=parsed.directory,
        extension=parsed.extension,
        rg_opts=rg_opts,
    )
    subprocess.run(cmd)
    return 0
