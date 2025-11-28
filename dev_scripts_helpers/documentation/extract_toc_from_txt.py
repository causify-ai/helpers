#!/usr/bin/env python3

"""
Extract headers from Markdown, LaTeX, or txt slide files and generate a Vim cfile.

The script:
- Processes the input Markdown `.md`, LaTeX `.tex`, or txt slide `.txt` file
- Extracts headers up to a specified maximum level
  - Markdown: # (level 1), ## (level 2), ### (level 3), etc.
  - LaTeX: \section{} (level 1), \subsection{} (level 2), \subsubsection{} (level 3)
  - Txt slides: # (level 1), ## (level 2), * (level 3)
- Prints a human-readable header map
- Generates an output file in a format that can be used with Vim's quickfix
  feature.

# Extract headers up to level 3 from a Markdown file and save to an output file:
> extract_toc_from_txt.py -i input.md -o cfile --mode cfile --max-level 3

# Extract headers up to level 2 from a LaTeX file and print to stdout:
> extract_toc_from_txt.py -i document.tex -o - --mode headers --max-level 2

# Extract headers up to level 3 from a txt slide file and print to stdout:
> extract_toc_from_txt.py -i slides.txt -o - --mode headers --max-level 3

# To use the generated cfile in Vim:
- Open Vim and run `:cfile output.cfile`
  ```
  > vim -c "cfile cfile"
  ```
- Navigate between headers using `:cnext` and `:cprev`
"""

import argparse
import logging
import os
from typing import List

import helpers.hdbg as hdbg
import helpers.hlatex as hlatex
import helpers.hmarkdown as hmarkdo
import helpers.hparser as hparser
import helpers.htxtslides as htxtsli

_LOG = logging.getLogger(__name__)


# TODO(ai_gp2): Remove repeated code from _extract_headers_from_markdown,
# _extract_headers_from_latex, and _extract_headers_from_txtslides.
def _extract_headers_from_markdown(
    input_file_name: str,
    lines: List[str],
    mode: str,
    max_level: int,
    out_file_name: str,
) -> None:
    """
    Extract headers from a Markdown file.

    :param input_file_name: path to the input Markdown file
    :param lines: list of lines in the input Markdown file
    :param mode: output mode
    :param max_level: maximum header levels to parse
    :param out_file_name: path to the output file
    """
    hdbg.dassert_isinstance(lines, list)
    # We don't want to sanity check since we want to show the headers, even
    # if malformed.
    sanity_check = False
    header_list = hmarkdo.extract_headers_from_markdown(
        lines, max_level=max_level, sanity_check=sanity_check
    )
    # Print the headers.
    if mode == "cfile":
        output_content = hmarkdo.header_list_to_vim_cfile(input_file_name, header_list)
    else:
        output_content = hmarkdo.header_list_to_markdown(header_list, mode)
    hparser.write_file(output_content, out_file_name)
    # Sanity check the headers.
    hmarkdo.sanity_check_header_list(header_list)


def _extract_headers_from_latex(
    input_file_name: str,
    lines: List[str],
    mode: str,
    max_level: int,
    out_file_name: str,
) -> None:
    """
    Extract headers from a LaTeX file.

    This function processes a LaTeX file to extract section headers
    (\section{}, \subsection{}, \subsubsection{}) and generates output
    in the requested format (cfile, headers, or list). It follows the
    same pattern as _extract_headers_from_markdown() to ensure consistent
    behavior across file types.

    :param input_file_name: path to the input LaTeX file
    :param lines: list of lines in the input LaTeX file
    :param mode: output mode ('cfile' for Vim quickfix, 'headers' for
        Markdown headers, 'list' for indented list)
    :param max_level: maximum header levels to parse (1-3 for LaTeX)
    :param out_file_name: path to the output file
    """
    hdbg.dassert_isinstance(lines, list)
    # We don't want to sanity check since we want to show the headers, even
    # if malformed.
    sanity_check = False
    header_list = hlatex.extract_headers_from_latex(
        lines, max_level=max_level, sanity_check=sanity_check
    )
    # Print the headers.
    if mode == "cfile":
        output_content = hmarkdo.header_list_to_vim_cfile(input_file_name, header_list)
    else:
        output_content = hmarkdo.header_list_to_markdown(header_list, mode)
    hparser.write_file(output_content, out_file_name)
    # Sanity check the headers.
    hmarkdo.sanity_check_header_list(header_list)


def _extract_headers_from_txtslides(
    input_file_name: str,
    lines: List[str],
    mode: str,
    max_level: int,
    out_file_name: str,
) -> None:
    """
    Extract headers from a txt slide file.

    This function processes a txt slide file to extract headers
    (# for level 1, ## for level 2, * for level 3) and generates output
    in the requested format (cfile, headers, or list). It follows the
    same pattern as _extract_headers_from_markdown() to ensure consistent
    behavior across file types.

    :param input_file_name: path to the input txt slide file
    :param lines: list of lines in the input txt slide file
    :param mode: output mode ('cfile' for Vim quickfix, 'headers' for
        Markdown headers, 'list' for indented list)
    :param max_level: maximum header levels to parse (1-3 for txt slides)
    :param out_file_name: path to the output file
    """
    hdbg.dassert_isinstance(lines, list)
    # Use convert_slide_to_markdown to convert txt slide format to standard markdown format.
    lines = hmarkdo.convert_slide_to_markdown(lines, level=3)
    # Use standard markdown header extraction.
    # We don't want to sanity check since we want to show the headers, even
    # if malformed.
    sanity_check = False
    header_list = hmarkdo.extract_headers_from_markdown(
        lines, max_level=max_level, sanity_check=sanity_check
    )
    # Print the headers.
    if mode == "cfile":
        output_content = hmarkdo.header_list_to_vim_cfile(input_file_name, header_list)
    else:
        output_content = hmarkdo.header_list_to_markdown(header_list, mode)
    hparser.write_file(output_content, out_file_name)
    # Sanity check the headers.
    hmarkdo.sanity_check_header_list(header_list)


# #############################################################################


# TODO(gp): _parse() -> _build_parser() everywhere.
def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # Print to stdout by default.
    out_default = "-"
    hparser.add_input_output_args(parser, out_default=out_default)
    parser.add_argument(
        "--mode",
        type=str,
        default="list",
        choices=["list", "headers", "cfile"],
        help="Output mode",
    )
    parser.add_argument(
        "--max_level",
        type=int,
        default=3,
        help="Maximum header levels to parse",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    # Do not print information.
    verbose = False
    hparser.init_logger_for_input_output_transform(args, verbose=verbose)
    in_file_name, out_file_name = hparser.parse_input_output_args(args)
    #
    input_content = hparser.read_file(in_file_name)
    # Detect file type and dispatch to appropriate extraction function.
    _, ext = os.path.splitext(in_file_name)
    if ext == ".md":
        _extract_headers_from_markdown(
            in_file_name, input_content, args.mode, args.max_level, out_file_name
        )
    elif ext == ".tex":
        _extract_headers_from_latex(
            in_file_name, input_content, args.mode, args.max_level, out_file_name
        )
    elif ext == ".txt":
        _extract_headers_from_txtslides(
            in_file_name, input_content, args.mode, args.max_level, out_file_name
        )
    else:
        raise ValueError(f"Unsupported file type: {in_file_name}")


if __name__ == "__main__":
    _main(_parse())
