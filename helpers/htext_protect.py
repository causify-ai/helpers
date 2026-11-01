"""
Utilities for protecting content during text processing.

Extract and restore content that should not be modified by formatters and text
transformations (code blocks, comments, etc.).

Import as:

import helpers.htext_protect as htexprot
"""

import logging
import re
from typing import Dict, List, Optional, Tuple

import helpers.hdbg as hdbg

_LOG = logging.getLogger(__name__)


# #############################################################################
# Helper functions
# #############################################################################


def _is_fenced_block_delimiter(line: str) -> bool:
    """
    Check if line is a fenced block delimiter (```).

    :param line: Line to check
    :return: True if line matches fenced block delimiter pattern
    """
    return bool(re.match(r"^\s*```", line))


def _get_fence_length(line: str) -> int:
    """
    Get the number of backticks of a fenced block delimiter.

    E.g., a line starting with 3 backticks returns 3, one with 4 backticks
    returns 4.

    :param line: Line to check
    :return: number of leading backticks, 0 if the line is not a delimiter
    """
    m = re.match(r"^\s*(`{3,})", line)
    length = len(m.group(1)) if m else 0
    return length


def _get_fence_length_key(placeholder: str) -> str:
    """
    Get the key of `protected_map` storing the fence length of a block.

    A formatter can shorten the delimiters of a block with more than 3
    backticks, e.g., `prettier` uses the shortest fence that its content
    allows, and the content is hidden behind a placeholder. So we store the
    original length, to restore the delimiters.

    :param placeholder: placeholder of a fenced block
    :return: key of `protected_map`, which never appears in the text
    """
    return placeholder.replace("PROTECTED_BLOCK_", "PROTECTED_FENCE_LENGTH_")


def _get_stored_fence_length(
    placeholder: str, protected_map: Dict[str, str]
) -> int:
    """
    Get the original fence length stored for a placeholder.

    :param placeholder: any placeholder
    :param protected_map: mapping of placeholders to original content
    :return: number of backticks of the original delimiters, 0 if the
        placeholder is not a fenced block with more than 3 backticks
    """
    length = 0
    if "PROTECTED_BLOCK_" in placeholder:
        length = int(protected_map.get(_get_fence_length_key(placeholder), 0))
    return length


def _set_fence_length(line: str, length: int) -> str:
    """
    Set the number of backticks of a fenced block delimiter, keeping the rest.

    :param line: line with a fenced block delimiter
    :param length: number of backticks to use
    :return: line with the new delimiter
    """
    return re.sub(r"^(\s*)`{3,}", lambda m: m.group(1) + "`" * length, line)


def _restore_fence_length_around(
    text: str, placeholder: str, length: int
) -> str:
    """
    Set the fence length of the delimiters around a placeholder in a text.

    :param text: text with lines separated by `\\n`, containing the placeholder
    :param placeholder: placeholder of a fenced block
    :param length: number of backticks of the original delimiters
    :return: text where the lines before and after the placeholder line, if
        they are fenced block delimiters, have `length` backticks
    """
    lines = text.split("\n")
    for idx, line in enumerate(lines):
        if placeholder not in line:
            continue
        for delimiter_idx in [idx - 1, idx + 1]:
            if 0 <= delimiter_idx < len(lines) and _is_fenced_block_delimiter(
                lines[delimiter_idx]
            ):
                lines[delimiter_idx] = _set_fence_length(
                    lines[delimiter_idx], length
                )
    return "\n".join(lines)


def _is_fenced_block_closing(line: str, opening_length: int) -> bool:
    """
    Check if line closes a fenced block opened with `opening_length` backticks.

    As in CommonMark, a closing fence has no info string and at least as many
    backticks as the opening one. So a line with an info string (e.g., after 3
    backticks) or a shorter fence is content of the block, e.g., when a
    4-backtick block shows a 3-backtick fence.

    :param line: Line to check
    :param opening_length: number of backticks of the opening delimiter
    :return: True if the line closes the block
    """
    m = re.match(r"^\s*(`{3,})\s*$", line)
    return bool(m) and len(m.group(1)) >= opening_length


def _is_math_block_delimiter(line: str) -> bool:
    """
    Check if line is a math block delimiter ($$).

    :param line: Line to check
    :return: True if line matches math block delimiter pattern
    """
    return bool(re.match(r"^\s*\$\$\s*$", line))


def _extract_single_line_html_comment(line: str) -> Optional[str]:
    """
    Extract single-line HTML comment from line if present.

    Skips TOC markers (<!-- toc --> and <!-- tocstop -->) as they need to be
    processed by the TOC generation logic.

    :param line: Line to check
    :return: Full comment string if found, None otherwise
    """
    # Skip TOC markers: they are processed by `refresh_toc`.
    if "<!-- toc -->" in line or "<!-- tocstop -->" in line:
        return None
    # Match <!-- ... --> on single line.
    m = re.match(r"^(\s*<!--.*?-->\s*)$", line)
    if m:
        return m.group(1)
    return None


def _is_html_comment_start(line: str) -> bool:
    """
    Check if line starts an HTML comment.

    Skips TOC markers as they need to be processed by TOC generation logic.

    :param line: Line to check
    :return: True if line contains <!-- without closing -->
    """
    # Skip TOC markers.
    if "<!-- toc -->" in line or "<!-- tocstop -->" in line:
        return False
    return "<!--" in line and "-->" not in line


def _is_html_comment_end(line: str) -> bool:
    """
    Check if line ends an HTML comment.

    :param line: Line to check
    :return: True if line contains --> without opening <!--
    """
    return "-->" in line and "<!--" not in line


def _is_latex_comment(line: str) -> bool:
    """
    Check if line is a LaTeX comment (starts with %).

    :param line: Line to check
    :return: True if line starts with %
    """
    return bool(re.match(r"^\s*%", line))


def _is_smd_line_comment(line: str) -> bool:
    """
    Check if line is a smd line comment (starts with //).

    :param line: Line to check
    :return: True if line starts with //
    """
    return bool(re.match(r"^\s*//", line))


# #############################################################################
# Main functions
# #############################################################################


def extract_protected_content(
    lines: List[str],
    file_type: str,
) -> Tuple[List[str], Dict[str, str]]:
    """
    Extract protected content and replace with placeholders.

    Protected content includes:
    - Fenced code blocks (``` ... ```) for .md, .txt, and .smd files
    - Math blocks ($$ ... $$) for all file types
    - HTML comments (<!-- ... -->) for .md, .txt, and .smd files
    - LaTeX comments (% ...) for .tex files
    - `//` line comments for .smd files

    :param lines: The lines to be processed
    :param file_type: File extension ('md', 'txt', 'tex', or 'smd')
    :return: Tuple of (lines with placeholders, mapping of placeholders to
        original content)
    """
    hdbg.dassert_isinstance(lines, list)
    hdbg.dassert_in(file_type, ["md", "txt", "tex", "smd"])
    _LOG.debug("Extracting protected content for file_type=%s", file_type)
    protected_map: Dict[str, str] = {}
    counter = 1
    lines_new: List[str] = []
    # State tracking.
    in_fenced_block = False
    in_math_block = False
    in_html_comment = False
    fenced_block_lines: List[str] = []
    math_block_lines: List[str] = []
    html_comment_lines: List[str] = []
    # Indentation of the currently open fenced/math block's opening delimiter,
    # so the placeholder line we emit for its content can be indented to match.
    fenced_block_indent = 0
    math_block_indent = 0
    # Number of backticks of the currently open fenced block's opening
    # delimiter, since only a delimiter at least as long closes it.
    fenced_block_length = 0
    # Process each line.
    for line in lines:
        # Handle fenced blocks (for .md, .txt, and .smd files).
        if file_type in ["md", "txt", "smd"] and (
            _is_fenced_block_closing(line, fenced_block_length)
            if in_fenced_block
            else _is_fenced_block_delimiter(line)
        ):
            if not in_fenced_block:
                # Opening delimiter.
                in_fenced_block = True
                lines_new.append(line)
                fenced_block_lines = []
                fenced_block_indent = len(line) - len(line.lstrip())
                fenced_block_length = _get_fence_length(line)
            else:
                # Closing delimiter: protect only content, keep delimiters visible.
                placeholder = f"<<<PROTECTED_BLOCK_{counter:03d}>>>"
                protected_map[placeholder] = "\n".join(fenced_block_lines)
                if fenced_block_length > 3:
                    protected_map[_get_fence_length_key(placeholder)] = str(
                        fenced_block_length
                    )
                counter += 1
                # Indent the placeholder to match the fence's own indentation
                # (e.g., a code block nested inside a list item).
                lines_new.append(" " * fenced_block_indent + placeholder)
                lines_new.append(line)
                in_fenced_block = False
                fenced_block_lines = []
            continue
        # Inside fenced block: accumulate.
        if in_fenced_block:
            fenced_block_lines.append(line)
            continue
        # Handle math blocks (for all file types).
        if _is_math_block_delimiter(line):
            if not in_math_block:
                # Opening delimiter.
                in_math_block = True
                lines_new.append(line)
                math_block_lines = []
                math_block_indent = len(line) - len(line.lstrip())
            else:
                # Closing delimiter: protect only content, keep delimiters
                # visible. Indent the placeholder to match the delimiter's
                # indentation, for the same reason as fenced code blocks above
                # (a math block can likewise be nested inside a list item).
                placeholder = f"<<<PROTECTED_MATH_{counter:03d}>>>"
                protected_map[placeholder] = "\n".join(math_block_lines)
                counter += 1
                lines_new.append(" " * math_block_indent + placeholder)
                lines_new.append(line)
                in_math_block = False
                math_block_lines = []
            continue
        # Inside math block: accumulate.
        if in_math_block:
            math_block_lines.append(line)
            continue
        # Handle HTML comments (for .md, .txt, and .smd files).
        if file_type in ["md", "txt", "smd"]:
            # Single-line HTML comment.
            single_line_comment = _extract_single_line_html_comment(line)
            if single_line_comment:
                placeholder = f"<<<PROTECTED_COMMENT_{counter:03d}>>>"
                protected_map[placeholder] = single_line_comment
                counter += 1
                lines_new.append(placeholder)
                continue
            # Multi-line HTML comment start.
            if _is_html_comment_start(line):
                in_html_comment = True
                html_comment_lines = [line]
                continue
            # Multi-line HTML comment end.
            if in_html_comment and _is_html_comment_end(line):
                html_comment_lines.append(line)
                placeholder = f"<<<PROTECTED_COMMENT_{counter:03d}>>>"
                protected_map[placeholder] = "\n".join(html_comment_lines)
                counter += 1
                lines_new.append(placeholder)
                in_html_comment = False
                html_comment_lines = []
                continue
            # Inside multi-line HTML comment: accumulate.
            if in_html_comment:
                html_comment_lines.append(line)
                continue
        # Handle LaTeX comments (for .tex files).
        if file_type == "tex" and _is_latex_comment(line):
            placeholder = f"<<<PROTECTED_COMMENT_{counter:03d}>>>"
            protected_map[placeholder] = line
            counter += 1
            # Prefix placeholder with '%' so the LaTeX parser still recognizes
            # this line as a comment and never reflows/joins it with neighbors.
            lines_new.append(f"%{placeholder}")
            continue
        # Handle `//` line comments (for .smd files).
        if file_type == "smd" and _is_smd_line_comment(line):
            placeholder = f"<<<PROTECTED_LINE_COMMENT_{counter:03d}>>>"
            protected_map[placeholder] = line
            counter += 1
            # Disguise the placeholder as an HTML comment so the `beautify`
            # step (which runs the text through a markdown-aware formatter,
            # even for `smd`/`txt` files) recognizes it as an HTML block and
            # never reflows/merges it with neighboring `//` comment lines.
            lines_new.append(f"<!--{placeholder}-->")
            continue
        # Regular line: keep as-is.
        lines_new.append(line)
    # Check for unclosed blocks.
    if in_fenced_block:
        _LOG.warning("Unclosed fenced block detected")
        # The block extends to the end of the text, as in CommonMark. Protect
        # its content like for a closed block, otherwise it is silently lost.
        if fenced_block_lines:
            placeholder = f"<<<PROTECTED_BLOCK_{counter:03d}>>>"
            protected_map[placeholder] = "\n".join(fenced_block_lines)
            if fenced_block_length > 3:
                protected_map[_get_fence_length_key(placeholder)] = str(
                    fenced_block_length
                )
            counter += 1
            lines_new.append(" " * fenced_block_indent + placeholder)
    if in_math_block:
        _LOG.warning("Unclosed math block detected")
        # Protect the content like for a closed block, otherwise it is
        # silently lost.
        if math_block_lines:
            placeholder = f"<<<PROTECTED_MATH_{counter:03d}>>>"
            protected_map[placeholder] = "\n".join(math_block_lines)
            counter += 1
            lines_new.append(" " * math_block_indent + placeholder)
    if in_html_comment:
        _LOG.warning("Unclosed HTML comment detected")
        # Protect the content like for a closed comment, otherwise it is
        # silently lost.
        placeholder = f"<<<PROTECTED_COMMENT_{counter:03d}>>>"
        protected_map[placeholder] = "\n".join(html_comment_lines)
        counter += 1
        lines_new.append(placeholder)
    _LOG.debug("Extracted %d protected content blocks", len(protected_map))
    return lines_new, protected_map


def restore_protected_content(
    lines: List[str],
    protected_map: Dict[str, str],
) -> List[str]:
    """
    Restore protected content by replacing placeholders with original text.

    :param lines: Lines containing placeholders
    :param protected_map: Mapping of placeholders to original content
    :return: Lines with restored content
    """
    hdbg.dassert_isinstance(lines, list)
    hdbg.dassert_isinstance(protected_map, dict)
    _LOG.debug("Restoring %d protected content blocks", len(protected_map))
    lines_new: List[str] = []
    # Length of the fence that the next line should close, after restoring a
    # block with more than 3 backticks.
    closing_fence_length = 0
    for line in lines:
        # Restore the length of the closing delimiter of the previous block.
        if closing_fence_length and _is_fenced_block_delimiter(line):
            line = _set_fence_length(line, closing_fence_length)
        closing_fence_length = 0
        # Check if line contains any placeholder.
        restored = False
        for placeholder, original in protected_map.items():
            if placeholder in line:
                stripped = line.strip()
                # Exact match, LaTeX comment with '%' prefix (and optional
                # space), or `//` line comment disguised as an HTML comment
                # (`<!--...-->`). `.strip()` also makes this tolerant of the
                # leading indentation that `extract_protected_content()` adds
                # to fenced-code/math-block placeholders (to keep them valid
                # inside nested lists): the indentation is discarded here and
                # the original block's own indentation (captured verbatim in
                # `original`) is restored instead.
                if (
                    stripped == placeholder
                    or re.fullmatch(rf"%\s*{re.escape(placeholder)}", stripped)
                    or re.fullmatch(
                        rf"<!--\s*{re.escape(placeholder)}\s*-->", stripped
                    )
                ):
                    # Placeholder is entire line: replace with multi-line content.
                    # Restore the length of the opening delimiter of a fenced
                    # block with more than 3 backticks, and of its closing one
                    # on the next line.
                    fence_length = _get_stored_fence_length(
                        placeholder, protected_map
                    )
                    if (
                        fence_length
                        and lines_new
                        and _is_fenced_block_delimiter(lines_new[-1])
                    ):
                        lines_new[-1] = _set_fence_length(
                            lines_new[-1], fence_length
                        )
                        closing_fence_length = fence_length
                    lines_new.extend(original.split("\n"))
                    restored = True
                    break
                else:
                    # Placeholder embedded in line: replace inline. The line
                    # can hold a whole fenced block (delimiters and
                    # placeholder), if a formatter joined them.
                    fence_length = _get_stored_fence_length(
                        placeholder, protected_map
                    )
                    if fence_length:
                        line = _restore_fence_length_around(
                            line, placeholder, fence_length
                        )
                    line = line.replace(placeholder, original)
        if not restored:
            lines_new.append(line)
    return lines_new
