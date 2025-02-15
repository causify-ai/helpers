#!/usr/bin/env python
"""
Validate TOC and header levels in markdown files.

Steps:
1. Extract the contents of the markdown file.
2. Verify that there is no content before the Table of Contents (TOC)
 except for headers.
3. Ensure headers start at level 1 and do not skip levels.
"""

import argparse
import logging
import re
from typing import List, Tuple

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import linters.action as liaction
import linters.utils as liutils

_LOG = logging.getLogger(__name__)

# Regex to match headers at the start of a line.
HEADER_REGEX = re.compile(r"^(#+)(\s.*)")
# Regex to match TOC markers.
TOC_REGEX = re.compile(r"<!--\s*toc\s*-->")


def fix_md_headers(lines: List[str], file_name: str) -> List[str]:
    """
    Fix header levels in the file content.

    Ensure that header levels in the file start at level 1 and do not
    skip levels.

    :param lines: the lines of the markdown file being linted
    :param file_name: the name of the markdown file being processed
    :return: lines with fixed header levels
    """
    fixed_lines = []
    last_header_level = 0
    for idx, line in enumerate(lines):
        fixed_line = line
        match = HEADER_REGEX.match(line)
        if match:
            # Count the number of leading `#`.
            current_level = len(match.group(1))
            # Capture the rest of the line (after the initial `#` header).
            rest_of_line = match.group(2)
            # Adjust the header level if needed.
            if current_level > last_header_level + 1:
                adjusted_level = last_header_level + 1
                fixed_line = f"{'#' * adjusted_level}{rest_of_line}"
                _LOG.info(
                    "%s, line %s: Adjusted header level from %s to %s.",
                    file_name,
                    idx + 1,
                    match.group(1),
                    "#" * adjusted_level,
                )
                current_level = adjusted_level
            # Update the last header level.
            last_header_level = current_level
        fixed_lines.append(fixed_line)
    return fixed_lines


def verify_toc_position(lines: List[str], file_name: str) -> List[str]:
    """
    Verify that the position of the table of contents is correct.

    There should be no content before the table of contents (TOC)
    besides optional headers.

    :param lines: the lines of the markdown file
    :param file_name: the name of the markdown file being linted
    :return: warnings about the incorrect positioning of the TOC
    """
    warnings = []
    # Check for the start TOC markers.
    toc_start_found: bool = False
    for line_num, line in enumerate(lines):
        # Check for the start of TOC markers.
        stripped_line = line.strip()
        if TOC_REGEX.match(stripped_line):
            toc_start_found = True
            # Exit if the TOC is found.
            break
        # Ignore empty or whitespace-only lines and header lines before TOC.
        if stripped_line and not stripped_line.startswith("#"):
            warnings.append(f"{file_name}:{line_num}: Content found before TOC.")
    # Issue no warnings if the TOC is not found.
    if not toc_start_found:
        _LOG.warning("TOC not found. Skipping file_name='%s'.", file_name)
        warnings = []
    return warnings


def fix_md_toc_headers(file_name: str) -> Tuple[List[str], List[str], List[str]]:
    """
    Fix header levels and verify the Table of Contents.

    :param file_name: path to the markdown file being linted
    :return:
        - original lines of file
        - lines after fixing headers
        - warnings of TOC placements
    """
    # Read file content.
    lines = hio.from_file(file_name).splitlines()
    # Fix headers.
    fixed_lines = fix_md_headers(lines, file_name)
    # Verify TOC.
    toc_warnings = verify_toc_position(fixed_lines, file_name)
    return lines, fixed_lines, toc_warnings


# #############################################################################
# _TOCHeaderFixer
# #############################################################################


class _TOCHeaderFixer(liaction.Action):

    def check_if_possible(self) -> bool:
        return True

    def _execute(self, file_name: str, pedantic: int) -> List[str]:
        _ = pedantic
        if not file_name.endswith(".md"):
            # Apply only to Markdown files.
            _LOG.debug("Skipping file_name='%s'", file_name)
            return []
        # Fix headers in the file.
        lines, updated_lines, warnings = fix_md_toc_headers(file_name)
        # Save the updated file with the fixed headers.
        liutils.write_file_back(file_name, lines, updated_lines)
        return warnings


# #############################################################################


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
    action = _TOCHeaderFixer()
    if action.check_if_possible():
        action.run(args.files)


if __name__ == "__main__":
    _main(_parse())
