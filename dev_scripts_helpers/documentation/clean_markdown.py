#!/usr/bin/env python

"""
Clean up HTML markup in markdown files.

> clean_markdown.py --input INPUT --output OUTPUT
"""

import argparse
import logging

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import dev_scripts_helpers.documentation.documentation_utils as dshdocut

_LOG = logging.getLogger(__name__)


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Clean up HTML markup in markdown files."
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        type=str,
        help="Path to the input markdown file",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        type=str,
        help="Path to the output markdown file",
    )
    hparser.add_verbosity_arg(parser)
    return parser




def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main function to clean markdown files.
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Read input file.
    _LOG.info("Reading input file: %s", args.input)
    content = hio.from_file(args.input)
    # Remove all junk from markdown.
    content = dshdocut.remove_junk(content)
    # Write output file.
    _LOG.info("Writing output file: %s", args.output)
    hio.to_file(args.output, content)
    _LOG.info("Done")


if __name__ == "__main__":
    parser = _parse()
    _main(parser)
