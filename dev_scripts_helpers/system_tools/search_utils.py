"""
Code shared by `rig` and `ffind` to keep their interfaces identical.

Both tools accept:

  <tool> <pattern> [<dir>] [<ext>] [--dir <dir>] [--dry_run]

- <pattern>: what to look for
- <dir>: directory to search in (default: current directory `.`)
- <ext>: file extension filter, e.g., `py` or `py,md` (requires <dir>)

Import as:

import dev_scripts_helpers.system_tools.search_utils as dshstseut
"""

import argparse
from typing import List, Tuple

import helpers.hdbg as hdbg

_DEFAULT_DIR = "."


# #############################################################################
# Parser
# #############################################################################


def add_search_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """
    Add the arguments shared by `rig` and `ffind` to a parser.

    Adds:
    - `positional`: `<pattern> [<dir>] [<ext>]`
    - `--dir`: alternative to the positional `<dir>`
    - `--dry_run`: print the command and exit without running it

    :param parser: `ArgumentParser` to add arguments to
    :return: the same parser with arguments added
    """
    parser.add_argument(
        "positional",
        nargs="*",
        help="<pattern> [<dir>] [<ext>]: what to look for, the directory to "
        f"search in (default: `{_DEFAULT_DIR}`), and the file extensions "
        "(e.g., `py` or `py,md`), which requires <dir>",
    )
    parser.add_argument(
        "--dir",
        action="store",
        default="",
        help="Directory to search in, as an alternative to the positional "
        "<dir>",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Print the command and exit without running it",
    )
    return parser


# #############################################################################
# Positional arguments
# #############################################################################


def parse_extensions(ext_str: str) -> List[str]:
    """
    Split a comma-separated list of extensions.

    E.g., `"py, md"` -> `["py", "md"]`.

    :param ext_str: comma-separated extensions, without dot prefix
    :return: extensions without whitespace
    """
    extensions = [ext.strip() for ext in ext_str.split(",")]
    for ext in extensions:
        # Tools expect bare extension names (e.g., "py" not ".py").
        hdbg.dassert(
            ext != "" and not ext.startswith("."),
            "Extension '%s' must be non-empty and must not start with dot",
            ext,
        )
    return extensions


def parse_positional(
    positional: List[str],
    dir_flag: str,
    *,
    has_pattern: bool = True,
) -> Tuple[str, str, List[str]]:
    """
    Parse `[<pattern>] [<dir>] [<ext>]` into its components.

    :param positional: positional arguments
    :param dir_flag: value of `--dir` (`""` if not passed)
    :param has_pattern: whether the first positional argument is the pattern;
        modes that don't use a pattern (e.g., `rig --todo`) start from `<dir>`
    :return: pattern (`""` if not passed), directory (default: `.`), and
        extensions (`[]` if not passed)
    """
    positional = list(positional)
    pattern = positional.pop(0) if has_pattern and positional else ""
    dir_name = positional.pop(0) if positional else ""
    ext_str = positional.pop(0) if positional else ""
    hdbg.dassert_eq(
        len(positional), 0, "Too many parameters: %s", str(positional)
    )
    # The directory can also be passed with `--dir`.
    if dir_flag:
        hdbg.dassert_eq(
            dir_name,
            "",
            "Pass the dir either as positional arg or with --dir, not both",
        )
        dir_name = dir_flag
    if not dir_name:
        dir_name = _DEFAULT_DIR
    extensions = parse_extensions(ext_str) if ext_str else []
    return pattern, dir_name, extensions
