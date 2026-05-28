#!/usr/bin/env python3

r"""
Extract text from a file between two markdown headers or slides.

The script:
- Processes the input Markdown `.md` or txt slide `.txt` file
- Extracts text based on --select range specification
- Outputs the extracted text to a file or stdout

For `.txt` slide files, headers can be specified as:
- Slides: "* Slide Title" (shorthand for `##### Slide Title`)
- Full header format: "##### Section 1" (includes the # symbols)
- Substring: "Section 1" (matches if unique)
- Line number: "42" (1-based)

For `.md` files, headers can be specified as:
- Full format: "## Section 1" (includes the # symbols)
- Substring: "Section 1" (matches if unique)
- Line number: "42" (1-based)

--select syntax (START:END):
- "START:END" - extract from START to END
- ":END" - extract from beginning to END
- "START:" - extract from START until next same-level header
- "START" (no colon) - extract from START to EOF

# Examples:

- Extract text between two headers (full format)
  > extract_from_md.py -i input.md --select "## Section 1:## Section 2" -o output.txt

- Extract text using substring match
  > extract_from_md.py -i input.md --select "Section 1:Section 2" -o output.txt

- Extract text from "## Section 1" until next same-level header
  > extract_from_md.py -i input.md --select "## Section 1:" -o output.txt

- Extract from beginning until "Section 2"
  > extract_from_md.py -i input.md --select ":Section 2" -o output.txt

- Extract text to EOF
  > extract_from_md.py -i input.md --select "Chapter 1" -o -

- Extract text between slides in a .txt file (using slide notation)
  > extract_from_md.py -i input.txt --select "* Slide 1:* Slide 2" -o output.txt

- Extract text from a slide using substring match
  > extract_from_md.py -i input.txt --select "Introduction" -o output.txt
"""

import argparse
import logging
import os

import helpers.hdbg as hdbg
import helpers.hmarkdown_select as hmarsele
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)




def _parse() -> argparse.ArgumentParser:
    """
    Create and return the argument parser for the script.

    :return: ArgumentParser configured with input, output, and select arguments
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    out_default = "-"
    hparser.add_input_output_args(parser, out_default=out_default)
    hmarsele.add_select_arg(parser, required=True)
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
    start_str, end_str = hmarsele.parse_select_arg(args.select)
    extracted_lines = hmarsele.extract_text_from_markdown_lines(
        input_content,
        start_str,
        end_str,
        is_slide_format=is_slide_format,
    )
    output_content = "\n".join(extracted_lines)
    _LOG.info(f"Extracted {len(extracted_lines)} lines")
    hparser.to_file(output_content, out_file_name)


if __name__ == "__main__":
    _main(_parse())
