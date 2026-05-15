#!/usr/bin/env python3

r"""
Extract text from a file between two markdown headers or slides.

The script:
- Processes the input Markdown `.md` or txt slide `.txt` file
- Extracts text between specified start and end headers/slides
- If `--md_end` is not provided, extracts until the next header at the same or
  higher level (fewer # symbols)
- If `--md_start` header is not found, raises an error
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
> extract_text_from_txt.py -i input.md --md_start "## Section 1" --md_end "## Section 2" -o output.txt

# Extract text using partial header match
> extract_text_from_txt.py -i input.md --md_start "Section 1" --md_end "Section 2" -o output.txt

# Extract text from "## Section 1" until the next level-2 header
> extract_text_from_txt.py -i input.md --md_start "## Section 1" -o output.txt

# Extract text and print to stdout
> extract_text_from_txt.py -i input.md --md_start "Chapter 1" --md_end "Chapter 2" -o -

# Extract text between slides in a .txt file (using slide notation)
> extract_text_from_txt.py -i input.txt --md_start "* Slide 1" --md_end "* Slide 2" -o output.txt

# Extract text from a slide until next same-level slide (no explicit end)
> extract_text_from_txt.py -i input.txt --md_start "* Introduction" -o output.txt
"""

import argparse
import logging
import os

import helpers.hdbg as hdbg
import helpers.hmarkdown_select as hmarsel
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


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
    hparser.add_md_start_end_args(parser, start_required=True)
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
    is_slide_format = ext == ".txt"
    extracted_lines = hmarsel.extract_text_from_markdown_lines(
        input_content, args.md_start, args.md_end, is_slide_format=is_slide_format
    )
    output_content = "\n".join(extracted_lines)
    start_line_idx = next(
        (
            i + 1
            for i, line in enumerate(input_content)
            if line.lstrip() == args.md_start.lstrip()
        ),
        1,
    )
    end_line_idx = start_line_idx + len(extracted_lines) - 1
    _LOG.info(f"Extracted lines {start_line_idx}-{end_line_idx}")
    hparser.to_file(output_content, out_file_name)


if __name__ == "__main__":
    _main(_parse())
