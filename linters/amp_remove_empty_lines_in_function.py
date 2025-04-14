#!/usr/bin/env python
"""
Remove empty lines within a function.

Import as:

import linters.amp_remove_empty_lines_in_function as larelinfu
"""
import argparse
import logging
import re
from typing import List

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hstring as hstring
import linters.action as liaction
import linters.utils as liutils

_LOG = logging.getLogger(__name__)


# TODO(allenmatt10): Add tests.
def _find_function_indices(text: List[str]) -> List[int]:
    """
    Get indices of lines of code that are inside functions and methods.
    For example:
        Input: [
            "import os",
            "",
            "def func1(x: int) -> None:",
            "",
            "    print('Inside function')",
            "    print(x)",
            "",
            "func1(10)",
            "print('Outside function')"
        ]
        Output: [2, 3, 4, 5]

    :param text: the code lines to check
    :return: the indices of function lines
    """
    function_line_indices = []
    i = 0
    n = len(text)
    while i < n:
        # Process each line to find function header.
        line = text[i]
        # Match lines that define a function, for example, 'def func1():' or 'def func2(a, b):'.
        match = re.match(r"(\s*)def\s+\w+", line)
        if not match:
            # Ignore lines outside the functions.
            i += 1
            continue
        base_indent = len(match.group(1))
        start = i
        _LOG.debug(
            "Function header found at line ",
            i,
            " with base indentation ",
            base_indent,
        )
        i += 1
        while i < n:
            # Process each line inside the function.
            current_line = text[i]
            if current_line.strip() == "":
                _LOG.debug("Empty line found at ", i, " inside function.")
                # Register empty lines that are inside the function.
                i += 1
                continue
            current_indent = len(current_line) - len(current_line.lstrip())
            if current_indent <= base_indent:
                # Exit if current line is indented at or below base level as function ends.
                while text[i - 1] == "":
                    # Do not register empty lines that follow the function.
                    i -= 1
                _LOG.debug("Function block ends at line ", i)
                break
            i += 1
        function_line_indices.extend(range(start, i))
    return function_line_indices


def _remove_empty_lines(text: str) -> List[str]:
    """
    Process file to remove empty lines in functions.

    :param text: file to process
    :return: formatted file without empty lines in functions
    """
    lines = text.splitlines()
    # Extract indices of docstrings and functions.
    docstring_indices = set(hstring.get_docstring_line_indices(lines))
    function_indices = set(_find_function_indices(lines))
    cleaned_file = []
    for i, line in enumerate(lines):
        # Skip empty lines, except in docstrings.
        stripped = line.strip()
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
        updated_lines = _remove_empty_lines(file_content)
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
