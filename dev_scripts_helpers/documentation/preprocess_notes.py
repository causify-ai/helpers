#!/usr/bin/env python

"""
Convert a "notes" text file into markdown suitable for `notes_to_pdf.py`.

The full list of transformations is:
- Handle banners around chapters
- Handle comments
- Prepend some directive for pandoc
- Remove comments
- Expand abbreviations
- Process questions "* ..."
- remove empty lines in the questions and answers
- Remove all the lines with only spaces
- Add TOC
"""

import argparse
import logging
import re
from typing import List, Tuple

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hmarkdown as hmarkdo
import helpers.hparser as hparser
import helpers.hprint as hprint

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


def _process_enumerated_list(in_line: str) -> str:
    """
    Transform enumerated list with parenthesis to `.`.

    E.g., "1) foo bar" is transformed into "1. foo bar".
    """
    line = re.sub(r"^(\s*)(\d+)\)\s", r"\1\2. ", in_line)
    return line


def _process_question_to_markdown(line: str) -> Tuple[bool, str]:
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
        # TODO(gp): Not sure why we need to use the same number of spaces and
        # not just one.
        spaces = m.group(2)
        tag = m.group(3)
        line = f"-{spaces}{meta}{tag}{meta}"
        do_continue = True
    return do_continue, line


def _process_question_to_slides(line: str, *, level: int = 4) -> Tuple[bool, str]:
    """
    Transform `* foo bar` into `#### foo bar`.
    """
    hdbg.dassert_lte(1, level)
    prefix = "#" * level
    do_continue = False
    regex = r"^(\*|\*\*|\*:)\s+(\S.*)\s*$"
    m = re.search(regex, line)
    if m:
        tag = m.group(2)
        line = f"{prefix} {tag}"
        do_continue = True
    return do_continue, line


def _transform_lines(txt: str, type_: str, *, is_qa: bool = False) -> str:
    """
    Process the notes to convert them into a format suitable for pandoc.

    :param lines: List of lines of the notes.
    :param type_: Type of output to generate (e.g., `pdf`, `html`, `slides`).
    :param is_qa: True if the input is a QA file.
    :return: List of lines of the notes.
    """
    _LOG.debug("\n%s", hprint.frame("Add navigation slides"))
    hdbg.dassert_isinstance(txt, str)
    lines = [line.rstrip("\n") for line in txt.split("\n")]
    out: List[str] = []
    # a) Prepend some directive for pandoc, if they are missing.
    if lines[0] != "---":
        txt = r"""
        ---
        fontsize: 10pt
        ---
        \let\emph\textit
        \let\uline\underline
        \let\ul\underline
        """
        txt = hprint.dedent(txt)
        out.append(txt)
    # b) Process text.
    # True inside a block to skip.
    in_skip_block = False
    # True inside a code block.
    in_code_block = False
    for i, line in enumerate(lines):
        _LOG.debug("%s:line=%s", i, line)
        # 1) Remove comment block.
        if _TRACE:
            _LOG.debug("# 1) Process comment block.")
        do_continue, in_skip_block = hmarkdo.process_comment_block(
            line, in_skip_block
        )
        # _LOG.debug("  -> do_continue=%s in_skip_block=%s",
        #   do_continue, in_skip_block)
        if do_continue:
            continue
        # 2) Remove code block.
        if _TRACE:
            _LOG.debug("# 2) Process code block.")
        do_continue, in_code_block, out_tmp = hmarkdo.process_code_block(
            line, in_code_block, i, lines
        )
        out.extend(out_tmp)
        if do_continue:
            continue
        # 3) Remove single line comment.
        if _TRACE:
            _LOG.debug("# 3) Process single line comment.")
        do_continue = hmarkdo.process_single_line_comment(line)
        if do_continue:
            continue
        # 4) Expand abbreviations.
        if _TRACE:
            _LOG.debug("# 4) Process abbreviations.")
        line = _process_abbreviations(line)
        # 5) Process enumerated list.
        if _TRACE:
            _LOG.debug("# 5) Process enumerated list.")
        line = _process_enumerated_list(line)
        # 5) Process question.
        if _TRACE:
            _LOG.debug("# 5) Process question.")
        if type_ == "slides":
            do_continue, line = _process_question_to_slides(line)
        else:
            do_continue, line = _process_question_to_markdown(line)
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
                # TODO(gp): Use is_header
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
    out = "\n".join(out_tmp)
    return out


def _add_navigation_slides(
    txt: str, max_level: int, *, sanity_check: bool = False
) -> str:
    """
    Add the navigation slides to the notes.

    :param txt: The notes text.
    :param max_level: The maximum level of headers to consider (e.g., 3
        create a navigation slide for headers of level 1, 2, and 3).
    :param sanity_check: If True, perform sanity checks.
    :return: The notes text with the navigation slides.
    """
    _LOG.debug("\n%s", hprint.frame("Add navigation slides"))
    hdbg.dassert_isinstance(txt, str)
    header_list = hmarkdo.extract_headers_from_markdown(
        txt, max_level, sanity_check=sanity_check
    )
    _LOG.debug("header_list=\n%s", header_list)
    tree = hmarkdo.build_header_tree(header_list)
    _LOG.debug("tree=\n%s", tree)
    out: List[str] = []
    open_modifier = r"**\textcolor{purple}{"
    close_modifier = r"}**"
    for line in txt.split("\n"):
        is_header, level, description = hmarkdo.is_header(line)
        if is_header and level <= max_level:
            _LOG.debug(hprint.to_str("line level description"))
            # Get the navigation string corresponding to the current header.
            nav_str = hmarkdo.selected_navigation_to_str(
                tree,
                level,
                description,
                open_modifier=open_modifier,
                close_modifier=close_modifier,
            )
            _LOG.debug("nav_str=\n%s", nav_str)
            # Replace the header slide with the navigation slide.
            # TODO(gp): We assume the slide level is 4.
            line_tmp = f"#### {description}\n"
            # line_tmp += '<span style="color:blue">\n' + nav_str
            line_tmp += nav_str
            # line_tmp += "\n</span>\n"
            # Add an extra newline to avoid to have the next title adjacent,
            # confusing pandoc.
            line_tmp += "\n"
            out.append(line_tmp)
        else:
            out.append(line)
    txt_out = "\n".join(out)
    return txt_out


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--input", action="store", type=str, required=True)
    parser.add_argument("--output", action="store", type=str, default=None)
    parser.add_argument(
        "--type",
        required=True,
        choices=["pdf", "html", "slides"],
        action="store",
        help="Type of output to generate",
    )
    parser.add_argument(
        "--toc_type",
        action="store",
        default="none",
        choices=["none", "pandoc_native", "navigation"],
    )
    # TODO(gp): Unclear what it doesn.
    parser.add_argument(
        "--qa", action="store_true", default=None, help="The input file is QA"
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    _LOG.info("cmd line=%s", hdbg.get_command_line())
    # Read file.
    txt = hio.from_file(args.input)
    # Apply transformations.
    out = _transform_lines(txt, args.type, is_qa=args.qa)
    # Add TOC, if needed.
    if args.toc_type == "navigation":
        hdbg.dassert_eq(args.type, "slides")
        max_level = 2
        out = _add_navigation_slides(out, max_level, sanity_check=True)
    # Save results.
    hio.to_file(args.output, out)


if __name__ == "__main__":
    _main(_parse())
