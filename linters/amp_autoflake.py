#!/usr/bin/env python
"""
Wrapper for autoflake.
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


class _Autoflake(liaction.Action):
    """
    Run the `autoflake` code formatter.

    - Remove unused imports
    - Remove unused variables
    """

    def __init__(self) -> None:
        executable = "autoflake"
        super().__init__(executable)

    def check_if_possible(self) -> bool:
        check: bool = hsystem.check_exec(self._executable)
        return check

    def _execute(self, file_name: str, pedantic: int) -> List[str]:
        _ = pedantic
        if not liutils.is_py_file(file_name) and not file_name.endswith(".ipynb"):
            # Applicable only to Python files and Ipynb notebooks.
            _LOG.debug("Skipping file_name='%s'", file_name)
            return []
        # Make changes to files instead of printing diffs.
        in_place_arg = "--in-place"
        # Remove all unused imports, not just those from the standard library.
        unused_imports_arg = "--remove-all-unused-imports"
        # Remove unused variables.
        unused_vars_arg = "--remove-unused-variables"
        # Compose the command with selected options.
        cmd = f"{self._executable} {in_place_arg} {unused_imports_arg} {unused_vars_arg} {file_name}"
        # Run.
        output: List[str]
        _, output = liutils.tee(cmd, self._executable, abort_on_error=False)
        output = [line for line in output if not line.startswith("<string>")]
        return output


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--abort_on_change",
        action="store_true",
        default=os.environ.get("ABORT_ON_CHANGE", False),
        help="Exit with error code if file was changed",
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
    action = _Autoflake()
    action.run(args.files, args.abort_on_change)


if __name__ == "__main__":
    _main(_parse())
