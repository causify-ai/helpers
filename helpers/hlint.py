"""
Linting utilities for text and code files.

Import as:

import helpers.hlint as hlint
"""

import logging

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


def lint_file(file_path: str) -> None:
    """
    Run lint_txt.py on the file to ensure proper formatting.

    :param file_path: path to the file to lint
    """
    _LOG.info("Linting file: %s", file_path)
    lint_script = hgit.find_file_in_git_tree("lint_txt.py", super_module=True)
    # Run lint_txt.py.
    cmd = f"{lint_script} -i {file_path} -v CRITICAL"
    _LOG.debug("Running command: %s", cmd)
    hsystem.system(cmd, suppress_output=True)
    _LOG.info("File linted successfully: %s", file_path)
