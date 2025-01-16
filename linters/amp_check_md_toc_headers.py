#!/usr/bin/env python
"""
Validate TOC and header levels in markdown files.

Steps:
1. Extract the contents of the markdown file.
1. Verify that there is no content before the Table of Contents (TOC)
 except for headers.
2. Ensure headers start at level 1 and do not skip levels.
"""

import argparse
import logging
import os
import re
from typing import List, Tuple

import helpers.hio as hio
import helpers.hdbg as hdbg
import helpers.hparser as hparser
import linters.utils as liutils
import linters.action as liaction

_LOG = logging.getLogger(__name__)

# Regex to match headers at the start of a line.
HEADER_REGEX = re.compile(r"^(\s*)(#+)(\s.*)")

def _fix_md_headers(lines: List[str], file_name: str) -> Tuple[List[str], List[str]]:
    """
    Fix header levels in the file content.

    Ensure that header levels in the file start at level 1 and do not skip levels.
    Adjusts the header levels accordingly.

    :param file_name: the name of the markdown file being processed
    :return:
        - fixed lines
        - warnings
    """
    fixed_lines = []
    warnings = []
    last_header_level = 0
    for idx, line in enumerate(lines):
        fixed_line = line
        match = HEADER_REGEX.match(line)
        if match:
            leading_spaces = match.group(1)  
            # Count the number of leading `#`.
            current_level = len(match.group(2))
             # Capture the rest of the line (after the initial `#` header)  
            rest_of_line = match.group(3) 
            # Adjust the header level if needed
            if current_level > last_header_level + 1:
                adjusted_level = last_header_level + 1
                fixed_line = f"{leading_spaces}{'#' * adjusted_level}{rest_of_line}"
                _LOG.info(
                    "%s, %s: Adjusted header level from %s to %s.",
                    file_name,
                    idx + 1,
                    match.group(2),
                    "#" * adjusted_level,
                )
                current_level = adjusted_level
            # Update the last header level.
            last_header_level = current_level
        fixed_lines.append(fixed_line)
    return fixed_lines, warnings

def _verify_toc_and_warnings_from_lines(lines: List[str], file_name: str) -> List[str]:
    """
    Verify that there is no content before 
    the Table of Contents (TOC) in the lines of a file.

    :param lines: the lines of the markdown file
    :param file_name: The name of the markdown file being processed
    :return: warnings
    """
    warnings = []
    toc_found = False
    for lin_num, line in enumerate(lines, start=1):
        # Check if the Table of Contents (TOC) has been found.
        if not toc_found and line.strip().lower().startswith("table of contents"):
            toc_found = True
        if not toc_found and not line.strip().startswith("#") and line.strip():
            warnings.append(f"{file_name}:{lin_num}: Content found before Table of Contents (TOC).")
    return warnings

def process_markdown_file(file_name: str) -> Tuple[List[str], List[str], List[str]]:
    """
    Process a markdown file to fix header levels and verify the Table of Contents (TOC).

    :param file_name: markdown file
    :return:
        - original lines, 
        - fixed lines, 
        - combined warnings.
    """
    # Read file content.
    lines = hio.from_file(file_name).splitlines()
    warnings: List[str] = []
    # Fix headers.
    fixed_lines, header_warnings = _fix_md_headers(lines, file_name)
    warnings.extend(header_warnings)
    # Verify TOC.
    toc_warnings = _verify_toc_and_warnings_from_lines(lines, file_name)
    warnings.extend(toc_warnings)
    return lines, fixed_lines, warnings

# #############################################################################
# _LintMarkdown
# #############################################################################

class _TOCHeaderFixer(liaction.Action):

    def __init__(self) -> None:
        pass

    def check_if_possible(self) -> bool:
        return True

    def _execute(self, file_name, pedantic) -> List[str]:
        _ = pedantic
        if not file_name.endswith(".md"):
            # Apply only to Markdown files.
            _LOG.debug("Skipping file_name='%s'", file_name)
            return []
        # Fix links in the file.
        lines, updated_lines, warnings = process_markdown_file(file_name)
        # Save the updated file with the fixed links.
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
    action = _LintMarkdown()
    if action.check_if_possible():
        action.run(args.files)

if __name__ == "__main__":
    _main(_parse())
