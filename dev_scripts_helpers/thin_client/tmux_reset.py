#!/usr/bin/env python

"""
Reset the names of the windows in the current tmux session.

Every window's name is cleared (set to an empty string), except the first
window whose active pane is inside a `helpers_root` directory, which is
named `helpers` instead. The working directory and the executable running
in the foreground of every pane are printed, and the screen of every idle
pane (i.e., running a shell with nothing else in the foreground) is
cleared.

# Usage Example

- Reset window names in the current tmux session:
> tmux_reset.py

- Preview what would be renamed without actually renaming anything:
> tmux_reset.py --dry_run

Import as:

import dev_scripts_helpers.thin_client.tmux_reset as dsthctmre
"""

import argparse
import logging
import os
from typing import List, Tuple

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# Names of shells that `pane_current_command` reports when a pane is idle
# (i.e., nothing else is running in the foreground).
_SHELL_COMMANDS = {"bash", "zsh", "sh", "fish", "csh", "tcsh", "ksh"}

# #############################################################################


def _get_tmux_windows() -> List[Tuple[int, str]]:
    """
    Get index and pane working directory of each window in the tmux session.

    :return: list of (window_index, pane_current_path), ordered by
        window index
        ```
        [(0, "/Users/saggese/src/umd_classes1/helpers_root"),
         (1, "/Users/saggese/src/umd_classes1")]
        ```
    """
    hdbg.dassert_in("TMUX", os.environ, "Script must run inside a tmux session")
    # `pane_current_path` refers to the active pane of each window.
    cmd = "tmux list-windows -F '#{window_index}:#{pane_current_path}'"
    _, output = hsystem.system_to_string(cmd)
    _LOG.debug(hprint.to_str("output"))
    windows = []
    for line in output.splitlines():
        window_index_str, pane_current_path = line.split(":", 1)
        windows.append((int(window_index_str), pane_current_path))
    _LOG.debug(hprint.to_str("windows"))
    return windows


def _compute_window_names(
    windows: List[Tuple[int, str]],
) -> List[Tuple[int, str, str]]:
    """
    Compute the new name for each window.

    The first window whose pane working directory is `helpers_root` is
    named `helpers`. Every other window (including further `helpers_root`
    matches) gets an empty name.

    :param windows: list of (window_index, pane_current_path), as returned
        by `_get_tmux_windows()`
    :return: list of (window_index, pane_current_path, new_name)
    """
    _LOG.debug(hprint.to_str("windows"))
    window_names = []
    # Only the first `helpers_root` window is special-cased; track whether
    # it was already found.
    found_helpers_root = False
    for window_index, pane_current_path in windows:
        is_helpers_root = os.path.basename(pane_current_path) == "helpers_root"
        if is_helpers_root and not found_helpers_root:
            new_name = "helpers"
            found_helpers_root = True
        else:
            new_name = ""
        window_names.append((window_index, pane_current_path, new_name))
    _LOG.debug(hprint.to_str("window_names"))
    return window_names


def _rename_window(
    window_index: int, pane_current_path: str, new_name: str, *, dry_run: bool
) -> None:
    """
    Rename one tmux window.

    :param window_index: index of the window to rename
    :param pane_current_path: current working directory of the window's active
        pane, only used for the dry-run log message
    :param new_name: name to assign to the window
    :param dry_run: if True, only show what would be done without doing it
    """
    _LOG.debug(hprint.to_str("window_index pane_current_path new_name dry_run"))
    cmd = f"tmux rename-window -t {window_index} '{new_name}'"
    if dry_run:
        _LOG.warning(
            "[DRY_RUN] Would rename window %d ('%s') to '%s'",
            window_index,
            pane_current_path,
            new_name,
        )
    else:
        _LOG.info("Renaming window %d to '%s'", window_index, new_name)
        hsystem.system(cmd)


def _get_tmux_panes() -> List[Tuple[int, int, str, str, str]]:
    """
    Get index, working directory, current command, and TTY of each pane.

    :return: list of (window_index, pane_index, pane_current_path,
        pane_current_command, pane_tty), ordered by window index and then
        pane index
        ```
        [(0, 0, "/Users/saggese/src/umd_classes1/helpers_root", "zsh", "/dev/ttys002"),
         (0, 1, "/Users/saggese/src/umd_classes1", "vim", "/dev/ttys003")]
        ```
    """
    hdbg.dassert_in("TMUX", os.environ, "Script must run inside a tmux session")
    # `-s` restricts the listing to the panes of the current session (as
    # opposed to `-a`, which lists panes across all tmux sessions).
    cmd = (
        "tmux list-panes -s -F "
        "'#{window_index}:#{pane_index}:#{pane_current_path}:"
        "#{pane_current_command}:#{pane_tty}'"
    )
    _, output = hsystem.system_to_string(cmd)
    _LOG.debug(hprint.to_str("output"))
    panes = []
    for line in output.splitlines():
        (
            window_index_str,
            pane_index_str,
            pane_current_path,
            pane_current_command,
            pane_tty,
        ) = line.split(":", 4)
        panes.append(
            (
                int(window_index_str),
                int(pane_index_str),
                pane_current_path,
                pane_current_command,
                pane_tty,
            )
        )
    _LOG.debug(hprint.to_str("panes"))
    return panes


def _get_pane_executable(pane_tty: str) -> str:
    """
    Get the full command line of the executable running in a pane.

    `pane_current_command` (reported by tmux and used elsewhere in this
    script) only gives the short process name (e.g., `python3`), not its
    arguments. This looks up, via `ps`, the process that belongs to the
    foreground process group of the pane's TTY (the `+` flag in `ps`'s
    `stat` column), which is the executable actually running in the pane
    (e.g., `python3 foo.py --bar`) instead of just its name.

    :param pane_tty: TTY device of the pane (e.g., "/dev/ttys002"), as
        reported by tmux's `#{pane_tty}`
    :return: full command line of the foreground process, or empty string
        if none is found (e.g., the pane was closed in the meantime)
    """
    _LOG.debug(hprint.to_str("pane_tty"))
    # `ps -t` wants the device name without the `/dev/` prefix.
    tty_name = os.path.basename(pane_tty)
    cmd = f"ps -t {tty_name} -o stat=,args="
    _, output = hsystem.system_to_string(cmd, abort_on_error=False)
    _LOG.debug(hprint.to_str("output"))
    executable = ""
    for line in output.splitlines():
        stat, _, args = line.strip().partition(" ")
        if "+" in stat:
            executable = args.strip()
            break
    _LOG.debug(hprint.to_str("executable"))
    return executable


def _print_pane_info(panes: List[Tuple[int, int, str, str, str]]) -> None:
    """
    Print the working directory and running executable of every pane.

    :param panes: list of (window_index, pane_index, pane_current_path,
        pane_current_command, pane_tty), as returned by `_get_tmux_panes()`
    """
    for window_index, pane_index, pane_current_path, _, pane_tty in panes:
        executable = _get_pane_executable(pane_tty)
        _LOG.info(
            "Window %d, pane %d: %s [%s]",
            window_index,
            pane_index,
            pane_current_path,
            executable,
        )


def _clear_pane(
    window_index: int,
    pane_index: int,
    pane_current_command: str,
    *,
    dry_run: bool,
) -> None:
    """
    Clear one tmux pane's screen, only if the pane is idle.

    A pane is idle when its foreground command is a shell (i.e., nothing
    else is running in it).

    :param window_index: index of the window containing the pane
    :param pane_index: index of the pane to clear
    :param pane_current_command: name of the command currently running in
        the foreground of the pane, used to decide whether the pane is
        idle
    :param dry_run: if True, only show what would be done without doing it
    """
    _LOG.debug(
        hprint.to_str(
            "window_index pane_index pane_current_command dry_run"
        )
    )
    target = f"{window_index}.{pane_index}"
    if pane_current_command not in _SHELL_COMMANDS:
        _LOG.debug(
            "Skipping pane %s: '%s' is running", target, pane_current_command
        )
        return
    cmd = f"tmux send-keys -t {target} 'clear' Enter"
    if dry_run:
        _LOG.warning("[DRY_RUN] Would clear pane %s", target)
    else:
        _LOG.info("Clearing pane %s", target)
        hsystem.system(cmd)


def _clear_idle_panes(
    panes: List[Tuple[int, int, str, str, str]], *, dry_run: bool
) -> None:
    """
    Clear the screen of every idle pane (i.e., with nothing running).

    :param panes: list of (window_index, pane_index, pane_current_path,
        pane_current_command, pane_tty), as returned by `_get_tmux_panes()`
    :param dry_run: if True, only show what would be done without doing it
    """
    for window_index, pane_index, _, pane_current_command, _ in panes:
        _clear_pane(
            window_index, pane_index, pane_current_command, dry_run=dry_run
        )


def _reset_tmux_window_names(*, dry_run: bool) -> None:
    """
    Reset the name of each window in the current tmux session.

    :param dry_run: if True, only show what would be done without doing it
    """
    _LOG.debug(hprint.to_str("dry_run"))
    windows = _get_tmux_windows()
    _LOG.info("Found %d tmux window(s)", len(windows))
    window_names = _compute_window_names(windows)
    for window_index, pane_current_path, new_name in window_names:
        _rename_window(
            window_index, pane_current_path, new_name, dry_run=dry_run
        )


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Show what would be done without actually doing it",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    _reset_tmux_window_names(dry_run=args.dry_run)
    panes = _get_tmux_panes()
    _LOG.info("Found %d tmux pane(s)", len(panes))
    _print_pane_info(panes)
    _clear_idle_panes(panes, dry_run=args.dry_run)


if __name__ == "__main__":
    _main(_parse())
