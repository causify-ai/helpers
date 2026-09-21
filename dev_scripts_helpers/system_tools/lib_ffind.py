#!/usr/bin/env python
"""
Find files and directories whose name matches a pattern, wrapping the `find`
command.

Import as:

import dev_scripts_helpers.system_tools.lib_ffind as dshstliff
"""

import argparse
import logging
from typing import List, Optional

import dev_scripts_helpers.system_tools.search_utils as dshstseut
import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# #############################################################################
# Command building
# #############################################################################


def _build_find_command(
    pattern: str,
    dir_name: str,
    extensions: List[str],
    *,
    only_files: bool = False,
) -> str:
    """
    Build the `find` shell command to look for files/dirs matching `pattern`.

    :param pattern: substring to look for in the file/dir name
    :param dir_name: directory to search in
    :param extensions: file extensions to filter by (e.g., `["py", "md"]`), or
        `[]` for no filter
    :param only_files: restrict the search to files, skipping directories
    :return: shell command ready to run, including the `grep`/`sort` pipeline
    """
    _LOG.debug(hprint.to_str("pattern dir_name extensions only_files"))
    name = "*" + pattern + "*"
    # Match the name against each extension, if any.
    names = [f"{name}.{ext}" for ext in extensions] if extensions else [name]
    cmd = []
    cmd.append(f"find {dir_name}")
    # Skip certain dirs.
    cmd.append(
        r"\( -path './.git' -o -path './.ipynb_checkpoints' -o -path ./.mypy_cache \) -prune -o"
    )
    if only_files:
        cmd.append("-type f")
    iname_cmds = [f'-iname "{name}"' for name in names]
    if len(iname_cmds) == 1:
        cmd.append(iname_cmds[0])
    else:
        cmd.append(r"\( " + " -o ".join(iname_cmds) + r" \)")
    # Guarantee that only non-pruned files are printed.
    cmd.append("-print")
    cmd.append("| grep -v __pycache__")
    cmd.append("| sort")
    cmd = " ".join(cmd)
    return cmd


# #############################################################################
# Parser and main
# #############################################################################


def parse(description: str = "") -> argparse.ArgumentParser:
    """
    Create and return the `ArgumentParser` for the `ffind` utility.

    :param description: custom description for help output
        - Default: `""` (use the module docstring)
    :return: configured `ArgumentParser` instance
    """
    if not description:
        description = __doc__ or ""
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=hparser.CustomHelpFormatter,
    )
    # Add `<pattern> [<dir>] [<ext>]`, `--dir`, `--dry_run`, shared with `rig`.
    dshstseut.add_search_args(parser)
    parser.add_argument("--only_files", action="store_true", help="Only files")
    parser.add_argument("--log", action="store_true", help="Report logging")
    hparser.add_verbosity_arg(parser)
    return parser


def main(
    args: Optional[List[str]] = None,
    description: str = "",
) -> int:
    """
    Main entry point for the `ffind` utility.

    :param args: command-line arguments
        - Default: `None` (use `sys.argv[1:]`)
    :param description: custom description for help output
    :return: exit code (0 for success, -1 for a usage error)
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
    # Error check.
    if len(parsed.positional) < 1:
        print("Error: not enough parameters")
        parser.print_help()
        return -1
    # Parse `<pattern> [<dir>] [<ext>]` with the code shared with `rig`.
    pattern, dir_name, extensions = dshstseut.parse_positional(
        parsed.positional, parsed.dir
    )
    hdbg.dassert_dir_exists(dir_name)
    cmd = _build_find_command(
        pattern, dir_name, extensions, only_files=parsed.only_files
    )
    if parsed.dry_run:
        # Print the command and exit without running it.
        print(cmd)
        return 0
    if (parsed.log_level == "DEBUG") or parsed.log:
        print(cmd)
        print()
    hsystem.system(cmd, suppress_output=False, abort_on_error=False)
    return 0


if __name__ == "__main__":
    exit(main())
