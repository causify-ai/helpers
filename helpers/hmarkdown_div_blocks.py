"""
Utilities for handling div blocks in markdown files.

This module provides functions to add and remove prettier-ignore comments
around div blocks in markdown files.

Import as:

import helpers.hmarkdown_div_blocks as hmadiblo
"""

from typing import List, Tuple


def _split_lines_into_chunks(
    lines: List[str],
) -> List[Tuple[bool, List[str]]]:
    """
    Split lines into chunks of div blocks and non-div blocks.

    A div block starts with a line containing ::: and ends with another
    line containing :::.

    :param lines: List of strings representing lines in a markdown file.
    :return: List of tuples (is_div_block, chunk_lines) where is_div_block
        indicates if the chunk is a div block.
    """
    chunks = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Check if this line starts a div block.
        if line.strip().startswith(":::"):
            # Look ahead to find the closing div block.
            j = i + 1
            while j < len(lines):
                if lines[j].strip().startswith(":::"):
                    # Found the end of the div block.
                    chunk_lines = lines[i : j + 1]
                    chunks.append((True, chunk_lines))
                    i = j + 1
                    break
                j += 1
            else:
                # No closing div block found, treat as regular line.
                chunks.append((False, [line]))
                i += 1
        else:
            # Start a non-div block chunk.
            chunk_lines = [line]
            i += 1
            # Continue collecting non-div lines.
            while i < len(lines) and not lines[i].strip().startswith(":::"):
                chunk_lines.append(lines[i])
                i += 1
            chunks.append((False, chunk_lines))
    return chunks


def add_prettier_ignore_to_div_blocks(lines: List[str]) -> List[str]:
    """
    Add prettier-ignore comments around div blocks.

    A div block starts with a line containing ::: and has another line
    with ::: following it.

    Examples of div blocks:
    - ::::
      ::::{.column width=40%}
    - :::columns
      ::::{.column width=60%}
    - ::::
      :::

    :param lines: List of strings representing lines in a markdown file.
    :return: List of strings with prettier-ignore comments added.
    """
    # Step 1: Split into chunks.
    chunks = _split_lines_into_chunks(lines)
    # Step 2: Process chunks and add prettier-ignore comments.
    result = []
    for is_div_block, chunk_lines in chunks:
        if is_div_block:
            # Add prettier-ignore comments around div blocks.
            result.append("")
            result.append("<!-- prettier-ignore-start -->")
            result.extend(chunk_lines)
            result.append("<!-- prettier-ignore-end -->")
            result.append("")
        else:
            # Add non-div block lines as-is.
            result.extend(chunk_lines)
    return result


def remove_prettier_ignore_from_div_blocks(lines: List[str]) -> List[str]:
    """
    Remove all prettier-ignore comments from lines.

    This function removes:
    - <!-- prettier-ignore-start --> lines
    - <!-- prettier-ignore-end --> lines
    - Empty lines before prettier-ignore-start
    - Empty lines after prettier-ignore-end

    :param lines: List of strings representing lines in a markdown file.
    :return: List of strings with prettier-ignore comments removed.
    """
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Check if this is a prettier-ignore-start comment.
        if line.strip() == "<!-- prettier-ignore-start -->":
            # Remove empty line before prettier-ignore-start if present.
            if result and result[-1] == "":
                result.pop()
            # Skip the prettier-ignore-start line.
            i += 1
            continue
        # Check if this is a prettier-ignore-end comment.
        if line.strip() == "<!-- prettier-ignore-end -->":
            # Skip the prettier-ignore-end line.
            i += 1
            # Skip empty line after prettier-ignore-end if present.
            if i < len(lines) and lines[i] == "":
                i += 1
            continue
        # Add all other lines.
        result.append(line)
        i += 1
    return result
