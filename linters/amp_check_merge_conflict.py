#!/usr/bin/env python

"""
Check for git merge conflicts in a file.
"""

import argparse
import logging
from typing import List

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import linters.action as liaction

_LOG = logging.getLogger(__name__)

MERGE_CONFLICT_MARKERS = [
    "<<<<<<< ",
    "======= ",
    "=======\r\n",
    "=======\n",
    ">>>>>>> ",
]


def _check_merge_conflict(file_name: str, line_num: int, line: str) -> str:
    """
    Issue a warning if a git merge conflict marker is found.
    """
    msg = ""
    if any(line.startswith(marker) for marker in MERGE_CONFLICT_MARKERS):
        msg = f"{file_name}:{line_num}: git merge conflict marker detected"
    return msg


# #############################################################################
# _CheckMergeConflict
# #############################################################################


class _CheckMergeConflict(liaction.Action):
    """
    Check if there is a git merge conflict marker in the file.
    """

    def check_if_possible(self) -> bool:
        return True

    def _execute(self, file_name: str, pedantic: int) -> List[str]:
        _ = pedantic
        try:
            # Read the input file.
            lines = hio.from_file(file_name).split("\n")
        except RuntimeError:
            _LOG.debug("Cannot read file_name='%s'; skipping", file_name)
            return []
        output = []
        # Check the file lines for merge conflict markers.
        for i, line in enumerate(lines):
            msg = _check_merge_conflict(file_name, i, line)
            if msg:
                # Store the warning message.
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
    action = _CheckMergeConflict()
    action.run(args.files)


if __name__ == "__main__":
    _main(_parse())
