#!/usr/bin/env python

"""
Notify the user that the last command is completed through different channels:
- Blinking the current tmux pane until interrupted
- Using a macOS notification

- The last executed shell command is read from the shell history file
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

# #############################################################################


def _get_history_file_path() -> str:
    """
    Return the path to the current shell's history file.

    :return: absolute path to `~/.zsh_history` or `~/.bash_history`
    """
    shell = os.environ.get("SHELL", "")
    if "zsh" in shell:
        file_name = "~/.zsh_history"
    elif "bash" in shell:
        file_name = "~/.bash_history"
    else:
        raise ValueError(f"Can't recognize SHELL='{shell}'")
    file_name = os.path.expanduser(file_name)
    return file_name


def _parse_last_command(
    history_text: str,
    *,
    n: int = 1,
    exclude_substrings: Optional[List[str]] = None,
) -> str:
    """
    Extract the n-th most recent command from shell history text.

    Handle both plain `bash` history lines and `zsh` extended history lines
    (e.g., `: 1700000000:0;ls -la`). Commands containing any of
    `exclude_substrings` are skipped (e.g., to exclude invocations of the
    calling script itself).

    :param history_text: raw content of a shell history file
    :param n: index (1 = most recent) of the command to return, counting
        from the end after exclusions are applied
    :param exclude_substrings: skip commands containing any of these
        substrings
    :return: n-th most recent command line, with any `zsh` timestamp prefix
        stripped
    """
    lines = [line.strip() for line in history_text.splitlines() if line.strip()]
    # E.g., `: 1700000000:0;ls -la` becomes `ls -la`.
    zsh_prefix_regex = r"^: \d+:\d+;"
    commands = [re.sub(zsh_prefix_regex, "", line) for line in lines]
    if exclude_substrings:
        commands = [
            command
            for command in commands
            if not any(sub in command for sub in exclude_substrings)
        ]
    hdbg.dassert_lt(0, len(commands), "History is empty")
    hdbg.dassert_lte(
        n,
        len(commands),
        "Not enough history: n=%s len(commands)=%s",
        n,
        len(commands),
    )
    last_command = commands[-n]
    return last_command


def _get_last_command_and_dir() -> Tuple[str, str]:
    """
    Return the last executed shell command and the current directory.

    :return: tuple of (last command, current working directory)
    """
    history_file = _get_history_file_path()
    history_text = hio.from_file(history_file)
    last_command = _parse_last_command(history_text)
    #
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
    last_command, current_dir = _get_last_command_and_dir()
    message = f"{last_command} (in {current_dir})"
    if args.notify:
        _send_notification(message, title=args.title, sound_name=args.sound)
    if args.blink:
        _blink_pane(last_command)


if __name__ == "__main__":
    _main(_parse())
