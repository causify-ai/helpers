#!/usr/bin/env python

"""
Convert a notes text file into markdown suitable for `notes_to_pdf.py`.

E.g.,
- convert the text in pandoc / latex format
- handle banners around chapters
- handle comments
"""

# TODO(gp):
#  - Add spaces between lines
#  - Add index counting the indices
#  - Convert // comments in code into #
#  - Fix /* and */

import argparse
import logging
import re
from typing import List, Tuple

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hmarkdown as hmarkdo
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

_NUM_SPACES = 2

_TRACE = False


def _process_abbreviations(in_line: str) -> str:
    r"""
    Transform some abbreviations into LaTeX.

    E.g., - `->` into `$\rightarrow$`
    """
    line = in_line
    for x, y in [
        (r"=>", r"\implies"),
        (r"->", r"\rightarrow"),
        (r"-^", r"\uparrow"),
        (r"-v", r"\downarrow"),
    ]:
        line = re.sub(
            r"(\s)%s(\s)" % re.escape(x), r"\1$%s$\2" % re.escape(y), line
        )
    if line != in_line:
        _LOG.debug("    -> line=%s", line)
    return line


def _process_question(line: str) -> Tuple[bool, str]:
    """
    Transform `* foo bar` into `- **foo bar**`.
    """
    # Bold.
    meta = "**"
    # Bold + italic: meta = "_**"
    # Underline (not working): meta = "__"
    # Italic: meta = "_"
    do_continue = False
    regex = r"^(\*|\*\*|\*:)(\s+)(\S.*)\s*$"
    m = re.search(regex, line)
    if m:
        line = "-%s%s%s%s" % (m.group(2), meta, m.group(3), meta)
        do_continue = True
    return do_continue, line


# #############################################################################


def _transform_lines(lines: List[str], *, is_qa: bool = False) -> List[str]:
    """
    Process the notes to convert them into a format suitable for pandoc.

    E.g.,
    - prepend some directive for pandoc
    - remove comments
    - expand abbreviations
    """
    out: List[str] = []
    # a) Prepend some directive for pandoc.
    out.append(r"""\let\emph\textit""")
    out.append(r"""\let\uline\underline""")
    out.append(r"""\let\ul\underline""")
    # b) Process text.
    # True inside a block to skip.
    in_skip_block = False
    # True inside a code block.
    in_code_block = False
    for i, line in enumerate(lines):
        _LOG.debug("%s:line=%s", i, line)
        # 1) Process comment block.
        if _TRACE:
            _LOG.debug("# 1) Process comment block.")
        do_continue, in_skip_block = hmarkdo.process_comment_block(
            line, in_skip_block
        )
        # _LOG.debug("  -> do_continue=%s in_skip_block=%s",
        #   do_continue, in_skip_block)
        if do_continue:
            continue
        # 2) Process code block.
        if _TRACE:
            _LOG.debug("# 2) Process code block.")
        do_continue, in_code_block, out_tmp = hmarkdo.process_code_block(
            line, in_code_block, i, lines
        )
        out.extend(out_tmp)
        if do_continue:
            continue
        # 3) Process single line comment.
        if _TRACE:
            _LOG.debug("# 3) Process single line comment.")
        do_continue = hmarkdo.process_single_line_comment(line)
        if do_continue:
            continue
        # 4) Process abbreviations.
        if _TRACE:
            _LOG.debug("# 4) Process abbreviations.")
        line = _process_abbreviations(line)
        # 5) Process question.
        if _TRACE:
            _LOG.debug("# 5) Process question.")
        do_continue, line = _process_question(line)
        if do_continue:
            out.append(line)
            continue
        # 6) Process empty lines in the questions and answers.
        if _TRACE:
            _LOG.debug("# 6) Process empty lines in the questions and answers.")
        if not is_qa:
            out.append(line)
        else:
            is_empty = line.rstrip(" ").lstrip(" ") == ""
            if not is_empty:
                if line.startswith("#"):
                    # It's a chapter.
                    out.append(line)
                else:
                    # It's a line in an answer.
                    out.append(" " * _NUM_SPACES + line)
            else:
                # Empty line.
                prev_line_is_verbatim = ((i - 1) > 0) and lines[i - 1].startswith(
                    "```"
                )
                next_line_is_verbatim = ((i + 1) < len(lines)) and (
                    lines[i + 1].startswith("```")
                )
                # The next line has a chapter or the start of a new note.
                next_line_is_chapter = ((i + 1) < len(lines)) and (
                    lines[i + 1].startswith("#") or lines[i + 1].startswith("* ")
                )
                _LOG.debug(
                    "  is_empty=%s prev_line_is_verbatim=%s next_line_is_chapter=%s",
                    is_empty,
                    prev_line_is_verbatim,
                    next_line_is_chapter,
                )
                if (
                    next_line_is_chapter
                    or prev_line_is_verbatim
                    or next_line_is_verbatim
                ):
                    out.append(" " * _NUM_SPACES + line)
    # c) Clean up.
    _LOG.debug("Clean up")
    # Remove all the lines with only spaces.
    out_tmp = []
    for line in out:
        if re.search(r"^\s+$", line):
            line = ""
        out_tmp.append(line)
    # Return result.
    out = out_tmp
    return out


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--input", action="store", type=str, required=True)
    parser.add_argument("--output", action="store", type=str, default=None)
    parser.add_argument(
        "--qa", action="store_true", default=None, help="The input file is QA"
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    _LOG.info("cmd line=%s", hdbg.get_command_line())
    # Slurp file.
    lines = hio.from_file(args.input).split("\n")
    lines = [l.rstrip("\n") for l in lines]
    out: List[str] = []
    # Transform.
    out_tmp = _transform_lines(lines)
    out.extend(out_tmp)
    # Save results.
    txt = "\n".join(out)
    hio.to_file(args.output, txt)


if __name__ == "__main__":
    _main(_parse())
