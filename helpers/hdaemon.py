"""
File watching utilities with debouncing for daemon-mode operations.

Provides file hashing and command execution on file changes, useful for
watch-mode file processors (e.g., document rebuilders, format watchers).

Import as:

import helpers.hdaemon as hdaem
"""

import argparse
import hashlib
import logging
import shlex
import sys
import time
from typing import Optional

import helpers.hdbg as hdbg
import helpers.hsystem as hsystem
import helpers.htmux as htmux

_LOG = logging.getLogger(__name__)


def add_daemon_arg(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    """
    Add --daemon argument to an argument parser.

    :param parser: Argument parser to add daemon argument to
    :return: The parser (for method chaining)
    """
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Watch input file for changes and regenerate on change",
    )
    return parser


def run_daemon_mode(
    input_file: str,
    window_name_str: str,
    watch_cmd_suffix: Optional[str] = None,
) -> None:
    """
    Run daemon mode: watch file for changes and regenerate with debouncing.

    Handles command building (removing --daemon flag), logging, tmux window
    naming, and daemon watching. Blocks until the user interrupts.

    :param input_file: File to watch for changes
    :param window_name_str: Tmux window name to use while daemon is running
    :param watch_cmd_suffix: Suffix to append to command for watch runs
    """
    # Build command without --daemon flag for daemon_watch to execute.
    cmd_parts = [sys.argv[0]] + [
        arg for arg in sys.argv[1:] if arg != "--daemon"
    ]
    cmd = " ".join(shlex.quote(part) for part in cmd_parts)
    _LOG.info("Daemon mode: watching '%s' for changes", input_file)
    with htmux.window_name(window_name_str):
        daemon_watch(input_file, cmd, watch_cmd_suffix=watch_cmd_suffix)


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


def daemon_watch(
    file_path: str,
    cmd: str,
    *,
    wait_in_sec: int = 1,
    debounce_sec: int = 2,
    abort_on_error: bool = True,
    watch_cmd_suffix: Optional[str] = None,
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
    :param watch_cmd_suffix: Suffix to append to cmd for watch runs (default: None).
        If provided, initial run uses cmd and watch runs use cmd + suffix.
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

    # Run immediately on first launch, opening the output file so the user
    # has a viewer (e.g., Skim) attached to it.
    _LOG.info("Initial run...")
    _run_cmd(cmd)
    # Build watch command with optional suffix.
    watch_cmd = cmd if watch_cmd_suffix is None else cmd + watch_cmd_suffix
    prev_hash = file_hash(file_path)
    stable_hash: Optional[str] = None
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
        elif stable_hash is not None:
            # In debounce period, tracking time without changes.
            time_since_last_change += 1
            if time_since_last_change >= debounce_sec:
                # Debounce complete, regenerate.
                _LOG.info("Debounce complete. Regenerating...")
                _run_cmd(watch_cmd)
                stable_hash = None
