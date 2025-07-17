"""
Import as:

import helpers.hmarkdown as hmarkdo
"""

import logging

from helpers.hmarkdown_headers import is_markdown_line_separator

_LOG = logging.getLogger(__name__)


def process_single_line_comment(line: str) -> bool:
    """
    Handle single line comment.

    We need to do it after the // in code blocks have been handled.
    """
    do_continue = False
    if line.startswith(r"%%") or line.startswith(r"//"):
        do_continue = True
        _LOG.debug("  -> do_continue=True")
        return do_continue
    # Skip frame.
    if is_markdown_line_separator(line):
        do_continue = True
        _LOG.debug("  -> do_continue=True")
        return do_continue
    # Nothing to do.
    return do_continue
