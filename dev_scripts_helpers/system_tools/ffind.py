#!/usr/bin/env python

"""
# Find all files/dirs whose name contains Task243, i.e., the regex "*Task243*"

> ffind.py Task243

# Look for files / dirs with name containing "stocktwits" in "this_dir"
> ffind.py stocktwits this_dir

# Look only for files.
> ffind.py stocktwits --only_files

Import as:

import dev_scripts_helpers.ffind as dscrffin
"""

import argparse
import logging
import os
import sys

import helpers.hdbg as hdbg
import helpers.hparser as hparser

_log = logging.getLogger(__name__)


def _print_help(parser):
    print(parser.format_help())
    sys.exit(-1)


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "positional",
        nargs="*",
        help="First param is regex, optional second param is dirname",
    )
    parser.add_argument("--only_files", action="store_true", help="Only files")
    parser.add_argument("--log", action="store_true", help="Report logging")
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    if (args.log_level == "DEBUG") or args.log:
        hdbg.init_logger(verbosity=args.log_level)
    positional = args.positional
    # Error check.
    if len(positional) < 1:
        print("Error: not enough parameters")
        _print_help(parser)
    if len(positional) > 2:
        print("Error: too many parameters")
        _print_help(parser)
    # Parse.
    if len(positional) == 2:
        dir_name = positional[1]
    else:
        dir_name = "."
    hdbg.dassert_path_exists(dir_name)
    name = "*" + positional[0].rstrip("").lstrip("") + "*"
    #
    cmd = []
    cmd.append(f"find {dir_name}")
    # Skip certain dirs.
    cmd.append(
        r"\( -path './.git' -o -path './.ipynb_checkpoints' -o -path ./.mypy_cache \) -prune -o"
    )
    if args.only_files:
        cmd.append("-type f")
    cmd.append(f'-iname "{name}"')
    # Guarantee that only non-pruned files are printed.
    cmd.append("-print")
    cmd.append("| grep -v __pycache__")
    cmd.append("| sort")
    cmd = " ".join(cmd)
    if (args.log_level == "DEBUG") or args.log:
        print(cmd)
        print()
    os.system(cmd)


if __name__ == "__main__":
    _main(_parse())
