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
import helpers.hgit as hgit
import helpers.hlatex as hlatex
import helpers.hmarkdown as hmarkdo
import helpers.hmarkdown_toc as hmartoc
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.htext_protect as htexprot
import dev_scripts_helpers.dockerize.lib_prettier as dshdlipr

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
    # Replace \t with 2 spaces.
    txt = re.sub(r"\t", "  ", txt)
    # Convert bullet points like `• ` to `- `.
    txt = re.sub(r"^\s*•\s+", "- ", txt, flags=re.MULTILINE)
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


def _handle_empty_lines(lines: List[str]) -> List[str]:
    """
    Remove empty lines in specific contexts.

    This function removes:
    1. All empty lines immediately after markdown headers (lines starting
       with #).
    2. All empty lines between a text line and a code block marker (```).

    :param lines: The lines to be processed.
    :return: The lines with empty lines removed in specific contexts.
    """
    _LOG.debug("lines=%s", lines)
    lines_new: List[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        lines_new.append(line)
        # Check if current line is a header.
        if re.match(r"^(#+)\s+(.*)$", line):
            # Skip all following empty lines after the header.
            i += 1
            while i < len(lines) and re.match(r"^\s*$", lines[i]):
                i += 1
            continue
        # Check if current line is non-empty text followed by empty lines
        # and then a code block.
        if line.strip() and not re.match(r"^\s*```", line):
            # Look ahead for empty lines followed by code block.
            j = i + 1
            # Count empty lines.
            empty_line_count = 0
            while j < len(lines) and re.match(r"^\s*$", lines[j]):
                empty_line_count += 1
                j += 1
            # Check if we found a code block after empty lines.
            if (
                empty_line_count > 0
                and j < len(lines)
                and re.match(r"^\s*```", lines[j])
            ):
                # Skip the empty lines.
                i = j
                continue
        i += 1
    hdbg.dassert_isinstance(lines_new, list)
    return lines_new


def _add_blank_lines_between_headers(lines: List[str]) -> List[str]:
    """
    Add blank lines between consecutive markdown headers.

    When two headers (lines starting with #) appear on consecutive lines,
    insert a blank line between them. This improves readability and follows
    markdown best practices.

    :param lines: The lines to be processed.
    :return: The lines with blank lines added between consecutive headers.
    """
    _LOG.debug("lines=%s", lines)
    lines_new: List[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        lines_new.append(line)
        # Check if current line is a header.
        if re.match(r"^(#+)\s+(.*)$", line):
            # Check if next line is also a header.
            if i + 1 < len(lines) and re.match(r"^(#+)\s+(.*)$", lines[i + 1]):
                # Add a blank line between the two consecutive headers.
                lines_new.append("")
        i += 1
    hdbg.dassert_isinstance(lines_new, list)
    return lines_new


def _convert_asterisk_bullets_to_dashes(lines: List[str]) -> List[str]:
    """
    Convert bullet points from asterisk format to dash format.

    Converts lines starting with `* ` or `*\t` (with optional leading
    whitespace) to use `- ` instead. This ensures consistent bullet point
    formatting across the document.

    :param lines: The lines to be processed.
    :return: The lines with asterisk bullets converted to dash bullets.
    """
    _LOG.debug("lines=%s", lines)
    lines_new: List[str] = []
    for line in lines:
        # Convert asterisk bullets to dash bullets.
        # Match: optional whitespace + * + space/tab + content.
        m = re.match(r"^(\s*)\*(\s+.*)$", line)
        if m:
            line = m.group(1) + "-" + m.group(2)
        lines_new.append(line)
    hdbg.dassert_isinstance(lines_new, list)
    return lines_new


def _check_links(in_file_name: str) -> None:
    """
    Check if all URLs in the file are reachable by calling check_links.py.

    This action calls the standalone check_links.py script to validate URL
    reachability. The script performs HTTP/HTTPS requests to verify each link.
    Broken links are reported via logging but do NOT cause the action to fail,
    maintaining the formatting workflow.

    :param in_file_name: The name of the input file to check.
    """
    _LOG.info("Checking links in file: %s", in_file_name)
    # Find the check_links.py script.
    script_path = hgit.find_file_in_git_tree("check_links.py")
    hdbg.dassert_file_exists(script_path)
    _LOG.debug("Found check_links.py at: %s", script_path)
    # Build command.
    cmd = f"{script_path} --in_file {in_file_name}"
    hsystem.system(cmd, abort_on_error=False, suppress_output=False)


def _remove_trailing_periods(lines: List[str]) -> List[str]:
    """
    Remove trailing periods from all lines.

    Periods are removed from the end of any line that ends with one or more
    periods (e.g., "text.", "text..."). Trailing whitespace after the periods
    is also removed.

    This improves consistency in markdown and text formatting where periods
    at the end of list items and standalone lines are often not needed.

    :param lines: The lines to be processed.
    :return: The lines with trailing periods removed.
    """
    _LOG.debug("lines=%s", lines)
    lines_new: List[str] = []
    for line in lines:
        # Remove trailing periods (one or more) from any line.
        line = re.sub(r"\.+\s*$", "", line)
        lines_new.append(line)
    hdbg.dassert_isinstance(lines_new, list)
    return lines_new


def _remove_markdown_formatting(lines: List[str]) -> List[str]:
    """
    Remove markdown formatting from text while preserving content.

    Removes the following markdown syntax:
    - Bold formatting: **text** or __text__ -> text
    - Italic formatting: *text* or _text_ -> text (outside of code blocks)
    - Strikethrough: ~~text~~ -> text
    - Inline code: `text` -> text
    - Links: [text](url) -> text
    - Images: ![alt](url) -> alt
    - Headers: # text -> text

    Code blocks (triple backticks) and their content are preserved unchanged.

    :param lines: The lines to be processed.
    :return: The lines with markdown formatting removed.
    """
    _LOG.debug("lines=%s", lines)
    txt = "\n".join(lines)
    in_code_block = False
    lines_new: List[str] = []
    # Process line by line to preserve code blocks.
    for line in txt.split("\n"):
        # Check for code block markers.
        if re.match(r"^\s*```", line):
            in_code_block = not in_code_block
            lines_new.append(line)
            continue
        # Skip markdown removal inside code blocks.
        if in_code_block:
            lines_new.append(line)
            continue
        # Remove markdown formatting from non-code-block lines.
        # Remove bold: **text** or __text__ -> text.
        line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
        line = re.sub(r"__(.+?)__", r"\1", line)
        # Remove italic: *text* or _text_ -> text (but not _variable_).
        line = re.sub(r"\*(.+?)\*", r"\1", line)
        line = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"\1", line)
        # Remove strikethrough: ~~text~~ -> text.
        line = re.sub(r"~~(.+?)~~", r"\1", line)
        # Remove inline code: `text` -> text.
        line = re.sub(r"`(.+?)`", r"\1", line)
        # Remove images before links: ![alt](url) -> alt.
        # Must be done before link removal to avoid orphaned ! characters.
        line = re.sub(r"!\[(.+?)\]\(.+?\)", r"\1", line)
        # Remove links: [text](url) -> text.
        line = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", line)
        # Remove headers: # text -> text.
        line = re.sub(r"^(#+)\s+(.*)$", r"\2", line)
        lines_new.append(line)
    hdbg.dassert_isinstance(lines_new, list)
    return lines_new


def _remove_code_block_extra_indentation(lines: List[str]) -> List[str]:
    """
    Remove extra indentation from code block lines.

    Prettier may add unwanted indentation to lines inside code blocks,
    especially in indented contexts (lists, nested blocks). This function
    detects and removes that extra indentation while preserving the block's
    base indentation.

    :param lines: The lines to be processed
    :return: Lines with extra indentation removed from code blocks
    """
    _LOG.debug(
        "remove_code_block_extra_indentation: Processing %d lines", len(lines)
    )
    lines_new: List[str] = []
    in_code_block = False
    base_indent = 0
    first_code_line = True
    for line in lines:
        # Handle case where code and opening delimiter are on same line
        # due to inline placeholder restoration (prettier put them together).
        if "\n" in line and "```" in line:
            m = re.match(r"^(\s*```[^\n]*)\n(.*)", line, re.DOTALL)
            if m:
                delim = m.group(1)
                rest = m.group(2)
                base_indent = len(delim) - len(delim.lstrip())
                # Fix indentation in the rest of the content.
                rest_lines = rest.split("\n")
                fixed_lines = []
                for i, rest_line in enumerate(rest_lines):
                    if i == 0 and rest_line.strip():
                        # First code line in the block
                        rest_indent = len(rest_line) - len(rest_line.lstrip())
                        if (
                            rest_indent > base_indent
                            and rest_indent >= base_indent + 2
                        ):
                            # Remove extra indentation.
                            content = rest_line.lstrip()
                            fixed_lines.append(" " * base_indent + content)
                        else:
                            fixed_lines.append(rest_line)
                    else:
                        fixed_lines.append(rest_line)
                line = delim + "\n" + "\n".join(fixed_lines)
        # Track code blocks that span multiple lines.
        if re.match(r"^\s*```", line):
            in_code_block = not in_code_block
            if in_code_block:
                base_indent = len(line) - len(line.lstrip())
                first_code_line = True
            lines_new.append(line)
            continue
        # Fix indentation for code lines on separate lines.
        if (
            in_code_block
            and first_code_line
            and line.strip()
            and not re.match(r"^\s*```", line)
        ):
            line_indent = len(line) - len(line.lstrip())
            if line_indent > base_indent and line_indent >= base_indent + 2:
                # Remove extra 2 spaces of indentation
                content = line.lstrip()
                line = " " * base_indent + content
            first_code_line = False
        elif in_code_block and line.strip():
            first_code_line = False
        lines_new.append(line)
    hdbg.dassert_isinstance(lines_new, list)
    return lines_new


# TODO(gp): Clarify what are the transformations for this.
# TODO(gp): Reuse the code in htext_protect
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
                    _LOG.warning(
                        "%s:%d: Missing syntax tag in ```", in_file_name, i + 1
                    )
        if not in_triple_tick_block:
            # Upper case for `- hello`.
            m = re.match(r"(\s*-\s+)(\S)(.*)", line)
            if m:
                line = m.group(1) + m.group(2).upper() + m.group(3)
            # Upper case for `\d) hello`.
            m = re.match(r"(\s*\d+[\)\.]\s+)(\S)(.*)", line)
            if m:
                line = m.group(1) + m.group(2).upper() + m.group(3)
        lines_new.append(line)
    if in_triple_tick_block:
        _LOG.error("%s: A ``` block was not ending", in_file_name)
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

    Protected content (fenced blocks, comments) is extracted before processing
    and restored afterward to prevent formatters from modifying it.

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
        yaml_frontmatter, lines = hmartoc.extract_yaml_frontmatter(lines)
    # Extract protected content (fenced blocks, comments, math blocks).
    lines, protected_map = htexprot.extract_protected_content(lines, extension)
    # Pre-process text.
    action = "preprocess"
    if _to_execute_action(action, actions):
        lines = _preprocess_txt(lines)
    # Prettify.
    action = "prettier"
    if _to_execute_action(action, actions):
        txt = "\n".join(lines)
        txt = dshdlipr.prettier_on_str(txt, file_type=extension, **kwargs)
        lines = txt.split("\n")
    # Post-process text.
    action = "postprocess"
    if _to_execute_action(action, actions):
        lines = _postprocess_txt(lines, in_file_name)
    # Remove page separators.
    action = "remove_page_separators"
    if _to_execute_action(action, actions):
        lines = _remove_page_separators(lines)
    # Handle empty lines.
    action = "handle_empty_lines"
    if _to_execute_action(action, actions):
        lines = _handle_empty_lines(lines)
    # Add blank lines between consecutive headers.
    action = "add_blank_lines_between_headers"
    if _to_execute_action(action, actions):
        lines = _add_blank_lines_between_headers(lines)
    # Convert asterisk bullets to dashes.
    action = "convert_asterisk_bullets_to_dashes"
    if _to_execute_action(action, actions):
        lines = _convert_asterisk_bullets_to_dashes(lines)
    # Remove trailing periods.
    action = "remove_trailing_periods"
    if _to_execute_action(action, actions):
        lines = _remove_trailing_periods(lines)
    # Remove markdown formatting.
    action = "remove_markdown_formatting"
    if _to_execute_action(action, actions):
        lines = _remove_markdown_formatting(lines)
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
            lines = hmartoc.refresh_toc(lines, **kwargs)
    # Check links.
    action = "check_links"
    if _to_execute_action(action, actions):
        # Only check links for markdown and text files.
        if is_md_file or is_txt_file:
            _check_links(in_file_name)
        else:
            _LOG.debug("Skipping link check for non-text file type")
    # Restore protected content.
    lines = htexprot.restore_protected_content(lines, protected_map)
    # Remove extra indentation from code blocks (after restore).
    action = "remove_code_block_extra_indentation"
    if _to_execute_action(action, actions):
        lines = _remove_code_block_extra_indentation(lines)
    # Reattach YAML front matter if it was extracted.
    lines = hmartoc.reattach_yaml_frontmatter(yaml_frontmatter, lines)
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
    # _remove_code_block_extra_indentation(): remove unwanted indentation
    # added by prettier to code block lines starting with `>`.
    "remove_code_block_extra_indentation",
    # _remove_page_separators(): remove page separator lines (---).
    "remove_page_separators",
    # _handle_empty_lines(): remove empty lines after headers and before code
    # blocks.
    "handle_empty_lines",
    # _add_blank_lines_between_headers(): add blank lines between consecutive
    # headers.
    "add_blank_lines_between_headers",
    # _convert_asterisk_bullets_to_dashes(): convert `* ` bullets to `- `.
    "convert_asterisk_bullets_to_dashes",
    # _remove_trailing_periods(): remove trailing periods from bullet points,
    # headers, and numbered lists.
    "remove_trailing_periods",
    # _remove_markdown_formatting(): remove markdown syntax from text (bold,
    # italic, links, images, etc.).
    "remove_markdown_formatting",
    #
    "frame_chapters",
    "capitalize_header",
    # _refresh_toc(): refresh the table of contents.
    "refresh_toc",
    # _check_links(): check if URLs in the file are reachable.
    "check_links",
]


# By default, exclude refresh_toc, check_links, and remove_markdown_formatting
# actions. Users can explicitly enable them via --action.
_DEFAULT_ACTIONS = [
    action
    for action in _VALID_ACTIONS
    if action
    not in [
        "frame_chapters",
        "refresh_toc",
        "check_links",
        "remove_markdown_formatting",
    ]
]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hparser.add_input_output_args(parser, in_required=False, out_required=False)
    parser.add_argument(
        "--files",
        action="store",
        type=str,
        default=None,
        help="Space or comma-separated list of files to process",
    )
    parser.add_argument(
        "--from_file",
        action="store",
        type=str,
        default=None,
        help="Path to a file containing a list of files to process (one per line)",
    )
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


def _get_files_from_args(args: argparse.Namespace) -> Optional[List[str]]:
    """
    Parse files from --files or --from_file arguments.

    :param args: Parsed arguments.
    :return: List of files to process, or None if neither option is provided.
    """
    if args.files:
        # Support both space and comma-separated lists.
        files = args.files.replace(",", " ").split()
        return files
    elif args.from_file:
        # Read files from the specified file.
        if not os.path.exists(args.from_file):
            _LOG.error("File not found: %s", args.from_file)
            raise FileNotFoundError(f"File not found: {args.from_file}")
        with open(args.from_file, "r") as f:
            files = [line.strip() for line in f if line.strip()]
        return files
    return None


def _process_single_file(
    in_file_name: str,
    out_file_name: str,
    args: argparse.Namespace,
    actions: Optional[List[str]],
) -> None:
    """
    Process a single file.

    :param in_file_name: Input file name.
    :param out_file_name: Output file name.
    :param args: Parsed arguments.
    :param actions: List of actions to perform.
    """
    # If the input is stdin, then user needs to specify the type.
    if in_file_name == "-":
        hdbg.dassert_ne(args.type, "")
    # Read input.
    lines = hparser.from_file(in_file_name)
    _LOG.debug("in_file_name=%s", in_file_name)
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


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hparser.init_logger_for_input_output_transform(args)
    # Print actions (once for all files).
    actions = hparser.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    add_frame = True
    actions_as_str = hparser.actions_to_string(
        actions, _VALID_ACTIONS, add_frame
    )
    _LOG.info("\n%s", actions_as_str)
    # Check if processing multiple files or a single file.
    files = _get_files_from_args(args)
    if files:
        # Process multiple files.
        _LOG.info("Processing %d file(s)", len(files))
        for file_path in files:
            if not os.path.exists(file_path):
                _LOG.error("File not found: %s", file_path)
                continue
            _LOG.info("Processing: %s", file_path)
            _process_single_file(file_path, file_path, args, actions)
    else:
        # Process single file (original behavior).
        in_file_name, out_file_name = hparser.parse_input_output_args(
            args, clear_screen=False
        )
        _process_single_file(in_file_name, out_file_name, args, actions)


if __name__ == "__main__":
    _main(_parser())
