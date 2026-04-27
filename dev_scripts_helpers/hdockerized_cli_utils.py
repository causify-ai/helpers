"""
Utilities for dockerized CLI scripts.
"""

import argparse
import logging
import platform
import subprocess

_LOG = logging.getLogger(__name__)


def add_open_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--open",
        action="store_true",
        default=False,
        help="Open the output file on macOS",
    )


def open_file_on_macos(file_path: str) -> None:
    if platform.system() != "Darwin":
        _LOG.warning("--open flag only works on macOS")
        return
    subprocess.run(["open", file_path], check=True)
    _LOG.info("Opened file with macOS 'open' command: %s", file_path)
