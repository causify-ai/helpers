#!/usr/bin/env python
"""
Ripgrep wrapper utility with file type filtering support.

Provides a command-line interface for ripgrep (rg) with support for filtering
by file extensions and searching only in modified, branched, or user-specified
files.
"""

import argparse
import logging
import os
import shlex
import subprocess
from typing import Any, Dict, List, Optional

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hparser as hparser

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
    Build `ripgrep` command with given parameters.

    :param pattern: Search pattern (supports regex)
    :param directory: Directory to search in
    :param extensions: File extensions to search (without dot), optional list
    :param rg_opts: Additional ripgrep options
    :param files: Specific files to search in, optional list
    :return: Command list ready for subprocess
    """
    cmd = ["rg", pattern, directory]
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
    # Look also in hidden files, like `.claude`.
    cmd.append("--hidden")
    if files:
        cmd.extend(files)
    cmd.extend(rg_opts)
    return cmd


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
    hparser.add_file_selection_args(parser)
    # Special search mode.
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
        dest="todo_str",
        nargs="?",
        const="_default_",
        default=None,
        help="Search for TODO(<string>) patterns (optional <string> parameter"
    )
    parser.add_argument(
        "--cfile",
        dest="cfile",
        action="store_true",
        help="Save output to cfile and open in vim",
    )
    # Modifiers for `rg`.
    parser.add_argument(
        "-i",
        dest="case_insensitive",
        action="store_true",
        help="Case-insensitive search (expands to -S -i for ripgrep)",
    )
    parser.add_argument(
        "--rg_opts",
        type=str,
        default="",
        help="Additional ripgrep options (e.g., '-S -i' for smart case and ignore case)",
    )
    # Dry-run.
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Print the ripgrep command and exit without running it",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _parse_arguments(parsed: argparse.Namespace) -> Dict[str, Any]:
    """
    Process parsed command-line arguments into ripgrep command components.

    Build the ripgrep command components one at a time using independent
    variables:
    - `ripgrep_pattern`: search pattern
    - `ripgrep_dir`: directory to search
    - `ripgrep_extensions`: file extensions to filter
    - `ripgrep_opts`: extra rg options

    :param parsed: Raw parsed arguments from `ArgumentParser`
    :return: Dictionary with processed ripgrep command components and flags
    """
    # Build ripgrep pattern from first positional arg.
    ripgrep_pattern = parsed.positional[0] if parsed.positional else None
    # Build ripgrep directory from second positional arg (default: current dir).
    ripgrep_dir = "."
    if len(parsed.positional) > 1:
        ripgrep_dir = parsed.positional[1]
    # Build ripgrep extensions from third positional arg.
    ripgrep_extensions = None
    if len(parsed.positional) > 2:
        ripgrep_extensions = [
            ext.strip() for ext in parsed.positional[2].split(",")
        ]
        # Ensure extensions don't have a dot prefix since ripgrep expects
        # bare extension names (e.g., "py" not ".py") when using `-g glob`.
        for ext in ripgrep_extensions:
            hdbg.dassert(
                not ext.startswith("."),
                "Extension '%s' must not start with dot",
                ext,
            )
    # Build extra rg options from user input.
    ripgrep_opts = parsed.rg_opts
    # Expand -i to -S -i for ripgrep (smart-case + ignore-case).
    if parsed.case_insensitive:
        ripgrep_opts = (ripgrep_opts + " -S -i").strip()
    # Determine if output should be captured for --cfile post-processing.
    need_capture = parsed.cfile
    rule_filter = None
    # Apply mode-specific overrides.
    if parsed.def_mode:
        # --def: search for class/def definitions in Python files.
        pattern_suffix = f" {ripgrep_pattern}" if ripgrep_pattern else ""
        ripgrep_pattern = f"(class|def){pattern_suffix}"
        ripgrep_extensions = ["py"]
    elif parsed.rule_mode:
        # --rule: search for markdown headers in `.claude/skills`.
        ripgrep_dir = ".claude/skills"
        ripgrep_extensions = ["md"]
        # First positional arg becomes part of the regex pattern (if provided).
        if parsed.positional:
            rule_filter = parsed.positional[0]
            ripgrep_pattern = f"^#+.*{rule_filter}"
        else:
            ripgrep_pattern = "^#"
        # Make rule search case-insensitive by default.
        ripgrep_opts = (ripgrep_opts + " -i").strip()
    elif parsed.todo_str:
        # --todo: search for `# TODO(<string>)` or `// TODO(<string>)` patterns.
        if parsed.todo_str == "_default_":
            todo_pattern = "ai_gp\s*"
        else:
            todo_pattern = parsed.todo_str
        ripgrep_pattern = rf"^\s*(#|//)\s*TODO\({todo_pattern}\)"
        # Directory and extensions can come from positional args.
        if len(parsed.positional) > 1:
            ripgrep_dir = parsed.positional[1]
        if len(parsed.positional) > 2:
            ripgrep_extensions = [
                ext.strip() for ext in parsed.positional[2].split(",")
            ]
            for ext in ripgrep_extensions:
                hdbg.dassert(
                    not ext.startswith("."),
                    "Extension '%s' must not start with dot",
                    ext,
                )
    # Package computed components and behavioral flags into a result dictionary.
    result: Dict[str, Any] = {
        "pattern": ripgrep_pattern,
        "directory": ripgrep_dir,
        "extensions": ripgrep_extensions,
        "rg_opts": ripgrep_opts,
        "need_capture": need_capture,
        "files": parsed.files,
        "from_file": parsed.from_file,
        "modified": parsed.modified,
        "branch": parsed.branch,
        "last_commit": parsed.last_commit,
        "all_files": parsed.all_files,
        "dry_run": parsed.dry_run,
    }
    return result


def main(
    args: Optional[List[str]] = None,
    description: Optional[str] = None,
) -> int:
    """
    Main entry point for rig utility.

    :param args: Command-line arguments (defaults to sys.argv[1:])
    :param description: Custom description for help output
    :return: Exit code (0 for success, 1 for error)
    """
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
    if not parsed["pattern"]:
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
        # Exclude .git directory from search.
        "-g",
        "!.git",
    ]
    # Append user-provided ripgrep options if any.
    if parsed["rg_opts"]:
        rg_opts.extend(parsed["rg_opts"].split())
    # Retrieve filtered file list if user specified file selection criteria;
    # otherwise search entire directory.
    if any(
        [
            parsed["files"],
            parsed["from_file"],
            parsed["modified"],
            parsed["branch"],
            parsed["last_commit"],
            parsed["all_files"],
        ]
    ):
        files = hgit.get_files_to_process(
            parsed["files"],
            parsed["from_file"],
            parsed["modified"],
            parsed["branch"],
            parsed["last_commit"],
            parsed["all_files"],
            mutually_exclusive=True,
            remove_dirs=True,
        )
        files = files if files else None
    else:
        files = None
    cmd = _build_ripgrep_command(
        parsed["pattern"],
        parsed["directory"],
        parsed["extensions"],
        rg_opts,
        files=files,
    )
    # Log the command for debugging.
    cmd_str = " ".join(shlex.quote(arg) for arg in cmd)
    _LOG.debug("> %s", cmd_str)
    if parsed["dry_run"]:
        # Print the command and exit without running it.
        print(cmd_str)
        return 0
    # Run the command using system call and capture output.
    try:
        if parsed["need_capture"]:
            # For piping to tee, use shell=True with the string command.
            cmd_str = cmd_str + " 2>&1 | tee cfile"
            result = subprocess.run(cmd_str, shell=True, text=True)
            # Open vim with the cfile if it was created.
            if os.path.exists("cfile"):
                vim_cmd = 'vim -c "cfile cfile"'
                subprocess.run(vim_cmd, shell=True)
        else:
            # For normal execution, pass the command as a list.
            result = subprocess.run(cmd, text=True)
        return result.returncode if result else 0
    except FileNotFoundError:
        _LOG.error(
            "Command not found: %s",
            cmd_str if parsed["need_capture"] else cmd[0],
        )
        return 1
