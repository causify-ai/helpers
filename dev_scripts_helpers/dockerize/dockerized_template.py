#!/usr/bin/env python
"""
Convert Docx file to Markdown.

- Download a Google Doc as a docx document

- Run this command in the same directory as the Markdown file:
> FILE_NAME="tmp"; ls $FILE_NAME
> dev_scripts/convert_docx_to_markdown.py --docx_file $FILE_NAME.docx --md_file $FILE_NAME.md
"""

import argparse
import logging

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--docx_file",
        required=True,
        type=str,
        help="Path to the Docx file to convert.",
    )
    parser.add_argument(
        "--md_file",
        required=True,
        type=str,
        help="Path to the output Markdown file.",
    )
    hparser.add_dockerized_script_arg(parser)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(
        verbosity=args.log_level, use_exec_path=True, force_white=False
    )
    # Define the folder for extracted figures.
    md_file_figs = args.md_file.replace(".md", "_figs")
    _LOG.info("Converting '%s' to Markdown...", args.docx_file)
    # Run the dockerized conversion function.
    hdocker.run_dockerized_pandoc(
        args.docx_file,
        args.md_file,
        md_file_figs,
        force_rebuild=args.dockerized_force_rebuild,
        use_sudo=args.dockerized_use_sudo,
    )
    _LOG.info("Finished converting '%s' to '%s'.", args.docx_file, args.md_file)


if __name__ == "__main__":
    _main(_parse())
