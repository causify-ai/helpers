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
        if lines[i] == "":
            # Stop at the last empty line to separate decorators/comments from preceding code.
            break
        # Count non-empty lines (decorators/comments) that must stay with the class.
        non_empty_lines_counter += 1
    if i == 0:
        # There are no empty lines and no frame between the first line of the
        # file and the class initialization.
        return non_empty_lines_counter, empty_lines_counter, remove_old_frame
    for j in range(i - 1, -1, -1):
        empty_lines_counter += 1
        if lines[j] != "":
            # Found the last non-empty line; the frame will be inserted after the empty lines.
            break
    if (
        j > 1
        and lines[j] == lines[j - 2] == f"# {'#' * (MAX_LINE_LENGTH - 2)}"
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
    current_line = lines[line_num]
    class_init_match = re.match(r"^class\s(\w+)", current_line)
    if not class_init_match:
        # Not a class definition; pass through without modification.
        updated_lines.append(current_line)
        return updated_lines
    # Analyze preceding decorators/comments to determine frame insertion point.
    (
        num_non_empty_lines,
        num_empty_lines,
        remove_old_frame,
    ) = _check_above_initialization(lines, line_num)
    if remove_old_frame:
        # Remove the frame that was already present above the class.
        # The frame consists of 3 lines (top border, class name, bottom border)
        # plus num_empty_lines empty lines after it.
        frame_size = 3 + num_empty_lines
        if num_non_empty_lines > 0:
            updated_lines = (
                updated_lines[: -(num_non_empty_lines + frame_size)]
                + updated_lines[-num_non_empty_lines:]
            )
        else:
            updated_lines = updated_lines[:-frame_size]
    # Ensure exactly 2 empty lines before the frame (unless at file start).
    if num_non_empty_lines > 0:
        # Exclude decorators/comments from trailing empty line count.
        lines_to_check = updated_lines[:-num_non_empty_lines]
    else:
        lines_to_check = updated_lines
    # Count trailing empty lines to determine adjustment needed.
    num_trailing_empty = 0
    for i in range(len(lines_to_check) - 1, -1, -1):
        if lines_to_check[i] == "":
            num_trailing_empty += 1
        else:
            break
    # Only enforce 2 empty lines if there is actual code before the class.
    has_content_before = len(lines_to_check) > num_trailing_empty
    if num_trailing_empty < 2 and has_content_before:
        # Add empty lines to reach the required 2 empty lines before frame.
        lines_to_add = 2 - num_trailing_empty
        if num_non_empty_lines > 0:
            updated_lines = (
                updated_lines[:-num_non_empty_lines]
                + [""] * lines_to_add
                + updated_lines[-num_non_empty_lines:]
            )
        else:
            updated_lines.extend([""] * lines_to_add)
    elif num_trailing_empty > 2:
        # Remove excess empty lines to keep exactly 2 before frame.
        excess = num_trailing_empty - 2
        if num_non_empty_lines > 0:
            updated_lines = (
                updated_lines[: -(num_non_empty_lines + excess)]
                + updated_lines[-num_non_empty_lines:]
            )
        else:
            updated_lines = updated_lines[:-excess]
    # Build the class frame.
    class_name = class_init_match.group(1)
    class_frame = [
        f"# {'#' * (MAX_LINE_LENGTH - 2)}",
        f"# {class_name}",
        f"# {'#' * (MAX_LINE_LENGTH - 2)}",
        "",
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


def _remove_extra_bars(lines: List[str]) -> List[str]:
    """
    Remove extra/redundant comment bars that appear before complete frames.

    Detects complete frames (bar -> class name -> bar) and removes
    preceding bars and empty lines before the frame, but only if they are
    not preceded by actual code (to preserve decorative bars between sections).

    :param lines: the lines of the file
    :return: lines with extra bars removed
    """
    frame_border = f"# {'#' * (MAX_LINE_LENGTH - 2)}"
    result = []
    i = 0
    while i < len(lines):
        if lines[i] == frame_border:
            # Check if this bar starts a complete frame (bar -> name -> bar).
            if (
                i + 1 < len(lines)
                and re.match(r"#\s\w+", lines[i + 1])
                and i + 2 < len(lines)
                and lines[i + 2] == frame_border
            ):
                # Collect any preceding bars and empty lines to check if removable.
                trailing_items = []
                for j in range(len(result) - 1, -1, -1):
                    if result[j] == frame_border or result[j] == "":
                        trailing_items.append(result[j])
                    else:
                        break
                # Check if preceding items are preceded by code (not just trailing decorations).
                preceded_by_code = (
                    len(result) > len(trailing_items)
                    and result[-(len(trailing_items) + 1)] != frame_border
                )
                # Remove trailing bars/empty lines only if preceded by code (unnecessary duplicates).
                # Keep them if preceded by another complete frame (preserves visual separation).
                if (
                    any(item == frame_border for item in trailing_items)
                    and not preceded_by_code
                ):
                    for _ in range(len(trailing_items)):
                        result.pop()
                result.append(lines[i])
                result.append(lines[i + 1])
                result.append(lines[i + 2])
                i += 3
            else:
                result.append(lines[i])
                i += 1
        else:
            result.append(lines[i])
            i += 1
    return result


def update_class_frames(file_content: str) -> List[str]:
    """
    Update frames located above class initializations.

    - Old frames located above classes are removed
    - Frames with class names are added before the classes are initialized
    - Extra/redundant bars before frames are removed

    :param file_content: the contents of the Python file
    :return: the lines of the updated file
    """
    lines = file_content.split("\n")
    updated_lines: List[str] = []
    for line_num in range(len(lines)):
        updated_lines = _insert_frame(lines, line_num, updated_lines)
    # Remove any extra bars that appear before complete frames.
    updated_lines = _remove_extra_bars(updated_lines)
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
    parser.add_argument(
        "--no_report_command_line",
        action="store_false",
        default=True,
        help="Do not report the command line",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(
        verbosity=args.log_level, report_command_line=args.no_report_command_line
    )
    action = _ClassFramer()
    action.run(args.files)


if __name__ == "__main__":
    _main(_parse())
