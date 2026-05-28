"""
Linting utilities for text and code files.

Import as:

import helpers.hlint as hlint
"""

import logging

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hsystem as hsystem
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


# TODO(ai_gp): Pass an option to call executable or library.
def lint_file(file_path: str) -> None:
    """
    Lint a file to ensure proper formatting.

    Applies text formatting transformations including prettier formatting,
    markdown processing, and style enforcement.

    :param file_path: path to the file to lint
    """
    _LOG.info("Linting file: %s", file_path)
    if True:
        # Find the lint_txt.py script.
        script_path = hgit.find_file_in_git_tree("lint_txt.py")
        hdbg.dassert_file_exists(script_path)
        _LOG.debug("Found lint_txt.py at: %s", script_path)
        # Build command to call the lint_txt.py script.
        cmd = f"{script_path} -i {file_path}"
        hsystem.system(cmd, abort_on_error=True, suppress_output=False)
    else:
        # Direct library call to lint_txt.py
        lines = hparser.from_file(file_path)
        out_lines = dshdlitx._perform_actions(lines, file_path)
        hparser.to_file(out_lines, file_path)
    _LOG.info("File linted successfully: %s", file_path)
