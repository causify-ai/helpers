"""
Import as:

import helpers.hmarkdown_tables as hmarktab
"""

import logging
from typing import Dict, List, Tuple

import helpers.hdbg as hdbg

_LOG = logging.getLogger(__name__)


def replace_tables_with_tags(
    lines: List[str],
) -> Tuple[List[str], Dict[str, str]]:
    """
    Replace markdown tables with tag and return mapping from tags to the table.

    E.g.,
        ```
        Some text before
        | Column 1 | Column 2 |
        |----------|----------|
        | Value 1  | Value 2  |
        | Value 3  | Value 4  |
        More text after
        ```
    is replaced with:
        ```
        Some text before
        <table1>
        More text after
        ```

    :param lines: list of lines to process
    :return: tuple containing:
        - list of lines with the tables replaced by tags
        - mapping from tags to the table text
    """
    hdbg.dassert_isinstance(lines, list)
    result = []
    table_map = {}
    table_count = 0
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Check if this line starts a table (contains |).
        if "|" in line and line.strip():
            # Look ahead to see if next line is a separator.
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                # Check if next line is a table separator (contains --- and |).
                if "|" in next_line and "-" in next_line:
                    # Found a table, collect all table lines.
                    table_lines = []
                    # Add header line.
                    table_lines.append(lines[i])
                    i += 1
                    # Add separator line.
                    table_lines.append(lines[i])
                    i += 1
                    # Add data rows (continue while lines contain |).
                    while (
                        i < len(lines)
                        and "|" in lines[i].strip()
                        and lines[i].strip()
                    ):
                        table_lines.append(lines[i])
                        i += 1
                    # Store the table.
                    table_count += 1
                    table_text = "\n".join(table_lines)
                    table_map[str(table_count)] = table_text
                    result.append(f"<table{table_count}>")
                    continue
        # Not a table line, add as-is.
        result.append(lines[i])
        i += 1
    return result, table_map


def replace_tags_with_tables(
    lines: List[str], table_map: Dict[str, str]
) -> List[str]:
    """
    Replace tags with markdown tables.

    :param lines: list of lines to process
    :param table_map: mapping from tags to table text
    :return: list of lines with tags replaced by tables
    """
    hdbg.dassert_isinstance(lines, list)
    hdbg.dassert_isinstance(table_map, dict)
    # Initialize output.
    result = []
    table_map_copy = table_map.copy()
    # Parse data.
    for line in lines:
        if line.startswith("<table") and line.endswith(">"):
            # Extract table number from tag like <table1>.
            tag_match = line[6:-1]  # Remove '<table' and '>'
            hdbg.dassert_in(
                tag_match, table_map_copy, f"Found unmatched tag {tag_match}"
            )
            # Split table text into lines and add them.
            table_text = table_map_copy[tag_match]
            table_lines = table_text.split("\n")
            result.extend(table_lines)
            # Remove used tag from map.
            del table_map_copy[tag_match]
        else:
            result.append(line)
    # Ensure all tags were used.
    hdbg.dassert_eq(
        len(table_map_copy),
        0,
        f"Found {len(table_map_copy)} unmatched tags: {list(table_map_copy.keys())}",
    )
    return result
