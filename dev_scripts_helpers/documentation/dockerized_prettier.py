#!/usr/bin/env python
"""
Run `prettier` inside a Docker container to ensure consistent formatting across
different environments.

This script builds the container dynamically if necessary and formats the
specified file using the provided `prettier` options.

Examples
# Basic usage:
> dockerized_prettier.py --parser markdown --prose-wrap always --write \
    --tab-width 2 test.md

# Use sudo for Docker commands:
> dockerized_prettier.py --use_sudo --parser markdown --prose-wrap always \
    --write --tab-width 2 test.md

# Set logging verbosity:
> dockerized_prettier.py -v DEBUG --parser markdown --prose-wrap always \
    --write --tab-width 2 test.md </pre>

# Process a file:
> cat test.md
- a
  - b
        - c
> dockerized_prettier.py --parser markdown --prose-wrap always \
    --write --tab-width 2 test.md
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
    hparser.add_input_output_args(parser)
    hparser.add_dockerized_script_arg(parser)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    # Parse everything that can be parsed and returns the rest.
    args, cmd_opts = parser.parse_known_args()
    in_file_name, out_file_name = hparser.parse_input_output_args(
        args, clear_screen=True
    )
    if not cmd_opts:
        cmd_opts = []
    hdbg.init_logger(
        verbosity=args.log_level, use_exec_path=True, force_white=False
    )
    _LOG.debug("cmd_opts: %s", cmd_opts)
    hdocker.run_dockerized_prettier(
        in_file_name,
        cmd_opts,
        out_file_name,
        force_rebuild=args.dockerized_force_rebuild,
        use_sudo=args.dockerized_use_sudo,
    )
    _LOG.info("Output written to '%s'", args.output)


if __name__ == "__main__":
    _main(_parse())
