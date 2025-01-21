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
from typing import List

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