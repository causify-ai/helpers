#!/usr/bin/env python3

r"""
Extract text from a file between two markdown headers.

The script:
- Processes the input Markdown `.md` or txt slide `.txt` file
- Extracts text between specified start and end headers
- If `--end` is not provided, extracts until the next header at the same or
  higher level (fewer # symbols)
- If `--start` header is not found, raises an error
- Outputs the extracted text to a file or stdout

Examples:
# Extract text between two headers
> extract_text_from_txt.py -i input.md --start "## Section 1" --end "## Section 2" -o output.txt

# Extract text from "## Section 1" until the next level-2 header
> extract_text_from_txt.py -i input.md --start "## Section 1" -o output.txt

# Extract text and print to stdout
> extract_text_from_txt.py -i input.md --start "# Chapter 1" --end "# Chapter 2" -o -
"""

import argparse
import logging
import os
from typing import List, Optional, Tuple

import helpers.hdbg as hdbg
import helpers.hmarkdown as hmarkdo
import helpers.hmarkdown_headers as hmarhead
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


def _parse_header_string(header_str: str) -> Tuple[int, str]:
    """
    Parse a header string and extract level and title.

    :param header_str: header string like "## Section Title"
    :return: tuple of (level, title)
    """
    hdbg.dassert_isinstance(header_str, str)
    hdbg.dassert_ne(header_str, "", "Header string cannot be empty")
    is_header_, level, title = hmarhead.is_header(header_str)
    hdbg.dassert(
        is_header_,
        "Invalid header format: '%s'. Expected format like '# Title', '## Subtitle', etc.",
        header_str,
    )
    return level, title


def _find_header_by_title(
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


def _find_end_line(
    header_list: hmarhead.HeaderList,
    start_header_info: hmarhead.HeaderInfo,
    end_header_title: Optional[str],
) -> Optional[int]:
    """
    Find the line number where the text extraction should end.

    If end_header_title is provided, find that header. Otherwise, find the
    next header at the same or higher level (fewer or equal # symbols).

    :param header_list: list of HeaderInfo objects
    :param start_header_info: the start header
    :param end_header_title: title of end header (None to auto-detect)
    :return: line number where extraction ends (exclusive)
    """
    hdbg.dassert_isinstance(header_list, list)
    hdbg.dassert_isinstance(start_header_info, hmarhead.HeaderInfo)
    start_idx = None
    for i, header_info in enumerate(header_list):
        if header_info.line_number == start_header_info.line_number:
            start_idx = i
            break
    hdbg.dassert_is_not(start_idx, None, "Start header not found in header list")
    if end_header_title is not None:
        end_header_info = _find_header_by_title(header_list, end_header_title)
        hdbg.dassert_is_not(
            end_header_info,
            None,
            "End header not found: '%s'",
            end_header_title,
        )
        return end_header_info.line_number - 1
    for i in range(start_idx + 1, len(header_list)):
        candidate_header = header_list[i]
        if candidate_header.level <= start_header_info.level:
            return candidate_header.line_number - 1
    return None


def _extract_text_from_markdown(
    lines: List[str],
    start_header_str: str,
    end_header_str: Optional[str],
) -> List[str]:
    """
    Extract text from Markdown lines between two headers.

    :param lines: list of lines in the input file
    :param start_header_str: starting header string (e.g., "## Section 1")
    :param end_header_str: ending header string (optional)
    :return: extracted lines
    """
    hdbg.dassert_isinstance(lines, list)
    start_level, start_title = _parse_header_string(start_header_str)
    sanity_check = False
    header_list = hmarkdo.extract_headers_from_markdown(
        lines, max_level=10, sanity_check=sanity_check
    )
    start_header_info = _find_header_by_title(header_list, start_title)
    hdbg.dassert_is_not(
        start_header_info,
        None,
        "Start header not found: '%s'",
        start_header_str,
    )
    hdbg.dassert_eq(
        start_header_info.level,
        start_level,
        "Header level mismatch for '%s': expected level %d, got %d",
        start_title,
        start_level,
        start_header_info.level,
    )
    end_header_title = None
    if end_header_str is not None:
        end_level, end_title = _parse_header_string(end_header_str)
        end_header_title = end_title
    end_line = _find_end_line(header_list, start_header_info, end_header_title)
    start_idx = start_header_info.line_number - 1
    if end_line is None:
        end_idx = len(lines)
    else:
        end_idx = end_line
    extracted_lines = lines[start_idx:end_idx]
    return extracted_lines


def _extract_text_from_txtslides(
    lines: List[str],
    start_header_str: str,
    end_header_str: Optional[str],
) -> List[str]:
    """
    Extract text from txt slide lines between two headers.

    :param lines: list of lines in the input file
    :param start_header_str: starting header string
    :param end_header_str: ending header string (optional)
    :return: extracted lines
    """
    hdbg.dassert_isinstance(lines, list)
    lines = hmarkdo.convert_slide_to_markdown(lines, level=3)
    sanity_check = False
    header_list = hmarkdo.extract_headers_from_markdown(
        lines, max_level=10, sanity_check=sanity_check
    )
    start_level, start_title = _parse_header_string(start_header_str)
    start_header_info = _find_header_by_title(header_list, start_title)
    hdbg.dassert_is_not(
        start_header_info,
        None,
        "Start header not found: '%s'",
        start_header_str,
    )
    hdbg.dassert_eq(
        start_header_info.level,
        start_level,
        "Header level mismatch for '%s': expected level %d, got %d",
        start_title,
        start_level,
        start_header_info.level,
    )
    end_header_title = None
    if end_header_str is not None:
        end_level, end_title = _parse_header_string(end_header_str)
        end_header_title = end_title
    end_line = _find_end_line(header_list, start_header_info, end_header_title)
    start_idx = start_header_info.line_number - 1
    if end_line is None:
        end_idx = len(lines)
    else:
        end_idx = end_line
    extracted_lines = lines[start_idx:end_idx]
    return extracted_lines


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    out_default = "-"
    hparser.add_input_output_args(parser, out_default=out_default)
    parser.add_argument(
        "--start",
        type=str,
        required=True,
        help="Starting header (e.g., '## Section 1')",
    )
    parser.add_argument(
        "--end",
        type=str,
        default=None,
        help="Ending header (e.g., '## Section 2'). If not provided, extracts until the next header at the same or higher level",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    verbose = False
    hparser.init_logger_for_input_output_transform(args, verbose=verbose)
    in_file_name, out_file_name = hparser.parse_input_output_args(args)
    input_content = hparser.from_file(in_file_name)
    hdbg.dassert_isinstance(input_content, list)
    hdbg.dassert_ne(len(input_content), 0, "Input file is empty")
    _, ext = os.path.splitext(in_file_name)
    if ext == ".md":
        extracted_lines = _extract_text_from_markdown(
            input_content, args.start, args.end
        )
    elif ext == ".txt":
        extracted_lines = _extract_text_from_txtslides(
            input_content, args.start, args.end
        )
    else:
        raise ValueError(f"Unsupported file type: {in_file_name}")
    output_content = "\n".join(extracted_lines)
    start_line_idx = next(
        (i + 1 for i, line in enumerate(input_content) if line.lstrip() == args.start.lstrip()),
        1
    )
    end_line_idx = start_line_idx + len(extracted_lines) - 1
    line_numbers = f"\n\n[Lines: {start_line_idx}-{end_line_idx}]"
    output_content += line_numbers
    hparser.to_file(output_content, out_file_name)


if __name__ == "__main__":
    _main(_parse())
