"""
Tmux window name management utilities.

Import as:

import helpers.htmux as htmux
"""

import contextlib
import logging
import os
import subprocess
from typing import Generator, List, Optional

import helpers.hdbg as hdbg

_LOG = logging.getLogger(__name__)


# #############################################################################
# Helper functions
# #############################################################################


def _in_tmux() -> bool:
    """
    Check if running inside a tmux session.

    :return: `True` if inside tmux, `False` otherwise
    """
    return "TMUX" in os.environ


def _run_tmux_command(args: List[str]) -> Optional[str]:
    """
    Run a tmux command and return stdout.

    :param args: Command arguments to pass to `tmux`
    :return: Command output stripped of whitespace, or `None` on error
    """
    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


# #############################################################################
# Public API
# #############################################################################


def get_window_name() -> Optional[str]:
    """
    Get the current tmux window name.

    :return: Window name if in tmux session, `None` otherwise
    """
    hdbg.dassert(_in_tmux())
    _LOG.debug("Fetching tmux window name")
    window_name = _run_tmux_command(["tmux", "display-message", "-p", "#{window_name}"])
    _LOG.debug("window_name='%s'", window_name)
    return window_name


def set_window_name(name: str) -> bool:
    """
    Set the tmux window name.

    :param name: New window name
    :return: `True` if successful, `False` if not in tmux or operation failed
    """
    hdbg.dassert_isinstance(name, str, "Window name must be a string")
    hdbg.dassert_ne(name, "", "Window name cannot be empty")
    hdbg.dassert(_in_tmux())
    #
    _LOG.debug("Setting window name to '%s'", name)
    result = _run_tmux_command(["tmux", "rename-window", name])
    success = result is not None
    _LOG.debug("Window rename result: %s", success)
    return success


@contextlib.contextmanager
def window_name(name: str) -> Generator[None, None, None]:
    """
    Context manager to temporarily rename tmux window.

    Saves the current window name on entry and restores it on exit, even if an
    error occurs. Safe to use outside tmux session (no-op).

    :param name: Temporary window name
    :yield: None
        Example:
            with `window_name("build")`:
                run_build_process()
                # Window is restored after this block
    """
    hdbg.dassert_isinstance(name, str, "Window name must be a string")
    hdbg.dassert_ne(name, "", "Window name cannot be empty")
    if not _in_tmux():
        _LOG.debug("Not in tmux: skipping")
        yield
        return
    # Save original window name and rename to new name.
    original_name = get_window_name()
    try:
        set_window_name(name)
        yield
    finally:
        # Restore original window name.
        if original_name is not None:
            set_window_name(original_name)
