"""
Module for Python code analysis utilities.

Import as:

import helpers.hpython_code as hpythcode
"""

import re
from typing import List


def get_docstring_line_indices(lines: List[str]) -> List[int]:
    """
    Get indices of lines of code that are inside (doc)strings.

    :param lines: the code lines to check
    :return: the indices of docstrings
    """
    docstring_line_indices = []
    quotes = {'"""': False, "'''": False, "```": False}
    for i, line in enumerate(lines):
        # Determine if the current line is inside a (doc)string.
        for quote in quotes:
            quotes_matched = re.findall(quote, line)
            for q in quotes_matched:
                # Switch the docstring flag.
                # pylint: disable=modified-iterating-dict
                quotes[q] = not quotes[q]
                if q in ('"""', "'''") and not quotes[q]:
                    # A triple-quote has just been closed.
                    # Reset the triple backticks flag.
                    quotes["```"] = False
        if any(quotes.values()):
            # Store the index if the quotes have been opened but not closed yet.
            docstring_line_indices.append(i)
    return docstring_line_indices


def get_docstrings(lines: List[str]) -> List[List[int]]:
    """
    Get line indices grouped together by the docstring they belong to.

    :param lines: lines from the file to process
    :return: grouped lines within docstrings
    """
    # Get indices of lines that are within docstrings.
    doc_indices = get_docstring_line_indices(lines)
    # Group these indices into consecutive docstrings.
    docstrings = []
    if doc_indices:
        current_docstring = [doc_indices[0]]
        for idx in doc_indices[1:]:
            if idx == current_docstring[-1] + 1:
                current_docstring.append(idx)
            else:
                docstrings.append(current_docstring)
                current_docstring = [idx]
        docstrings.append(current_docstring)
    return docstrings


def get_code_block_line_indices(lines: List[str]) -> List[int]:
    """
    Get indices of lines that are inside code blocks.

    Code blocks are lines surrounded by triple backticks, e.g.,
    ```
    This line.
    ```
    Note that the backticks need to be the leftmost element of their line.

    :param lines: the lines to check
    :return: the indices of code blocks
    """
    code_block_line_indices = []
    quotes = {"```": False}
    for i, line in enumerate(lines):
        # Determine if the current line is inside a code block.
        for quote in quotes:
            quotes_matched = re.findall(rf"^\s*({quote})", line)
            for q in quotes_matched:
                # Switch the flag.
                # pylint: disable=modified-iterating-dict
                quotes[q] = not quotes[q]
        if any(quotes.values()):
            # Store the index if the quotes have been opened but not closed yet.
            code_block_line_indices.append(i)
    return code_block_line_indices
