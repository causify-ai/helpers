#!/usr/bin/env python
"""
Remove empty lines within a function.

Import as:

import linters.amp_fix_empty_lines as lafiemli
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


def update_function_blocks(file_content: str) -> List[str]:
    """
    Remove empty lines in functions.

    :param file_content: file to process
    :return: formatted file without empty lines in functions
    """
    #TODO(allenmatt10): Insert code here after approval.
    return []


class _FixEmptyLines(liaction.Action):

    def check_if_possible(self) -> bool:
        return True

    def _execute(self, file_name: str, pedantic: int) -> List[str]:
        _ = pedantic
        if self.skip_if_not_py_or_ipynb(file_name):
            # Apply only to Python files and Ipynb Notebooks.
            return []
        # Remove empty lines from functions in the file.
        file_content = hio.from_file(file_name)
        updated_lines = update_function_blocks(file_content)
        # Save the updated file with the added class frames.
        liutils.write_file_back(
            file_name, file_content.split("\n"), updated_lines
        )
        return []


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "files",
        nargs="+",
        action="store",
        type=str,
        help="files to process",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Run _FixEmptyLines.

    :param parser: argparse.ArgumentParser:
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level)
    action = _FixEmptyLines()
    action.run(args.files)


if __name__ == "__main__":
    _main(_parse())
