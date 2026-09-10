"""
Utilities for daemon-mode operations, i.e., scripts that keep re-running
instead of exiting after one pass

- There are two flows:
  1. Reactive daemon (`_daemon_watch()` / `run_reactive_daemon_mode()`):
     - Watch a file
     - Re-run (debounced) only when it changes
     - E.g., rebuilding a PDF from a `.tex` file that's being edited
  2. Periodic daemon (`run_periodic_daemon_mode()`):
     - Re-run on a fixed cadence regardless of whether anything changed
     - E.g., refreshing a GitHub workflow status or a pytest log's parsed
       summary every N seconds

Import as:

import helpers.hdaemon as hdaemon
"""

import argparse
import hashlib
import logging
import os
import shlex
import tempfile
import time
from typing import Callable, Optional

import helpers.hdbg as hdbg
import helpers.hsystem as hsystem
import helpers.htmux as htmux

_LOG = logging.getLogger(__name__)


# #############################################################################
# Periodic daemon.
# #############################################################################


def add_daemon_arg(
    parser: argparse.ArgumentParser,
    *,
    help_text: str = "Watch input file for changes and regenerate on change",
) -> argparse.ArgumentParser:
    """
    Add --daemon argument to an argument parser.

    :param parser: Argument parser to add daemon argument to
    :param help_text: help text for the flag, overridable since it means
        something different for the reactive vs. periodic flow
    :return: The parser (for method chaining)
    """
    parser.add_argument(
        "--daemon",
        action="store_true",
        help=help_text,
    )
    return parser


def add_periodic_daemon_args(
    parser: argparse.ArgumentParser, *, default_interval: int = 5
) -> argparse.ArgumentParser:
    """
    Add `--daemon` and `--interval` arguments to an argument parser, for
    scripts using periodic daemon mode (see `run_periodic_daemon_mode()`).

    :param parser: argument parser to add arguments to
    :param default_interval: default seconds between periodic runs
    :return: the parser (for method chaining)
    """
    add_daemon_arg(
        parser,
        help_text="Periodically re-run and report status (see --interval)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=default_interval,
        help="Seconds between periodic runs in daemon mode "
        f"(default: {default_interval})",
    )
    return parser


def run_periodic_daemon_mode(
    func: Callable[[], None],
    interval_in_sec: int,
    *,
    window_name_str: str = "",
) -> None:
    """
    Run periodic daemon mode: call `func()` every `interval_in_sec` seconds,
    forever, regardless of whether anything changed.

    E.g., watching on a fixed cadence:
    - a GitHub workflow's status with `invoke gh_workflow_list --daemon`
    - a pytest log's parsed summary with `pytest_failed.py --daemon`

    :param func: zero-arg callable to invoke on each iteration
    :param interval_in_sec: seconds to sleep between iterations
    :param window_name_str: tmux window name to use while daemon is running
        (no-op outside tmux)
    """
    _LOG.info("Periodic daemon mode: running every %ds", interval_in_sec)
    with htmux.window_name(window_name_str):
        while True:
            func()
            _LOG.info("Sleeping %ds before next run", interval_in_sec)
            time.sleep(interval_in_sec)


# #############################################################################
# Reactive daemon
# #############################################################################


def _file_hash(file_path: str) -> str:
    """
    Compute MD5 hash of a file.

    :param file_path: Path to the file
    :return: MD5 hash of the file contents
    """
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_conflict_marker_path(file_path: str) -> str:
    """
    Return the marker file path used to signal a write conflict on
    `file_path`.

    A watched command that rewrites `file_path` in place (e.g.
    `render_images.py` re-rendering a `.typ` file) can detect that the user
    changed the file while it was running and, instead of overwriting that
    newer edit, touch this marker file. `_daemon_watch()` checks for it after
    each run to tell a benign self-rewrite (settle, don't re-fire) apart from a
    real conflict (keep waiting for quiet, then retry).

    :param file_path: path to the watched file
    :return: path to its conflict marker file
    """
    key = hashlib.md5(file_path.encode()).hexdigest()
    return os.path.join(tempfile.gettempdir(), f"hdaemon.{key}.conflict")


def _daemon_watch(
    file_path: str,
    cmd: str,
    *,
    wait_in_sec: int = 1,
    debounce_sec: int = 2,
    abort_on_error: bool = True,
    watch_cmd_suffix: str = "",
) -> None:
    """
    Watch a file for changes and re-run command with debouncing.

    Polls the file at regular intervals by computing its MD5 hash. When a
    change is detected, waits for `debounce_sec` seconds with no further
    changes before executing the command. This prevents repeatedly running
    the command while the user is still editing the file.

    :param file_path: Path to file to monitor
    :param cmd: Command to execute when file changes
    :param wait_in_sec: Poll interval in seconds (default: 1)
    :param debounce_sec: Debounce duration in seconds (default: 2)
    :param abort_on_error: Whether to abort on command failure (default: True)
    :param watch_cmd_suffix: Suffix to append to cmd for watch runs.
        If provided, initial run uses cmd and watch runs use cmd + suffix
    """
    _LOG.info(
        "Daemon mode: watching '%s' for changes (poll every %ds, debounce %ds)...",
        file_path,
        wait_in_sec,
        debounce_sec,
    )
    hdbg.dassert_file_exists(file_path)

    def _run_cmd(cmd_to_run: str) -> None:
        try:
            hsystem.system(cmd_to_run, abort_on_error=abort_on_error)
        except Exception as e:
            _LOG.error("Daemon: command failed: %s", e)

    # Run immediately on first launch.
    _LOG.info("Initial run...")
    _run_cmd(cmd)
    _LOG.info("Initial run complete")
    # Build watch command with optional suffix.
    watch_cmd = cmd if not watch_cmd_suffix else cmd + watch_cmd_suffix
    # Clear any stale marker left over from a previous, unrelated run.
    conflict_marker = get_conflict_marker_path(file_path)
    if os.path.exists(conflict_marker):
        os.remove(conflict_marker)
    prev_hash = _file_hash(file_path)
    # Wall-clock timestamp of the last detected change, so `debounce_sec` is
    # measured in actual seconds regardless of `wait_in_sec` (counting polls
    # instead would make the debounce period `wait_in_sec * debounce_sec`,
    # correct only when `wait_in_sec == 1`).
    last_change_time: Optional[float] = None
    while True:
        time.sleep(wait_in_sec)
        cur_hash = _file_hash(file_path)
        if cur_hash != prev_hash:
            # File changed, (re)start the debounce countdown.
            _LOG.info(
                "File changed (hash: %s -> %s). Debouncing...",
                prev_hash,
                cur_hash,
            )
            prev_hash = cur_hash
            last_change_time = time.time()
        elif (
            last_change_time is not None
            and time.time() - last_change_time >= debounce_sec
        ):
            # Debounce complete, regenerate.
            _LOG.info("Debounce complete. Regenerating...")
            _run_cmd(watch_cmd)
            _LOG.info("Regeneration complete")
            # Re-baseline against the post-run file content. The watched
            # command itself can rewrite `file_path` in place (e.g.
            # `render_images.py` rewriting a `.typ` file), and without this
            # that self-inflicted change would look like a new user edit and
            # immediately re-trigger another debounce cycle.
            prev_hash = _file_hash(file_path)
            if os.path.exists(conflict_marker):
                # The command found the user had changed `file_path` while
                # it was running and skipped writing its own output to avoid
                # clobbering that edit. Don't treat this as settled: go back
                # to waiting for quiet on the user's newer content, then
                # retry.
                os.remove(conflict_marker)
                _LOG.info(
                    "'%s' changed during the run; waiting for quiet again "
                    "before retrying",
                    file_path,
                )
                last_change_time = time.time()
            else:
                last_change_time = None


def run_reactive_daemon_mode(
    input_file: str,
    cmd: str,
    window_name_str: str,
    *,
    watch_cmd_suffix: str = "",
    debounce_sec: int = 2,
    wait_in_sec: int = 1,
) -> None:
    """
    Run daemon mode: watch file for changes and regenerate with debouncing.

    Handles command building (removing --daemon flag), logging, tmux window
    naming, and daemon watching. Blocks until the user interrupts.

    :param input_file: File to watch for changes
    :param cmd: Full command line that invoked the script (including
        --daemon), used to rebuild the command for the watch runs
    :param window_name_str: Tmux window name to use while daemon is running
    :param watch_cmd_suffix: Suffix to append to command for watch runs
    :param debounce_sec: Debounce duration in seconds
    :param wait_in_sec: Poll interval in seconds
    """
    # Build command without --daemon flag for _daemon_watch to execute.
    cmd_parts = [part for part in shlex.split(cmd) if part != "--daemon"]
    cmd = " ".join(shlex.quote(part) for part in cmd_parts)
    _LOG.info("Daemon mode: watching '%s' for changes", input_file)
    with htmux.window_name(window_name_str):
        _daemon_watch(
            input_file,
            cmd,
            wait_in_sec=wait_in_sec,
            watch_cmd_suffix=watch_cmd_suffix,
            debounce_sec=debounce_sec,
        )
