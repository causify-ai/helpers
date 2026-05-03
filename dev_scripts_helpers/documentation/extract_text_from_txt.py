#!/usr/bin/env python3

r"""
Extract a chunk of a markdown file between two headers.

The script:
- Reads the input Markdown file
- Extracts all headers using the same logic as extract_toc_from_txt.py
- Finds the specified start and end headers
- Extracts the text between them (including start header line, excluding end header)
- Writes to output file or stdout

Examples:
# Extract section between two headers
> extract_text_from_txt.py -i input.md --start "# Chapter 1" --end "# Chapter 2" -o output.md

# Extract from start of file to a header
> extract_text_from_txt.py -i input.md --end "## Conclusion" -o output.md

# Extract from a header to end of file
> extract_text_from_txt.py -i input.md --start "# Appendix" -o output.md

# Print to stdout
> extract_text_from_txt.py -i input.md --start "## Results" -o -

# Dry run: check line numbers only
> extract_text_from_txt.py -i input.md --start "# Intro" --end "# Methods" --dry_run
"""

import argparse
import logging
from typing import List

import helpers.hdbg as hdbg
import helpers.hmarkdown_headers as hmarhead
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


def _find_header_line(
    header_str: str, header_list: List[hmarhead.HeaderInfo]
) -> int:
    """
    Find the line number of a header in the header list.

    The header_str is parsed to extract the level and description, then
    searched for in the header_list.

    :param header_str: header string in markdown format, e.g., "# Chapter 1"
    :param header_list: list of HeaderInfo objects from extract_headers_from_markdown
    :return: line number (1-indexed) of the matching header
    :raise ValueError: if no matching header is found
    """
    is_header_, level, title = hmarhead.is_header(header_str)
    if not is_header_:
        raise ValueError(f"Invalid header format: '{header_str}'")
    for header_info in header_list:
        if header_info.level == level and header_info.description == title:
            return header_info.line_number
    raise ValueError(
        f"Header not found: '{header_str}' (level={level}, title='{title}')"
    )


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
        default=None,
        help="Start header (e.g., '# Chapter 1'). If omitted, start from beginning.",
    )
    parser.add_argument(
        "--end",
        type=str,
        default=None,
        help="End header (e.g., '## Section'). If omitted, extract to end of file.",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Print line numbers only; do not write output file",
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
    header_list = hmarhead.extract_headers_from_markdown(
        input_content, max_level=6, sanity_check=False
    )
    start_line_num = 1
    end_line_num = len(input_content) + 1
    if args.start is not None:
        start_line_num = _find_header_line(args.start, header_list)
    if args.end is not None:
        end_line_num = _find_header_line(args.end, header_list)
    if args.dry_run:
        output = f"start_line_num={start_line_num} end_line_num={end_line_num}"
        _LOG.info(output)
        print(output)
    else:
        extracted_lines = input_content[start_line_num - 1 : end_line_num - 1]
        output_content = "\n".join(extracted_lines)
        hparser.to_file(output_content, out_file_name)


if __name__ == "__main__":
    _main(_parse())
