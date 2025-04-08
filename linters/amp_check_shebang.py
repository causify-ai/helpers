#!/usr/bin/env python
"""
Import as:

import linters.amp_check_shebang as lamchshe
"""

import argparse
import logging
import os
from typing import List

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import linters.action as liaction
import linters.utils as liutils

_LOG = logging.getLogger(__name__)


def _check_shebang(file_name: str, lines: List[str]) -> str:
    """
    Return warning if:

    - a python executable has no shebang
    - a python file has a shebang and isn't executable

    Note: the function ignores __init__.py files  & test code.
    """
    msg = ""
    if os.path.basename(file_name) == "__init__.py" or liutils.is_test_code(
        file_name
    ):
        return msg

    has_shebang = liutils.is_shebang(lines[0])
    is_executable = liutils.is_executable(file_name)

    if is_executable and not has_shebang:
        msg = f"{file_name}:1: any executable needs to start with a shebang '#!/usr/bin/env python'"
    elif not is_executable and has_shebang:
        msg = f"{file_name}:1: a non-executable can't start with a shebang."

    return msg


# #############################################################################
# _CheckShebang
# #############################################################################


class _CheckShebang(liaction.Action):
    """
    Check if executables start with a shebang.
    """

    def check_if_possible(self) -> bool:
        return True

    def _execute(self, file_name: str, pedantic: int) -> List[str]:
        _ = pedantic
        if self.skip_if_not_py_or_ipynb(file_name):
            # Apply only to Python files or Ipynb notebooks.
            return []
        lines = hio.from_file(file_name).split("\n")
        out = _check_shebang(file_name, lines)
        return [out] if out else []


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
    action = _CheckShebang()
    action.run(args.files)


if __name__ == "__main__":
    _main(_parse())
