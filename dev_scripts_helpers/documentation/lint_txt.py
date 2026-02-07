#!/usr/bin/env python

"""
See instructions at
docs/tools/documentation_toolchain/all.notes_toolchain.how_to_guide.md.
"""

import argparse
import logging
import os
import re
from typing import Any, List, Optional

import helpers.hdbg as hdbg
import helpers.hdockerized_executables as hdocexec
import helpers.hio as hio
import helpers.hlatex as hlatex
import helpers.hmarkdown as hmarkdo
import helpers.hmarkdown_toc as hmarktoc
import helpers.hparser as hparser
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)


# #############################################################################


def _preprocess_txt(lines: List[str]) -> List[str]:
    """
    Preprocess the given text before applying `prettier`.

    E.g.,
    - Handle stars `*` from txt files
    - Remove various artifacts (e.g., from Google Docs)
    - Format math equations
    - Format bullet points
    - Format frames

    :param lines: The lines to be processed.
    :return: The preprocessed lines.
    """
    _LOG.debug("lines=%s", lines)
    # 1) Remove some artifacts when copying from Google Docs.
    # TODO(gp): Extract this into remove_google_docs_artifacts() since it is
    # used in other places.
    txt = "\n".join(lines)
    txt = re.sub(r"“", '"', txt)
    txt = re.sub(r"”", '"', txt)
    txt = re.sub(r"’", "'", txt)
    # Convert
    #   ## **How We Ask for Feedback at Causify**
    # to
    #   ## How We Ask for Feedback at Causify
    txt = re.sub(r"^(#+)\s+\*\*(.*?)\*\*\s*$", r"\1 \2", txt, flags=re.MULTILINE)
    # Remove lines with ---.
    txt = re.sub(r"^---\s*$", "", txt, flags=re.MULTILINE)
    # Collapse repeated lines.
    # txt = re.sub(r"\n{2,}", "\n", txt)
    # Replace … with ...
    txt = re.sub(r"…", "...", txt)
    # Replace \t with 2 spaces
    txt = re.sub(r"\t", "  ", txt)
    txt_new: List[str] = []
    for line in txt.split("\n"):
        # 2) Skip frames for all the type formats.
        if re.match(r"#+ [#\/\-\=]{6,}$", line):
            continue
        # 3) Transforms * and ** bullets to - STAR and - SSTAR (temporary markers).
        line = re.sub(r"^\s*\*\s+", "- STAR", line)
        line = re.sub(r"^\s*\*\*\s+", "- SSTAR", line)
        # 4) Format math equations.
        #   $$E_{in} = \frac{1}{N} \sum_i e(h(\vx_i), y_i)$$
        # into:
        #   $$E_{in}(\vw) = \frac{1}{N} \sum_i \big(
        #   -y_i \log(\Pr(h(\vx) = 1|\vx)) - (1 - y_i) \log(1 - \Pr(h(\vx)=1|\vx))
        #   \big)$$
        # $$
        if re.search(r"^\s*\$\$\s*$", line):
            txt_new.append(line)
            continue
        # $$ ... $$
        m = re.search(r"^(\s*)(\$\$)(.+)(\$\$)\s*$", line)
        if m:
            for i in range(3):
                txt_new.append(m.group(1) + m.group(2 + i))
            continue
        # ... $$
        m = re.search(r"^(\s*)(\$\$)(.+)$", line)
        if m:
            for i in range(2):
                txt_new.append(m.group(1) + m.group(2 + i))
            continue
        # $$ ...
        m = re.search(r"^(\s*)(.*)(\$\$)$", line)
        if m:
            for i in range(2):
                txt_new.append(m.group(1) + m.group(2 + i))
            continue
        txt_new.append(line)
    # 5) Replace multiple empty lines with one, to avoid `prettier` to start
    #    using `*` instead of `-`.
    txt_new_as_str = "\n".join(txt_new)
    txt_new_as_str = re.sub(r"\n\s*\n", "\n\n", txt_new_as_str)
    _LOG.debug("txt_new_as_str=%s", txt_new_as_str)
    txt = txt_new_as_str.split("\n")
    # 6) Remove more than 2 consecutive empty lines.
    hprint.remove_empty_lines(txt_new, mode="no_consecutive_empty_lines")
    hdbg.dassert_isinstance(txt_new, list)
    return txt_new


def _remove_page_separators(lines: List[str]) -> List[str]:
    """
    Remove page separator lines from the given text.

    Page separators are lines that match the pattern `^---\\s*$`.
    Note: YAML front matter should be extracted before calling this function.

    :param lines: The lines to be processed.
    :return: The lines with page separators removed.
    """
    _LOG.debug("lines=%s", lines)
    txt = "\n".join(lines)
    # Remove lines with ---.
    txt = re.sub(r"^---\s*$", "", txt, flags=re.MULTILINE)
    ret = txt.split("\n")
    hdbg.dassert_isinstance(ret, list)
    return ret


# TODO(ai_gp): Move to hmarkdown_toc.py
def _reattach_yaml_frontmatter(
    yaml_frontmatter: List[str], lines: List[str]
) -> List[str]:
    """
    Reattach YAML front matter to the beginning of the content lines.

    :param yaml_frontmatter: The YAML front matter lines to reattach.
    :param lines: The content lines to prepend the front matter to.
    :return: Combined lines with YAML front matter reattached.
    """
    if not yaml_frontmatter:
        return lines
    # Add an empty line after the front matter if the remaining content doesn't
    # start with one.
    if lines and lines[0] != "":
        return yaml_frontmatter + [""] + lines
    return yaml_frontmatter + lines


def _postprocess_txt(lines: List[str], in_file_name: str) -> List[str]:
    """
    Post-process the given text by applying various transformations.

    :param lines: The lines to be processed.
    :param in_file_name: The name of the input file.
    :return: The post-processed lines.
    """
    _LOG.debug("lines=%s", lines)
    txt = "\n".join(lines)
    # Remove empty lines before ```.
    txt = re.sub(r"^\s*\n(\s*```)$", r"\1", txt, count=0, flags=re.MULTILINE)
    # Remove empty lines before higher level bullets, but not chapters.
    txt = re.sub(r"^\s*\n(\s+-\s+.*)$", r"\1", txt, count=0, flags=re.MULTILINE)
    # True if one is in inside a ``` .... ``` block.
    in_triple_tick_block: bool = False
    lines_new: List[str] = []
    for i, line in enumerate(txt.split("\n")):
        # Undo the transformation `* -> STAR`.
        line = re.sub(r"^\-(\s*)STAR", r"*\1", line, count=0)
        line = re.sub(r"^\-(\s*)SSTAR", r"**\1", line, count=0)
        # Remove empty lines.
        line = re.sub(
            r"^\s*\n(\s*\$\$)", r"\1", line, count=0, flags=re.MULTILINE
        )
        # Handle ``` block.
        m = re.match(r"^\s*```(.*)\s*$", line)
        if m:
            in_triple_tick_block = not in_triple_tick_block
            if in_triple_tick_block:
                tag = m.group(1)
                if not tag:
                    print(f"{in_file_name}:{i + 1}: Missing syntax tag in ```")
        if not in_triple_tick_block:
            # Upper case for `- hello`.
            m = re.match(r"(\s*-\s+)(\S)(.*)", line)
            if m:
                line = m.group(1) + m.group(2).upper() + m.group(3)
            # Upper case for `\d) hello`.
            m = re.match(r"(\s*\d+[\)\.]\s+)(\S)(.*)", line)
            if m:
                line = m.group(1) + m.group(2).upper() + m.group(3)
        #
        lines_new.append(line)
    if in_triple_tick_block:
        print(f"{in_file_name}:{1}: A ``` block was not ending")
    hdbg.dassert_isinstance(lines_new, list)
    return lines_new


# #############################################################################
# Perform all actions.
# #############################################################################


def _to_execute_action(action: str, actions: Optional[List[str]] = None) -> bool:
    to_execute = actions is None or action in actions
    if not to_execute:
        _LOG.debug("Skipping %s", action)
    return to_execute


def _perform_actions(
    lines: List[str],
    in_file_name: str,
    *,
    actions: Optional[List[str]] = None,
    **kwargs: Any,
) -> List[str]:
    """
    Process the given text by applying a series of actions.

    :param lines: The lines to be processed.
    :param in_file_name: The name of the input file.
    :param actions: A list of actions to be performed on the text. If
        None, all default actions are performed.
    :param kwargs: Additional keyword arguments to be passed to the
        actions.
    :return: The processed lines.
    """
    hdbg.dassert_isinstance(lines, list)
    # Get the file type.
    is_md_file = in_file_name.endswith(".md")
    is_tex_file = in_file_name.endswith(".tex")
    is_txt_file = in_file_name.endswith(".txt")
    hdbg.dassert_eq(
        is_md_file + is_tex_file + is_txt_file, 1, msg="Invalid file type"
    )
    #
    extension = os.path.splitext(in_file_name)[1]
    # Remove the . from the extenstion (e.g., ".txt").
    hdbg.dassert(extension.startswith("."), "Invalid extension='%s'", extension)
    extension = extension[1:]
    # Extract YAML front matter if present (only for markdown files).
    yaml_frontmatter: List[str] = []
    if is_md_file:
        yaml_frontmatter, lines = hmarktoc.extract_yaml_frontmatter(lines)
    # Pre-process text.
    action = "preprocess"
    if _to_execute_action(action, actions):
        lines = _preprocess_txt(lines)
    # Prettify.
    action = "prettier"
    if _to_execute_action(action, actions):
        txt = "\n".join(lines)
        txt = hdocexec.prettier_on_str(txt, file_type=extension, **kwargs)
        lines = txt.split("\n")
    # Post-process text.
    action = "postprocess"
    if _to_execute_action(action, actions):
        lines = _postprocess_txt(lines, in_file_name)
    # Remove page separators.
    action = "remove_page_separators"
    if _to_execute_action(action, actions):
        lines = _remove_page_separators(lines)
    # Frame chapters.
    action = "frame_chapters"
    if _to_execute_action(action, actions):
        if is_txt_file:
            lines = hmarkdo.frame_chapters(lines)
        elif is_tex_file:
            lines = hlatex.frame_sections(lines)
        elif is_md_file:
            # For markdown files, we don't use the frame since it's not rendered
            # correctly.
            pass
        else:
            raise ValueError("Invalid format")
    # Improve header and slide titles.
    action = "capitalize_header"
    if _to_execute_action(action, actions):
        lines = hmarkdo.capitalize_header(lines)
    # Refresh table of content.
    action = "refresh_toc"
    if _to_execute_action(action, actions):
        if is_md_file:
            lines = hmarktoc.refresh_toc(lines, **kwargs)
    # Reattach YAML front matter if it was extracted.
    lines = _reattach_yaml_frontmatter(yaml_frontmatter, lines)
    return lines


# #############################################################################

_VALID_ACTIONS = [
    # _preprocess(): preprocess the given text before applying `prettier`.
    "preprocess",
    # _prettier(): prettify the given text with `prettier` for both latex and
    # markdown.
    "prettier",
    # _postprocess(): post-process the given text.
    "postprocess",
    # _remove_page_separators(): remove page separator lines (---).
    "remove_page_separators",
    #
    "frame_chapters",
    "capitalize_header",
    # _refresh_toc(): refresh the table of contents.
    "refresh_toc",
]


# By default, exclude refresh_toc action. Users can explicitly enable it via
# --action.
_DEFAULT_ACTIONS = [
    action for action in _VALID_ACTIONS if action != "refresh_toc"
]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hparser.add_input_output_args(parser)
    parser.add_argument(
        "--type",
        action="store",
        type=str,
        default="",
        help="The type of the input file, e.g., `md`, `tex`, `txt`",
    )
    parser.add_argument(
        "-w",
        "--print-width",
        action="store",
        type=int,
        default=None,
        help="The maximum line width for the formatted text.",
    )
    parser.add_argument(
        "--use_dockerized_prettier",
        dest="use_dockerized_prettier",
        action="store_true",
        default=True,
    )
    parser.add_argument(
        "--no_use_dockerized_prettier",
        dest="use_dockerized_prettier",
        action="store_false",
    )
    parser.add_argument(
        "--use_dockerized_markdown_toc",
        dest="use_dockerized_markdown_toc",
        action="store_true",
        default=True,
    )
    parser.add_argument(
        "--no_use_dockerized_markdown_toc",
        dest="use_dockerized_markdown_toc",
        action="store_false",
    )
    hparser.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    hparser.add_dockerized_script_arg(parser)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hparser.init_logger_for_input_output_transform(args)
    #
    in_file_name, out_file_name = hparser.parse_input_output_args(
        args, clear_screen=False
    )
    # If the input is stdin, then user needs to specify the type.
    if in_file_name == "-":
        hdbg.dassert_ne(args.type, "")
    # Read input.
    lines = hparser.from_file(in_file_name)
    _LOG.debug("in_file_name=%s", in_file_name)
    # Print actions.
    actions = hparser.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    add_frame = True
    actions_as_str = hparser.actions_to_string(
        actions, _VALID_ACTIONS, add_frame
    )
    _LOG.info("\n%s", actions_as_str)
    # Process.
    out_lines = _perform_actions(
        lines,
        in_file_name,
        actions=actions,
        print_width=args.print_width,
        use_dockerized_prettier=args.use_dockerized_prettier,
        use_dockerized_markdown_toc=args.use_dockerized_markdown_toc,
    )
    # Write output.
    hparser.to_file(out_lines, out_file_name)


if __name__ == "__main__":
    _main(_parser())
