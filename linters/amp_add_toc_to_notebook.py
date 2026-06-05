#!/usr/bin/env python

"""
Add a table of contents to a notebook.

Wrapper for dev_scripts_helpers/notebooks/add_toc_to_notebook.py.
"""

import argparse
import logging
from typing import List

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hparser as hparser
import linters.action as liaction
import linters.utils as liutils

_LOG = logging.getLogger(__name__)


# #############################################################################
# _AddTOC
# #############################################################################


class _AddTOC(liaction.Action):
    def __init__(self) -> None:
        try:
            executable = hgit.find_file_in_git_tree("add_toc_to_notebook.py")
            super().__init__(executable)
            self._is_possible = True
        except AssertionError:
            super().__init__("")
            self._is_possible = False

    def check_if_possible(self) -> bool:
        return self._is_possible

    def _execute(self, file_name: str, pedantic: int) -> List[str]:
        _ = pedantic
        if self.skip_if_not_ipynb(file_name):
            # Apply only to Ipynb notebooks.
            return []
        output: List[str] = []
        # Run the script that adds a TOC to a notebook.
        cmd = []
        cmd.append(self._executable)
        cmd.append(f"--input_files {file_name}")
        cmd_as_str = " ".join(cmd)
        rc, output = liutils.tee(
            cmd_as_str, self._executable, abort_on_error=False
        )
        if rc != 0:
            # Store the encountered error.
            error = f"add_toc_to_notebook.py failed with command `{cmd}`\n"
            output.append(error)
            _LOG.error(output)
        return output


# #############################################################################


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
    hdbg.init_logger(verbosity=args.log_level)
    action = _AddTOC()
    action.run(args.files)


if __name__ == "__main__":
    _main(_parse())
