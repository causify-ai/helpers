#!/usr/bin/env python
"""
Run `latex` inside a Docker container.

This script builds the container dynamically if necessary and formats the
specified file using the provided `prettier` options.

"""

import argparse
import logging
import os

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    hparser.add_dockerized_script_arg(parser)
    parser.add_argument("-i", "--input", action="store", required=True)
    parser.add_argument("-o", "--output", action="store", required=True)
    parser.add_argument(
        "--run_latex_again", action="store_true", default=False
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    # Parse everything that can be parsed and returns the rest.
    args, cmd_opts = parser.parse_known_args()
    if not cmd_opts:
        cmd_opts = []
    hdbg.init_logger(
        verbosity=args.log_level, use_exec_path=True, force_white=False
    )
    run_latex_again = True
    hdocker.run_basic_latex(args.input, cmd_opts, run_latex_again, args.output,
                            force_rebuild=args.dockerized_force_rebuild,
                            use_sudo=args.dockerized_use_sudo)
    _LOG.info("Output written to '%s'", args.output)


if __name__ == "__main__":
    _main(_parse())
