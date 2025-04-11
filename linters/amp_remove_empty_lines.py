#!/usr/bin/env python
"""
Remove empty lines within a function.

Import as:

import linters.amp_remove_empty_lines as lareemli
"""

import argparse
from typing import List

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hstring as hstring
import linters.action as liaction
import linters.utils as liutils


def update_function_blocks(file_content: str) -> List[str]:
    """
    Process file to find and update functions.

    :param file_content: file to process
    :return: formatted file without empty lines in functions
    """
    lines = file_content.splitlines()
    if file_content.endswith("\n"):
        lines.append("")
    docstring_indices = set(hstring.get_docstring_line_indices(lines))
    function_indices = set(hstring.get_function_indices(lines))
    cleaned_file = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Skip empty lines, except in docstrings.
        if (
            i in function_indices
            and i not in docstring_indices
            and stripped == ""
        ):
            continue
        cleaned_file.append(line)
    return cleaned_file


# #############################################################################
# _RemoveEmptyLines
# #############################################################################


class _RemoveEmptyLines(liaction.Action):

    def check_if_possible(self) -> bool:
        return True

    def _execute(self, file_name: str, pedantic: int) -> List[str]:
        _ = pedantic
        if self.skip_if_not_py(file_name):
            # Apply only to Python files.
            return []
        # Remove empty lines from functions in the file.
        file_content = hio.from_file(file_name)
        updated_lines = update_function_blocks(file_content)
        # Save the updated file with cleaned functions.
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
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level)
    action = _RemoveEmptyLines()
    action.run(args.files)


if __name__ == "__main__":
    _main(_parse())
