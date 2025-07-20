#!/usr/bin/env python

"""
Dockerized template.

This script is a template for creating a Dockerized script.
"""

import argparse
import logging

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


def _parse() -> argparse.ArgumentParser:
    # Create an ArgumentParser instance with the provided docstring.
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # TODO(*): Add more options.
    # parser.add_argument(
    #     "--docx_file",
    #     required=True,
    #     type=str,
    #     help="Path to the DOCX file to convert.",
    # )
    # Add Docker-specific arguments (e.g., --dockerized_force_rebuild,
    # --dockerized_use_sudo).
    hparser.add_dockerized_script_arg(parser)
    # Add logging verbosity parsing.
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    # Parse everything that can be parsed and returns the rest.
    args, cmd_opts = parser.parse_known_args()
    if not cmd_opts:
        cmd_opts = []
    # Start the logger.
    hdbg.init_logger(
        verbosity=args.log_level, use_exec_path=True, force_white=False
    )
    # Run latex.
    hdocker.run_basic_latex(
        args.input,
        cmd_opts,
        args.run_latex_again,
        args.output,
        force_rebuild=args.dockerized_force_rebuild,
        use_sudo=args.dockerized_use_sudo,
    )
    _LOG.info("Output written to '%s'", args.output)


    hdbg.init_logger(
        verbosity=args.log_level, use_exec_path=True, force_white=False
    )
    # TODO(*): Implement this.
    # pandoc_cmd = ()
    # _LOG.debug("Command: %s", pandoc_cmd)
    # hdocker.run_dockerized_pandoc(
    #    pandoc_cmd,
    #    container_type="pandoc_only",
    #    force_rebuild=args.dockerized_force_rebuild,
    #    use_sudo=args.dockerized_use_sudo,
    #)
    #_LOG.info("Finished converting '%s' to '%s'.", args.docx_file, args.md_file)


if __name__ == "__main__":
    _main(_parse())
