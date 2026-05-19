r"""
Utilities for selecting header ranges in markdown files.

Provides functions to find and validate markdown headers by full format or
partial title match, and to determine section boundaries for text extraction.

Import as:

import helpers.hmarkdown_select as hmarsele
"""

from typing import List, Optional, Tuple

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hmarkdown_headers as hmarhead
import helpers.hmarkdown_slides as hmarslid


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


def find_header_from_input(
    header_list: hmarhead.HeaderList,
    header_input: str,
) -> Tuple[hmarhead.HeaderInfo, int]:
    """
    Find a header from user input using partial title matching.

    Supports both "## Title" (full header format) and "Title" (partial match).
    Both formats will use partial matching, so "2 Cheap" and "# 2 Cheap" both work.

    :param header_list: list of HeaderInfo objects
    :param header_input: either "## Title" (full header) or "Title" (partial match)
    :return: tuple of (HeaderInfo, level)
    :raises: AssertionError if input is ambiguous or header not found
    """
    # Extract title from input, removing # symbols if present
    if header_input.lstrip().startswith("#"):
        # Full header format like "## Title" - extract the title part
        _, title = parse_header_string(header_input)
    else:
        # Already just a title
        title = header_input
    # Always use partial matching for flexibility
    header_info = find_header_by_partial_title(header_list, title.strip())
    hdbg.dassert_is_not(
        header_info, None, "No header matches: '%s'", header_input
    )
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


def extract_text_from_markdown_lines(
    lines: List[str],
    start_header_str: str,
    end_header_str: Optional[str],
    is_slide_format: bool = False,
) -> List[str]:
    """
    Extract text from markdown lines between two headers.

    For .txt slide files, headers can be specified as:
    - Slides: "* Slide Title" (shorthand for `##### Slide Title`)
    - Full header format: "##### Section 1" (includes the # symbols)
    - Partial match: "Section 1" (just the title, matches if unique)

    For .md files, headers can be specified as:
    - Full format: "## Section 1" (includes the # symbols)
    - Partial match: "Section 1" (just the title, matches if unique)

    Special values for end_header_str:
    - "END": Extract from start_header to the end of the file

    :param lines: list of lines in the input file
    :param start_header_str: starting header (e.g., "## Section 1" or "Section 1")
    :param end_header_str: ending header (optional, same formats accepted), or "END" for end of file
    :param is_slide_format: whether the input is in slide format (*.txt)
    :return: extracted lines with trailing blank lines removed
    """
    hdbg.dassert_isinstance(lines, list, "lines must be a list of strings")
    # Convert slide notation ('* Title') to header notation if needed.
    start_header_str_converted = start_header_str
    end_header_str_converted = end_header_str
    lines_converted = lines
    if is_slide_format:
        start_header_str_converted = hmarslid.convert_slide_to_markdown(
            [start_header_str]
        )[0]
        if end_header_str is not None and end_header_str != "END":
            end_header_str_converted = hmarslid.convert_slide_to_markdown(
                [end_header_str]
            )[0]
        lines_converted = hmarslid.convert_slide_to_markdown(lines)
    sanity_check = False
    header_list = hmarhead.extract_headers_from_markdown(
        lines_converted, max_level=10, sanity_check=sanity_check
    )
    start_header_info, _ = find_header_from_input(
        header_list, start_header_str_converted
    )
    # Handle special "END" value to extract to end of file
    if end_header_str == "END":
        end_line = None
    else:
        end_line = find_end_line(
            header_list, start_header_info, end_header_str_converted
        )
    start_idx = start_header_info.line_number - 1
    if end_line is None:
        end_idx = len(lines_converted)
    else:
        end_idx = end_line
    extracted_lines = lines_converted[start_idx:end_idx]
    while extracted_lines and extracted_lines[-1].strip() == "":
        extracted_lines.pop()
    return extracted_lines


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
    hdbg.dassert_file_exists(file_path, "Rule file does not exist: %s", file_path)
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
