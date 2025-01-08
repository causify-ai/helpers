#!/usr/bin/env python
r"""
Wrapper for flake8

> amp_flake8.py sample_file1.py sample_file2.py

Import as:

import linters.amp_flake8 as lampflak
"""
import argparse
import logging
from typing import List

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hsystem as hsystem
import linters.action as liaction
import linters.utils as liutils

_LOG = logging.getLogger(__name__)


# #############################################################################


class _Flake8(liaction.Action):
    """
    Look for formatting and semantic issues in code and docstrings. It relies
    on:

    - mccabe
    - pycodestyle
    - pyflakes
    """

    def __init__(self) -> None:
        executable = "flake8"
        super().__init__(executable)

    def check_if_possible(self) -> bool:
        check: bool = hsystem.check_exec(self._executable)
        return check

    def _execute(self, file_name: str, pedantic: int) -> List[str]:
        _ = pedantic
        # Applicable to only python file.
        if not liutils.is_py_file(file_name):
            _LOG.debug("Skipping file_name='%s'", file_name)
            return []
        # TODO(gp): Check if -j 4 helps.
        opts = "--exit-zero --doctests --max-line-length=82 -j 4"
        ignore = [
            # W503 line break before binary operator.
            # - Disabled because in contrast with black formatting.
            "W503",
            # W504 line break after binary operator.
            # - Disabled because in contrast with black formatting.
            "W504",
            # E203 whitespace before ':'
            # - Disabled because in contrast with black formatting.
            "E203",
            # E266 too many leading '#' for block comment.
            # - We have disabled this since it is a false positive for Jupytext files.
            "E266,"
            # E501 line too long (> 82 characters)
            ## - We have disabled this since it triggers also for docstrings
            ## at the beginning of the line. We let pylint pick the lines
            ## too long, since it seems to be smarter.
            "E501",
            # E731 do not assign a lambda expression, use a def.
            "E731",
            # E265 block comment should start with '# '
            "E265",
        ]
        is_jupytext_code = liutils.is_paired_jupytext_file(file_name)
        _LOG.debug("is_jupytext_code=%s", is_jupytext_code)
        if is_jupytext_code:
            ignore.extend(
                [
                    # E501 line too long.
                    "E501"
                ]
            )
        opts += " --ignore=" + ",".join(ignore)
        cmd = self._executable + f" {opts} {file_name}"
        ## Adding type anotation for 'output' in a seperate line as
        ## annotating it while unpacking the tuple is invalid syntax.
        output: List[str]
        _, output = liutils.tee(cmd, self._executable, abort_on_error=True)
        # Remove some errors.
        is_jupytext_code = liutils.is_paired_jupytext_file(file_name)
        _LOG.debug("is_jupytext_code=%s", is_jupytext_code)
        if is_jupytext_code:
            output_tmp: List[str] = []
            for line in output:
                # F821 undefined name 'display' [flake8]
                if "F821" in line and "undefined name 'display'" in line:
                    continue
                output_tmp.append(line)
            output = output_tmp
        output = [line for line in output if not line.startswith("<unknown>")]
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
    action = _Flake8()
    action.run(args.files)


if __name__ == "__main__":
    _main(_parse())
