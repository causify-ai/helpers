"""
Utilities for daemon-mode operations, i.e., scripts that keep re-running
instead of exiting after one pass

- There are two flows:
  1. Reactive daemon (`daemon_watch()` / `run_daemon_mode()`):
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
import shlex
import time
from typing import Callable

import helpers.hdbg as hdbg
import helpers.hsystem as hsystem
import helpers.htmux as htmux

_LOG = logging.getLogger(__name__)


# #############################################################################
# Periodic daemon.
# #############################################################################


# TODO(ai_gp): Inline if it's called only once
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
        # TODO(ai_gp): fn -> func
    fn: Callable[[], None],
    interval_in_sec: int,
    *,
    window_name_str: str = "",
) -> None:
    """
    Run periodic daemon mode: call `fn()` every `interval_in_sec` seconds,
    forever, regardless of whether anything changed.

    E.g., watching on a fixed cadence:
    - a GitHub workflow's status with `invoke gh_watch()`)
    - a pytest log's parsed summary with `pytest_failed.py --daemon`

    :param fn: zero-arg callable to invoke on each iteration
    :param interval_in_sec: seconds to sleep between iterations
    :param window_name_str: tmux window name to use while daemon is running
        (no-op outside tmux)
    """
    _LOG.info("Periodic daemon mode: running every %ds", interval_in_sec)
    with htmux.window_name(window_name_str):
        while True:
            fn()
            _LOG.info("Sleeping %ds before next run", interval_in_sec)
            time.sleep(interval_in_sec)


# #############################################################################
# Reactive daemon
# #############################################################################


# TODO(ai_gp): Who uses it? If nobody else -> private
def file_hash(file_path: str) -> str:
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


# TODO(ai_gp): Who uses it? If nobody else -> private
def daemon_watch(
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
    prev_hash = file_hash(file_path)
    stable_hash: str = ""
    time_since_last_change = 0
    while True:
        time.sleep(wait_in_sec)
        cur_hash = file_hash(file_path)
        if cur_hash != prev_hash:
            # File changed, start debounce.
            _LOG.info(
                "File changed (hash: %s -> %s). Debouncing...",
                prev_hash,
                cur_hash,
            )
            stable_hash = cur_hash
            time_since_last_change = 0
            prev_hash = cur_hash
        elif stable_hash:
            # In debounce period, tracking time without changes.
            time_since_last_change += 1
            if time_since_last_change >= debounce_sec:
                # Debounce complete, regenerate.
                _LOG.info("Debounce complete. Regenerating...")
                _run_cmd(watch_cmd)
                _LOG.info("Regeneration complete")
                stable_hash = ""


# TODO(ai_gp): -> run_reactive_daemon_mode
def run_daemon_mode(
    input_file: str,
    cmd: str,
    window_name_str: str,
    *,
    watch_cmd_suffix: str = "",
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
    """
    # Build command without --daemon flag for daemon_watch to execute.
    cmd_parts = [part for part in shlex.split(cmd) if part != "--daemon"]
    cmd = " ".join(shlex.quote(part) for part in cmd_parts)
    _LOG.info("Daemon mode: watching '%s' for changes", input_file)
    with htmux.window_name(window_name_str):
        daemon_watch(input_file, cmd, watch_cmd_suffix=watch_cmd_suffix)
