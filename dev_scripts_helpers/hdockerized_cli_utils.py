"""
Utilities for dockerized CLI scripts.

Import as:

import dev_scripts_helpers.hdockerized_cli_utils as dshhclut
"""

import argparse
import logging
import platform
import subprocess

_LOG = logging.getLogger(__name__)


def add_open_arg(parser: argparse.ArgumentParser) -> None:
    """
    Add --open option to parser for opening output files on macOS.

    :param parser: ArgumentParser instance to add the option to
    """
    parser.add_argument(
        "--open",
        action="store_true",
        default=False,
        help="Open the output file on macOS",
    )


def open_file_on_macos(file_path: str) -> None:
    """
    Open a file on macOS using the 'open' command.

    :param file_path: Path to the file to open
    :raises subprocess.CalledProcessError: If open command fails
    """
    if platform.system() != "Darwin":
        _LOG.warning("--open flag only works on macOS")
        return
    subprocess.run(["open", file_path], check=True)
    _LOG.info("Opened file with macOS 'open' command: %s", file_path)
