#!/usr/bin/env python

"""
Notify the user that the last command is completed through different channels:
- Blinking the current tmux pane until interrupted
- Using a macOS notification

- The last executed shell command is read from the tmp file written by
  `last_cmd.sh`, which must be *sourced* (not executed) in the interactive
  shell so that `history -a` / `history 10` run in that shell's process.
  A Python child process can't call `history` itself: it can't reach into
  the parent shell's memory, so it would only ever see its own empty
  history, never the interactive shell's
- The directory is the current working directory, since history files don't
  store a per-command `cwd`

# Blink the current tmux pane until Ctrl-C.
> notify.py --blink

# Send a one-shot macOS notification.
> notify.py --notify

# Do both.
> notify.py --blink --notify
"""

import argparse
import logging
import os
import platform
import re
import time
from typing import List, Optional, Tuple

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
    # > history 10
    #  529  cd ~/src
    #  530  ls -la
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


def _get_last_command_and_dir() -> Tuple[str, str]:
    """
    Return the last executed shell command and the current directory.

    :return: tuple of (last command, current working directory)
    """
    last_command = _get_nth_command(1)
    current_dir = os.getcwd()
    return last_command, current_dir


def _send_notification(
    message: str, title: str, sound_name: str = "Glass"
) -> None:
    """
    Send a macOS notification via `osascript`.

    No-op with a warning on non-macOS systems.

    :param message: text to display in the notification
    :param title: title of the notification
    :param sound_name: name of the macOS sound to play
    """
    hdbg.dassert_eq(platform.system(), "Darwin",
        "Notifications are only supported on macOS")
    cmd = (
        f"osascript -e 'display notification \"{message}\" "
        f'with title "{title}" sound name "{sound_name}"\''
    )
    hsystem.system(cmd)


def _blink_pane(title: str) -> None:
    """
    Blink the current tmux pane background until interrupted with Ctrl-C.

    Restore the original pane title and background color on exit.

    :param title: text to set as the pane title while blinking
    """
    _, orig_title = hsystem.system_to_one_line(
        "tmux display-message -p '#{pane_title}'"
    )
    hsystem.system(f"tmux select-pane -T 'Finished: {title}'")
    try:
        while True:
            hsystem.system("tmux select-pane -P 'bg=red'")
            time.sleep(0.4)
            hsystem.system("tmux select-pane -P 'bg=default'")
            time.sleep(0.4)
    except KeyboardInterrupt:
        _LOG.info("Interrupted, restoring pane state")
    finally:
        hsystem.system("tmux select-pane -P 'bg=default'")
        hsystem.system(f"tmux select-pane -T '{orig_title}'")


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--blink",
        action="store_true",
        help="Blink the tmux pane background until Ctrl-C",
    )
    parser.add_argument(
        "--notify",
        action="store_true",
        help="Send a macOS notification",
    )
    parser.add_argument(
        "--title",
        action="store",
        default="",
        help="Title of the macOS notification",
    )
    parser.add_argument(
        "--sound",
        action="store",
        default="Glass",
        help="Name of the macOS sound to play with the notification",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    #
    hdbg.dassert_in("bash", os.environ.get("SHELL", ""))
    last_command, current_dir = _get_last_command_and_dir()
    message = f"{last_command} (in {current_dir})"
    if args.notify:
        _send_notification(message, title=args.title, sound_name=args.sound)
    if args.blink:
        _blink_pane(last_command)


if __name__ == "__main__":
    _main(_parse())
