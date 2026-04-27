"""
Utilities for dockerized CLI scripts.

Import as:

import dev_scripts_helpers.dockerize.dockerized_cli_utils as dsddhclut
"""

import argparse
import logging
import os
import platform
import subprocess
from typing import Any

import helpers.hio as hio
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)


def create_test_file(self_: Any, txt: str, extension: str) -> str:
    """
    Create a scratch file with the given content and extension for testing.

    :param self_: test instance (needs `get_scratch_space()`)
    :param txt: file contents (leading/trailing blank lines are stripped)
    :param extension: file extension without leading dot
    :return: absolute path to the created file
    """
    file_path = os.path.join(self_.get_scratch_space(), f"input.{extension}")
    txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
    _LOG.debug("txt=\n%s", txt)
    hio.to_file(file_path, txt)
    return file_path


# TODO(gp): Consider adding these as TestCase.assert_file_exists similar to the
# hdbg counterparts.
def assert_output_file_exists(self_: Any, out_file_path: str) -> None:
    """
    Assert that a file exists at the given path.

    :param self_: test instance (needs `assertTrue()`)
    :param out_file_path: path to check
    """
    self_.assertTrue(
        os.path.exists(out_file_path),
        msg=f"Output file {out_file_path} not found",
    )


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
