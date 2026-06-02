#!/usr/bin/env python
"""
Convert single-line docstrings to multi-line format.

Transforms one-line docstrings to three-line format.

Import as:

import linters2.fix_comments as lficom
"""

import argparse
import re
from typing import List, Tuple

import helpers.hio as hio
import helpers.hparser as hparser
import linters.action as liaction


def _find_single_line_docstrings(
    lines: List[str],
) -> List[Tuple[int, str, int]]:
    """
    Find all single-line docstrings in the file.

    :param lines: list of file lines
    :return: list of tuples (line_num, quote_type, indentation_level)
        where quote_type is triple double or single quotes
    """
    results = []
    for line_num, line in enumerate(lines):
        # Match single-line docstrings with """ or '''
        match = re.search(r'^(\s*)("""|\'\'\')(.*?)\2\s*$', line)
        if match:
            indentation = len(match.group(1))
            quote_type = match.group(2)
            results.append((line_num, quote_type, indentation))
    return results


def _transform_docstring(
    line: str,
    *,
    quote_type: str,
    indentation: int,
) -> List[str]:
    """
    Transform a single-line docstring to multi-line format.

    :param line: the original docstring line
    :param quote_type: type of quotes (triple double or single)
    :param indentation: the indentation level
    :return: list of three lines (opening, content, closing)
    """
    match = re.search(
        r'^(\s*)("""|\'\'\')(.*?)\2\s*$',
        line,
    )
    if not match:
        # Should not happen if called correctly
        return [line]
    content = match.group(3)
    indent_str = " " * indentation
    return [
        f"{indent_str}{quote_type}",
        f"{indent_str}{content}",
        f"{indent_str}{quote_type}",
    ]


def convert_single_line_docstrings(file_content: str) -> List[str]:
    """
    Convert all single-line docstrings to multi-line format.

    :param file_content: the contents of the Python file
    :return: the lines of the updated file
    """
    lines = file_content.split("\n")
    docstring_positions = _find_single_line_docstrings(lines)

    if not docstring_positions:
        # No single-line docstrings found
        return lines

    # Process from the end to avoid index shifting
    updated_lines = lines[:]
    for line_num, quote_type, indentation in reversed(docstring_positions):
        original_line = updated_lines[line_num]
        transformed = _transform_docstring(
            original_line,
            quote_type=quote_type,
            indentation=indentation,
        )
        # Replace the single line with the three-line version
        updated_lines[line_num : line_num + 1] = transformed

    return updated_lines


# #############################################################################
# _CommentFixer
# #############################################################################


class _CommentFixer(liaction.Action):
    def check_if_possible(self) -> bool:
        return True

    def _execute(self, file_name: str, pedantic: int) -> List[str]:
        _ = pedantic
        if self.skip_if_not_py(file_name):
            # Apply only to Python files.
            return []
        # Convert single-line docstrings in the file.
        file_content = hio.from_file(file_name)
        updated_lines = convert_single_line_docstrings(file_content)
        # Save the updated file.
        hio.write_file_back(file_name, file_content.split("\n"), updated_lines)
        return []


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
    hparser.parse_verbosity_args(args)
    action = _CommentFixer()
    action.run(args.files)


if __name__ == "__main__":
    _main(_parse())
