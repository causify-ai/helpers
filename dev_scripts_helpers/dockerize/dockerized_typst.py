#!/usr/bin/env python
"""
Run `typst` inside a Docker container.

This script builds the container dynamically if necessary.

> dockerized_typst.py --input document.typ --output document.pdf
> dockerized_typst.py \
        --input document.typ \
        --output document.pdf \
        -- --font-path /path/to/fonts
"""

import argparse
import logging

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import dev_scripts_helpers.dockerize.lib_typst as dshdlity

_LOG = logging.getLogger(__name__)


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hparser.add_dockerized_script_arg(parser)
    parser.add_argument("-i", "--input", action="store", required=True)
    parser.add_argument("-o", "--output", action="store", default="")
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    # Parse everything that can be parsed and return the rest as extra options.
    args, cmd_opts = parser.parse_known_args()
    if not cmd_opts:
        cmd_opts = []
    hdbg.init_logger(
        verbosity=args.log_level, use_exec_path=True, force_white=False
    )
    _LOG.debug("cmd_opts: %s", cmd_opts)
    # Default output to input with .pdf extension if not specified.
    if not args.output:
        args.output = hio.change_file_extension(args.input, ".pdf")
    dshdlity.run_dockerized_typst(
        args.input,
        args.output,
        cmd_opts,
        force_rebuild=args.dockerized_force_rebuild,
        use_sudo=args.dockerized_use_sudo,
    )
    _LOG.info("Output written to '%s'", args.output)


if __name__ == "__main__":
    _main(_parse())
