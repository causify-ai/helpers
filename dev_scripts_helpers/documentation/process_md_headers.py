#!/usr/bin/env python3
import re

import argparse
import logging
from typing import Tuple

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


def extract_headers(
    markdown_file: str, input_content: str, *, max_level: int = 6
) -> str:
    """
    Extract headers from a Markdown file and generate a Vim cfile.

    :param markdown_file: Path to the input Markdown file.
    :param input_content: Path to the input Markdown file.
    :param max_level: Maximum header levels to parse (1 for `#`, 2 for `##`, etc.).
                      Default is 6.
    :return: the generated output file content, e.g.,
        The generated cfile format:
            <file path>:<line number>:<header title>

    Usage in Vim:
        :cfile <output_file>
        Use :cnext and :cprev to navigate between headers.
    """
    header_pattern = re.compile(r"^(#+)\s+(.*)")
    headers = []
    # Process the input file to extract headers.
    for line_number, line in enumerate(input_content.splitlines(), start=1):
        if "########################################" in line:
            continue
        match = header_pattern.match(line)
        if match:
            # Number of '#' determines level.
            level = len(match.group(1))
            if level <= max_level:
                title = match.group(2).strip()
                headers.append((line_number, level, title))
    # Generate the output file content.
    output_lines = [
        f"{markdown_file}:{line_number}:{title}" for line_number, level, title in
        headers
    ]
    output_content = "\n".join(output_lines)
    return output_content


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description = __doc__,
        formatter_class = argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-i", "--input", type=str, help="Path to the input Markdown file."
    )
    parser.add_argument(
        "-o", "--output", type=str, help="Path to the output cfile."
    )
    parser.add_argument(
        "--max-level",
        type=int,
        default=6,
        help="Maximum header levels to parse (default: 6).",
    )
    hparser.add_verbosity_arg(parser, log_level="CRITICAL")
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(
        verbosity=args.log_level, use_exec_path=True, force_white=False
    )
    input_content = hio.from_file(args.input)
    output_content = extract_headers(
        args.input, input_content, max_level=args.max_level
    )
    if args.output == "-":
        print(output_content)
    else:
        hio.to_file(args.output, output_content)
    _LOG.info(f"Successfully generated Vim cfile: {args.output}")


if __name__ == "__main__":
    _main(_parse())
