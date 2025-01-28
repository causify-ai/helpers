#!/usr/bin/env python
r"""
Wrapper for isort

> amp_isort.py sample_file1.py sample_file2.py

Import as:

import linters.amp_isort as lampisor
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


class _ISort(liaction.Action):
    """
    Apply isort code formatter.
    """

    def __init__(self) -> None:
        executable = "isort"
        super().__init__(executable)

    def check_if_possible(self) -> bool:
        check: bool = hsystem.check_exec(self._executable)
        return check

    def _execute(self, file_name: str, pedantic: int) -> List[str]:
        _ = pedantic
        # Applicable to only python file.
        if not liutils.is_py_file(file_name):
            _LOG.debug("Skipping file_name='%s'", file_name)
            return []
        # Use `--treat-all-comment-as-code` switch to ensure that `isort`
        # doesn't move comments between imports, like
        # ```
        # import pandas as pd
        #
        # # Comment.
        #
        # import helpers.hio as hio
        # ```
        # See DevTools448 "Linter moves comment for no reason".
        cmd = self._executable + f" --treat-all-comment-as-code {file_name}"
        output: List[str]
        _, output = liutils.tee(cmd, self._executable, abort_on_error=False)
        output = [line for line in output if not line.startswith("Fixing")]
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
    action = _ISort()
    action.run(args.files, args.abort_on_change)


if __name__ == "__main__":
    _main(_parse())
