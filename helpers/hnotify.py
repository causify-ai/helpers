"""
Notification context manager wrapper for `notify.py`.

Import as:

import helpers.hnotify as hnotify
"""

import contextlib
import logging
import subprocess
from typing import Generator

import helpers.hdbg as hdbg
import helpers.hgit as hgit

_LOG = logging.getLogger(__name__)


# #############################################################################
# Helper functions
# #############################################################################


def _get_notify_script_path() -> str:
    """
    Locate the `notify.py` script in the git tree.

    :return: Absolute path to `notify.py`
    """
    script_path = hgit.find_file_in_git_tree("notify.py")
    hdbg.dassert_is_not(
        script_path,
        None,
        "Could not find 'notify.py' in git tree",
    )
    return script_path


def _run_notify(
    title : str, *, sound: str = "Glass", timeout: int = -1, no_blink: bool = False
) -> None:
    """
    Call the notify script to send notification or blink window.

    :param title: Title of the notification (empty uses last command)
    :param sound: macOS sound name to play
    :param timeout: Seconds to blink for; -1 means forever until Ctrl-C
    :param no_blink: Skip blinking, only send notification
    """
    hdbg.dassert_isinstance(title, str, "Title must be a string")
    hdbg.dassert_ne(title, "")
    hdbg.dassert_isinstance(sound, str, "Sound must be a string")
    hdbg.dassert_isinstance(timeout, int, "Timeout must be an integer")
    # Build command line.
    script_path = _get_notify_script_path()
    cmd = [
        script_path,
        f"--timeout {timeout}",
        f"--sound {sound}",
    ]
    cmd.append(f"--title '{title}'")
    if no_blink:
        cmd.append("--no_blink")
    cmd_str = " ".join(cmd)
    _LOG.debug("Running notify command: %s", cmd_str)
    subprocess.run(cmd_str, shell=True, check=False)


# #############################################################################
# Public API
# #############################################################################


@contextlib.contextmanager
def notify(
    title: str, *,
    sound: str = "Glass", timeout: int = -1, no_blink: bool = False
) -> Generator[None, None, None]:
    """
    Context manager that notifies on exit via `notify.py`.

    Calls the notify script when exiting the context block, whether successful
    or on error. Safe to use on non-macOS systems (skips notification).

    :param title: Title of the notification
    :param sound: macOS sound name to play with notification
    :param timeout: Seconds to blink tmux window for; -1 means forever
    :param no_blink: Skip blinking, only send notification
        - Default: `False` (enable blinking)
    :yield: None

    - Example:
      ```
      with `notify()`:
          long_running_operation()
          # Notification sent after block exits.
      ```
    """
    try:
        yield
    finally:
        _run_notify(title=title, sound=sound, timeout=timeout, no_blink=no_blink)
