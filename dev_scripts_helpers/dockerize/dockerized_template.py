#!/usr/bin/env python

"""
Dockerized template.

This script is a template for creating a Dockerized script. It is
intended as a template to explain the process.
"""

import argparse
import logging

import helpers.hdbg as hdbg
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


def _parse() -> argparse.ArgumentParser:
    # Create an ArgumentParser instance with the provided docstring.
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    # FILL THIS.
    # parser.add_argument(
    #     "--docx_file",
    #     required=True,
    #     type=str,
    #     help="Path to the DOCX file to convert.",
    # )
    # Add Docker-specific arguments (e.g., --dockerized_force_rebuild,
    # --dockerized_use_sudo).
    hparser.add_dockerized_script_arg(parser)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(
        verbosity=args.log_level, use_exec_path=True, force_white=False
    )
    # FILL THIS.
    cmd = ()
    _LOG.debug("Command: %s", cmd)
    hdocker.run_dockerized_pandoc(
        pandoc_cmd,
        container_type="pandoc_only",
        force_rebuild=args.dockerized_force_rebuild,
        use_sudo=args.dockerized_use_sudo,
    )
    _LOG.info("Finished converting '%s' to '%s'.", args.docx_file, args.md_file)


if __name__ == "__main__":
    _main(_parse())
