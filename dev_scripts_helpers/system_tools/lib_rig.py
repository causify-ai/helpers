#!/usr/bin/env python
"""
Ripgrep wrapper utility with file type filtering support.

Provides a command-line interface for ripgrep (rg) with support for filtering
by file extensions and searching only in modified, branched, or user-specified
files.
"""

import argparse
import logging
import subprocess
from typing import List, Optional

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.lib_tasks.lib_tasks_utils as hlitauti

_LOG = logging.getLogger(__name__)


def _build_ripgrep_command(
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
            # Ensure extensions don't have a dot prefix since ripgrep expects
            # bare extension names (e.g., "py" not ".py") when using the
            # `-g glob` filter.
            hdbg.dassert(
                not ext.startswith("."),
                "Extension '%s' must not start with dot",
                ext,
            )
            cmd.extend(["-g", f"*.{ext}"])
    cmd.append(pattern)
    # Look also in hidden files, like `.claude`.
    cmd.append("--hidden")
    if files:
        cmd.extend(files)
    else:
        cmd.append(directory)
    cmd.extend(rg_opts)
    return cmd


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


def parse(description: Optional[str] = None) -> argparse.ArgumentParser:
    """
    Create and return ArgumentParser for rig utility.

    Configures arguments for: search pattern, directory, file extensions,
    file selection filters (modified, branch, last-commit, all), and verbosity.

    :param description: Custom description for help output (defaults to module docstring)
    :return: Configured ArgumentParser instance
    """
    if description is None:
        description = __doc__
    parser = argparse.ArgumentParser(
        description=description,
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
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Print the ripgrep command and exit without running it",
    )
    parser.add_argument(
        "--rg_opts",
        type=str,
        default="",
        help="Additional ripgrep options (e.g., '-S -i' for smart case and ignore case)",
    )
    parser.add_argument(
        "--def",
        dest="def_mode",
        action="store_true",
        help="Search for Python class/def definitions",
    )
    parser.add_argument(
        "--rule",
        dest="rule_mode",
        action="store_true",
        help="Search for Markdown headers in .claude/skills/*.md",
    )
    parser.add_argument(
        "--todo",
        dest="todo_mode",
        action="store_true",
        help="Search for TODO(ai_gp) patterns",
    )
    parser.add_argument(
        "--cfile",
        dest="cfile",
        action="store_true",
        help="Save output to cfile and open in vim",
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
    result.dry_run = parsed.dry_run
    result.rg_opts = parsed.rg_opts
    result.def_mode = parsed.def_mode
    result.rule_mode = parsed.rule_mode
    result.todo_mode = parsed.todo_mode
    result.cfile = parsed.cfile
    result.rule_filter = None
    if parsed.positional:
        result.pattern = parsed.positional[0]
    if len(parsed.positional) > 1:
        result.directory = parsed.positional[1]
    if len(parsed.positional) > 2:
        result.extensions = [
            ext.strip() for ext in parsed.positional[2].split(",")
        ]
        # Ensure extensions don't have a dot prefix since ripgrep expects bare
        # extension names (e.g., "py" not ".py") when using the `-g glob` filter.
        for ext in result.extensions:
            hdbg.dassert(
                not ext.startswith("."),
                "Extension '%s' must not start with dot",
                ext,
            )
    # Apply mode-specific overrides.
    if result.def_mode:
        # --def: search for class/def definitions in Python files.
        pattern_suffix = f" {result.pattern}" if result.pattern else ""
        result.pattern = f"(class|def){pattern_suffix}"
        result.extensions = ["py"]
        # Directory can come from positional[1] if provided, otherwise stays as "."
        if len(parsed.positional) > 1:
            result.directory = parsed.positional[1]
    elif result.rule_mode:
        # --rule: search for markdown headers in `.claude/skills`.
        result.pattern = "^#"
        result.directory = ".claude/skills"
        result.extensions = ["md"]
        # First positional arg becomes a grep-i filter (if provided)
        if parsed.positional:
            result.rule_filter = parsed.positional[0]
    elif result.todo_mode:
        # --todo: search for `TODO(ai_gp)` pattern.
        result.pattern = r"TODO\(ai_gp\)"
        # Directory and extensions can come from positional args
        if len(parsed.positional) > 1:
            result.directory = parsed.positional[1]
        if len(parsed.positional) > 2:
            result.extensions = [
                ext.strip() for ext in parsed.positional[2].split(",")
            ]
            for ext in result.extensions:
                hdbg.dassert(
                    not ext.startswith("."),
                    "Extension '%s' must not start with dot",
                    ext,
                )
    return result


def main(
    args: Optional[List[str]] = None,
    parser: Optional[argparse.ArgumentParser] = None,
    description: Optional[str] = None,
) -> int:
    """
    Main entry point for rig utility.

    :param args: Command-line arguments (defaults to sys.argv[1:])
    :param parser: ArgumentParser instance (created if not provided)
    :param description: Custom description for help output
    :return: Exit code (0 for success, 1 for error)
    """
    if parser is None:
        parser = parse(description=description)
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
    parsed = _parse_arguments(parsed)
    if not parsed.pattern:
        parser.print_help()
        return 0
    # Default ripgrep options for consistent output formatting.
    rg_opts = [
        # Show line numbers.
        "-n",
        # Omit file headers.
        "--no-heading",
        # Plain output without ANSI colors.
        "--color=never",
    ]
    # Append user-provided ripgrep options if any.
    if parsed.rg_opts:
        rg_opts.extend(parsed.rg_opts.split())
    # Retrieve filtered file list if user specified file selection criteria;
    # otherwise search entire directory.
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
    # Log the command in shell format for easy copy-paste debugging.
    _LOG.debug("> %s", " ".join(cmd))
    if parsed.dry_run:
        # Print the command and exit without running it.
        print(" ".join(cmd))
        return 0

        if need_capture:
            # Capture output for post-processing
            result = subprocess.run(cmd, capture_output=True, text=True)
            # In tests with mocks, result might be None or lack stdout attribute
            if result is None or not hasattr(result, "stdout"):
                return 0
            lines = result.stdout.splitlines()

            # Apply --todo filter: exclude lines containing 'cfile'
            if parsed.todo_mode:
                lines = [line for line in lines if "cfile" not in line]

            # Apply --rule filter: case-insensitive grep
            if parsed.rule_mode and parsed.rule_filter:
                filter_lower = parsed.rule_filter.lower()
                lines = [
                    line for line in lines if filter_lower in line.lower()
                ]

            output = "\n".join(lines)
            print(output)

            # Save to cfile and open in vim if requested
            if parsed.cfile:
                hio.to_file("cfile", output)
                subprocess.run(["vim", "-c", "cfile cfile"])
        else:
            subprocess.run(cmd)
    return 0
