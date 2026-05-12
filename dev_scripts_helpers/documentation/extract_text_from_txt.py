#!/usr/bin/env python3

r"""
Extract text from a file between two markdown headers or slides.

The script:
- Processes the input Markdown `.md` or txt slide `.txt` file
- Extracts text between specified start and end headers/slides
- If `--end` is not provided, extracts until the next header at the same or
  higher level (fewer # symbols)
- If `--start` header is not found, raises an error
- Outputs the extracted text to a file or stdout

For `.txt` slide files, headers can be specified as:
- Slides: "* Slide Title" (shorthand for `##### Slide Title`)
- Full header format: "##### Section 1" (includes the # symbols)
- Partial match: "Section 1" (just the title, matches if unique)

For `.md` files, headers can be specified as:
- Full format: "## Section 1" (includes the # symbols)
- Partial match: "Section 1" (just the title, matches if unique)

Examples:
# Extract text between two headers (full format)
> extract_text_from_txt.py -i input.md --start "## Section 1" --end "## Section 2" -o output.txt

# Extract text using partial header match
> extract_text_from_txt.py -i input.md --start "Section 1" --end "Section 2" -o output.txt

# Extract text from "## Section 1" until the next level-2 header
> extract_text_from_txt.py -i input.md --start "## Section 1" -o output.txt

# Extract text and print to stdout
> extract_text_from_txt.py -i input.md --start "Chapter 1" --end "Chapter 2" -o -

# Extract text between slides in a .txt file (using slide notation)
> extract_text_from_txt.py -i input.txt --start "* Slide 1" --end "* Slide 2" -o output.txt

# Extract text from a slide until next same-level slide (no explicit end)
> extract_text_from_txt.py -i input.txt --start "* Introduction" -o output.txt
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
    hdbg.dassert_isinstance(header_str, str, "header_str must be a string")
    hdbg.dassert_ne(header_str, "", "Header string cannot be empty")
    is_header_, level, title = hmarhead.is_header(header_str)
    hdbg.dassert(
        is_header_,
        "Invalid header format '%s'; expected format like '# Title' or '## Subtitle'",
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


def _find_header_by_partial_title(
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


def _find_header_from_input(
    header_list: hmarhead.HeaderList,
    header_input: str,
) -> Tuple[hmarhead.HeaderInfo, int]:
    """
    Find a header from user input that can be either a full header string or partial title.

    :param header_list: list of HeaderInfo objects
    :param header_input: either "## Title" (full header) or "Title" (partial match)
    :return: tuple of (HeaderInfo, level) where level is from the input if it was a full header
    :raises: ValueError if input is ambiguous or header not found
    """
    if header_input.lstrip().startswith("#"):
        # Full header format like "## Title"
        level, title = _parse_header_string(header_input)
        header_info = _find_header_by_title(header_list, title)
        hdbg.dassert_is_not(
            header_info, None, "Header not found: '%s'", header_input
        )
        hdbg.dassert_eq(
            header_info.level,
            level,
            "Header level mismatch for '%s': expected level %s, got %s",
            title,
            level,
            header_info.level,
        )
        return header_info, level
    else:
        # Partial title match
        header_info = _find_header_by_partial_title(header_list, header_input)
        hdbg.dassert_is_not(
            header_info, None, "No header matches: '%s'", header_input
        )
        return header_info, header_info.level


def _find_end_line(
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
        end_header_info, _ = _find_header_from_input(
            header_list, end_header_input
        )
        return end_header_info.line_number - 1
    # Search for the next header at the same or higher level (fewer # symbols).
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
    :param start_header_str: starting header (e.g., "## Section 1" or "Section 1")
    :param end_header_str: ending header (optional, same formats accepted)
    :return: extracted lines
    """
    hdbg.dassert_isinstance(lines, list, "lines must be a list of strings")
    sanity_check = False
    header_list = hmarkdo.extract_headers_from_markdown(
        lines, max_level=10, sanity_check=sanity_check
    )
    start_header_info, _ = _find_header_from_input(header_list, start_header_str)
    end_line = _find_end_line(header_list, start_header_info, end_header_str)
    start_idx = start_header_info.line_number - 1
    if end_line is None:
        end_idx = len(lines)
    else:
        end_idx = end_line
    extracted_lines = lines[start_idx:end_idx]
    # Strip trailing blank lines from extracted content.
    while extracted_lines and extracted_lines[-1].strip() == "":
        extracted_lines.pop()
    return extracted_lines


def _extract_text_from_txtslides(
    lines: List[str],
    start_header_str: str,
    end_header_str: Optional[str],
) -> List[str]:
    """
    Extract text from txt slide lines between two headers/slides.

    Slides (`* Title`) are automatically converted to headers (`##### Title`) for
    consistent processing. Users can pass either format: `* Slide Title` or
    `##### Slide Title` or just the title for partial match.

    :param lines: list of lines in the input file
    :param start_header_str: starting header/slide (e.g., "* Slide 1", "##### Section 1", or "Section 1")
    :param end_header_str: ending header/slide (optional, same formats accepted)
    :return: extracted lines
    """
    hdbg.dassert_isinstance(lines, list, "lines must be a list of strings")
    # Convert slide notation ('* Title') to header notation so the same header
    # search logic works for both inputs.
    start_header_str = hmarkdo.convert_slide_to_markdown([start_header_str])[0]
    if end_header_str is not None:
        end_header_str = hmarkdo.convert_slide_to_markdown([end_header_str])[0]
    # Convert all lines from slide to markdown format.
    lines = hmarkdo.convert_slide_to_markdown(lines)
    sanity_check = False
    header_list = hmarkdo.extract_headers_from_markdown(
        lines, max_level=10, sanity_check=sanity_check
    )
    start_header_info, _ = _find_header_from_input(header_list, start_header_str)
    end_line = _find_end_line(header_list, start_header_info, end_header_str)
    start_idx = start_header_info.line_number - 1
    if end_line is None:
        end_idx = len(lines)
    else:
        end_idx = end_line
    extracted_lines = lines[start_idx:end_idx]
    # Strip trailing blank lines from extracted content.
    while extracted_lines and extracted_lines[-1].strip() == "":
        extracted_lines.pop()
    return extracted_lines


def _parse() -> argparse.ArgumentParser:
    """
    Create and return the argument parser for the script.

    :return: ArgumentParser configured with input, output, start, and end arguments
    """
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
        help="Starting header/slide: either full format (e.g., '## Section 1' or '* Slide Title'), or partial match (e.g., 'Section 1'). For .txt slides, can use '* Slide Title' notation. Partial match must be unique.",
    )
    parser.add_argument(
        "--end",
        type=str,
        default=None,
        help="Ending header/slide: either full format (e.g., '## Section 2' or '* Slide Title'), or partial match (e.g., 'Section 2'). If not provided, extracts until the next header at the same or higher level. For .txt slides, can use '* Slide Title' notation. Partial match must be unique.",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Parse arguments and extract text from the input file between specified headers.

    :param parser: ArgumentParser with configured arguments
    """
    args = parser.parse_args()
    verbose = False
    hparser.init_logger_for_input_output_transform(args, verbose=verbose)
    in_file_name, out_file_name = hparser.parse_input_output_args(args)
    input_content = hparser.from_file(in_file_name)
    hdbg.dassert_isinstance(
        input_content, list, "input_content must be a list of lines"
    )
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
        (
            i + 1
            for i, line in enumerate(input_content)
            if line.lstrip() == args.start.lstrip()
        ),
        1,
    )
    end_line_idx = start_line_idx + len(extracted_lines) - 1
    _LOG.info(f"Extracted lines {start_line_idx}-{end_line_idx}")
    hparser.to_file(output_content, out_file_name)


if __name__ == "__main__":
    _main(_parse())
