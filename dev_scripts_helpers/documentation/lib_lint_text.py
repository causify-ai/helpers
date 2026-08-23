"""
Core library for linting and formatting text files.

Provides transformation functions and file processing logic used by lint_text.py.

Import as:

import dev_scripts_helpers.documentation.lib_lint_text as dshdllite
"""

import argparse
import logging
import os
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

import helpers.hdbg as hdbg
import helpers.hselect_input_output as hseinout
import helpers.hgit as hgit
import helpers.hlatex as hlatex
import helpers.hmarkdown as hmarkdo
import helpers.hmarkdown_formatting as hmarform
import helpers.hmarkdown_toc as hmartoc
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.htext_protect as htexprot
import dev_scripts_helpers.dockerize.lib_prettier as dshdlipr

_LOG = logging.getLogger(__name__)


# #############################################################################


_SMD_LINE_COMMENT_PLACEHOLDER_RE = re.compile(
    r"^<!--<<<PROTECTED_LINE_COMMENT_\d+>>>-->$"
)


def _add_blank_line_before_smd_comment_placeholder(
    lines: List[str],
) -> List[str]:
    """
    Add a blank line before a `//`-comment placeholder run that directly
    follows non-comment content.

    `htexprot.extract_protected_content()` disguises `.smd` `//` comments as
    an HTML comment (`<!--<<<PROTECTED_LINE_COMMENT_NNN>>>-->`) so `beautify`
    (a markdown-aware formatter) never merges/reflows them. Per CommonMark,
    an HTML comment block can interrupt a paragraph without a blank line
    before it, and empirically `beautify`'s formatter then fails to reflow
    (re-indent) the *preceding* wrapped list-item continuation line when the
    comment placeholder immediately follows it with no blank line, e.g.:
    ```
    - @Definition@: some long text that wraps onto a
    second line              <- stays unindented, should be `  second line`
    // a trailing comment right after the bullet, no blank line
    ```
    Forcing a blank line in front of the *first* placeholder of a comment
    run (not before every placeholder, so consecutive `//` lines stay
    adjacent) avoids this. This is deliberately not done inside
    `extract_protected_content()`/`restore_protected_content()` themselves,
    since those two are an exact roundtrip pair elsewhere in the codebase;
    this is a `lint_text.py`-specific workaround for `beautify`.

    :param lines: The lines to be processed.
    :return: The lines with a blank line added before each comment-run
        start.
    """
    _LOG.debug("lines=%s", lines)
    lines_new: List[str] = []
    for line in lines:
        if _SMD_LINE_COMMENT_PLACEHOLDER_RE.match(line):
            prev_line = lines_new[-1] if lines_new else ""
            if prev_line.strip() and not _SMD_LINE_COMMENT_PLACEHOLDER_RE.match(
                prev_line
            ):
                lines_new.append("")
        lines_new.append(line)
    hdbg.dassert_isinstance(lines_new, list)
    return lines_new


def _preprocess_txt(
    lines: List[str], extension: str
) -> Tuple[List[str], Dict[str, Any]]:
    """
    Preprocess the given text before applying `beautify`.

    Extracts protected content (fenced blocks, comments, math blocks) before
    processing and returns both the processed lines and the protected map for
    later restoration.

    E.g.,
    - Extract protected content (fenced blocks, comments, math blocks)
    - For `.smd` files, add a blank line before a `//`-comment placeholder
      run that directly follows content, working around a `beautify`
      reflow bug (see `_add_blank_line_before_smd_comment_placeholder()`)
    - Handle stars `*` from txt files
    - Remove various artifacts (e.g., from Google Docs)
    - Format math equations
    - Format bullet points
    - Format frames

    :param lines: The lines to be processed.
    :param extension: The file extension (md, tex, txt, smd).
    :return: Tuple of (preprocessed lines, protected content map).
    """
    _LOG.debug("lines=%s", lines)
    # 0) Extract protected content (fenced blocks, comments, math blocks).
    lines, protected_map = htexprot.extract_protected_content(lines, extension)
    if extension == "smd":
        # Work around `beautify` failing to reflow a wrapped list-item line
        # that's immediately followed (no blank line) by a `//`-comment
        # placeholder; see the function's docstring for why.
        lines = _add_blank_line_before_smd_comment_placeholder(lines)
    # 1) Remove some artifacts when copying from Google Docs.
    # TODO(gp): Extract this into remove_google_docs_artifacts() since it is
    # used in other places.
    txt = "\n".join(lines)
    txt = re.sub(r"“", '"', txt)
    txt = re.sub(r"”", '"', txt)
    txt = re.sub(r"[‘’]", "'", txt)
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
    # 5) Replace multiple empty lines with one, to avoid `beautify` to start
    #    using `*` instead of `-`.
    txt_new_as_str = "\n".join(txt_new)
    txt_new_as_str = re.sub(r"\n\s*\n", "\n\n", txt_new_as_str)
    _LOG.debug("txt_new_as_str=%s", txt_new_as_str)
    txt = txt_new_as_str.split("\n")
    # 6) Remove more than 2 consecutive empty lines.
    hprint.remove_empty_lines(txt_new, mode="no_consecutive_empty_lines")
    hdbg.dassert_isinstance(txt_new, list)
    return txt_new, protected_map


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


def _convert_asterisk_bullets_to_dashes(
    lines: List[str], *, is_smd_file: bool = False
) -> List[str]:
    """
    Convert bullet points from asterisk format to dash format.

    Converts lines starting with `* ` or `*\t` (with optional leading
    whitespace) to use `- ` instead. This ensures consistent bullet point
    formatting across the document.

    Lines that end with a closing `*` (optionally followed by trailing
    whitespace) are skipped, since these are `*emphasis*` spans (e.g.,
    `* Some Title *`) rather than bullet points.

    In `.smd` (slide markdown) files, a top-level `* <slide title>` line
    (i.e., no leading whitespace) is a slide-title marker, not a bullet
    point (see the `Slide Structure` convention: every real bullet starts
    with `- `, while a bare `*` at the start of a line introduces a new
    slide). Such lines are left unchanged when `is_smd_file` is True.

    :param lines: The lines to be processed.
    :param is_smd_file: whether `lines` come from a `.smd` slide file, in
        which case top-level `* <title>` lines are slide titles and are
        not converted.
    :return: The lines with asterisk bullets converted to dash bullets.
    """
    _LOG.debug("lines=%s", lines)
    lines_new: List[str] = []
    for line in lines:
        # Convert asterisk bullets to dash bullets.
        # Match: optional whitespace + * + space/tab + content.
        m = re.match(r"^(\s*)\*(\s+.*)$", line)
        # Skip lines that end with a closing `*` (e.g., `*emphasis*`), since
        # those are not bullet points.
        is_emphasis = re.search(r"\*\s*$", line) is not None
        # Skip top-level `* <slide title>` lines in `.smd` files, since
        # those are slide-title markers, not bullet points.
        is_slide_title = is_smd_file and m is not None and not m.group(1)
        if m and not is_emphasis and not is_slide_title:
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

    Beautify may add unwanted indentation to lines inside code blocks,
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
        # due to inline placeholder restoration (beautify put them together).
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


def _replace_em_dash_with_colon(lines: List[str]) -> List[str]:
    """
    Replace em dash followed by a space with a colon.

    When a non-whitespace character is followed by ` — ` (em dash surrounded
    by spaces), the em dash is replaced with `: ` (colon space e.g., for list
    items).

    Example: `- foo — bar` -> `- foo: bar`

    :param lines: The lines to be processed.
    :return: The lines with em dashes replaced by colons.
    """
    _LOG.debug("lines=%s", lines)
    lines_new: List[str] = []
    for line in lines:
        # Replace em dash with colon when preceded by a non-whitespace char.
        line = re.sub(r"(\S)\s*—\s+", r"\1: ", line)
        lines_new.append(line)
    hdbg.dassert_isinstance(lines_new, list)
    return lines_new


# #############################################################################


def _is_smd_fence_line(line: str) -> bool:
    """
    Check if a line is a pandoc fenced div marker (e.g., `::: columns`).

    :param line: The line to check.
    :return: True if the line starts with at least 3 colons.
    """
    return bool(re.match(r"^\s*:{3,}", line))


def _is_smd_slide_title_line(line: str) -> bool:
    """
    Check if a line is a top-level `* <slide title>` marker.

    A top-level `*` line (i.e., no leading whitespace) followed by a space
    and text is a slide-title marker in `.smd` files, not a bullet point
    (see `_convert_asterisk_bullets_to_dashes`).

    :param line: The line to check.
    :return: True if the line is a top-level slide-title marker.
    """
    return bool(re.match(r"^\*\s+.*$", line))


def _is_smd_header_or_title_line(line: str) -> bool:
    """
    Check if a line is a markdown header or a top-level slide-title marker.

    :param line: The line to check.
    :return: True if the line is a header (`#`, `##`, ...) or a slide-title
        marker (`* <title>`).
    """
    return _is_md_header_line(line) or _is_smd_slide_title_line(line)


def _is_md_header_line(line: str) -> bool:
    """
    Check if a line is a markdown header (`#`, `##`, ...).

    :param line: The line to check.
    :return: True if the line is a header.
    """
    return bool(re.match(r"^#+\s+", line))


def _is_md_fence_line(line: str) -> bool:
    """
    Check if a line is a markdown code-fence delimiter or the placeholder
    standing in for the (protected) content between such delimiters.

    `htexprot.extract_protected_content()` collapses the content between a
    fenced code block's opening and closing ` ``` ` delimiters into a single
    `<<<PROTECTED_BLOCK_NNN>>>` placeholder line sitting directly between
    them. Treating that placeholder as a "fence" line too keeps it glued to
    its delimiters (so no blank line ever gets forced inside a code block),
    the same way consecutive `:::` fence lines stay glued for `.smd` files.

    :param line: The line to check.
    :return: True if the line is a code-fence delimiter or a protected
        fenced-block placeholder.
    """
    if re.match(r"^\s*```", line):
        return True
    return bool(re.match(r"^\s*<<<PROTECTED_BLOCK_\d+>>>\s*$", line))


def _format_header_spacing(
    lines: List[str], is_header_or_title_line: Callable[[str], bool]
) -> List[str]:
    """
    Normalize blank lines around headers (and, for `.smd` files, slide-title
    markers).

    Ensures there is exactly one blank line immediately before and after
    every header (`#`, `##`, ...) and every top-level slide-title marker
    (`* <title>`), including when two such lines are directly adjacent to
    each other (e.g., a header followed by another header, or by a slide
    title).

    E.g.,
    ```
    # Blockchain Consensus Foundations
    ## Agreement Without a Trusted Party
    * Why Distributed Systems Need Consensus
    ```
    ->
    ```
    # Blockchain Consensus Foundations

    ## Agreement Without a Trusted Party

    * Why Distributed Systems Need Consensus
    ```

    :param lines: The lines to be processed.
    :param is_header_or_title_line: predicate marking header (and, for
        `.smd`, slide-title) lines.
    :return: The lines with normalized spacing around headers and slide
        titles.
    """
    _LOG.debug("lines=%s", lines)
    # 1) Drop every blank line that borders a header/title line (on either
    # side): it will be re-inserted (at most once) in the next step.
    no_blank_near_special: List[str] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if line.strip() == "":
            prev_line = no_blank_near_special[-1] if no_blank_near_special else ""
            # Look past the run of blank lines to find the next real line.
            j = i
            while j < n and lines[j].strip() == "":
                j += 1
            next_line = lines[j] if j < n else ""
            if is_header_or_title_line(prev_line) or is_header_or_title_line(
                next_line
            ):
                i = j
                continue
        no_blank_near_special.append(line)
        i += 1
    # 2) Re-insert exactly one blank line at every boundary touching a
    # header/title line, on either side. Unlike fenced div blocks, two
    # consecutive header/title lines still get a blank between them (they
    # don't stay glued together).
    lines_new: List[str] = []
    for idx, line in enumerate(no_blank_near_special):
        if idx > 0:
            prev_line = no_blank_near_special[idx - 1]
            if is_header_or_title_line(prev_line) or is_header_or_title_line(
                line
            ):
                lines_new.append("")
        lines_new.append(line)
    hdbg.dassert_isinstance(lines_new, list)
    return lines_new


def _format_block_spacing(
    lines: List[str], is_block_line: Callable[[str], bool]
) -> List[str]:
    """
    Normalize blank lines around a run of "block" lines matched by
    `is_block_line` (e.g., `::: columns` fence markers for `.smd`, ` ``` `
    code fences for `.md`, or comment-placeholder lines).

    - Consecutive block lines (e.g., an opening `:::: {.column ...}` right
      after a `::: columns`, two closing fences in a row, or two `//`
      comment-placeholder lines in the same block) are kept adjacent, with
      no blank line between them.
    - Everywhere a block line borders a chunk of content that doesn't match
      `is_block_line`, exactly one blank line is enforced.

    :param lines: The lines to be processed.
    :param is_block_line: predicate marking the "block" lines that should
        stay glued to each other and get exactly one blank line at their
        boundary with everything else (e.g., `:::` markers for `.smd`,
        code-fence delimiters/placeholders for `.md`, comment placeholders).
    :return: The lines with normalized spacing around the matched blocks.
    """
    _LOG.debug("lines=%s", lines)
    # 1) Drop every blank line that borders a block line (on either side): it
    # will be re-inserted (at most once) in the next step.
    no_blank_near_block: List[str] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if line.strip() == "":
            prev_line = no_blank_near_block[-1] if no_blank_near_block else ""
            # Look past the run of blank lines to find the next real line.
            j = i
            while j < n and lines[j].strip() == "":
                j += 1
            next_line = lines[j] if j < n else ""
            if is_block_line(prev_line) or is_block_line(next_line):
                i = j
                continue
        no_blank_near_block.append(line)
        i += 1
    # 2) Re-insert exactly one blank line wherever a block line borders a
    # chunk of content that isn't one (but not between two consecutive block
    # lines).
    lines_new: List[str] = []
    for idx, line in enumerate(no_blank_near_block):
        if idx > 0:
            prev_line = no_blank_near_block[idx - 1]
            if is_block_line(prev_line) != is_block_line(line):
                lines_new.append("")
        lines_new.append(line)
    hdbg.dassert_isinstance(lines_new, list)
    return lines_new


_COMMENT_PLACEHOLDER_RE = re.compile(
    r"^(?:<<<PROTECTED_COMMENT_\d+>>>|<!--<<<PROTECTED_LINE_COMMENT_\d+>>>-->)$"
)

# Sentinel standing in for the blank line separating two distinct
# comment-placeholder blocks, so it survives `_rebuild_blank_lines()`'s
# blanket strip; see `_protect_inter_comment_blank_lines()`.
_COMMENT_BLOCK_BLANK_SENTINEL = "<<<COMMENT_BLOCK_BLANK_SENTINEL>>>"


def _is_comment_placeholder_line(line: str) -> bool:
    """
    Check if a line is a placeholder standing in for a protected comment: an
    HTML comment (`.md` and `.smd`) or a `//` line comment (`.smd`).

    :param line: The line to check.
    :return: True if the line is a comment placeholder.
    """
    return bool(_COMMENT_PLACEHOLDER_RE.match(line.strip()))


def _is_comment_placeholder_or_sentinel_line(line: str) -> bool:
    """
    Check if a line is a comment placeholder, or the sentinel
    `_protect_inter_comment_blank_lines()` inserts for the blank line
    between two such blocks.

    The sentinel must be treated the same as a comment placeholder here: it
    stands in for the single blank line that already separates two comment
    blocks, so `_format_block_spacing()` must keep it glued to the blocks on
    either side (not force an extra blank line around it too).

    :param line: The line to check.
    :return: True if the line is a comment placeholder or the blank-line
        sentinel.
    """
    return (
        _is_comment_placeholder_line(line)
        or line.strip() == _COMMENT_BLOCK_BLANK_SENTINEL
    )


def _protect_inter_comment_blank_lines(lines: List[str]) -> List[str]:
    """
    Replace the blank-line run separating two distinct comment-placeholder
    blocks with a single sentinel line.

    `_rebuild_blank_lines()` rebuilds blank-line spacing from scratch by
    first stripping every blank line, then re-deriving only the ones it
    recognizes (bullets, fences, headers). Once that strip runs, two comment
    blocks that were originally separated only by blank line(s) become
    textually indistinguishable from a single contiguous block of
    comment-placeholder lines, and get merged. Swapping that blank-line run
    for a sentinel (a non-blank line, so the strip leaves it alone) before
    the strip runs preserves the boundary between the two blocks; the
    sentinel is swapped back for a single blank line at the end of
    `_rebuild_blank_lines()`.

    :param lines: The lines to be processed.
    :return: The lines with inter-comment-block blank-line runs replaced by
        the sentinel.
    """
    _LOG.debug("lines=%s", lines)
    lines_new: List[str] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if line.strip() == "":
            prev_line = lines_new[-1] if lines_new else ""
            # Look past the run of blank lines to find the next real line.
            j = i
            while j < n and lines[j].strip() == "":
                j += 1
            next_line = lines[j] if j < n else ""
            if _is_comment_placeholder_line(
                prev_line
            ) and _is_comment_placeholder_line(next_line):
                lines_new.append(_COMMENT_BLOCK_BLANK_SENTINEL)
                i = j
                continue
        lines_new.append(line)
        i += 1
    hdbg.dassert_isinstance(lines_new, list)
    return lines_new


def _rebuild_blank_lines(
    lines: List[str],
    *,
    is_fence_line: Callable[[str], bool],
    is_header_or_title_line: Callable[[str], bool],
) -> List[str]:
    """
    Rebuild blank-line spacing from scratch.

    Strip every blank line and then re-derive exactly the ones needed:
    - one blank line between blocks of level-1 bullets (nested bullets stay
      glued to their parent, with no blank line)
    - one blank line around fenced blocks
    - one blank line around blocks of comment placeholders, so two distinct
      comment blocks never get merged into one
    - exactly one blank line before and after every header (and, for `.smd`
      files, every slide-title marker).

    This is the shared "standard" blank-line rule applied to both `.smd` and
    `.md` files.

    :param lines: The lines to be processed.
    :param is_fence_line: predicate marking fence lines (see
        `_format_block_spacing()`).
    :param is_header_or_title_line: predicate marking header (and, for
        `.smd`, slide-title) lines (see `_format_header_spacing()`).
    :return: The lines with rebuilt blank-line spacing.
    """
    _LOG.debug("lines=%s", lines)
    # Protect the blank line separating two distinct comment-placeholder
    # blocks before the blanket strip below (see
    # `_protect_inter_comment_blank_lines()` for why).
    lines = _protect_inter_comment_blank_lines(lines)
    # Strip every blank line, then re-derive exactly the ones needed.
    lines_new = [line for line in lines if line.strip()]
    # Add a blank line before every level-1 bullet (i.e., between blocks of
    # level-1 bullets), leaving nested bullets glued to their parent.
    lines_new = hmarform.format_first_level_bullets(lines_new)
    # Normalize the blank lines around fenced blocks. This only touches
    # blanks bordering a fence line, so it can't undo the bullet spacing just
    # added, and it fixes spacing where a fence sits next to a bullet with no
    # blank line yet.
    lines_new = _format_block_spacing(lines_new, is_fence_line)
    # Normalize the blank lines around blocks of comment placeholders the
    # same way: exactly one blank line wherever such a block borders
    # anything else, while a run of placeholder lines (and the sentinel
    # protecting the blank line between two originally-separate blocks)
    # stays glued together.
    lines_new = _format_block_spacing(
        lines_new, _is_comment_placeholder_or_sentinel_line
    )
    # Ensure exactly one blank line before and after every header (and slide
    # title). Runs last: like `_format_block_spacing()`, it drops and
    # re-derives the blanks it cares about, so it correctly cleans up after
    # (and is unaffected by) whatever the bullet/fence/comment steps above
    # did.
    lines_new = _format_header_spacing(lines_new, is_header_or_title_line)
    # Swap the sentinel back for the single blank line it stands for.
    lines_new = [
        "" if line == _COMMENT_BLOCK_BLANK_SENTINEL else line
        for line in lines_new
    ]
    hdbg.dassert_isinstance(lines_new, list)
    return lines_new


# #############################################################################

# TODO(ai_gp): Removing trailing white spaces and empty lines at the beginning
# and at the end is a transform step by itself for all the formats. This will
# change `postprocess` behavior for `md`/`tex`/`txt` files too (e.g.,
# markdown's trailing double-space hard line break)


def _smd_format(lines: List[str]) -> List[str]:
    """
    Apply "smd" (slide markdown) specific formatting.

    - Remove white spaces before the newline (i.e., trailing white spaces).
    - Remove the `:` after a lone `@tag@` on its own line
      - E.g., `@Problem@:` -> `@Problem@`
    - Capitalize the first letter of the text following a `:`, skipping over
      leading markdown emphasis markers (`*`, `_`)
      - E.g., `- _Explicit assumptions_: instead` ->
        `- _Explicit assumptions_: Instead`
      - E.g., `@Definition@: **models**` -> `@Definition@: **Models**`
    - Make sure there is exactly one empty line between a fenced div block
      (a line starting with at least 3 `:`, e.g., `::: columns`) and the
      surrounding chunk of code, while consecutive fence lines stay adjacent
    - Rebuild blank-line spacing from scratch: strip every blank line and then
      re-derive exactly the ones smd formatting needs, i.e., one blank line
      between blocks of level-1 bullets (nested bullets stay glued to their
      parent, with no blank line), around fenced div blocks, and exactly one
      blank line before and after every header (`#`, `##`, ...) and every
      slide-title marker (`* <title>`)

    :param lines: The lines to be processed.
    :return: The lines formatted according to the smd conventions.
    """
    _LOG.debug("lines=%s", lines)
    lines_new: List[str] = []
    for line in lines:
        # Remove white spaces before the newline.
        line = line.rstrip()
        # Fenced div marker lines (e.g., `::: columns`) are structural: don't
        # apply the tag-colon or capitalization rules to their `:::`.
        if not _is_smd_fence_line(line):
            # Remove the `:` after a lone `@tag@` (e.g., `@Problem@:` ->
            # `@Problem@`).
            line = re.sub(r"^(\s*(?:-\s+)?@[^@]+@):\s*$", r"\1", line)
            # Capitalize the first letter after a `:`, skipping over leading
            # markdown emphasis markers so `**models**` becomes `**Models**`.
            line = re.sub(
                r"(:\s+)([*_]*)([a-zA-Z])",
                lambda m: m.group(1) + m.group(2) + m.group(3).upper(),
                line,
            )
        lines_new.append(line)
    # Rebuild all blank-line spacing from scratch, instead of reconciling
    # separate add/remove rules that can drift out of sync. This is the same
    # "standard" rebuild `_md_format()` applies to `.md` files, parametrized
    # here with the `.smd`-specific fence (`:::`) and header/slide-title
    # predicates.
    lines_new = _rebuild_blank_lines(
        lines_new,
        is_fence_line=_is_smd_fence_line,
        is_header_or_title_line=_is_smd_header_or_title_line,
    )
    hdbg.dassert_isinstance(lines_new, list)
    return lines_new


def _md_format(lines: List[str]) -> List[str]:
    """
    Apply the same blank-line rebuild used for `.smd` files to `.md` files.

    This is the standard blank-line rule shared across file types: rebuild
    blank-line spacing from scratch, i.e., strip every blank line and then
    re-derive exactly the ones needed, one blank line between blocks of
    level-1 bullets (nested bullets stay glued to their parent, with no
    blank line), one blank line around fenced code blocks (` ``` `), and
    exactly one blank line before and after every header (`#`, `##`, ...).

    Unlike `_smd_format()`, this doesn't touch anything else (no `@tag@`
    colon removal, no post-colon capitalization): those are `.smd`-only
    semantic-markup conventions that don't apply to plain markdown.

    :param lines: The lines to be processed.
    :return: The lines with rebuilt blank-line spacing.
    """
    _LOG.debug("lines=%s", lines)
    lines_new = _rebuild_blank_lines(
        lines,
        is_fence_line=_is_md_fence_line,
        is_header_or_title_line=_is_md_header_line,
    )
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


# This is different than `hselacti.mark_action()` since it only checks membership
# without mutating the state.
def _to_execute_action(action: str, actions: Optional[List[str]]) -> bool:
    to_execute = actions is None or action in actions
    if not to_execute:
        _LOG.debug("Skipping %s", action)
    return to_execute


VALID_ACTIONS = {
    # Preprocess text before formatting: normalize artifacts, handle math equations.
    # - Convert Google Docs smart quotes to ASCII
    # - Protect math blocks (`$$...$$`)
    # - Normalize bullet points and whitespace
    "preprocess": ["md", "tex", "txt", "smd"],
    # Apply prettier/mdformat formatting.
    # - Wrap lines to specified width
    # - Reformat bullet lists and code blocks
    # - Normalize markdown/text syntax
    "beautify": ["md", "tex", "txt", "smd"],
    # Post-process formatted text: restore protected content, capitalize lists.
    # - Restore starred bullets `*` -> `*`
    # - Capitalize first letter of bullet points
    # - Remove empty lines around code blocks
    "postprocess": ["md", "tex", "txt", "smd"],
    # Remove extra indentation added by beautify inside code blocks.
    # - Fixes over-indented code lines
    "remove_code_block_extra_indentation": ["md", "tex", "txt", "smd"],
    # Remove page separator lines (`---`).
    # - Cleans up document structure
    "remove_page_separators": ["md", "tex", "txt", "smd"],
    # Remove empty lines after headers and before code blocks.
    # - `# Header\n\ntext` -> `# Header\ntext`
    # - `text\n\n\`\`\`` -> `text\n\`\`\``
    "handle_empty_lines": ["md", "smd"],
    # Add blank lines between consecutive markdown headers.
    # - `# H1\n## H2` -> `# H1\n\n## H2`
    "add_blank_lines_between_headers": ["md", "smd"],
    # Convert asterisk bullets (`*`) to dash bullets (`-`).
    # - `* item` -> `- item`
    # - `* nested` -> `- nested`
    "convert_asterisk_bullets_to_dashes": ["md", "txt", "smd"],
    # Remove trailing periods from bullet points and list items.
    # - `- item.` -> `- item`
    # - `1) numbered.` -> `1) numbered`
    "remove_trailing_periods": ["md", "tex", "txt", "smd"],
    # Replace em dash (`—`) with colon (`:`) in list items.
    # - `- term — definition` -> `- term: definition`
    "replace_em_dash_with_colon": ["md", "tex", "txt", "smd"],
    # Remove markdown syntax from text: bold, italic, links, images, headers.
    # - `**bold** *italic* [link](url)` -> `bold italic link`
    # - `# Header` -> `Header`
    "remove_markdown_formatting": ["md", "smd"],
    # Add visual frame around section headers.
    # - `# Chapter` -> `# ###############\n# Chapter\n# ###############`
    "frame_chapters": ["md", "tex", "txt", "smd"],
    # Capitalize first letter of bullet points and headers.
    # - `- hello world` -> `- Hello world`
    # - `# my title` -> `# My Title`
    "capitalize_header": ["md", "txt", "smd"],
    # Regenerate table of contents (markdown only).
    # - `<!-- toc --> ... <!-- tocstop -->` -> auto-generated TOC
    "refresh_toc": ["md", "smd"],
    # Validate all URLs in the document are reachable.
    # - Performs HTTP requests to check link status
    "check_links": ["md", "tex", "txt", "smd"],
    # Apply smd (slide markdown) specific formatting (smd only).
    # - Remove trailing white spaces
    # - Remove the `:` after a lone `@tag@`
    # - Capitalize the first letter after a `:`
    # - Rebuild blank-line spacing: one blank line between blocks of level-1
    #   bullets, around fenced div blocks (`:::`), and exactly one blank line
    #   before/after every header and slide-title marker (`* <title>`)
    "smd_format": ["smd"],
    # Apply the same blank-line rebuild as `smd_format`, but for `.md` files
    # (markdown only).
    # - Rebuild blank-line spacing: one blank line between blocks of level-1
    #   bullets, around fenced code blocks (```), and exactly one blank line
    #   before/after every header
    "md_format": ["md"],
}


DEFAULT_ACTIONS = [
    action
    for action in VALID_ACTIONS
    if action
    not in [
        "frame_chapters",
        "refresh_toc",
        "check_links",
        "remove_markdown_formatting",
    ]
]


def _is_action_supported_for_format(action: str, extension: str) -> bool:
    """
    Check if an action is supported for a given file format.

    :param action: The action name.
    :param extension: The file extension (md, tex, txt, smd).
    :return: True if the action is supported, False otherwise.
    """
    hdbg.dassert_in(action, VALID_ACTIONS, msg=f"Unknown action: {action}")
    return extension in VALID_ACTIONS[action]


def _filter_actions_by_format(
    actions: Optional[List[str]], extension: str
) -> Optional[List[str]]:
    """
    Filter actions to keep only those supported by the given format.

    Warns about unsupported actions and removes them from the list.

    :param actions: List of actions to filter, or None (all default actions).
    :param extension: The file extension (md, tex, txt, smd).
    :return: Filtered list of actions, or None if input was None.
    """
    if actions is None:
        return None
    hdbg.dassert_isinstance(actions, list)
    filtered = [
        a for a in actions if _is_action_supported_for_format(a, extension)
    ]
    unsupported = [
        a for a in actions if not _is_action_supported_for_format(a, extension)
    ]
    for action in unsupported:
        _LOG.warning(
            "Action '%s' is not supported for .%s files, skipping",
            action,
            extension,
        )
    return filtered


def _perform_actions(
    lines: List[str],
    in_file_name: str,
    file_type_override: str = "",
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
    :param file_type_override: Force a specific file type (md, tex, txt, smd).
        If provided, overrides detection from file extension.
    :param kwargs: Additional keyword arguments to be passed to the
        actions.
    :return: The processed lines.
    """
    hdbg.dassert_isinstance(lines, list)
    # Determine the extension: use override if provided, otherwise infer from filename.
    if file_type_override:
        hdbg.dassert_in(file_type_override, ["md", "tex", "txt", "smd"])
        extension = file_type_override
    else:
        extension = os.path.splitext(in_file_name)[1]
        # Remove the . from the extenstion (e.g., ".txt").
        hdbg.dassert(
            extension.startswith("."), "Invalid extension='%s'", extension
        )
        extension = extension[1:]
    # Get the file type.
    is_md_file = extension == "md"
    is_tex_file = extension == "tex"
    is_txt_file = extension == "txt"
    # `smd` (slide markdown) is a `txt`-like format used for lecture slide
    # sources (e.g., `@tag@` semantic markup, pandoc `:::` fenced divs).
    is_smd_file = extension == "smd"
    hdbg.dassert_eq(
        is_md_file + is_tex_file + is_txt_file + is_smd_file,
        1,
        msg="Invalid file type",
    )
    # Filter actions based on file format.
    actions = _filter_actions_by_format(actions, extension)
    # Extract YAML front matter if present (only for markdown files).
    yaml_frontmatter: List[str] = []
    if is_md_file:
        yaml_frontmatter, lines = hmartoc.extract_yaml_frontmatter(lines)
    # Pre-process text (including protected content extraction).
    action = "preprocess"
    protected_map: dict = {}
    if _to_execute_action(action, actions):
        lines, protected_map = _preprocess_txt(lines, extension)
    # Beautify.
    action = "beautify"
    if _to_execute_action(action, actions):
        txt = "\n".join(lines)
        # Use hmarkdown_formatting for markdown files with specified backend/mode,
        # otherwise use the legacy prettier for other file types.
        if is_md_file and "backend" in kwargs and "mode" in kwargs:
            backend = kwargs.pop("backend")
            mode = kwargs.pop("mode")
            width = kwargs.pop("width")
            txt = hmarform.format_md(txt, backend, mode, width=width)
        else:
            # Use prettier for all file types (e.g., tex and txt). `prettier`
            # only understands `md`/`txt`/`tex`, so treat `smd` as `txt`.
            prettier_extension = "txt" if is_smd_file else extension
            txt = dshdlipr.prettier_on_str(
                txt, file_type=prettier_extension, **kwargs
            )
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
        lines = _convert_asterisk_bullets_to_dashes(
            lines, is_smd_file=is_smd_file
        )
    # Remove trailing periods.
    action = "remove_trailing_periods"
    if _to_execute_action(action, actions):
        lines = _remove_trailing_periods(lines)
    # Replace em dash with colon.
    action = "replace_em_dash_with_colon"
    if _to_execute_action(action, actions):
        lines = _replace_em_dash_with_colon(lines)
    # Apply smd-specific formatting (tag colons, capitalization, fence spacing).
    action = "smd_format"
    if _to_execute_action(action, actions):
        if is_smd_file:
            lines = _smd_format(lines)
    # Apply the same blank-line rebuild as `smd_format`, but for `.md` files.
    action = "md_format"
    if _to_execute_action(action, actions):
        if is_md_file:
            lines = _md_format(lines)
    # Remove markdown formatting.
    action = "remove_markdown_formatting"
    if _to_execute_action(action, actions):
        lines = _remove_markdown_formatting(lines)
    # Frame chapters.
    action = "frame_chapters"
    if _to_execute_action(action, actions):
        if is_txt_file or is_smd_file:
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
        if is_md_file or is_txt_file or is_smd_file:
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


def _get_backup_filename(file_path: str) -> str:
    """
    Get the backup filename for a given file path.

    Example: `.claude/skills/testing.rules.md` ->
    `.claude/skills/tmp.lint_text.testing.rules.md`

    :param file_path: The original file path.
    :return: The backup file path.
    """
    dir_name = os.path.dirname(file_path)
    file_name = os.path.basename(file_path)
    backup_name = f"tmp.lint_text.{file_name}"
    if dir_name:
        backup_path = os.path.join(dir_name, backup_name)
    else:
        backup_path = backup_name
    return backup_path


def _create_backup(file_path: str) -> str:
    """
    Create a backup copy of the file.

    :param file_path: The original file path.
    :return: The backup file path.
    """
    backup_path = _get_backup_filename(file_path)
    _LOG.debug("Creating backup: %s -> %s", file_path, backup_path)
    hsystem.system(f"cp {file_path} {backup_path}")
    return backup_path


def _revert_from_backup(file_path: str) -> None:
    """
    Restore a file from its backup.

    :param file_path: The original file path to restore.
    """
    backup_path = _get_backup_filename(file_path)
    hdbg.dassert_file_exists(backup_path, "Backup file not found")
    _LOG.info("Reverting from backup: %s -> %s", backup_path, file_path)
    hsystem.system(f"cp {backup_path} {file_path}")
    _LOG.info("File reverted successfully")


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
    # Create backup before processing (if processing in-place).
    if in_file_name == out_file_name and in_file_name != "-":
        _create_backup(in_file_name)
    # Read input.
    lines = hseinout.from_file(in_file_name)
    _LOG.debug("in_file_name=%s", in_file_name)
    # Process.
    kwargs = {
        "width": args.width,
        "use_dockerized_prettier": args.use_dockerized_prettier,
        "use_dockerized_markdown_toc": args.use_dockerized_markdown_toc,
    }
    # Add backend and mode if specified.
    if args.backend:
        kwargs["backend"] = args.backend
    if args.mode:
        kwargs["mode"] = args.mode
    out_lines = _perform_actions(
        lines,
        in_file_name,
        file_type_override=args.type,
        actions=actions,
        **kwargs,
    )
    # Write output.
    hseinout.to_file(out_lines, out_file_name)
