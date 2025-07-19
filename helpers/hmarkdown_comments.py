"""
Import as:

import helpers.hmarkdown as hmarkdo
"""

import logging
import re
from typing import Tuple

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


def process_comment_block(line: str, in_skip_block: bool) -> Tuple[bool, bool]:
    """
    Process lines of text to identify blocks that start with '<!--' or '/*' and
    end with '-->' or '*/'.

    :param line: The current line of text being processed.
    :param in_skip_block: A flag indicating if the function is currently
        inside a comment block.
    :return: A tuple
        - do_continue: whether to continue processing the current line or skip
          it
        - in_skip_block: a boolean indicating whether the function is currently
          inside a comment block
    """
    do_continue = False
    if line.startswith(r"<!--") or re.search(r"^\s*\/\*", line):
        hdbg.dassert(not in_skip_block)
        # Start skipping comments.
        in_skip_block = True
    if in_skip_block:
        if line.endswith(r"-->") or re.search(r"^\s*\*\/", line):
            # End skipping comments.
            in_skip_block = False
        # Skip comment.
        _LOG.debug("  -> skip")
        do_continue = True
    return do_continue, in_skip_block


