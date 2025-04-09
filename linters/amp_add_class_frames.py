#!/usr/bin/env python
"""
Add frames with class names before classes are initialized.

Import as:

import linters.amp_add_class_frames as laadclfr
"""

import argparse
import logging
import re
from typing import List, Tuple

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import linters.action as liaction
import linters.utils as liutils

_LOG = logging.getLogger(__name__)

# The maximum line length according to PEP-8.
MAX_LINE_LENGTH = 79


def _check_above_initialization(
    lines: List[str],
    line_num: int,
) -> Tuple[int, int, bool]:
    """
    Inspect the lines above the class initialization.

    - Get the number of non-empty lines to skip before inserting a class
      frame. This is done to make sure we don't separate class decorators
      and comments from the class initialization. E.g.,
        - 1 line should be skipped here:
            ```
            @pytest.mark.requires_ck_infra
            class MyClass():
            ```
        - 2 lines should be skipped here:
            ```
            # TODO(*): Refactor.
            @pytest.mark.requires_ck_infra
            class MyClass():
            ```
        - 0 lines should be skipped here:
            ```
            <some code>

            class MyClass():
            ```
    - Get the number of empty lines located above the class initialization
      and below the previous code. This is needed for removing pre-existing
      class frames (see below).

    - Check if there is an existing frame above the class initialization, in
      which case it will be removed before the new one is inserted.

    :param lines: original lines of the file
    :param line_num: the number of the line that initializes a class
    :return: the results of the lines check
       - the number of non-empty lines above the class
       - the number of empty lines above the class
       - whether there is a pre-existing frame to remove
    """
    non_empty_lines_counter = 0
    empty_lines_counter = 0
    remove_old_frame = False
    if line_num == 0:
        # No lines to skip and no frame to remove since the class is
        # initialized on the first line of the file.
        return non_empty_lines_counter, empty_lines_counter, remove_old_frame
    for i in range(line_num - 1, -1, -1):
        # Find the last empty line before the class initialization.
        if lines[i] == "":
            break
        # Keep score of how many non-empty lines there are immediately
        # before the class initialization; these lines should be skipped
        # for the class frame insertion.
        non_empty_lines_counter += 1
    if i == 0:
        # There are no empty lines and no frame between the first line of the
        # file and the class initialization.
        return non_empty_lines_counter, empty_lines_counter, remove_old_frame
    for j in range(i - 1, -1, -1):
        # Find the last non-empty line before the last empty line; the frame
        # will be inserted after it.
        empty_lines_counter += 1
        if lines[j] != "":
            break
    if (
        j > 1
        and lines[j] == lines[j - 2] == f"# {'#' * (MAX_LINE_LENGTH-2)}"
        and re.match(r"#\s\w+", lines[j - 1])
    ):
        # There is already a frame above this class that needs to be removed.
        remove_old_frame = True
    return non_empty_lines_counter, empty_lines_counter, remove_old_frame


def _insert_frame(
    lines: List[str], line_num: int, updated_lines: List[str]
) -> List[str]:
    """
    Add a frame with the class name before the class initialization.

    :param lines: original lines of the file
    :param line_num: the number of the line that is currently being
        processed
    :param updated_lines: lines that have already been stored to be
        written into the updated file
    :return: lines to write into the updated file, possibly with the
        added class frame
    """
    # Check if the current line contains a class initialization.
    current_line = lines[line_num]
    class_init_match = re.match(r"^class\s(\w+)", current_line)
    if not class_init_match:
        # No class initialization in the current line; skip further checks.
        updated_lines.append(current_line)
        return updated_lines
    # Inspect the lines above the class initialization to get the number of
    # lines to skip before inserting a class frame.
    (
        num_non_empty_lines,
        num_empty_lines,
        remove_old_frame,
    ) = _check_above_initialization(lines, line_num)
    if remove_old_frame:
        # Remove the frame that was already present above the class.
        updated_lines = (
            updated_lines[: -(num_non_empty_lines + num_empty_lines + 4)]
            + updated_lines[-(num_non_empty_lines + num_empty_lines) :]
        )
    # Build the class frame.
    class_name = class_init_match.group(1)
    class_frame = [
        f"# {'#' * (MAX_LINE_LENGTH-2)}",
        f"# {class_name}",
        f"# {'#' * (MAX_LINE_LENGTH-2)}",
        "",
    ]
    # Add the class frame to the lines to be written into the updated file.
    if num_non_empty_lines == 0:
        updated_lines.extend(class_frame + [current_line])
    else:
        updated_lines = (
            updated_lines[:-num_non_empty_lines]
            + class_frame
            + updated_lines[-num_non_empty_lines:]
            + [current_line]
        )
    return updated_lines


def update_class_frames(file_content: str) -> List[str]:
    """
    Update frames located above class initializations.

    - Old frames located above classes are removed
    - Frames with class names are added before the classes are initialized

    :param file_content: the contents of the Python file
    :return: the lines of the updated file
    """
    lines = file_content.split("\n")
    updated_lines: List[str] = []
    for line_num in range(len(lines)):
        updated_lines = _insert_frame(lines, line_num, updated_lines)
    return updated_lines


# #############################################################################
# _ClassFramer
# #############################################################################


class _ClassFramer(liaction.Action):

    def check_if_possible(self) -> bool:
        return True

    def _execute(self, file_name: str, pedantic: int) -> List[str]:
        _ = pedantic
        if self.skip_if_not_py(file_name):
            # Apply only to Python files.
            return []
        # Update class frames in the file.
        file_content = hio.from_file(file_name)
        updated_lines = update_class_frames(file_content)
        # Save the updated file with the added class frames.
        liutils.write_file_back(
            file_name, file_content.split("\n"), updated_lines
        )
        return []


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "files",
        nargs="+",
        action="store",
        type=str,
        help="files to process",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level)
    action = _ClassFramer()
    action.run(args.files)


if __name__ == "__main__":
    _main(_parse())
