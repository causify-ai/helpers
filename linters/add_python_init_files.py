#!/usr/bin/env python

import argparse
import logging
import os
from typing import List

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hsystem as hsystem
import linters.action as liaction
import linters.utils as liutils

_LOG = logging.getLogger(__name__)


def _get_dirs_to_add_init(
    file_name: str, exclude_unimported_dirs: bool
) -> List[str]:
    """
    Get the dirs with missing `__init__.py` files.

    :param file_name: the name of the file in the dir to check
    :param exclude_unimported_dirs: see `liutils.get_dirs_with_missing_init()`
    :return: names of the dirs with missing inits
    """
    dir_name = os.path.dirname(file_name)
    dirs_missing_init: List[str] = liutils.get_dirs_with_missing_init(
        dir_name, exclude_unimported_dirs=exclude_unimported_dirs
    )
    _LOG.debug(
        "Missing an `__init__.py` file: %s",
        dirs_missing_init,
    )
    return dirs_missing_init


class _AddPythonInitFiles(liaction.Action):
    """
    Create `__init__.py` files that are missing.
    """

    def check_if_possible(self) -> bool:
        return True

    def _execute(self, file_name: str, pedantic: int) -> List[str]:
        _ = pedantic
        # Get the dirs with missing `__init__.py` files.
        dirs_missing_init = _get_dirs_to_add_init(
            file_name, exclude_unimported_dirs=True
        )
        # Create the required inits.
        output: List[str] = []
        for dir_ in dirs_missing_init:
            init_file_path = os.path.join(dir_, "__init__.py")
            if not os.path.exists(init_file_path):
                # Create an empty `__init__.py` file.
                hio.to_file(init_file_path, "")
                msg = f"Created {init_file_path}"
                output.append(msg)
                # Check in the file.
                cmd = f"git add {init_file_path}"
                hsystem.system(cmd)
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
    action = _AddPythonInitFiles()
    # Keep one file from each head dir.
    files = []
    file_dirs = set()
    for f in args.files:
        # "dir/subdir/file.py" -> "dir/subdir".
        file_dir = os.path.dirname(f)
        if file_dir not in file_dirs:
            files.append(f)
            file_dirs.add(file_dir)
    action.run(files)


if __name__ == "__main__":
    _main(_parse())
