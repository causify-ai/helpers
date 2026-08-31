"""
Support opening a file.

Import as:

import helpers.hopen as hopen
"""

# TODO(gp): -> open_file or move it to system_interaction.py

import argparse
import logging
import os
from typing import Optional

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# #############################################################################


def add_open_arg(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """
    Add `--open` / `--open_app` options to open the output file on macOS.

    :param parser: parser to add the options to
    """
    parser.add_argument(
        "--open",
        action="store_true",
        default=False,
        help="Open the output file on macOS",
    )
    parser.add_argument(
        "--open_app",
        action="store",
        default=None,
        help="App to open the output file with (e.g., 'Skim', 'Preview'); "
        "used only together with --open",
    )
    return parser


# #############################################################################


def _cmd_open_generic(file_name: str, os_name: str) -> Optional[str]:
    """
    Get OS-specific command to open a file with the default app.

    This is used both as the HTML handler and as the fallback for any
    extension without a dedicated handler (e.g., `png`, `svg`, `md`).
    """
    # Retrieve the executable.
    os_cmds = {
        "Darwin": "open",
        "Windows": "start",
        "Linux": "xdg-open",
    }
    hdbg.dassert_in(os_name, os_cmds)
    exec_name = os_cmds[os_name]
    # Build the command (don't check if it exists, as we may be generating
    # a command for a different OS than the current one).
    full_cmd = f"{exec_name} {file_name}"
    # Warn if the command won't work on the current system.
    current_os = hsystem.get_os_name()
    if current_os != os_name and not hsystem.check_exec(exec_name):
        _LOG.warning(
            "Can't execute '%s' command on current platform (%s), but this is expected",
            exec_name,
            current_os,
        )
    if os_name == "Linux":
        _LOG.warning(
            "To open files faster launch in background '%s &'", exec_name
        )
    return full_cmd


def _cmd_open_with_app(
    file_name: str, os_name: str, app: str
) -> Optional[str]:
    """
    Get OS-specific command to open a file with a specific application.

    :param app: name of the app to open the file with (e.g., "Skim",
        "Preview")
    """
    if os_name != "Darwin":
        _LOG.warning(
            "Opening a file with a specific app is only supported on "
            "macOS, not on '%s'; falling back to the default app",
            os_name,
        )
        full_cmd = _cmd_open_generic(file_name, os_name)
    else:
        full_cmd = f'open -a "{app}" {file_name}'
    return full_cmd


def _cmd_open_pdf(file_name: str, os_name: str) -> Optional[str]:
    """
    Get OS-specific command to open a PDF file.
    """
    os_cmds = {
        "Darwin": (
            "/usr/bin/osascript << EOF\n"
            f'set theFile to POSIX file "{file_name}" as alias\n'
            'tell application "Skim"\n'
            "activate\n"
            "set theDocs to get documents whose path is "
            "(get POSIX path of theFile)\n"
            "if (count of theDocs) > 0 then revert theDocs\n"
            "open theFile\n"
            "end tell\n"
            "EOF\n"
        )
    }
    if os_name not in os_cmds:
        _LOG.warning("Opening PDF files on '%s' is not supported yet", os_name)
        full_cmd = None
    else:
        full_cmd = os_cmds[os_name]
    return full_cmd


def open_file(file_name: str, app: Optional[str] = None) -> None:
    """
    Open a file locally, optionally with a specific application.

    :param file_name: path to the file to open
    :param app: name of the app to open the file with (e.g., "Skim",
        "Preview"); if `None`, use the extension-specific handler (`pdf`
        reopens in Skim on macOS) or the OS default app otherwise
    """
    # Detect file format by the (last) extension.
    # E.g., 'hello.html.txt' is considered a txt file.
    extension = os.path.split(file_name)[-1].split(".")[-1]
    extension = extension.lower()
    # Make sure file exists.
    _LOG.info(
        "\n%s",
        hprint.frame(
            f"Opening {extension} file '{file_name}'", char1="<", char2=">"
        ),
    )
    hdbg.dassert_path_exists(file_name)
    # Get opening command.
    os_name = hsystem.get_os_name()
    cmd: Optional[str] = None
    if app is not None:
        cmd = _cmd_open_with_app(file_name, os_name, app)
    elif extension == "pdf":
        cmd = _cmd_open_pdf(file_name, os_name)
    else:
        cmd = _cmd_open_generic(file_name, os_name)
    # Run command.
    if cmd is not None:
        _LOG.info("%s", cmd)
        hio.to_file("open_file_cmd.sh", cmd)
        hsystem.system("source open_file_cmd.sh", suppress_output=False)
