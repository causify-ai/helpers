#!/usr/bin/env python3

"""
Read a cfile and inject its content as todos in the code.
"""

import argparse
import logging

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hmarkdown as hmarkdo
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


# TODO(gp): -> _parser() or _get_parser() everywhere.
def _parse() -> argparse.ArgumentParser:
    """ """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--cfile",
        type=str,
        required=False,
        default="cfile",
        help="File containing the TODOs to inject",
    )
    parser.add_argument(
        "--todo_target",
        action="store",
        required=True,
        help="User name to use in the TODOs",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Read the cfile.
    cfile_txt = hio.from_file(args.cfile)
    # Inject the TODOs.
    hmarkdo.inject_todos_from_cfile(
        cfile_txt, args.todo_target, comment_prefix="#"
    )


if __name__ == "__main__":
    _main(_parse())
