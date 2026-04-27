#!/usr/bin/env python
"""
Convert a Graphviz dot file to a PNG image.
"""

import argparse
import logging

import helpers.hdbg as hdbg
import dev_scripts_helpers.dockerize.dockerized_cli_utils as dsddhclut
import dev_scripts_helpers.dockerize.lib_graphviz as dshdligr
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-i", "--input", action="store", required=True)
    parser.add_argument("-o", "--output", action="store", required=True)
    hparser.add_dockerized_script_arg(parser)
    hparser.add_verbosity_arg(parser)
    dsddhclut.add_open_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    # Parse everything that can be parsed and returns the rest.
    args, cmd_opts = parser.parse_known_args()
    hdbg.init_logger(
        verbosity=args.log_level, use_exec_path=True, force_white=False
    )
    dshdligr.run_dockerized_graphviz(
        args.input,
        cmd_opts,
        args.output,
        force_rebuild=args.dockerized_force_rebuild,
        use_sudo=args.dockerized_use_sudo,
    )
    _LOG.info("Output written to '%s'", args.output)
    if args.open:
        dsddhclut.open_file_on_macos(args.output)


if __name__ == "__main__":
    _main(_parse())
