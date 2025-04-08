#!/usr/bin/env python
r"""
Check if filenames are correct according to our standard.

> amp_check_filename.py sample_file1.py sample_file2.py

Import as:

import linters.amp_check_filename as lamchfil
"""
import argparse
import logging
import os
import re
from typing import Callable, List

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import linters.action as liaction
import linters.utils as liutils

_LOG = logging.getLogger(__name__)


def _check_notebook_dir(file_name: str) -> str:
    """
    Check if that notebooks are under `notebooks` dir.
    """
    msg = ""
    if liutils.is_ipynb_file(file_name):
        subdir_names = file_name.split("/")
        if "notebooks" not in subdir_names:
            msg = (
                f"{file_name}:1: each notebook should be under a 'notebooks' "
                "directory to not confuse pytest"
            )
    return msg


def _check_test_file_dir(file_name: str) -> str:
    """
    Check if test files are under `test` dir.
    """
    msg = ""
    # TODO(gp): A little annoying that we use "notebooks" and "test".
    if liutils.is_py_file(file_name) and os.path.basename(file_name).startswith(
        "test_"
    ):
        if not liutils.is_under_test_dir(file_name):
            msg = (
                f"{file_name}:1: test files should be under 'test' directory to "
                "be discovered by pytest"
            )
    return msg


def _check_notebook_filename(file_name: str) -> str:
    r"""
    Check notebook filenames start with `Master_` or match: `\S+Task\d+_...`
    """
    msg = ""

    basename = os.path.basename(file_name)
    if liutils.is_ipynb_file(file_name) and not any(
        [basename.startswith("Master_"), re.match(r"^\S+Task\d+_", basename)]
    ):
        msg = (
            f"{file_name}:1: "
            r"All notebook filenames start with `Master_` or match: `\S+Task\d+_...`"
        )
    return msg


# #############################################################################
# _CheckFilename
# #############################################################################


class _CheckFilename(liaction.Action):
    """
    Detect class methods that are in the wrong order.
    """

    def check_if_possible(self) -> bool:
        return True

    def _execute(self, file_name: str, pedantic: int) -> List[str]:
        """
        Perform various checks based on the path of a file:

        - check that notebook files are under a `notebooks` dir
        - check that test files are under `test` dir
        """
        _ = pedantic
        if self.skip_if_not_py_or_ipynb(file_name):
            # Apply only to Python files or Ipynb notebooks.
            return []
        FilePathCheck = Callable[[str], str]
        FILE_PATH_CHECKS: List[FilePathCheck] = [
            _check_notebook_dir,
            _check_test_file_dir,
            _check_notebook_filename,
        ]

        output: List[str] = []
        for func in FILE_PATH_CHECKS:
            msg = func(file_name)
            if msg:
                output.append(msg)

        return output


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "-e",
        "--enforce",
        action="store_true",
        default=False,
        help="Enforce method order",
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
    action = _CheckFilename()
    action.run(args.files)


if __name__ == "__main__":
    _main(_parse())
