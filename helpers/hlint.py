"""
Linting utilities for text and code files.

Import as:

import helpers.hlint as hlint
"""

import logging

import helpers.hparser as hparser
import dev_scripts_helpers.documentation.lint_txt as lintxt

_LOG = logging.getLogger(__name__)


def lint_file(file_path: str) -> None:
    """
    Lint a file to ensure proper formatting.

    Applies text formatting transformations including prettier formatting,
    markdown processing, and style enforcement.

    :param file_path: path to the file to lint
    """
    _LOG.info("Linting file: %s", file_path)
    # Read the file.
    lines = hparser.from_file(file_path)
    # Perform linting actions.
    out_lines = lintxt._perform_actions(lines, file_path)
    # Write the file back.
    hparser.to_file(out_lines, file_path)
    _LOG.info("File linted successfully: %s", file_path)
