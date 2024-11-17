#!/usr/bin/env python
"""
This script is designed to run `prettier` inside a Docker container to ensure
consistent formatting across different environments.

It builds the container dynamically if necessary and formats the specified file
using the provided `prettier` options.

To use this script, you need to provide the `prettier` command options and the
file to format. You can also specify whether to use `sudo` for Docker commands.

Examples
# Basic Usage
> dockerized_prettier.py --parser markdown --prose-wrap always --write \
    --tab-width 2 test.md

# Use Sudo for Docker Commands
> dockerized_prettier.py --use_sudo --parser markdown --prose-wrap always \
    --write --tab-width 2 test.md

# Set Logging Verbosity
> dockerized_prettier.py -v DEBUG --parser markdown --prose-wrap always \
    --write --tab-width 2 test.md </pre>

# Process a file
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
    hparser.add_dockerized_script_arg(parser)
    parser.add_argument("--input", action="store")
    parser.add_argument("--output", action="store", default="")
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    # Parse everything that can be parsed and returns the rest.
    args, prettier_cmd = parser.parse_known_args()
    if not prettier_cmd:
        prettier_cmd = []
    hdbg.init_logger(
        verbosity=args.log_level, use_exec_path=True, force_white=False
    )
    _LOG.debug("prettier_cmd: %s", prettier_cmd)
    # Assume that the last argument is the file to format.
    if not args.output:
        args.output = args.input
    hdocker.run_dockerized_prettier(
        prettier_cmd,
        args.input,
        args.output,
        args.dockerized_force_rebuild,
        args.dockerized_use_sudo,
    )
    _LOG.info("Output written to '%s'", args.output)


if __name__ == "__main__":
    _main(_parse())
