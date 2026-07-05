#!/usr/bin/env python

"""
Notify the user that the last command is completed through different channels:
- Blinking the current tmux window tab until interrupted
- Using a macOS notification

- The last executed shell command is read from the tmp file written by
  `last_cmd.sh`, which must be *sourced* (not executed) in the interactive
  shell so that `history -a` / `history 10` run in that shell's process.
  A Python child process can't call `history` itself: it can't reach into
  the parent shell's memory, so it would only ever see its own empty
  history, never the interactive shell's
- The directory is the current working directory, since history files don't
  store a per-command `cwd`

# Blink the current tmux window tab until Ctrl-C.
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


def _get_last_command_and_dir() -> Tuple[str, str]:
    """
    Return the last executed shell command and the current directory.

    :return: tuple of (last command, current working directory)
    """
    # TODO(ai_gp): Get the last command using 
    last_command = 
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


def _blink_pane() -> None:
    """
    Blink the current tmux window tab until interrupted with Ctrl-C.

    Blink by renaming the window, alternating between "DONE" and a blank
    name with the same number of characters as the original window name
    (so the tab width doesn't change while blinking).

    Restore the original window name on exit.
    """
    _, window_id = hsystem.system_to_one_line(
        "tmux display-message -p '#{window_id}'"
    )
    _, orig_name = hsystem.system_to_one_line(
        "tmux display-message -p '#{window_name}'"
    )
    blank_name = " " * len(orig_name)
    try:
        while True:
            hsystem.system(f"tmux rename-window -t {window_id} 'DONE'")
            time.sleep(0.4)
            hsystem.system(f"tmux rename-window -t {window_id} '{blank_name}'")
            time.sleep(0.4)
    except KeyboardInterrupt:
        _LOG.info("Interrupted, restoring window name")
    finally:
        hsystem.system(f"tmux rename-window -t {window_id} '{orig_name}'")


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--blink",
        action="store_true",
        help="Blink the tmux window tab until Ctrl-C",
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
        _blink_pane()


if __name__ == "__main__":
    _main(_parse())