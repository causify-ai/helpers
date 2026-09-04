#!/usr/bin/env python

"""
Reset the names of the windows in the current tmux session.

Every window's name is cleared (set to an empty string), except the first
window whose active pane is inside a `helpers_root` directory, which is
named `helpers` instead.

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


if __name__ == "__main__":
    _main(_parse())
