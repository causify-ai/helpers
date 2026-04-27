# """
# Wrapper around ripgrep (rg) to search files by pattern and extension.
# Core logic module that can be imported and tested.
# """

import os
import subprocess
import sys
from typing import List, Optional


def build_ripgrep_command(
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


def get_default_rg_opts() -> List[str]:
    """
    Get default ripgrep options.

    :return: List of default options
    """
    return ["-n", "--no-heading", "--color=never"]


def parse_arguments(args: List[str]):
    """
    Parse command-line arguments for rig.

    :param args: List of command-line arguments
    :return: Parsed arguments object with attributes:
             pattern, directory, extension, rg_opts, todo, help
    """

    class Args:
        def __init__(self):
            self.pattern: Optional[str] = None
            self.directory: str = "."
            self.extension: Optional[str] = None
            self.rg_opts: List[str] = []
            self.todo: Optional[str] = None
            self.help: bool = False

    result = Args()

    # Check for help flags first
    if "-h" in args or "--help" in args:
        result.help = True
        return result

    # Check for --todo flag
    if "--todo" in args:
        todo_idx = args.index("--todo")
        remaining = args[todo_idx + 1 :]

        # Get user name for todo (default: ai_gp)
        if remaining and not remaining[0].startswith("-"):
            result.todo = remaining[0]
            remaining = remaining[1:]
        else:
            result.todo = "ai_gp"

        # Get directory if present
        if remaining and not remaining[0].startswith("-"):
            result.directory = remaining[0]
            remaining = remaining[1:]

        # Get extension if present
        if remaining and not remaining[0].startswith("-"):
            result.extension = remaining[0]
            remaining = remaining[1:]

        result.rg_opts = remaining
        result.pattern = None
        return result

    # Regular pattern mode
    if args:
        # First argument is pattern
        result.pattern = args[0]
        remaining = args[1:]

        # Check if next argument is a directory
        if remaining and not remaining[0].startswith("-"):
            arg = remaining[0]
            # Treat as directory if: exists as dir, or is . or .., or there's a next arg (extension)
            is_likely_dir = (
                os.path.isdir(arg) or
                arg in (".", "..") or
                (len(remaining) > 1 and not remaining[1].startswith("-"))
            )
            if is_likely_dir:
                result.directory = arg
                remaining = remaining[1:]

        # Check if next argument is an extension
        if remaining and not remaining[0].startswith("-"):
            result.extension = remaining[0]
            remaining = remaining[1:]

        # Remaining arguments are rg options
        result.rg_opts = remaining

    return result


def main(args: List[str] = None) -> int:
    """
    Main entry point for rig command.

    :param args: Command-line arguments (if None, uses sys.argv[1:])
    :return: Exit code (0 for success, 1 for error)
    """
    if args is None:
        args = sys.argv[1:]

    parsed = parse_arguments(args)

    if parsed.help or (not parsed.pattern and not parsed.todo):
        _show_help()
        return 0

    # Determine pattern and options
    if parsed.todo:
        pattern: str = f"TODO\\({parsed.todo}\\)"
        directory: str = parsed.directory
        extension: Optional[str] = parsed.extension
        rg_opts: List[str] = parsed.rg_opts if parsed.rg_opts else get_default_rg_opts()
    else:
        pattern = parsed.pattern or ""
        directory = parsed.directory
        extension = parsed.extension
        rg_opts = parsed.rg_opts if parsed.rg_opts else get_default_rg_opts()

    # Build ripgrep command
    cmd = build_ripgrep_command(
        pattern=pattern,
        directory=directory,
        extension=extension,
        rg_opts=rg_opts,
    )

    try:
        subprocess.run(cmd, check=False)
        return 0
    except FileNotFoundError:
        print("Error: ripgrep (rg) not found. Please install it.", file=sys.stderr)
        return 1


def _show_help() -> None:
    """Display help message."""
    help_text = """rig - Utility for ripgrep searches and directory operations

USAGE:
    rig <pattern> [<dir>] [<extension>] [<rg OPTS>]
    rig --todo [<user>] [<dir>] [<extension>]

COMMANDS:
    Search mode:
        rig <pattern> [<dir>] [<extension>] [<rg OPTS>]
        Search for pattern in files with optional extension filter

    TODO mode:
        rig --todo [<user>] [<dir>] [<extension>]
        Search for TODO(user) markers (default user: ai_gp)

ARGUMENTS:
    <pattern>      Search pattern (supports regex)
    [<dir>]        Directory to search in (default: current directory '.')
    [<extension>]  File extension filter (e.g., py, js, txt), optional
    [<rg OPTS>]    Additional ripgrep options (optional)

EXAMPLES:
    # Search for "TODO" in Python files in src directory
    rig "TODO" src py

    # Search for "TODO" in all files in src directory
    rig "TODO" src

    # Search for "TODO" in all files in current directory
    rig "TODO"

    # Search in Python files in current directory
    rig "import" py

    # Search in JavaScript files with case-insensitive matching
    rig "import" . js -i

    # Search for TODO(ai_gp) in all files
    rig --todo

    # Search for TODO(gp) in all files
    rig --todo gp

    # Search for TODO(ai_gp) in Python files
    rig --todo ai_gp py

DEFAULT OPTIONS (for search):
    When no additional options are provided, these defaults are used:
      -n              Line numbers
      --no-heading    Suppress file path headings
      --color=never   No colored output

NOTES:
    - The extension parameter is optional; omit it to search all files
    - If provided, the extension should not include a dot (use 'py' not '.py')
    - If an argument starts with '-', it is treated as an rg option
    - Provide custom ripgrep options to override defaults
    - For full ripgrep documentation: rg --help
"""
    print(help_text)
