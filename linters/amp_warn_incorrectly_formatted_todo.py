#!/usr/bin/env python
"""
Import as:

import linters.amp_warn_incorrectly_formatted_todo as lawifoto
"""

import argparse
import logging
import re
from typing import List

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import linters.action as liaction
import linters.utils as liutils

_LOG = logging.getLogger(__name__)


def _warn_incorrectly_formatted_todo(
    file_name: str, line_num: int, line: str
) -> str:
    """
    Issues a warning for incorrectly formatted todo comments that don't match
    the format: (# TODO(assignee): (task).)
    """
    msg = ""

    match = liutils.parse_comment(line=line)
    if match is None:
        return msg

    comment = match.group(2)
    if not comment.lower().strip().startswith("todo"):
        return msg

    todo_regex = r"TODO\(\S+\): (.*)"

    match = re.search(todo_regex, comment)
    if match is None:
        msg = f"{file_name}:{line_num}: found incorrectly formatted TODO comment: '{comment}'"
    return msg


# #############################################################################
# _WarnIncorrectlyFormattedTodo
# #############################################################################


class _WarnIncorrectlyFormattedTodo(liaction.Action):
    """
    Apply specific lints.
    """

    def check_if_possible(self) -> bool:
        return True

    def _execute(self, file_name: str, pedantic: int) -> List[str]:
        _ = pedantic
        if self.skip_if_not_py(file_name):
            # Apply only to Python files.
            return []
        lines = hio.from_file(file_name).split("\n")
        output = []
        for i, line in enumerate(lines):
            msg = _warn_incorrectly_formatted_todo(file_name, i, line)
            if msg:
                output.append(msg)

        return output


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "files",
        nargs="+",
        action="store",
        type=str,
        help="Files to process",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level)
    action = _WarnIncorrectlyFormattedTodo()
    action.run(args.files)


if __name__ == "__main__":
    _main(_parse())
