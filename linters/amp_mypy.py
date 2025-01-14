#!/usr/bin/env python
r"""
Wrapper for mypy.

> amp_mypy.py sample_file1.py sample_file2.py

> amp_mypy.py sample_file1.py -v DEBUG

Import as:

import linters.amp_mypy as lampmypy
"""
import argparse
import functools
import logging
import re
from typing import List

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hsystem as hsystem
import linters.action as liaction
import linters.utils as liutils

_LOG = logging.getLogger(__name__)


# #############################################################################


def _ignore_misc_error(line: str, file_name: str) -> None:
    """
    Process the line of the file that produces specific error of `misc` type.

    :param line: the line that produces the error
    :param file_name: the path to the file
    """
    lines = hio.from_file(file_name).split("\n")
    # Extract the number of the line from the error message, e.g. 370 from
    # 'linters/base.py:370: error: "None" not callable  [misc]'.
    # TODO(Toma): pass the line number from the caller.
    line_n = re.findall(":([0-9]+):", line)[0]
    # Correct the number of the line since they are enumerated from 1, not from 0.
    line_n = int(line_n) - 1
    # Get the line that produces the error.
    target = lines[line_n]
    # Update the line with the error processing.
    processed_target = f"{target}  # type: ignore[misc]"
    lines[line_n] = processed_target
    content = "\n".join(lines)
    hio.to_file(file_name, content)


# #############################################################################
# _Mypy
# #############################################################################


class _Mypy(liaction.Action):

    def __init__(self) -> None:
        executable = "mypy"
        super().__init__(executable)

    def check_if_possible(self) -> bool:
        check: bool = hsystem.check_exec(self._executable)
        return check

    @staticmethod
    @functools.lru_cache()
    def _config_path() -> str:
        """
        Return path of mypy.ini file.

        Aborts the script if the file is not found.
        """
        cmd = "find -name 'mypy.ini'"
        _, path = hsystem.system_to_string(cmd)
        hdbg.dassert_path_exists(path)
        return path

    def _execute(self, file_name: str, pedantic: int) -> List[str]:
        _ = pedantic
        # Applicable to only python files, that are not paired with notebooks.
        if not liutils.is_py_file(file_name) or liutils.is_paired_jupytext_file(
            file_name
        ):
            _LOG.debug("Skipping file_name='%s'", file_name)
            return []
        # TODO(gp): Convert all these idioms into arrays and joins.
        cmd = (
            f"{self._executable} --config-file {self._config_path()} {file_name}"
        )
        _, output = liutils.tee(
            cmd,
            self._executable,
            # Mypy returns -1 if there are errors.
            abort_on_error=False,
        )
        # Remove some errors.
        output_tmp: List[str] = []
        for i, line in enumerate(output):
            if (
                line.startswith("Success:")
                or
                # Found 2 errors in 1 file (checked 1 source file)
                line.startswith("Found ")
                or
                # Note: See https://mypy.readthedocs.io.
                "note: See https" in line
            ):
                continue
            if "Slice index must be an integer" in line:
                _ignore_misc_error(line, file_name)
                continue
            if (
                i > 0
                and "SyntaxWarning: invalid escape sequence" in output[i - 1]
            ):
                continue
            output_tmp.append(line)
        output = output_tmp
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
    action = _Mypy()
    action.run(args.files)


if __name__ == "__main__":
    _main(_parse())
