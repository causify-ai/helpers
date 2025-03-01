#!/usr/bin/env python
r"""
Reflow, capitalize and add punctuation to python files.

> amp_fix_comments.py sample_file1.py sample_file2.py

Import as:

import linters.amp_fix_comments as lamficom
"""
import argparse
import dataclasses
import io
import logging
import re
import string
import tempfile
import tokenize
from typing import List, Optional, Tuple

import more_itertools

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import linters.action as liaction
import linters.utils as liutils

_LOG = logging.getLogger(__name__)


# #############################################################################
# _LinesWithComment
# #############################################################################


@dataclasses.dataclass
class _LinesWithComment:
    start_line: int
    end_line: int
    multi_line_comment: List[str]

    @property
    def is_single_line(self) -> bool:
        return len(self.multi_line_comment) == 1


def _extract_comments(lines: List[str]) -> List[_LinesWithComment]:
    """
    Extract comments (which can be single line or multi-lines) from a list of
    file lines, all consecutive lines with a comment would be merged into a
    single multiline comment.
    """
    content = "\n".join(lines)
    tokens = tokenize.tokenize(io.BytesIO(content.encode("utf-8")).readline)
    comments_by_line = {
        t.start[0]: t.line.rstrip() for t in tokens if t.type == tokenize.COMMENT
    }

    # Find consecutive line numbers to determine multi-line comments.
    comment_line_numbers = comments_by_line.keys()
    comments: List[_LinesWithComment] = []
    for group in more_itertools.consecutive_groups(comment_line_numbers):
        line_numbers = list(group)
        matching_comments = [
            line
            for line_num, line in comments_by_line.items()
            if line_num in line_numbers
        ]
        comments.append(
            _LinesWithComment(
                start_line=min(line_numbers),
                end_line=max(line_numbers),
                multi_line_comment=matching_comments,
            )
        )

    return comments


def _reflow_comment(comment: _LinesWithComment) -> _LinesWithComment:
    """
    Reflow comment using prettier.
    """
    content = ""
    whitespace: Optional[str] = None
    for line in comment.multi_line_comment:
        match = liutils.parse_comment(line)
        if match is None:
            if not liutils.is_shebang(line) and not liutils.is_separator(line):
                _LOG.warning("'%s' doesn't have a comment!", line)
            return comment
        content += "\n" + match.group(2)

        # Assumption: all consecutive comments have the same indentation.
        if whitespace is None:
            whitespace = match.group(1)
        else:
            hdbg.dassert_eq(whitespace, match.group(1))

    tmp = tempfile.NamedTemporaryFile(suffix=".md")
    hio.to_file(tmp.name, content)

    cmd = f"prettier --prose-wrap always --write {tmp.name}"
    liutils.tee(cmd, "prettier", abort_on_error=False)
    content: str = hio.from_file(file_name=tmp.name)
    tmp.close()

    updated_multi_line_comment: List[str] = []
    for line in content.strip().split("\n"):
        updated_multi_line_comment.append(str(whitespace) + "# " + line)

    comment.multi_line_comment = updated_multi_line_comment
    return comment


def _replace_comments_in_lines(
    lines: List[str], comments: List[_LinesWithComment]
) -> List[str]:
    """
    Replace comments in lines.

    - For each comment:
        1. finds the the index in lines where the new lines should be inserted
        2. removes the lines between the comment's start_line & end_line.
        3. adds the new multiline comment
    """
    LineWithNumber = Tuple[int, str]
    lines_with_numbers: List[LineWithNumber] = [
        (idx + 1, line) for idx, line in enumerate(lines)
    ]

    updated_lines_with_numbers = lines_with_numbers.copy()
    for comment in comments:
        # Find index of first line that matches those line nums.
        index_to_insert_at = next(
            idx
            for idx, (line_num, line) in enumerate(updated_lines_with_numbers)
            if line_num == comment.start_line
        )

        # Remove lines that are not between start_line & end_line.
        updated_lines_with_numbers = [
            (line_num, line)
            for line_num, line in updated_lines_with_numbers
            if line_num < comment.start_line or line_num > comment.end_line
        ]

        # Insert the new lines at that index.
        inserted_lines = [(-1, line) for line in comment.multi_line_comment]
        updated_lines_with_numbers = (
            updated_lines_with_numbers[:index_to_insert_at]
            + inserted_lines
            + updated_lines_with_numbers[index_to_insert_at:]
        )

    updated_lines = [line for line_num, line in updated_lines_with_numbers]
    return updated_lines


def _reflow_comments_in_lines(lines: List[str]) -> List[str]:
    comments = _extract_comments(lines=lines)
    reflowed_comments = [_reflow_comment(c) for c in comments]
    updated_lines = _replace_comments_in_lines(
        lines=lines,
        comments=reflowed_comments,
    )
    return updated_lines


def _fix_comment_style(lines: List[str]) -> List[str]:
    """
    Update comments to start with a capital letter and end with a `.`

    ignores:
    - empty line comments
    - comments that start with '##'
    - pylint & mypy comments
    - valid python statements
    """
    checks = (
        lambda x: x.startswith("##"),
        lambda x: x.startswith("# pylint"),
        lambda x: x.startswith("# type"),
        lambda x: x.startswith("#!"),
        lambda x: len(x.split()) == 2 and x.startswith("# "),
        lambda x: any(
            re.match(
                r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\."
                r"[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)",
                word,
            )
            is not None
            for word in x.split()
        ),
    )

    comments: List[_LinesWithComment] = _extract_comments(lines)

    for comment in comments:
        if not comment.is_single_line:
            continue
        # If any of the checks returns True, it means the check failed.
        if any(check(comment.multi_line_comment[0].strip()) for check in checks):
            continue
        match = liutils.parse_comment(
            comment.multi_line_comment[0], r"(^\s*)#(\s*)(.*)"
        )
        if not match:
            continue
        without_pound = match.group(3)
        # Make sure it doesn't try to capitalize an empty comment.
        if without_pound and not without_pound[0].isupper():
            without_pound = without_pound.capitalize()
        # Rebuild the comment and add punctuation if not already present.
        body = f"{match.group(1)}#{match.group(2)}{without_pound}"
        if body[-1] not in string.punctuation:
            body = f"{body}."
        comment.multi_line_comment[0] = body

    return _replace_comments_in_lines(lines, comments)


# #############################################################################
# _FixComment
# #############################################################################


class _FixComment(liaction.Action):
    """
    Reflow, capitalize and add punctuation to comments.
    """

    def check_if_possible(self) -> bool:
        return True

    def _execute(self, file_name: str, pedantic: int) -> List[str]:
        _ = pedantic
        if not liutils.is_py_file(file_name):
            _LOG.debug("Skipping file_name='%s'", file_name)
            return []
        lines = hio.from_file(file_name).split("\n")
        updated_lines = _reflow_comments_in_lines(lines)
        updated_lines = _fix_comment_style(updated_lines)
        liutils.write_file_back(file_name, lines, updated_lines)
        return []


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "files", nargs="+", action="store", type=str, help="Files to process"
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level)
    action = _FixComment()
    action.run(args.files)


if __name__ == "__main__":
    _main(_parse())
