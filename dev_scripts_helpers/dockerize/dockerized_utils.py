"""
Utilities for dockerized CLI scripts.

Import as:

import dev_scripts_helpers.dockerize.dockerized_utils as dshddout
"""

import argparse
import logging
import os
import platform
import subprocess
from typing import Any, Callable, Dict, Optional

import helpers.hdocker as hdocker
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


def test_container_build(
    self_: Any,
    input_content: str,
    input_ext: str,
    output_ext: str,
    run_func: Callable[..., None],
    *,
    run_kwargs: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Reusable helper for testing container builds in dockerized tools.

    Sets up input/output directories, creates input file with content, runs the
    dockerized function with `force_rebuild=True`, and verifies output file
    exists. This consolidates common test patterns across all containerized
    build tests.

    :param self_: test instance (needs `get_input_dir()`, `get_output_dir()`,
        `assertTrue()`)
    :param input_content: content to write to the input file
    :param input_ext: file extension for input (e.g., 'md', 'typ', 'tex')
    :param output_ext: file extension for output (e.g., 'pdf', 'html')
    :param run_func: dockerized function to call (e.g.,
        `run_dockerized_pandoc`)
    :param run_kwargs: additional keyword arguments to pass to `run_func`
    """
    if run_kwargs is None:
        run_kwargs = {}
    # Create input and output directories.
    input_dir = self_.get_input_dir()
    output_dir = self_.get_output_dir()
    hio.create_dir(output_dir, incremental=True)
    # Create input file with test content.
    input_file = os.path.join(input_dir, f"test.{input_ext}")
    input_content = hprint.dedent(input_content)
    hio.to_file(input_file, input_content)
    _LOG.debug("Created input file: %s", input_file)
    # Create output file path.
    output_file = os.path.join(output_dir, f"test_output.{output_ext}")
    # Get docker configuration and run the containerized function.
    use_sudo = hdocker.get_use_sudo()
    _LOG.debug(
        "Running containerized function with input_file=%s, output_file=%s",
        input_file,
        output_file,
    )
    run_func(
        input_file,
        output_file,
        force_rebuild=True,
        use_sudo=use_sudo,
        **run_kwargs,
    )
    # Verify output file was created.
    self_.assertTrue(
        os.path.exists(output_file),
        msg=f"Output file {output_file} was not created",
    )
    _LOG.debug("Output file verified: %s", output_file)


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
