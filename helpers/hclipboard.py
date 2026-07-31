"""
Clipboard utilities for reading and writing system clipboard content.

Import as:

import helpers.hclipboard as hclipbo
"""

import logging
import subprocess

_LOG = logging.getLogger(__name__)


def get_clipboard_content() -> str:
    """
    Get content from system clipboard (macOS/Linux compatible).

    Tries clipboard commands in order:
    - pbpaste (macOS)
    - xclip (Linux)
    - xsel (Linux)

    :return: clipboard content as string
    :raises RuntimeError: if no clipboard command is available
    """
    try:
        # Try macOS first.
        result = subprocess.run(
            ["pbpaste"], capture_output=True, text=True, check=False
        )
        if result.returncode == 0:
            _LOG.debug("Read clipboard using pbpaste")
            return result.stdout
    except FileNotFoundError:
        pass
    try:
        # Try Linux with xclip.
        result = subprocess.run(
            ["xclip", "-selection", "clipboard", "-o"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            _LOG.debug("Read clipboard using xclip")
            return result.stdout
    except FileNotFoundError:
        pass
    try:
        # Try Linux with xsel.
        result = subprocess.run(
            ["xsel", "--clipboard", "--output"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            _LOG.debug("Read clipboard using xsel")
            return result.stdout
    except FileNotFoundError:
        pass
    raise RuntimeError("Could not read clipboard: no suitable command found")


def set_clipboard_content(content: str) -> None:
    """
    Set content to system clipboard (macOS/Linux compatible).

    Tries clipboard commands in order:
    - pbcopy (macOS)
    - xclip (Linux)
    - xsel (Linux)

    :param content: content to write to clipboard
    :raises RuntimeError: if no clipboard command is available
    """
    try:
        # Try macOS first
        result = subprocess.run(
            ["pbcopy"],
            input=content,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            _LOG.debug("Wrote to clipboard using pbcopy")
            return
    except FileNotFoundError:
        pass
    try:
        # Try Linux with xclip
        result = subprocess.run(
            ["xclip", "-selection", "clipboard"],
            input=content,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            _LOG.debug("Wrote to clipboard using xclip")
            return
    except FileNotFoundError:
        pass
    try:
        # Try Linux with xsel
        result = subprocess.run(
            ["xsel", "--clipboard", "--input"],
            input=content,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            _LOG.debug("Wrote to clipboard using xsel")
            return
    except FileNotFoundError:
        pass
    raise RuntimeError("Could not write to clipboard: no suitable command found")


def to_clipboard_or_print(content: str, use_clipboard: bool) -> None:
    """
    Save content to clipboard or print (cross-platform compatible).

    Either copies to system clipboard or prints to stdout, depending on
    use_clipboard flag. Works on both macOS and Linux.

    :param content: content to save or print
    :param use_clipboard: if True, copy to clipboard; if False, print to stdout
    """
    content = content.rstrip("\n")
    if not use_clipboard:
        print(content)
        return
    if not content:
        print("Nothing to copy")
        return
    try:
        set_clipboard_content(content)
        print(f"\n# Copied to system clipboard:\n{content}")
    except RuntimeError as e:
        _LOG.warning("%s", str(e))
        print(content)
