#!/usr/bin/env python

"""
Parse MHTML files and extract HTML content or tables.

This script can:
- Extract HTML from MHTML files.
- Print the DOM structure of the HTML.
- Parse and extract tables from the HTML.

Import as:

import dev_scripts_helpers.scraping_script.parse_mhtml as dsspamht

Examples:
# Print DOM structure.
> python parse_mhtml.py file.mhtml

# Extract all tables to CSV.
> python parse_mhtml.py file.mhtml --mode tables --output-dir ./output

# Extract a specific table by index.
> python parse_mhtml.py file.mhtml --mode tables --table-index 0
"""

import argparse
import csv
import logging
import sys
from email import policy
from email.parser import BytesParser
from typing import List, Optional

from bs4 import BeautifulSoup

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

# #############################################################################
# HTML extraction
# #############################################################################


def _extract_html_from_mhtml(path: str) -> Optional[str]:
    """
    Extract HTML string from first text/html part in MHTML file.

    :param path: path to the MHTML file
    :return: HTML content as string or None if not found
    """
    _LOG.debug("Extracting HTML from MHTML file='%s'", path)
    hdbg.dassert_path_exists(path)
    with open(path, "rb") as f:
        msg = BytesParser(policy=policy.default).parse(f)
    # Check if the root itself is text/html.
    if msg.get_content_type() == "text/html":
        _LOG.debug("Found HTML in root message")
        return msg.get_content()
    # Walk all parts to find the first text/html.
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                _LOG.debug("Found HTML in multipart message")
                return part.get_content()
    _LOG.warning("No text/html part found in MHTML file")
    return None

# #############################################################################
# DOM printing
# #############################################################################


def _print_dom(node, *, depth: int = 0, max_depth: int = 10) -> None:
    """
    Recursively print DOM structure showing tag names and text snippets.

    :param node: BeautifulSoup node to print
    :param depth: current depth in the tree
    :param max_depth: maximum depth to traverse
    """
    from bs4.element import Tag

    indent = "  " * depth
    # Stop deep recursion if page is huge.
    if depth > max_depth:
        _LOG.debug("Max depth reached at depth=%s", depth)
        print(indent + "... (max depth reached)")
        return
    # Only process elements (tags), skip NavigableString etc.
    if isinstance(node, Tag):
        # Get small snippet of text inside this tag.
        text = node.get_text(strip=True)
        if len(text) > 60:
            text = text[:57] + "..."
        print(f"{indent}<{node.name}>  {repr(text)}")
        # Recurse into children.
        for child in node.children:
            _print_dom(child, depth=depth + 1, max_depth=max_depth)

# #############################################################################
# Table parsing
# #############################################################################


def _extract_tables_from_html(html: str) -> List[List[List[str]]]:
    """
    Extract all tables from HTML content.

    :param html: HTML content as string
    :return: list of tables, where each table is a list of rows, and each row is
        a list of cell values
    """
    _LOG.debug("Parsing HTML to extract tables")
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    _LOG.info("Found %s tables in HTML", len(tables))
    tables_data = []
    for table_idx, table in enumerate(tables):
        _LOG.debug("Processing table %s", table_idx)
        table_data = []
        # Process all rows in the table.
        rows = table.find_all("tr")
        for row_idx, row in enumerate(rows):
            # Extract cells from row (both th and td).
            cells = row.find_all(["th", "td"])
            row_data = []
            for cell in cells:
                # Get text content, stripping whitespace.
                cell_text = cell.get_text(strip=True)
                row_data.append(cell_text)
            if row_data:
                table_data.append(row_data)
        if table_data:
            tables_data.append(table_data)
    return tables_data


def _save_table_to_csv(
    table_data: List[List[str]], output_path: str
) -> None:
    """
    Save a table to a CSV file.

    :param table_data: table as list of rows, where each row is a list of cell
        values
    :param output_path: path to save the CSV file
    """
    _LOG.info("Saving table to file='%s'", output_path)
    hdbg.dassert_ne(table_data, [], "Table data cannot be empty")
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(table_data)
    _LOG.info("Table saved successfully")


def _print_table_summary(tables_data: List[List[List[str]]]) -> None:
    """
    Print a summary of extracted tables.

    :param tables_data: list of tables
    """
    _LOG.info("Printing table summary")
    print(f"\nFound {len(tables_data)} tables:")
    for idx, table_data in enumerate(tables_data):
        num_rows = len(table_data)
        num_cols = len(table_data[0]) if table_data else 0
        print(f"  Table {idx}: {num_rows} rows x {num_cols} columns")
        # Print first few cells as preview.
        if table_data:
            print(f"    Preview: {table_data[0][:3]}")


# #############################################################################
# Main execution
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
    parser.add_argument("mhtml_file", help="Path to MHTML file to parse")
    parser.add_argument(
        "--mode",
        choices=["dom", "tables"],
        default="dom",
        help="Parsing mode: dom (print DOM structure) or tables (extract tables)",
    )
    parser.add_argument(
        "--output-dir",
        help="Directory to save extracted tables (only for tables mode)",
    )
    parser.add_argument(
        "--table-index",
        type=int,
        help="Extract only the table at this index (only for tables mode)",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=10,
        help="Maximum depth for DOM traversal (only for dom mode)",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main execution function.

    :param parser: argument parser
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Extract HTML from MHTML file.
    _LOG.info("Processing MHTML file='%s'", args.mhtml_file)
    html = _extract_html_from_mhtml(args.mhtml_file)
    hdbg.dassert_is_not(
        html, None, "No text/html part found in MHTML file: %s", args.mhtml_file
    )
    # Process based on mode.
    if args.mode == "dom":
        # Print DOM structure.
        _LOG.info("Printing DOM structure")
        soup = BeautifulSoup(html, "html.parser")
        root = soup.html or soup
        _print_dom(root, max_depth=args.max_depth)
    elif args.mode == "tables":
        # Extract and process tables.
        _LOG.info("Extracting tables from HTML")
        tables_data = _extract_tables_from_html(html)
        hdbg.dassert_ne(
            tables_data,
            [],
            "No tables found in HTML from file: %s",
            args.mhtml_file,
        )
        # Print summary.
        _print_table_summary(tables_data)
        # Save tables if output directory specified.
        if args.output_dir:
            hio.create_dir(args.output_dir, incremental=True)
            # Determine which tables to save.
            if args.table_index is not None:
                hdbg.dassert_lte(
                    args.table_index,
                    len(tables_data) - 1,
                    "Table index out of range: %s",
                    args.table_index,
                )
                tables_to_save = [(args.table_index, tables_data[args.table_index])]
            else:
                tables_to_save = list(enumerate(tables_data))
            # Save each table to CSV.
            for idx, table_data in tables_to_save:
                output_path = f"{args.output_dir}/table_{idx}.csv"
                _save_table_to_csv(table_data, output_path)


if __name__ == "__main__":
    _main(_parse())
