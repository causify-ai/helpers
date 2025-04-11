#!/usr/bin/env python
"""
Remove empty lines within a function.

Import as:

import linters.amp_remove_empty_lines as lareemli
"""

import argparse
import re
from typing import List

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import linters.action as liaction
import linters.utils as liutils


def _clean_function_block(
    func_lines: List[str], docstring_done: bool, docstring_open: bool
) -> List[str]:
    """
    Remove empty lines inside function.

    :param func_lines: sequence of function lines
    :param docstring_done: indicates whether docstring is processed
        completely
    :param docstring_open: indicates whether docstring is currently
        processed
    :return: function without empty lines
    """
    cleaned_func_lines = []
    for line in func_lines:
        stripped_line = line.strip()
        if not docstring_done and (
            stripped_line.startswith('"""') or stripped_line.startswith("'''")
        ):
            # Skip if empty line is inside the docstring.
            docstring_open = not docstring_open
            cleaned_func_lines.append(line)
            if (
                stripped_line.endswith('"""')
                or stripped_line.endswith("'''")
                and len(stripped_line) > 3
            ):
                docstring_done = True
            continue
        if docstring_open:
            cleaned_func_lines.append(line)
            if stripped_line.endswith('"""') or stripped_line.endswith("'''"):
                docstring_open = False
                docstring_done = True
            continue
        if stripped_line == "":
            continue
        cleaned_func_lines.append(line)
    return cleaned_func_lines


def update_function_blocks(file_content: str) -> str:
    """
    Process file to find and update functions.

    :param file_content: file to process
    :return: formatted file without empty lines in functions
    """
    lines = file_content.splitlines()
    if file_content.endswith("\n"):
        lines.append("")
    cleaned_file = []
    i = 0
    n = len(lines)
    # Process each line to find function header.
    while i < n:
        line = lines[i]
        stripped = line.strip()
        # Check if the function header matches.
        if stripped.startswith("def ") and (re.match(r"\s*def\s+\w+", line)):
            func_lines = [line]
            i += 1
            indent_match = re.match(r"(\s*)def", line)
            base_indent = len(indent_match.group(1)) if indent_match else 0
            # Store all lines of the function separately.
            while i < n:
                next_line = lines[i]
                if next_line.strip() == "":
                    func_lines.append(next_line)
                    i += 1
                    continue
                # Check indentation.
                next_indent = len(next_line) - len(next_line.lstrip())
                if next_indent <= base_indent:
                    break
                func_lines.append(next_line)
                i += 1
            # Clean the function.
            docstring_open = False
            docstring_done = False
            cleaned_func_block = _clean_function_block(
                func_lines, docstring_done, docstring_open
            )
            for item in reversed(func_lines):
                # Empty lines after the function is included in the function
                # so it must be added separately.
                if item == "":
                    cleaned_func_block.append("")
                else:
                    break
            cleaned_file.extend(cleaned_func_block)
        else:
            cleaned_file.append(line)
            i += 1
    return "\n".join(cleaned_file)


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
            file_name, file_content.split("\n"), updated_lines.split("\n")
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
