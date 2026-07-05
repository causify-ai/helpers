#!/usr/bin/env python

"""
Capture a command from shell history and copy it to the clipboard.

# Copy the last command to the clipboard.
> last_cmd.py

# Copy the 3rd most recent command to the clipboard.
> last_cmd.py -n 3

# Print the last command instead of copying it to the clipboard.
> last_cmd.py --no_pb_copy
"""

import argparse
import logging
import re
from typing import List, Optional

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# The tmp file that `last_cmd.sh` dumps `history 10` output to.
_TMP_HISTORY_FILE = "/tmp/tmp.history.txt"

# #############################################################################


def _get_history_commands(
    *,
    history_file: str = _TMP_HISTORY_FILE,
    exclude_substrings: Optional[List[str]] = None,
) -> List[str]:
    """
    Return the shell history commands, in chronological order (oldest first).

    Read the output of `history 10` dumped to `history_file` by
    `last_cmd.sh`, instead of calling `history` here. A Python (or any
    child) process can't call the shell's `history` builtin itself: it runs
    in its own process, can't reach into the parent shell's memory, and so
    would only ever see its own empty history, never the interactive
    shell's. `last_cmd.sh` must be sourced (not executed) so `history -a`
    and `history 10` run in that actual interactive shell.

    :param history_file: path to the file with `history 10`-style output
        (each line is `<index> <command>`)
    :param exclude_substrings: skip commands containing any of these
        substrings (e.g., to exclude invocations of the calling script
        itself)
    :return: list of history commands
    """
    hdbg.dassert_file_exists(history_file)
    history_text = hio.from_file(history_file)
    lines = [line.strip() for line in history_text.splitlines() if line.strip()]
    hdbg.dassert_lt(0, len(lines), "History is empty")
    # ```
    # > history 10
    #  529  cd ~/src
    #  530  ls -la
    # ```
    # Strip the leading index.
    commands = [re.sub(r"^\s*\d+\s+", "", line) for line in lines]
    if exclude_substrings:
        commands = [
            command
            for command in commands
            if not any(sub in command for sub in exclude_substrings)
        ]
    return commands


def _get_nth_command(
    n: int, *, exclude_substrings: Optional[List[str]] = None
) -> str:
    """
    Return the n-th most recent shell command.

    :param n: index (1 = most recent) of the command to return
    :param exclude_substrings: skip commands containing any of these
        substrings
    :return: n-th most recent command
    """
    commands = _get_history_commands(exclude_substrings=exclude_substrings)
    hdbg.dassert_lte(
        n,
        len(commands),
        "Not enough history: n=%s len(commands)=%s",
        n,
        len(commands),
    )
    command = commands[-n]
    return command


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-n",
        dest="n",
        type=int,
        default=1,
        action="store",
        help="Index of the command to capture (1 is the most recent)",
    )
    parser.add_argument(
        "--no_pb_copy",
        action="store_true",
        help="Print the command instead of copying it to the clipboard",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, report_command_line=False)
    #
    exclude_substrings = ["last_cmd"]
    command = _get_nth_command(args.n, exclude_substrings=exclude_substrings)
    #
    if not args.no_pb_copy:
        _LOG.debug("Capturing command: %s", command)
        hsystem.to_pbcopy(command, pbcopy=True)
    else:
        print(command)


if __name__ == "__main__":
    _main(_parse())
