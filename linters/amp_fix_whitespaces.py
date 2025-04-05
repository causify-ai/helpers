#!/usr/bin/env python
"""
Fix whitespaces in a file.
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

_LOG = logging.getLogger(__name__)


def _replace_tabs_with_spaces(line: str, num_spaces: int = 4) -> str:
    """
    Replace tabs with space characters.

    :param line: original line
    :param num_spaces: tab size in spaces
    :return: line with tabs replaced
    """
    line_modified = line.expandtabs(num_spaces)
    return line_modified


def _remove_trailing_whitespaces(line: str) -> str:
    """
    Remove trailing whitespaces.

    A whitespace character is trailing if it is located between the last
    non-whitespace character of the line and the newline ("\n").

    :param line: original line
    :return: line without trailing whitespaces
    """
    line_modified = line.rstrip()
    return line_modified


def _format_end_of_file(lines: List[str]) -> List[str]:
    """
    Format the end of a file.

    - Non-empty files should end with a single newline ("\n")
    - Empty files (i.e. files without any non-whitespace characters) should remain
      empty, not ending with newline characters

    :param lines: lines of a file
    :return: lines with the end formatted
    """
    if not any(re.findall(r"\S", line) for line in lines):
        # There are no non-whitespace characters in the file;
        # keep the file empty.
        return []
    # Replace all whitespace characters from the end of the file with a single newline.
    lines_merged = "\n".join(lines)
    lines_merged = lines_merged.rstrip() + "\n"
    lines_end_formatted = lines_merged.split("\n")
    return lines_end_formatted


# #############################################################################
# _FixWhitespaces
# #############################################################################


class _FixWhitespaces(liaction.Action):
    """
    Fix irregularities with whitespace characters.

    - Replace tabs with spaces
    - Remove trailing whitespaces
    - Make sure non-empty files end with a single newline
    """

    def check_if_possible(self) -> bool:
        return True

    def _execute(self, file_name: str, pedantic: int) -> List[str]:
        _ = pedantic
        try:
            # Read the input file.
            lines = hio.from_file(file_name).split("\n")
        except RuntimeError:
            _LOG.debug("Cannot read file_name='%s'; skipping", file_name)
            return []
        updated_lines = []
        # Process the lines.
        for line in lines:
            line = _replace_tabs_with_spaces(line)
            line = _remove_trailing_whitespaces(line)
            updated_lines.append(line)
        updated_lines = _format_end_of_file(updated_lines)
        # Write the updated file back.
        liutils.write_file_back(file_name, lines, updated_lines)
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
        help="Files to process",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level)
    action = _FixWhitespaces()
    action.run(args.files)


if __name__ == "__main__":
    _main(_parse())
