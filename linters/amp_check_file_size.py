#!/usr/bin/env python
"""
Check if the file exceeds the maximum allowed size.
"""

import argparse
import logging
from typing import List

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hsystem as hsystem
import linters.action as liaction

_LOG = logging.getLogger(__name__)


def _check_file_size(file_name: str, max_kb: int = 500) -> str:
    """
    Issue a warning if the file is too large.

    :param file_name: path to the file being linted
    :param max_kb: the maximum allowed file size in kB
    :return: a warning about the file size
    """
    # Get the file size.
    cmd = f"du -sk {file_name} | cut -f1"
    _, file_size = hsystem.system_to_string(cmd)
    # Compose the warning message, if needed.
    if int(file_size) > max_kb:
        msg = f"{file_name}: file is too large ({file_size} kB > {max_kb} kB)"
    else:
        msg = ""
    return msg


# #############################################################################
# _FileSizeChecker
# #############################################################################


class _FileSizeChecker(liaction.Action):

    def check_if_possible(self) -> bool:
        return True

    def _execute(self, file_name: str, pedantic: int) -> List[str]:
        _ = pedantic
        out = _check_file_size(file_name)
        return [out] if out else []


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
    action = _FileSizeChecker()
    action.run(args.files)


if __name__ == "__main__":
    _main(_parse())
