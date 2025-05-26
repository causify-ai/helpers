#!/usr/bin/env python3

"""
Read a cfile and inject its content as todos in the code.
"""

import argparse
import logging
import os
import re
from typing import List, Optional

import dev_scripts_helpers.llms.llm_prompts as dshlllpr
import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hmarkdown as hmarkdo
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem
import dev_scripts_helpers.llms.llm_transform as dshlllpt

_LOG = logging.getLogger(__name__)


# TODO(gp): -> _parser() or _get_parser() everywhere.
def _parse() -> argparse.ArgumentParser:
    """
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--cfile",
        type=str,
        required=True,
        default="cfile",
        help="File containing the TODOs to inject",
    )
    parser.add_argument(
        "--todo_target",
        action="store_true",
        help="User name to use in the TODOs"
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    # Read the cfile.
    cfile_txt = hio.from_file(args.cfile)
    # Inject the TODOs.
    todo_txt = dshlllpr.inject_todos(cfile_txt, args.todo_target)
    # Write the TODOs to the cfile.
    hio.to_file(args.cfile, todo_txt)


if __name__ == "__main__":
    _main(_parse())
