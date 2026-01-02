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
- Remove empty lines in the questions and answers
- Remove all the lines with only spaces
- Add TOC

Import as:

import dev_scripts_helpers.documentation.preprocess_notes as dsdoprno
"""

import argparse
import logging
import re
from typing import List, Optional, Tuple

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hmarkdown as hmarkdo
import helpers.hparser as hparser
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)

# #############################################################################
# Constants
# #############################################################################


_NUM_SPACES = 2

_TRACE = False


_DEFAULT_ACTIONS = None
_VALID_ACTIONS = [
    "process_links",
    "colorize_bullets",
]

# #############################################################################
# Helper functions
# #############################################################################


def _process_abbreviations(in_line: str) -> str:
    r"""
    Transform some abbreviations into LaTeX.

    E.g., - `->` into `$\rightarrow$`

    :param in_line: input line to process
    :return: transformed line with abbreviations replaced
    """
    line = in_line
    for x, y in [
        (r"=>", r"\implies"),
        # TODO(gp): This collides with the arrow in graphviz commands. We
        # should skip this transformation if we are in a graphviz block.
        # (r"->", r"\rightarrow"),
        # (r"-^", r"\uparrow"),
        # (r"-v", r"\downarrow"),
    ]:
        line = re.sub(rf"(\s){re.escape(x)}(\s)", rf"\1${re.escape(y)}$\2", line)
    if line != in_line:
        _LOG.debug("    -> line=%s", line)
    return line


def _process_enumerated_list(in_line: str) -> str:
    """
    Transform enumerated list with parenthesis to `.`.

    E.g., "1) foo bar" is transformed into "1. foo bar".

    :param in_line: input line to process
    :return: transformed line with enumerated lists updated
    """
    line = re.sub(r"^(\s*)(\d+)\)\s", r"\1\2. ", in_line)
    return line


def _process_question_to_markdown(line: str) -> Tuple[bool, str]:
    """
    Transform `* foo bar` into `- **foo bar**`.

    :param line: input line to process
    :return: tuple of (should_continue, transformed_line)
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


def _process_question_to_slides(
    line: str, *, level: int = 4
) -> Tuple[bool, str]:
    """
    Transform `* foo bar` into `#### foo bar`.

    :param line: input line to process
    :param level: header level to use (default: 4)
    :return: tuple of (should_continue, transformed_line)
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


# TODO(gp): Use hmarkdown.process_lines().
# TODO(gp): Add a way to control the list of transformations.
def _transform_lines(
    lines: List[str],
    type_: str,
    is_qa: bool,
    *,
    actions: Optional[List[str]] = None,
) -> List[str]:
    """
    Process the notes to convert them into a format suitable for pandoc.

    :param lines: list of lines of the notes
    :param type_: type of output to generate (e.g., `pdf`, `html`, `slides`)
    :param is_qa: True if the input is a QA file
    :param actions: optional list of actions to perform
    :return: list of processed lines
    """
    _LOG.debug("\n%s", hprint.frame("transform_lines"))
    hdbg.dassert_isinstance(lines, list)
    lines = [line.rstrip("\n") for line in lines]
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
            _LOG.debug("# Process comment block.")
        do_continue, in_skip_block = hmarkdo.process_comment_block(
            line, in_skip_block
        )
        # _LOG.debug("  -> do_continue=%s in_skip_block=%s",
        #   do_continue, in_skip_block)
        if do_continue:
            continue
        # 2) Process code block.
        if _TRACE:
            _LOG.debug("# Process code block.")
        # TODO(gp): Not sure why this is needed. For sure the extra spacing
        # creates a problem with the Python code blocks rendered by pandoc beamer.
        if False:
            do_continue, in_code_block, out_tmp = hmarkdo.process_code_block(
                line, in_code_block, i, lines
            )
            out.extend(out_tmp)
            if do_continue:
                continue
        # 3) Remove single line comment.
        if _TRACE:
            _LOG.debug("# Process single line comment.")
        do_continue = hmarkdo.process_single_line_comment(line)
        if do_continue:
            continue
        # 4) Expand abbreviations.
        if _TRACE:
            _LOG.debug("# Process abbreviations.")
        line = _process_abbreviations(line)
        # 5) Process enumerated list.
        if _TRACE:
            _LOG.debug("# Process enumerated list.")
        line = _process_enumerated_list(line)
        # 6) Process color commands.
        if _TRACE:
            _LOG.debug("# Process color commands.")
        line = hmarkdo.process_color_commands(line)
        # 7) Process question.
        if _TRACE:
            _LOG.debug("# Process question.")
        if type_ == "slides":
            do_continue, line = _process_question_to_slides(line)
        else:
            do_continue, line = _process_question_to_markdown(line)
        if do_continue:
            out.append(line)
            continue
        # 8) Process empty lines in the questions and answers.
        if _TRACE:
            _LOG.debug("# Process empty lines in the questions and answers.")
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
                prev_line_is_verbatim = ((i - 1) > 0) and lines[
                    i - 1
                ].startswith("```")
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
    #
    if type_ == "slides":
        # Colorize links.
        to_execute, actions = hparser.mark_action("process_links", actions)
        # to_execute = False
        if to_execute:
            out = hmarkdo.format_md_links_to_latex_format(out)

        # Colorize bullets in the slides.

        def _colorize_bullets(slide_text: List[str]) -> str:
            """
            Color bullet points in the slide.

            :param slide_text: list of lines in the slide
            :return: colorized slide text
            """
            slide_text = "\n".join(slide_text)
            if not hmarkdo.has_color_command(slide_text):
                text_out = hmarkdo.colorize_bullet_points_in_slide(
                    slide_text, use_abbreviations=False
                )
            else:
                text_out = slide_text
            text_out = text_out.split("\n")
            return text_out

        out = "\n".join(out)
        to_execute, actions = hparser.mark_action("colorize_bullets", actions)
        if to_execute:
            out = hmarkdo.process_slides(out, _colorize_bullets)
        out = out.split("\n")

        # Colorize verbatim.

    # out = out.split("\n")
    out_tmp = []
    for line in out:
        if type_ == "slides":
            do_continue, line = _process_question_to_slides(line)
        else:
            do_continue, line = _process_question_to_markdown(line)
        if do_continue:
            out_tmp.append(line)
            continue
        out_tmp.append(line)
    out = out_tmp
    # c) Clean up.
    _LOG.debug("Clean up")
    hdbg.dassert_isinstance(out, list)
    # Remove all the lines with only spaces.
    out_tmp = []
    for line in out:
        if re.search(r"^\s+$", line):
            line = ""
        out_tmp.append(line)
    # Return result.
    hdbg.dassert_isinstance(out_tmp, list)
    return out_tmp


# TODO(ai): Move to helpers/hmarkdown_toc.py
def _add_navigation_slides(
    lines: List[str], max_level: int, *, sanity_check: bool = False
) -> List[str]:
    """
    Add the navigation slides to the notes.

    :param lines: list of lines of the notes
    :param max_level: maximum level of headers to consider (e.g., 3 creates a
        navigation slide for headers of level 1, 2, and 3)
    :param sanity_check: if True, perform sanity checks
    :return: list of lines with the navigation slides added
    """
    _LOG.debug("\n%s", hprint.frame("Add navigation slides"))
    hdbg.dassert_isinstance(lines, list)
    header_list = hmarkdo.extract_headers_from_markdown(
        lines, max_level, sanity_check=sanity_check
    )
    _LOG.debug("header_list=\n%s", header_list)
    tree = hmarkdo.build_header_tree(header_list)
    _LOG.debug("tree=\n%s", tree)
    out: List[str] = []
    open_modifier = r"_**\textcolor{red}{"
    close_modifier = r"}**_"
    for line in lines:
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
            # line_tmp = f"#### {description}\n"
            line_tmp = "####\n"
            # line_tmp += '<span style="color:blue">\n' + nav_str
            line_tmp += nav_str
            # line_tmp += "\n</span>\n"
            # Add an extra newline to avoid to have the next title adjacent,
            # confusing pandoc.
            line_tmp += "\n"
            out.append(line_tmp)
        else:
            out.append(line)
    hdbg.dassert_isinstance(out, list)
    return out


def _remove_headers(lines: List[str], max_level: int) -> List[str]:
    """
    Remove all markdown headers from the lines that are smaller than level 3.

    :param lines: list of lines to process
    :param max_level: maximum level of headers to consider (default: 3)
    :return: list of lines with relevant headers removed
    """
    _LOG.debug("\n%s", hprint.frame("Remove headers smaller than level 3"))
    hdbg.dassert_isinstance(lines, list)
    out: List[str] = []
    for line in lines:
        is_header_line, level, _ = hmarkdo.is_header(line)
        # Exclude header lines with level 1 or 2 (i.e., smaller than level 3).
        if not (is_header_line and level < max_level):
            out.append(line)
    hdbg.dassert_isinstance(out, list)
    return out


def _preprocess_lines(
    lines: List[str],
    type_: str,
    toc_type: str,
    is_qa: bool,
    *,
    actions: Optional[List[str]] = None,
) -> List[str]:
    """
    Preprocess the lines of the notes.

    :param lines: list of lines of the notes
    :param type_: type of output to generate
    :param toc_type: type of table of contents to add
    :param is_qa: True if the input is a QA file
    :param actions: optional list of actions to perform
    :return: list of preprocessed lines
    """
    hdbg.dassert_isinstance(lines, list)
    # Apply transformations.
    out = _transform_lines(lines, type_, is_qa=is_qa, actions=actions)
    # Add TOC, if needed.
    if toc_type == "navigation":
        hdbg.dassert_eq(type_, "slides")
        max_level = 2
        out = _add_navigation_slides(out, max_level, sanity_check=True)
    elif toc_type == "remove_headers":
        # Remove headers smaller than level 4 so that we leave only the `*`.
        out = _remove_headers(out, max_level=4)
    hdbg.dassert_isinstance(out, list)
    return out


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    """
    Parse command line arguments.

    :return: argument parser
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
        choices=["none", "pandoc_native", "navigation", "remove_headers"],
    )
    # TODO(gp): Unclear what it does.
    parser.add_argument(
        "--qa", action="store_true", default=False, help="The input file is QA"
    )
    hparser.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Execute the main preprocessing logic.

    :param parser: argument parser
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    _LOG.info("cmd line=%s", hdbg.get_command_line())
    # Get the selected actions.
    actions = hparser.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    _LOG.info("Selected actions: %s", actions)
    # Read file.
    txt = hio.from_file(args.input)
    # Process.
    lines = txt.split("\n")
    out = _preprocess_lines(
        lines, args.type, args.toc_type, args.qa, actions=actions
    )
    out = "\n".join(out)
    # Save results.
    hio.to_file(args.output, out)


if __name__ == "__main__":
    _main(_parse())
