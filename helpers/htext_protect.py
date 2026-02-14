"""
Utilities for protecting content during text processing.

Extract and restore content that should not be modified by formatters and text
transformations (code blocks, comments, etc.).
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
    - Fenced code blocks (``` ... ```) for .md and .txt files
    - Math blocks ($$ ... $$) for all file types
    - HTML comments (<!-- ... -->) for .md and .txt files
    - LaTeX comments (% ...) for .tex files

    :param lines: The lines to be processed
    :param file_type: File extension ('md', 'txt', or 'tex')
    :return: Tuple of (lines with placeholders, mapping of placeholders to
        original content)
    """
    hdbg.dassert_isinstance(lines, list)
    hdbg.dassert_in(file_type, ["md", "txt", "tex"])
    _LOG.debug("Extracting protected content for file_type=%s", file_type)
    #
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
    # Process each line.
    for line in lines:
        # Handle fenced blocks (for .md and .txt files).
        if file_type in ["md", "txt"] and _is_fenced_block_delimiter(line):
            if not in_fenced_block:
                # Opening delimiter.
                in_fenced_block = True
                lines_new.append(line)
                fenced_block_lines = []
            else:
                # Closing delimiter.
                placeholder = f"<<<PROTECTED_BLOCK_{counter:03d}>>>"
                protected_map[placeholder] = "\n".join(fenced_block_lines)
                counter += 1
                lines_new.append(placeholder)
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
            else:
                # Closing delimiter.
                placeholder = f"<<<PROTECTED_MATH_{counter:03d}>>>"
                protected_map[placeholder] = "\n".join(math_block_lines)
                counter += 1
                lines_new.append(placeholder)
                lines_new.append(line)
                in_math_block = False
                math_block_lines = []
            continue
        # Inside math block: accumulate.
        if in_math_block:
            math_block_lines.append(line)
            continue
        # Handle HTML comments (for .md and .txt files).
        if file_type in ["md", "txt"]:
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
            lines_new.append(placeholder)
            continue
        # Regular line: keep as-is.
        lines_new.append(line)
    # Check for unclosed blocks.
    if in_fenced_block:
        _LOG.warning("Unclosed fenced block detected")
    if in_math_block:
        _LOG.warning("Unclosed math block detected")
    if in_html_comment:
        _LOG.warning("Unclosed HTML comment detected")
    _LOG.debug(
        "Extracted %d protected content blocks", len(protected_map)
    )
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
    _LOG.debug(
        "Restoring %d protected content blocks", len(protected_map)
    )
    #
    lines_new: List[str] = []
    for line in lines:
        # Check if line contains any placeholder.
        restored = False
        for placeholder, original in protected_map.items():
            if placeholder in line:
                if line.strip() == placeholder:
                    # Placeholder is entire line: replace with multi-line content.
                    lines_new.extend(original.split("\n"))
                    restored = True
                    break
                else:
                    # Placeholder embedded in line: replace inline.
                    line = line.replace(placeholder, original)
        if not restored:
            lines_new.append(line)
    return lines_new
