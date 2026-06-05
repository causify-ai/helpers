"""
Linting utilities for text and code files.

Import as:

import helpers.hlint as hlint
"""

import logging

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hsystem as hsystem
import helpers.hselect_input_output as hseinout
import dev_scripts_helpers.documentation.lint_txt as dshdlitx

_LOG = logging.getLogger(__name__)


def lint_file(file_path: str, *, backend: str = "docker") -> None:
    """
    Lint a file to ensure proper formatting.

    Applies text formatting transformations including prettier formatting,
    markdown processing, and style enforcement.

    :param file_path: path to the file to lint
    :param backend: Backend to use for linting: "docker" (call lint_txt.py script)
        or "library" (use the library directly)
    """
    hdbg.dassert_in(backend, ["docker", "library"])
    _LOG.info("Linting file: %s", file_path)
    if backend == "docker":
        # Find the lint_txt.py script.
        script_path = hgit.find_file_in_git_tree("lint_txt.py")
        hdbg.dassert_file_exists(script_path)
        _LOG.debug("Found lint_txt.py at: %s", script_path)
        # Build command to call the lint_txt.py script.
        cmd = f"{script_path} -i {file_path}"
        hsystem.system(cmd, abort_on_error=True, suppress_output=False)
    else:
        # Direct library call to lint_txt.py
        lines = hseinout.from_file(file_path)
        out_lines = dshdlitx._perform_actions(lines, file_path)
        hseinout.to_file(out_lines, file_path)
    _LOG.info("File linted successfully: %s", file_path)
