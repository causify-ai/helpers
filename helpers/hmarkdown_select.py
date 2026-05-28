r"""
Utilities for selecting header ranges in markdown files.

Provides functions to find and validate markdown headers by full format or
partial title match, and to determine section boundaries for text extraction.

Import as:

import helpers.hmarkdown_select as hmarsele
"""

import argparse
from typing import List, Optional, Tuple

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hmarkdown_headers as hmarhead
import helpers.hmarkdown_slides as hmarslid


def add_select_arg(
    parser: argparse.ArgumentParser,
    *,
    required: bool = True,
) -> argparse.ArgumentParser:
    """
    Add option for markdown header range selection via --select START:END.

    :param parser: ArgumentParser to add arguments to
    :param required: whether the --select argument is required (default: True)
    :return: ArgumentParser with the new argument added
    """
    parser.add_argument(
        "--select",
        type=str,
        required=required,
        default=None,
        help=(
            "Select text range as START:END. Examples: "
            "'## Section 1:## Section 2', 'Section 1:Section 2', ':END', "
            "'START:', or 'START' (no colon implies to EOF). "
            "START/END can be a header (with # or * prefix), title substring, "
            "or line number."
        ),
    )
    return parser


# #############################################################################


def parse_select_arg(select_str: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse a --select argument into (start, end) components.

    Formats:
    - "START:END" -> ("START", "END")
    - ":END" -> (None, "END"): extract from file beginning
    - "START:" -> ("START", None): extract until next same-level header
    - "START" (no colon) -> ("START", "END"): extract from START to EOF

    :param select_str: the --select argument value
    :return: tuple of (start, end) where each can be None or a string
    """
    hdbg.dassert_isinstance(select_str, str, "select_str must be a string")
    hdbg.dassert_ne(select_str, "", "Select string cannot be empty")
    if ":" not in select_str:
        return select_str, "END"
    parts = select_str.split(":", 1)
    start = parts[0] if parts[0].strip() else None
    end = parts[1] if parts[1].strip() else None
    return start, end


# #############################################################################


def parse_header_string(header_str: str) -> Tuple[int, str]:
    """
    Parse a header string and extract level and title.

    :param header_str: header string like "## Section Title"
    :return: tuple of (level, title)
    """
    hdbg.dassert_isinstance(header_str, str, "header_str must be a string")
    hdbg.dassert_ne(header_str, "", "Header string cannot be empty")
    is_header_, level, title = hmarhead.is_header(header_str)
    hdbg.dassert(
        is_header_,
        "Invalid header format '%s'; expected format like '# Title' or '## Subtitle'",
        header_str,
    )
    return level, title


def find_header_by_title(
    header_list: hmarhead.HeaderList, target_title: str
) -> Optional[hmarhead.HeaderInfo]:
    """
    Find a header in the list matching the target title.

    :param header_list: list of HeaderInfo objects
    :param target_title: title to match (exact match required)
    :return: HeaderInfo if found, None otherwise
    """
    for header_info in header_list:
        if header_info.description == target_title:
            return header_info
    return None


def find_header_by_partial_title(
    header_list: hmarhead.HeaderList, partial_title: str
) -> Optional[hmarhead.HeaderInfo]:
    """
    Find a header by partial title match.

    The partial_title matches if any header's title starts with it (case-sensitive).
    Raises an error if multiple headers match.

    :param header_list: list of HeaderInfo objects
    :param partial_title: partial title to match (must be unique)
    :return: HeaderInfo if found, None otherwise
    """
    matches = []
    for header_info in header_list:
        if header_info.description.startswith(partial_title):
            matches.append(header_info)
    if len(matches) == 0:
        return None
    hdbg.dassert_eq(
        len(matches),
        1,
        "Partial title '%s' matches multiple headers: %s. Please provide a more specific match.",
        partial_title,
        [h.description for h in matches],
    )
    return matches[0]


def find_header_by_substring_title(
    header_list: hmarhead.HeaderList, substring: str
) -> Optional[hmarhead.HeaderInfo]:
    """
    Find a header by substring title match (anywhere in title).

    The substring matches if it appears anywhere in the header's title (case-sensitive).
    Raises an error if multiple headers match.

    :param header_list: list of HeaderInfo objects
    :param substring: substring to match (must be unique)
    :return: HeaderInfo if found, None otherwise
    """
    matches = []
    for header_info in header_list:
        if substring in header_info.description:
            matches.append(header_info)
    if len(matches) == 0:
        return None
    hdbg.dassert_eq(
        len(matches),
        1,
        "Substring '%s' matches multiple headers: %s. Please provide a more specific match.",
        substring,
        [h.description for h in matches],
    )
    return matches[0]


def find_header_by_level_and_prefix(
    header_list: hmarhead.HeaderList, level: int, title_prefix: str
) -> Optional[hmarhead.HeaderInfo]:
    """
    Find a header by exact level match and title prefix.

    Matches headers where level == target level AND title starts with prefix.
    Raises an error if multiple headers match.

    :param header_list: list of HeaderInfo objects
    :param level: exact header level to match
    :param title_prefix: prefix the title must start with
    :return: HeaderInfo if found, None otherwise
    """
    matches = []
    for header_info in header_list:
        if (header_info.level == level and
            header_info.description.startswith(title_prefix)):
            matches.append(header_info)
    if len(matches) == 0:
        return None
    hdbg.dassert_eq(
        len(matches),
        1,
        "Level %d with prefix '%s' matches multiple headers: %s. Please provide a more specific match.",
        level,
        title_prefix,
        [h.description for h in matches],
    )
    return matches[0]


def _find_header_by_line_number(
    header_list: hmarhead.HeaderList, line_number: int
) -> Optional[hmarhead.HeaderInfo]:
    """
    Find a header at a specific line number.

    :param header_list: list of HeaderInfo objects
    :param line_number: 1-based line number
    :return: HeaderInfo if found, None otherwise
    """
    for header_info in header_list:
        if header_info.line_number == line_number:
            return header_info
    return None


def find_header_from_input(
    header_list: hmarhead.HeaderList,
    header_input: str,
) -> Tuple[hmarhead.HeaderInfo, int]:
    """
    Find a header from user input with flexible matching.

    Supports multiple input formats:
    - Line number: "42" (1-based line number)
    - Slide format: "* Slide Title" (matches level-5 header with prefix)
    - Full header format: "## Title" (matches level-exact header with prefix)
    - Substring: "Title" (matches anywhere in title, must be unique)

    :param header_list: list of HeaderInfo objects
    :param header_input: various formats as described above
    :return: tuple of (HeaderInfo, level)
    :raises: AssertionError if input is ambiguous or header not found
    """
    hdbg.dassert_isinstance(header_input, str, "header_input must be a string")
    hdbg.dassert_ne(header_input, "", "Header input cannot be empty")
    header_input = header_input.strip()
    header_info = None
    # Check if input is a line number
    if header_input.isdigit():
        line_num = int(header_input)
        header_info = _find_header_by_line_number(header_list, line_num)
        hdbg.dassert_is_not(
            header_info, None, "No header at line %d", line_num
        )
        hdbg.dassert_isinstance(header_info, hmarhead.HeaderInfo)
    # Check if input is slide format (* Title)
    elif header_input.startswith("*"):
        title = header_input[1:].strip()
        header_info = find_header_by_level_and_prefix(
            header_list, hmarslid.SLIDE_LEVEL, title
        )
        hdbg.dassert_is_not(
            header_info, None, "No slide matches: '%s'", header_input
        )
        hdbg.dassert_isinstance(header_info, hmarhead.HeaderInfo)
    # Check if input is full header format (# Title)
    elif header_input.startswith("#"):
        level, title = parse_header_string(header_input)
        header_info = find_header_by_level_and_prefix(
            header_list, level, title
        )
        hdbg.dassert_is_not(
            header_info, None, "No header matches: '%s'", header_input
        )
        hdbg.dassert_isinstance(header_info, hmarhead.HeaderInfo)
    # Default: substring matching
    else:
        header_info = find_header_by_substring_title(header_list, header_input)
        hdbg.dassert_is_not(
            header_info, None, "No header matches: '%s'", header_input
        )
        hdbg.dassert_isinstance(header_info, hmarhead.HeaderInfo)
    hdbg.dassert_isinstance(header_info, hmarhead.HeaderInfo)
    return header_info, header_info.level


def find_end_line(
    header_list: hmarhead.HeaderList,
    start_header_info: hmarhead.HeaderInfo,
    end_header_input: Optional[str],
) -> Optional[int]:
    """
    Find the line number where the text extraction should end.

    If end_header_input is provided, find that header. Otherwise, find the
    next header at the same or higher level (fewer or equal # symbols).

    :param header_list: list of HeaderInfo objects
    :param start_header_info: the start header
    :param end_header_input: header input (full format or partial match) or None to auto-detect
    :return: line number where extraction ends (exclusive)
    """
    hdbg.dassert_isinstance(header_list, list, "header_list must be a list")
    hdbg.dassert_isinstance(
        start_header_info,
        hmarhead.HeaderInfo,
        "start_header_info must be a HeaderInfo object",
    )
    # Find the index of the start header in the list for iterating from that point.
    start_idx = None
    for i, header_info in enumerate(header_list):
        if header_info.line_number == start_header_info.line_number:
            start_idx = i
            break
    hdbg.dassert_is_not(start_idx, None, "Start header not found in header list")
    assert isinstance(start_idx, int)
    # If an explicit end header is provided, use it directly.
    if end_header_input is not None:
        end_header_info, _ = find_header_from_input(
            header_list, end_header_input
        )
        return end_header_info.line_number - 1
    # Search for the next header at the same or higher level (fewer # symbols).
    for i in range(start_idx + 1, len(header_list)):
        candidate_header = header_list[i]
        if candidate_header.level <= start_header_info.level:
            return candidate_header.line_number - 1
    return None


def get_chunk_bounds(
    lines: List[str],
    start_header_str: Optional[str],
    end_header_str: Optional[str],
    is_slide_format: bool = False,
) -> Tuple[int, int]:
    """
    Find the 0-based start and end indices for a text chunk between headers.

    Uses the same matching logic as extract_text_from_markdown_lines but returns
    indices instead of the actual lines. Useful for in-place file editing where
    you need to know positions to replace.

    :param lines: list of lines in the input file
    :param start_header_str: starting header (or None for file beginning)
    :param end_header_str: ending header (optional), or "END" for end of file
    :param is_slide_format: whether the input is in slide format (*.txt)
    :return: tuple of (start_idx, end_idx) where indices are 0-based
    """
    hdbg.dassert_isinstance(lines, list, "lines must be a list of strings")
    hdbg.dassert_ne(len(lines), 0, "Input lines cannot be empty")
    lines_converted = lines
    if is_slide_format:
        lines_converted = hmarslid.convert_slide_to_markdown(lines)
    sanity_check = False
    header_list = hmarhead.extract_headers_from_markdown(
        lines_converted, max_level=10, sanity_check=sanity_check
    )
    # Prepare converted header strings if needed
    start_header_str_converted = None
    end_header_str_converted = None
    if start_header_str is not None:
        start_header_str_converted = start_header_str
        if is_slide_format and start_header_str.startswith("*"):
            start_header_str_converted = hmarslid.convert_slide_to_markdown(
                [start_header_str]
            )[0]
    if end_header_str is not None and end_header_str != "END":
        end_header_str_converted = end_header_str
        if is_slide_format and end_header_str.startswith("*"):
            end_header_str_converted = hmarslid.convert_slide_to_markdown(
                [end_header_str]
            )[0]
    # Determine start index
    if start_header_str is None:
        start_idx = 0
    else:
        assert start_header_str_converted is not None
        start_header_info, _ = find_header_from_input(
            header_list, start_header_str_converted
        )
        start_idx = start_header_info.line_number - 1
    # Determine end index
    if end_header_str is None:
        if start_header_str is None:
            end_idx = len(lines_converted)
        else:
            # Auto-detect: find next same-level header
            assert start_header_str_converted is not None
            start_header_info, _ = find_header_from_input(
                header_list, start_header_str_converted
            )
            end_line = find_end_line(
                header_list, start_header_info, None
            )
            end_idx = len(lines_converted) if end_line is None else end_line
    elif end_header_str == "END":
        end_idx = len(lines_converted)
    else:
        assert end_header_str_converted is not None
        if start_header_str is None:
            # Extract from beginning to explicit end header
            end_header_info, _ = find_header_from_input(
                header_list, end_header_str_converted
            )
            end_idx = end_header_info.line_number - 1
        else:
            # Extract from start header to explicit end header
            assert start_header_str_converted is not None
            start_header_info, _ = find_header_from_input(
                header_list, start_header_str_converted
            )
            end_line = find_end_line(
                header_list, start_header_info, end_header_str_converted
            )
            end_idx = len(lines_converted) if end_line is None else end_line
    return start_idx, end_idx


def extract_text_from_markdown_lines(
    lines: List[str],
    start_header_str: Optional[str],
    end_header_str: Optional[str],
    is_slide_format: bool = False,
) -> List[str]:
    """
    Extract text from markdown lines between two headers.

    For .txt slide files, headers can be specified as:
    - Slides: "* Slide Title" (shorthand for `##### Slide Title`)
    - Full header format: "##### Section 1" (includes the # symbols)
    - Line number: "42" (1-based)
    - Substring: "Section 1" (matches anywhere in title)

    For .md files, headers can be specified as:
    - Full format: "## Section 1" (includes the # symbols)
    - Line number: "42" (1-based)
    - Substring: "Section 1" (matches anywhere in title)

    Special handling:
    - start_header_str=None: Extract from beginning of file
    - end_header_str="END": Extract to end of file
    - end_header_str=None: Extract until next same-level header

    :param lines: list of lines in the input file
    :param start_header_str: starting header (or None for file beginning)
    :param end_header_str: ending header (optional), or "END" for end of file
    :param is_slide_format: whether the input is in slide format (*.txt)
    :return: extracted lines with trailing blank lines removed
    """
    hdbg.dassert_isinstance(lines, list, "lines must be a list of strings")
    hdbg.dassert_ne(len(lines), 0, "Input lines cannot be empty")
    lines_converted = lines
    if is_slide_format:
        lines_converted = hmarslid.convert_slide_to_markdown(lines)
    start_idx, end_idx = get_chunk_bounds(
        lines_converted, start_header_str, end_header_str, is_slide_format=False
    )
    extracted_lines = lines_converted[start_idx:end_idx]
    while extracted_lines and extracted_lines[-1].strip() == "":
        extracted_lines.pop()
    return extracted_lines


# #############################################################################


def extract_rule_from_file(rule_spec: str) -> str:
    """
    Extract a rule section from a rules file based on a rule specification.

    :param rule_spec: rule specification in one of these formats:
        - `path/to/file.md`: return all content
        - `path/to/file.md:N`: extract section starting at line N (must be
          a markdown header)
        - `path/to/file.md:N:# Section Name`: same with header name
          validation
    :return: extracted rule text as a string
    """
    # Parse the rule specification.
    parts = rule_spec.split(":", 2)
    file_path = parts[0]
    # Check file exists.
    hdbg.dassert_file_exists(
        file_path, "Rule file does not exist: %s", file_path
    )
    # Read file content.
    content = hio.from_file(file_path)
    lines = content.splitlines()
    # If only path provided, return full content.
    if len(parts) == 1:
        return content
    # Parse line number.
    try:
        line_num = int(parts[1])
    except ValueError:
        raise ValueError(
            "Invalid line number '%s' in rule spec: %s" % (parts[1], rule_spec)
        )
    # Convert to 0-based index.
    line_idx = line_num - 1
    hdbg.dassert_lt(
        line_idx,
        len(lines),
        "Line number %d exceeds file length %d",
        line_num,
        len(lines),
    )
    # Check that the target line is a header.
    header_line = lines[line_idx]
    if not header_line.startswith("#"):
        raise ValueError(
            "Line %d is not a markdown header: '%s'" % (line_num, header_line)
        )
    # Validate section name if provided.
    if len(parts) == 3:
        expected_name = parts[2]
        if header_line.strip() != expected_name.strip():
            raise ValueError(
                "Section name mismatch at line %d: expected '%s', got '%s'"
                % (line_num, expected_name, header_line)
            )
    # Determine header level (number of leading '#' characters).
    header_level = len(header_line) - len(header_line.lstrip("#"))
    # Find the end of section (next header at same or higher level).
    end_idx = len(lines)
    for i in range(line_idx + 1, len(lines)):
        line = lines[i]
        if line.startswith("#"):
            this_level = len(line) - len(line.lstrip("#"))
            if this_level <= header_level:
                end_idx = i
                break
    # Extract and return the section.
    section_lines = lines[line_idx:end_idx]
    return "\n".join(section_lines)
