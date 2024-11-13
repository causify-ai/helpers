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
    # Use CRITICAL to avoid logging anything.
    hparser.add_verbosity_arg(parser, log_level="CRITICAL")
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    # Parse everything that can be parsed and returns the rest.
    args, remaining_args = parser.parse_known_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    _LOG.info("args for the wrapped executable: %s", remaining_args)
    # Assume that the last argument is the file to format.
    file_path = remaining_args[-1]
    hdbg.dassert_file_exists(file_path)
    prettier_cmd = " ".join(remaining_args[:-1])
    hdocker.run_dockerized_prettier(prettier_cmd, file_path,
                                    args.dockerized_force_rebuild,
                                    args.dockerized_use_sudo,
                                    args.log_level)


if __name__ == "__main__":
    _main(_parse())
