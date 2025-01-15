#!/usr/bin/env python
"""
Import as:

import linters.amp_format_separating_line as lafoseli
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


def _format_separating_line(
    line: str, min_num_chars: int = 6, line_width: int = 78
) -> str:
    """
    Transform a line into a separating line if more than 6 # are found.

    :param line: line to format
    :param min_num_chars: minimum number of # to match after '# ' to decide
        this is a seperator line
    :param line_width: desired width for the seperator line
    :return: modified line
    """
    regex = r"(\s*\#)\s*([\#\=\-\<\>]){%d,}\s*$" % min_num_chars

    m = re.match(regex, line)
    if m:
        char = m.group(2)
        line = m.group(1) + " " + char * (line_width - len(m.group(1)))
    return line


class _FormatSeparatingLine(liaction.Action):
    """
    Format separating lines.
    """

    def check_if_possible(self) -> bool:
        return True

    def _execute(self, file_name: str, pedantic: int) -> List[str]:
        _ = pedantic
        if not liutils.is_py_file(file_name):
            _LOG.debug("Skipping file_name='%s'", file_name)
            return []

        lines = hio.from_file(file_name).split("\n")
        updated_lines = []
        docstring_line_indices = hstring.get_docstring_line_indices(lines)
        for i, line in enumerate(lines):
            if i not in docstring_line_indices:
                # Format the separating line only if we are not in a multi-line
                # string.
                updated_lines.append(_format_separating_line(line))
            else:
                updated_lines.append(line)
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
    action = _FormatSeparatingLine()
    action.run(args.files)


if __name__ == "__main__":
    _main(_parse())
