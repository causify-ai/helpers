#!/usr/bin/env python
"""
Run prettier in a container.

E.g.,
> > cat test.md
- a
  - b
        - c
> dockerized_prettier.py --parser markdown --prose-wrap always --write --tab-width 2 test.md
"""

import argparse
import logging

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hparser as hparser

# import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--use_sudo", action="store_true", help="Use sudo inside the container")
    hparser.add_verbosity_arg(parser)
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
    use_sudo = args.use_sudo
    hdocker.run_dockerized_prettier(prettier_cmd, file_path,
                                    use_sudo=use_sudo)


if __name__ == "__main__":
    _main(_parse())