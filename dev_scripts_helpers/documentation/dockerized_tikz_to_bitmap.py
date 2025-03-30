#!/usr/bin/env python
"""
Convert a TikZ file to a PNG image using a dockerized version of `pdflatex` and
`imagemagick`.
"""

import argparse
import logging

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("-i", "--input", action="store", required=True)
    parser.add_argument("-o", "--output", action="store", required=True)
    hparser.add_dockerized_script_arg(parser)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    # Parse everything that can be parsed and returns the rest.
    args, cmd_opts = parser.parse_known_args()
    if not cmd_opts:
        cmd_opts = ["-density 300", "-quality 10"]
    hdbg.init_logger(
        verbosity=args.log_level, use_exec_path=True, force_white=False
    )
    hdocker.dockerized_tikz_to_bitmap(
        args.input,
        cmd_opts,
        args.output,
        force_rebuild=args.dockerized_force_rebuild,
        use_sudo=args.dockerized_use_sudo,
    )
    _LOG.info("Output written to '%s'", args.output)


if __name__ == "__main__":
    _main(_parse())
