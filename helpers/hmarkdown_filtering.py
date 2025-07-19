"""
Import as:

import helpers.hmarkdown as hmarkdo
"""

import logging
import re

import helpers.hdbg as hdbg
import helpers.hio as hio

_LOG = logging.getLogger(__name__)

# TODO(gp): Add a decorator like in hprint to process both strings and lists
#  of strings.


def filter_by_header(file_name: str, header: str, prefix: str) -> str:
    """
    Extract a specific header from a file.

    :param file_name: The input file to be processed
    :param header: The header to filter by (e.g., `# Introduction`)
    :param prefix: The prefix used for the output file (e.g., `tmp.pandoc`)
    :return: The path to the processed file
    """

    # Read the file.
    txt = hio.from_file(file_name)
    # Filter by header.
    txt = extract_section_from_markdown(txt, header)
    # Save the file.
    file_out = f"{prefix}.filter_by_header.txt"
    hio.to_file(file_out, txt)
    return file_out


def _parse_range(range_as_str: str, max_value: int) -> tuple[int, int]:
    """
    Parse a line range string like '1:10' into start and end line numbers.

    :param range_as_str: String in format 'start:end' where start/end
        can be numbers or 'None'
    :param max_value: Maximum value to use when 'None' is specified for
        end
    :return: Tuple of (start_line, end_line) as integers
    """
    m = re.match(r"^(\S+):(\S+)$", range_as_str)
    hdbg.dassert(m, "Invalid range_as_str='%s'", range_as_str)
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


def filter_by_lines(file_name: str, filter_by_lines: str, prefix: str) -> str:
    """
    Filter the lines of a file in [start_line, end_line[.

    :param file_name: The input file to be processed
    :param filter_by_lines: a string like `1:10` or `1:None` or `None:10`
    :param prefix: The prefix used for the output file (e.g., `tmp.pandoc`)
    :return: The path to the processed file
    """

    # Read the file.
    txt = hio.from_file(file_name)
    txt = txt.split("\n")
    # E.g., filter_by_lines='1:10'.
    start_line, end_line = _parse_range(filter_by_lines, len(txt))
    # Filter by header.
    hdbg.dassert_lte(start_line, end_line)
    txt = txt[start_line - 1 : end_line - 1]
    txt = "\n".join(txt)
    _LOG.warning(
        "filter_by_lines='%s' -> lines=[%s:%s]",
        filter_by_lines,
        start_line,
        end_line,
    )
    #
    file_out = f"{prefix}.filter_by_lines.txt"
    hio.to_file(file_out, txt)
    return file_out


def filter_by_slides(file_name: str, filter_by_slides: str, prefix: str) -> str:
    """
    Filter the lines of a file in [start_slide, end_slide[.

    :param file_name: The input file to be processed
    :param filter_by_slides: a string like `1:10` or `1:None` or `None:10`
    :param prefix: The prefix used for the output file (e.g., `tmp.pandoc`)
    :return: The path to the processed file
    """

    # Read the file.
    txt = hio.from_file(file_name)
    # Filter by header.
    slides_info, last_line_number = extract_slides_from_markdown(txt)
    _LOG.debug("slides_info=%s\n%s", len(slides_info), slides_info)
    # assert 0
    # E.g., filter_by_lines='1:10'.
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
    txt = txt.split("\n")
    txt = txt[start_line - 1 : end_line - 1]
    txt = "\n".join(txt)
    # Save the file.
    file_out = f"{prefix}.filter_by_slides.txt"
    hio.to_file(file_out, txt)
    return file_out
