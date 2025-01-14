#!/usr/bin/env python
r"""
Wrapper for lint_txt.py text.

> amp_lint_md.py sample_file1.md sample_file2.md

Import as:

import linters.amp_lint_md as lamlimd
"""
import argparse
import logging
import os
import re
from typing import List, Tuple

import helpers.hio as hio
import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hsystem as hsystem
import linters.action as liaction
import linters.utils as liutils

_LOG = logging.getLogger(__name__)


# #############################################################################


def _check_readme_is_capitalized(file_name: str) -> str:
    """
    Check if all readme markdown files are named README.md.
    """
    msg = ""
    basename = os.path.basename(file_name)

    if basename.lower() == "readme.md" and basename != "README.md":
        msg = f"{file_name}:1: All README files should be named README.md"
    return msg


# #############################################################################

def _fix_md_headers(lines: List[str], file_name: str) -> Tuple[List[str], List[str]]:
    """
    Fix header levels in the file content 
        - Ensure headers start at level 1 and do not skip levels.

    :param file_name: the name of the markdown file being processed
    :return:
        - a list of fixed lines 
        - a list of warnings
    """
    fixed_lines = []
    warnings = []
    header_pattern = re.compile(r"^(#+)\s+.*")
    last_header_level = 0
    for idx, line in enumerate(lines):
        fixed_line = line
        match = header_pattern.match(line)
        if match:
            current_level = len(match.group(1))
            if current_level > last_header_level + 1:
                original_level = "#" * current_level
                adjusted_level = "#" * (last_header_level + 1)
                fixed_line = fixed_line.replace(original_level, adjusted_level, 1)
                warnings.append(
                    f"{file_name}:{idx}: Header level adjusted from {original_level} to {adjusted_level}."
                )
                current_level = last_header_level + 1
            last_header_level = current_level
        fixed_lines.append(fixed_line)
    return fixed_lines, warnings

def _verify_toc_and_warnings_from_lines(lines: List[str], file_name: str) -> List[str]:
    """
    Verify that there is no content before the Table of Contents (TOC) in the lines of a file.

    :param lines: The lines of the markdown file.
    :param file_name: The name of the markdown file being processed.
    :return: A list of warnings.
    """
    warnings = []
    toc_found = False
    for idx, line in enumerate(lines, start=1):
        if not toc_found and line.strip().lower().startswith("table of contents"):
            toc_found = True
        if not toc_found and not line.strip().startswith("#") and line.strip():
            warnings.append(f"{file_name}:{idx}: Content found before Table of Contents (TOC).")
    return warnings

def process_markdown_file(file_name: str) -> Tuple[List[str], List[str], List[str]]:
    """
    Process a markdown file to fix header levels and verify the Table of Contents (TOC).

    :param file_name: The name of the markdown file being processed.
    :return: A tuple containing original lines, fixed lines, and a combined list of warnings.
    """
    # Read file content.
    lines = hio.from_file(file_name).splitlines("\n")
    warnings: List[str] = []
    # Fix headers.
    fixed_lines, header_warnings = _fix_md_headers(lines, file_name)
    warnings.append(header_warnings)
    # Verify TOC.
    toc_warnings = _verify_toc_and_warnings_from_lines(lines, file_name)
    warnings.append(toc_warnings)
    out_warnings = [w for w in warnings if len(w) > 0]
    return lines, fixed_lines, out_warnings

# #############################################################################
# _LintMarkdown
# #############################################################################


class _LintMarkdown(liaction.Action):

    def __init__(self) -> None:
        executable = "$(find -wholename '*dev_scripts_helpers/documentation/lint_notes.py')"
        super().__init__(executable)

    def check_if_possible(self) -> bool:
        check: bool = hsystem.check_exec(self._executable)
        return check

    def _execute(self, file_name: str, pedantic: int) -> List[str]:
        # Applicable only to Markdown files.
        ext = os.path.splitext(file_name)[1]
        output: List[str] = []
        if ext != ".md":
            _LOG.debug("Skipping file_name='%s' because ext='%s'", file_name, ext)
            return output
        lines, fixed_lines, warnings = process_markdown_file(file_name)
        liutils.write_file_back(file_name, lines, fixed_lines)
        # Run lint_notes.py.
        cmd = []
        cmd.append(self._executable)
        cmd.append(f"-i {file_name}")
        cmd.append("--in_place")
        cmd_as_str = " ".join(cmd)
        _, output = liutils.tee(cmd_as_str, self._executable, abort_on_error=True)
        # Check file name.
        msg = _check_readme_is_capitalized(file_name)
        if msg:
            output.append(msg)
        # Include the warnings.
        output.extend(warnings)
        # Remove cruft.
        output = [
            line
            for line in output
            if "Saving log to file" not in line
            # Remove reset character from output.
            and line != "\x1b[0m"
        ]

        return output


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
    action.run(args.files)


if __name__ == "__main__":
    _main(_parse())
