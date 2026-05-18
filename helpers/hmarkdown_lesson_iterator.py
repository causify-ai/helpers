"""
Import as:

import helpers.hmarkdown_lesson_iterator as hmaleite
"""

import logging
from typing import Any, Dict, Generator, List, Optional

import helpers.hdbg as hdbg
from helpers.hmarkdown_comments import process_comment_block
from helpers.hmarkdown_headers import is_markdown_line_separator

_LOG = logging.getLogger(__name__)


def _iterate_lesson_lines(
    lines: List[str],
) -> Generator[Dict[str, Any], None, None]:
    """
    Iterate through lesson lines and yield structured items.

    Processes lines to identify slides (starting with `*`), headers (starting
    with `#`), and comment blocks (<!-- --> or /* */). Single-line comments
    (// and %%) are grouped with surrounding slide/header content. Yields
    dictionaries for each item found with type, content, and line_number.

    :param lines: content of the lesson file as list of strings
    :return: generator yielding dicts with type, content, and line_number keys
        - `type`: 'slide', 'header', or 'comment'
        - `content`: list of lines for the item
        - `line_number`: starting line number (1-indexed)
    """
    hdbg.dassert_isinstance(lines, list)
    current_item_lines: List[str] = []
    current_item_type: Optional[str] = None
    current_item_start_line: int = 0
    in_comment_block = False
    accumulating_comment_block = False
    for line_number, line in enumerate(lines, start=1):
        # Strip trailing newline for processing.
        line_content = line.rstrip("\n")
        _LOG.debug("%d: %s", line_number, line_content)
        # Track comment block state separately from accumulation.
        prev_in_comment_block = in_comment_block
        is_comment_line, in_comment_block = process_comment_block(
            line_content, in_comment_block
        )
        # Handle accumulated comment blocks.
        if accumulating_comment_block:
            current_item_lines.append(line_content)
            # Check if this line ends the comment block.
            if not in_comment_block:
                yield {
                    "type": "comment",
                    "content": current_item_lines,
                    "line_number": current_item_start_line,
                }
                current_item_lines = []
                current_item_type = None
                accumulating_comment_block = False
            continue
        # Check if we're starting a new comment block.
        if is_comment_line and prev_in_comment_block is False:
            # Yield previous item if exists.
            if current_item_lines:
                yield {
                    "type": current_item_type,
                    "content": current_item_lines,
                    "line_number": current_item_start_line,
                }
                current_item_lines = []
                current_item_type = None
            # Check if this is a single-line comment.
            if not in_comment_block:
                yield {
                    "type": "comment",
                    "content": [line_content],
                    "line_number": line_number,
                }
            else:
                # Start accumulating multi-line comment block.
                accumulating_comment_block = True
                current_item_type = "comment"
                current_item_start_line = line_number
                current_item_lines = [line_content]
            continue
        # Skip lines that are part of processing but not slides/headers.
        if is_comment_line:
            continue
        # Skip line separators.
        if is_markdown_line_separator(line_content):
            # Line separators are usually part of surrounding content.
            if current_item_lines:
                current_item_lines.append(line_content)
            continue
        # Check for slide marker (starts with `* `).
        if line_content.startswith("* "):
            # Yield previous item if exists.
            if current_item_lines:
                yield {
                    "type": current_item_type,
                    "content": current_item_lines,
                    "line_number": current_item_start_line,
                }
            # Start new slide.
            current_item_type = "slide"
            current_item_start_line = line_number
            current_item_lines = [line_content]
            continue
        # Check for header (starts with `#`).
        if line_content.startswith("#"):
            # Yield previous item if exists.
            if current_item_lines:
                yield {
                    "type": current_item_type,
                    "content": current_item_lines,
                    "line_number": current_item_start_line,
                }
            # Start new header.
            current_item_type = "header"
            current_item_start_line = line_number
            current_item_lines = [line_content]
            continue
        # Regular content line: add to current item or start preamble.
        if current_item_type is None and not current_item_lines:
            # Start collecting preamble (content before first item).
            current_item_type = "preamble"
            current_item_start_line = line_number
            current_item_lines = [line_content]
            continue
        # Regular line content: add to current item or skip.
        if current_item_lines:
            current_item_lines.append(line_content)
    # Yield final item if exists.
    if current_item_lines:
        yield {
            "type": current_item_type,
            "content": current_item_lines,
            "line_number": current_item_start_line,
        }
    # Ensure we're not in an unclosed comment block.
    hdbg.dassert(
        not in_comment_block,
        "Found end of file while still parsing a comment block",
    )


def read_lesson_file(file_path: str) -> Generator[Dict[str, Any], None, None]:
    """
    Read a Markdown lesson file and yield structured items.

    Yields dictionaries for each slide, header, and comment block found in the
    file. Single-line comments (// and %%) are included in the surrounding
    slide/section content. Block comments (<!-- --> and /* */) are extracted
    as separate items.

    :param file_path: path to the lesson file to parse
    :return: generator yielding dicts with keys: type, content, line_number
        - `type`: 'slide', 'header', or 'comment'
        - `content`: list of lines for the item
        - `line_number`: starting line number (1-indexed)
    """
    hdbg.dassert_file_exists(file_path, "Lesson file must exist")
    with open(file_path, "r") as f:
        lines = f.readlines()
    yield from _iterate_lesson_lines(lines)


def reassemble_from_items(
    items: List[Dict[str, Any]],
    *,
    original_content: str = "",
) -> str:
    """
    Reassemble markdown content from parsed items.

    Reconstructs the original markdown file structure from parsed items by
    joining the content lines of each item. Preserves trailing newlines to
    match the original content exactly.

    :param items: list of parsed items with type, content, and line_number
    :param original_content: original file content to match trailing newlines
    :return: reassembled markdown content as string
    """
    all_lines: List[str] = []
    for item in items:
        all_lines.extend(item["content"])
    # Join with newlines to recreate original file.
    result = "\n".join(all_lines)
    # Preserve trailing newlines to match original.
    original_trailing_newlines = len(original_content) - len(
        original_content.rstrip("\n")
    )
    reassembled_trailing_newlines = len(result) - len(result.rstrip("\n"))
    if original_trailing_newlines > reassembled_trailing_newlines:
        result += "\n" * (
            original_trailing_newlines - reassembled_trailing_newlines
        )
    return result
