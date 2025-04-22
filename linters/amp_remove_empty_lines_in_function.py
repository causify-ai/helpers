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


def _remove_empty_lines(text: str) -> List[str]:
    """
    Process file to remove empty lines in functions.

    :param text: file to process
    :return: formatted file without empty lines in functions
    """
    lines = text.splitlines()
    # Extract indices of docstrings.
    docstring_indices = set(hstring.get_docstring_line_indices(lines))
    cleaned_file = []
    inside_function = False
    base_indent = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Match lines that define a function, for example, 'def func1():' or 'def func2(a, b):'.
        match = re.match(r"(\s*)def\s+\w+", line)
        if match:
            inside_function = True
            base_indent = len(match.group(1))
            _LOG.debug(
                "Function header found at line %d with base indentation %d",
                i,
                base_indent,
            )
        current_indent = len(line) - len(line.lstrip())
        if inside_function and i in docstring_indices and stripped == "":
            # Keep empty lines inside the docstring.
            cleaned_file.append("")
            continue
        if inside_function and stripped == "":
            # Remove empty lines inside the function.
            _LOG.debug("Removing empty line found at line %d inside function.", i)
            continue
        if inside_function and stripped != "" and current_indent <= base_indent:
            # Retain trailing empty lines after the function,
            # as Python doesn't distinguish between indented and non-indented empty lines,
            # so we preserve them manually to avoid accidental removal.
            if match:
                # Retain empty lines between the previous function and the current function.
                k = len(cleaned_file)
                while lines[i - 1] == "":
                    if cleaned_file[k - 1] == "":
                        # Check if no functions precede the current one,
                        # then the empty lines are already retained.
                        i -= 1
                        k -= 1
                    else:
                        # Retain empty lines between two functions.
                        cleaned_file.append("")
                        i -= 1
            else:
                # Retain empty lines between the previous function and the surrounding code.
                while lines[i - 1] == "":
                    cleaned_file.append("")
                    i -= 1
                inside_function = False
                base_indent = 0
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
