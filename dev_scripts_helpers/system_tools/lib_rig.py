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
import helpers.lib_tasks_utils as hlitauti

_LOG = logging.getLogger(__name__)


def _build_ripgrep_command(
    *,
    pattern: str,
    directory: str,
    extensions: Optional[List[str]],
    rg_opts: List[str],
    *,
    files: Optional[List[str]] = None,
) -> List[str]:
    """
    Build ripgrep command with given parameters.

    :param pattern: Search pattern (supports regex)
    :param directory: Directory to search in
    :param extensions: File extensions to search (without dot), optional list
    :param rg_opts: Additional ripgrep options
    :param files: Specific files to search in, optional list
    :return: Command list ready for subprocess
    """
    cmd = ["rg"]
    if extensions:
        for ext in extensions:
            cmd.extend(["-g", f"*.{ext}"])
    cmd.append(pattern)
    if files:
        cmd.extend(files)
    else:
        cmd.append(directory)
    cmd.extend(rg_opts)
    return cmd


def _get_default_rg_opts() -> List[str]:
    """
    Get default ripgrep options.

    :return: List of default options
    """
    return ["-n", "--no-heading", "--color=never"]


def _get_files_to_search(
    *,
    modified: bool,
    branch: bool,
    last_commit: bool,
    all_files: bool,
    files_from_user: Optional[str],
) -> Optional[List[str]]:
    """
    Get list of files to search based on selection criteria.

    :param modified: Return files modified in the client
    :param branch: Return files modified with respect to the branch point
    :param last_commit: Return files part of the previous commit
    :param all_files: Return all repo files
    :param files_from_user: Files passed by the user
    :return: List of files to search, or None to search entire directory
    """
    if not any([modified, branch, last_commit, all_files, files_from_user]):
        return None
    files = hlitauti._get_files_to_process(
        modified=modified,
        branch=branch,
        last_commit=last_commit,
        all_=all_files,
        files_from_user=files_from_user or "",
        mutually_exclusive=True,
        remove_dirs=True,
    )
    return files if files else None


def parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments for rig utility.

    :return: ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "positional", nargs="*", help="Positional arguments for search"
    )
    parser.add_argument(
        "--modified",
        action="store_true",
        help="Search only in files modified in the client (staged and unstaged)",
    )
    parser.add_argument(
        "--branch",
        action="store_true",
        help="Search only in files modified with respect to the branch point",
    )
    parser.add_argument(
        "--last-commit",
        action="store_true",
        help="Search only in files part of the previous commit",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="all_files",
        help="Search all repo files",
    )
    parser.add_argument(
        "--files",
        type=str,
        help="Search in specific files (space-separated list)",
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
    result.modified = parsed.modified
    result.branch = parsed.branch
    result.last_commit = parsed.last_commit
    result.all_files = parsed.all_files
    result.files_from_user = parsed.files
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


def main(
    args: Optional[List[str]] = None,
    parser: Optional[argparse.ArgumentParser] = None,
) -> int:
    """
    Main entry point for rig utility.

    :param args: Command-line arguments (defaults to sys.argv[1:])
    :param parser: ArgumentParser instance (created if not provided)
    :return: Exit code (0 for success, 1 for error)
    """
    if parser is None:
        parser = parse()
    if args is not None:
        parsed = parser.parse_args(args)
    else:
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
    rg_opts = _get_default_rg_opts()
    # Get files if file selection options are specified.
    files = _get_files_to_search(
        modified=parsed.modified,
        branch=parsed.branch,
        last_commit=parsed.last_commit,
        all_files=parsed.all_files,
        files_from_user=parsed.files_from_user,
    )
    cmd = _build_ripgrep_command(
        pattern=parsed.pattern,
        directory=parsed.directory,
        extensions=parsed.extensions,
        rg_opts=rg_opts,
        files=files,
    )
    _LOG.debug("> %s", cmd)
    _LOG.debug("> %s", " ".join(cmd))
    subprocess.run(cmd)
    return 0
