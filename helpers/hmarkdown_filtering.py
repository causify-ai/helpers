"""
Import as:

import helpers.hmarkdown as hmarkdo
"""

import logging
import re
from typing import Tuple

import helpers.hdbg as hdbg
from helpers.hmarkdown_headers import (
    extract_section_from_markdown,
    extract_slides_from_markdown,
)

_LOG = logging.getLogger(__name__)


def filter_by_header(text: str, header: str) -> str:
    """
    Extract a specific header from markdown text.

    :param text: markdown text to be processed
    :param header: header to filter by (e.g., `# Introduction`)
    :return: filtered text
    """
    # Filter by header.
    txt = extract_section_from_markdown(text, header)
    return txt


def _parse_range(range_as_str: str, max_value: int) -> Tuple[int, int]:
    """
    Parse a line range string like '1:10' into start and end line numbers.

    :param range_as_str: string in format 'start:end' where start/end
        can be numbers or 'None'
    :param max_value: maximum value to use when 'None' is specified for
        end
    :return: tuple of '(start_line, end_line)' as integers
    """
    m = re.match(r"^(\S+):(\S+)$", range_as_str)
    hdbg.dassert(m, "Invalid range_as_str='%s'", range_as_str)
    # Type narrowing after dassert since linter doesn't under that `dassert` is
    # equivalent to an `assert`.
    assert m is not None  
    start_value, end_value = m.groups()
    if start_value.lower() == "none":
        start_value = 1
    else:
        start_value = int(start_value)
    if end_value.lower() == "none":
        end_value = max_value + 1
    else:
        end_value = int(end_value)
    return start_value, end_value


def filter_by_lines(text: str, filter_by_lines: str) -> str:
    """
    Filter the lines of text in `[start_line, end_line[`.

    :param text: text to be processed
    :param filter_by_lines: string like `1:10` or `1:None` or `None:10`
    :return: filtered text
    """
    txt = text.split("\n")
    # E.g., filter_by_lines='1:10'.
    start_line, end_line = _parse_range(filter_by_lines, len(txt))
    # Filter by lines.
    hdbg.dassert_lte(start_line, end_line)
    txt = txt[start_line - 1 : end_line - 1]
    txt = "\n".join(txt)
    _LOG.warning(
        "filter_by_lines='%s' -> lines=[%s:%s]",
        filter_by_lines,
        start_line,
        end_line,
    )
    return txt


def filter_by_slides(text: str, filter_by_slides: str) -> str:
    """
    Filter the lines of text in `[start_slide, end_slide[`.

    :param text: text to be processed
    :param filter_by_slides: string like `1:10` or `1:None` or `None:10`
    :return: filtered text
    """
    # Filter by slides.
    slides_info, last_line_number = extract_slides_from_markdown(text)
    _LOG.debug("slides_info=%s\n%s", len(slides_info), slides_info)
    # E.g., filter_by_slides='1:10'.
    start_slide, end_slide = _parse_range(filter_by_slides, len(slides_info))
    _LOG.debug("start_slide=%s, end_slide=%s", start_slide, end_slide)
    hdbg.dassert_lte(start_slide, end_slide)
    # A number after the last slide is the end of the file.
    hdbg.dassert_lte(end_slide, len(slides_info) + 1)
    start_line = slides_info[start_slide].line_number
    if end_slide == len(slides_info) + 1:
        end_line = last_line_number
    else:
        end_line = slides_info[end_slide].line_number
    _LOG.warning(
        "filter_by_slides='%s' -> lines=[%s:%s]",
        filter_by_slides,
        start_line,
        end_line,
    )
    # Filter by slides.
    txt = text.split("\n")
    txt = txt[start_line - 1 : end_line - 1]
    txt = "\n".join(txt)
    return txt
