#!/usr/bin/env python
r"""
Check if imports use our standard.

> amp_check_import.py sample-file1.py sample-file2.py

Import as:

import linters.amp_check_import as lamchimp
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


def _check_import(file_name: str, line_num: int, line: str) -> str:
    # The maximum length of an 'import as'.
    MAX_LEN_IMPORT = 8
    msg = ""
    if liutils.is_init_py(file_name):
        # In **init**.py we can import in weird ways. (e.g., the evil
        # `from ... import *`).
        return msg
    m = re.match(r"\s*from\s+(\S+)\s+import\s+.*", line)
    if m:
        if m.group(1) != "typing":
            msg = (
                f"{file_name}:{line_num}: do not use '{line.rstrip().lstrip()}'"
                " use 'import foo.bar as fba'"
            )
    else:
        m = re.match(r"\s*import\s+\S+\s+as\s+(\S+)", line)
        if m:
            shortcut = m.group(1)
            if len(shortcut) > MAX_LEN_IMPORT:
                msg = (
                    f"{file_name}:{line_num}: the import shortcut '{shortcut}' in "
                    f"'{line.rstrip().lstrip()}' is longer than {MAX_LEN_IMPORT} characters"
                )
    return msg


# #############################################################################
# _CheckImport
# #############################################################################


class _CheckImport(liaction.Action):

    def check_if_possible(self) -> bool:
        return True

    def _execute(self, file_name: str, pedantic: int) -> List[str]:
        _ = pedantic
        if self.skip_if_not_py(file_name):
            # Apply only to Python files.
            return []
        output = []
        lines = hio.from_file(file_name).split("\n")
        for i, line in enumerate(lines, start=1):
            msg = _check_import(file_name, i, line)
            if msg:
                output.append(msg)
        return output


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
    action = _CheckImport()
    action.run(args.files)


if __name__ == "__main__":
    _main(_parse())
