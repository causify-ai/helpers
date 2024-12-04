#!/usr/bin/env python
"""
This script is designed to run `pandoc` inside a Docker container to ensure
consistent formatting across different environments.

It builds the container dynamically if necessary.

pandoc tmp.pandoc.no_spaces.txt \
    -t beamer --slide-level 4 -V theme:SimplePlus \
    --include-in-header=latex_abbrevs.sty \
    --toc --toc-depth 2 \
    -o tmp.pandoc.no_spaces.pdf
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
    hparser.add_dockerized_script_arg(parser)
    parser.add_argument("--input", action="store")
    parser.add_argument("--output", action="store", default="")
    parser.add_argument("--data_dir", action="store")
    #parser.add_argument("--include_in_header", action="store")
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
    _LOG.debug("cmd_opts: %s", cmd_opts)
    if not args.output:
        args.output = args.input
    hdocker.run_dockerized_pandoc(
        cmd_opts,
        args.input,
        args.output,
        args.dockerized_force_rebuild,
        args.dockerized_use_sudo,
    )
    _LOG.info("Output written to '%s'", args.output)


if __name__ == "__main__":
    _main(_parse())
