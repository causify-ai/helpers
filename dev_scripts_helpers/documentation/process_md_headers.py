#!/usr/bin/env python3

# TODO(gp): -> extract_headers_from_markdown.py
"""
Extract headers from a Markdown file and generate a Vim cfile.

The script
- processes the input Markdown file
- extracts headers up to a specified maximum level
- prints a human-readable header map
- generates an output file in a format that can be used with Vim's quickfix
  feature.

# Extract headers up to level 3 from a Markdown file and save to an output file:
> python process_md_headers.py -i input.md -o cfile --max-level 3

# Extract headers up to level 2 and print to stdout:
> python process_md_headers.py -i input.md -o - --max-level 2

# To use the generated cfile in Vim:
- Open Vim and run `:cfile output.cfile`
  ```
  > vim -c "cfile cfile"
  ```
- Navigate between headers using `:cnext` and `:cprev`
"""

import argparse
import logging

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hmarkdown as hmarkdo
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-i", "--input", type=str, help="Path to the input Markdown file."
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="cfile",
        help="Path to the output cfile. Use - for stdout",
    )
    parser.add_argument(
        "-m",
        "--max-level",
        type=int,
        default=6,
        help="Maximum header levels to parse (default: 6).",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(
        verbosity=args.log_level, use_exec_path=True, force_white=False
    )
    _LOG.info("Reading file '%s'", args.input)
    input_content = hio.from_file(args.input)
    output_content = hmarkdo.extract_headers(
        args.input, input_content, max_level=args.max_level
    )
    if args.output == "-":
        print(output_content)
    else:
        hio.to_file(args.output, output_content)
    _LOG.info("Generated Vim cfile '%s'", args.output)


if __name__ == "__main__":
    _main(_parse())
