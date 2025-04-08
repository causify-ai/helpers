#!/usr/bin/env python
r"""
Wrapper for black.

> amp_black.py sample_file1.py sample_file2.py

Import as:

import linters.amp_black as lampblac
"""
import argparse
import logging
import os
from typing import List

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hsystem as hsystem
import linters.action as liaction
import linters.utils as liutils

_LOG = logging.getLogger(__name__)


# #############################################################################


# #############################################################################
# _Black
# #############################################################################


class _Black(liaction.Action):
    """
    Apply black code formatter.
    """

    def __init__(self) -> None:
        executable = "black"
        super().__init__(executable)

    def check_if_possible(self) -> bool:
        check: bool = hsystem.check_exec(self._executable)
        return check

    def _execute(self, file_name: str, pedantic: int) -> List[str]:
        _ = pedantic
        if self.skip_if_not_py(file_name):
            # Apply only to Python files.
            return []
        #
        opts = "--line-length 82"
        cmd = self._executable + f" {opts} {file_name}"
        _, output = liutils.tee(cmd, self._executable, abort_on_error=False)
        # Remove the lines:
        # - reformatted core/test/test_core.py.
        # - 1 file reformatted.
        # - All done!
        # - 1 file left unchanged.
        to_remove = ["All done!", "file left unchanged", "reformatted"]
        output = [
            line for line in output if all(word not in line for word in to_remove)
        ]
        return output


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--abort_on_change",
        action="store_true",
        default=os.environ.get("ABORT_ON_CHANGE", False),
        help="Exit with error code if file was changed",
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
    action = _Black()
    action.run(args.files, args.abort_on_change)


if __name__ == "__main__":
    _main(_parse())
