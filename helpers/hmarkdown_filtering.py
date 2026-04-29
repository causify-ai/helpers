"""
Import as:

import helpers.hmarkdown_filtering as hmarfilt
"""

import logging
import re
from typing import List, Tuple

import helpers.hdbg as hdbg
from helpers.hmarkdown_headers import (
    extract_section_from_markdown,
)
from helpers.hmarkdown_slides import extract_slides_from_markdown

_LOG = logging.getLogger(__name__)


def filter_by_header(lines: List[str], header: str) -> List[str]:
    """
    Extract a specific header from markdown text.

    :param lines: list of markdown lines to be processed
    :param header: header to filter by (e.g., `# Introduction`)
    :return: filtered lines
    """
    hdbg.dassert_isinstance(lines, list)
    # Filter by header.
    txt_lines = extract_section_from_markdown(lines, header)
    hdbg.dassert_isinstance(txt_lines, list)
    return txt_lines


def _parse_range(range_as_str: str, max_value: int) -> Tuple[int, int]:
    """
    Parse a 0-indexed range string like '0:10' into start and end indices.

    :param range_as_str: string in format 'start:end' where start/end
        can be numbers or 'None' (None means 0 for start, max_value for end)
    :param max_value: maximum value to use when 'None' is specified for end
    :return: tuple of '(start_index, end_index)' as 0-indexed integers
    """
    m = re.match(r"^(\S+):(\S+)$", range_as_str)
    hdbg.dassert(m, "Invalid range_as_str='%s'", range_as_str)
    assert m is not None
    start_value, end_value = m.groups()
    if start_value.lower() == "none":
        start_value = 0
    else:
        start_value = int(start_value)
    if end_value.lower() == "none":
        end_value = max_value
    else:
        end_value = int(end_value)
    return start_value, end_value


def filter_by_lines(lines: List[str], filter_by_lines: str) -> List[str]:
    """
    Filter the lines of text in `[start_line, end_line[` (0-indexed).

    :param lines: list of lines to be processed
    :param filter_by_lines: 0-indexed range string like `0:10`, `0:None`, or `None:10`
    :return: filtered lines
    """
    hdbg.dassert_isinstance(lines, list)
    start_line, end_line = _parse_range(filter_by_lines, len(lines))
    hdbg.dassert_lte(start_line, end_line)
    txt = lines[start_line:end_line]
    _LOG.warning(
        "filter_by_lines='%s' -> lines=[%s:%s]",
        filter_by_lines,
        start_line,
        end_line,
    )
    hdbg.dassert_isinstance(txt, list)
    return txt


def filter_by_slides(lines: List[str], filter_by_slides: str) -> List[str]:
    """
    Filter the lines of text in `[start_slide, end_slide[` (0-indexed).

    :param lines: list of lines to be processed
    :param filter_by_slides: 0-indexed range string like `0:10`, `0:None`, or `None:10`
    :return: filtered lines
    """
    hdbg.dassert_isinstance(lines, list)
    slides_info, last_line_number = extract_slides_from_markdown(lines)
    _LOG.debug("slides_info=%s\n%s", len(slides_info), slides_info)
    start_slide, end_slide = _parse_range(filter_by_slides, len(slides_info))
    _LOG.debug("start_slide=%s, end_slide=%s", start_slide, end_slide)
    hdbg.dassert_lte(start_slide, end_slide)
    hdbg.dassert_lte(end_slide, len(slides_info))
    start_line = slides_info[start_slide].line_number
    if end_slide == len(slides_info):
        end_line = last_line_number
    else:
        end_line = slides_info[end_slide].line_number
    _LOG.warning(
        "filter_by_slides='%s' -> lines=[%s:%s]",
        filter_by_slides,
        start_line,
        end_line,
    )
    txt = lines[start_line - 1 : end_line - 1]
    hdbg.dassert_isinstance(txt, list)
    return txt
