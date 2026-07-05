#!/usr/bin/env python

"""
Capture a command from shell history and copy it to the clipboard.

# Copy the last command to the clipboard.
> last_cmd.py

# Copy the 3rd most recent command to the clipboard.
> last_cmd.py -n 3
"""

import argparse
import logging

import dev_scripts_helpers.coding_tools.notify as dsctonot
import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-n",
        dest="n",
        type=int,
        default=1,
        action="store",
        help="Index of the command to capture (1 is the most recent)",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, report_command_line=False)
    #
    exclude_substrings = ["last_cmd"]
    command = dsctonot._get_nth_command(
        args.n, exclude_substrings=exclude_substrings
    )
    #
    _LOG.info("Capturing command: %s", command)
    hsystem.to_pbcopy(command, pbcopy=True)


if __name__ == "__main__":
    _main(_parse())
