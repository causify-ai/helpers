#!/usr/bin/env python

"""
Notify the user that the last command is completed through different channels:
- Blinking the current tmux window tab until interrupted
- Using a macOS notification

By default both the blink and the notification are enabled.

# Do both (default behavior).
> notify.py

# Only send a one-shot macOS notification.
> notify.py --no_blink

# Only blink the current tmux window tab until Ctrl-C.
> notify.py --no_notify

# Blink for at most 10 seconds instead of forever.
> notify.py --timeout 10
"""

import argparse
import logging
import os
import platform
import time

import dev_scripts_helpers.coding_tools.last_cmd as dsclastc
import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


def _get_last_command() -> str:
    """
    Return the last executed shell command.

    Read the history file dumped by `notify2.sh` the same way `last_cmd.py`
    does, instead of shelling out to another script.

    :return: tuple of (last command, current working directory)
    """
    last_command = dsclastc._get_nth_command(
        1, exclude_substrings=["notify"]
    )
    return last_command


def _get_iterm2_name() -> str:
    """
    Return the name of the current iTerm2 session.

    :return: iTerm2 session name
    """
    cmd = (
        "osascript -e 'tell application \"iTerm2\" to name of current "
        "session of current window'"
    )
    _, name = hsystem.system_to_one_line(cmd)
    return name


def _send_notification(
    message: str, *, sound_name: str = "Glass"
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
        f'with title "" sound name "{sound_name}"\''
    )
    hsystem.system(cmd)


def _blink_pane(timeout: int) -> None:
    """
    Blink the current tmux window tab until interrupted with Ctrl-C.

    Blink by renaming the window, alternating between "DONE" and a blank
    name with the same number of characters as the original window name
    (so the tab width doesn't change while blinking).

    Restore the original window name on exit.

    :param timeout: number of seconds to blink for; -1 means blink
        forever until Ctrl-C
    """
    _, window_id = hsystem.system_to_one_line(
        "tmux display-message -p '#{window_id}'"
    )
    _, orig_name = hsystem.system_to_one_line(
        "tmux display-message -p '#{window_name}'"
    )
    done_name = "DONE" + " " * max(0, len(orig_name) - len("DONE"))
    blank_name = " " * len(orig_name)
    if timeout == -1:
        print("Waiting for CTRL-C...")
    else:
        print(f"Blinking for {timeout} seconds (Ctrl-C to stop early)...")
    start_time = time.time()
    try:
        while timeout == -1 or (time.time() - start_time) < timeout:
            hsystem.system(f"tmux rename-window -t {window_id} -- '{done_name}'")
            time.sleep(0.5)
            hsystem.system(f"tmux rename-window -t {window_id} -- '{blank_name}'")
            time.sleep(0.5)
    except KeyboardInterrupt:
        _LOG.info("Interrupted, restoring window name")
    finally:
        hsystem.system(f"tmux rename-window -t {window_id} -- '{orig_name}'")


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hparser.add_bool_arg(
        parser,
        "blink",
        default_value=True,
        help_="Blink the tmux window tab until Ctrl-C",
    )
    hparser.add_bool_arg(
        parser,
        "notify",
        default_value=True,
        help_="Send a macOS notification",
    )
    parser.add_argument(
        "--timeout",
        action="store",
        type=int,
        default=-1,
        help="Number of seconds to blink for; -1 means blink forever "
        "until Ctrl-C",
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
    message = []
    if args.title == "":
        last_command = _get_last_command()
        message.append(last_command)
    else:
        message.append(args.title)
    current_dir = os.getcwd()
    message.append(f"dir={current_dir}")
    current_iterm2_name = _get_iterm2_name()
    message.append(f"term={current_iterm2_name}")
    message = "\n".join(message)
    if args.notify:
        _send_notification(message, sound_name=args.sound)
    if args.blink:
        _blink_pane(args.timeout)


if __name__ == "__main__":
    _main(_parse())
