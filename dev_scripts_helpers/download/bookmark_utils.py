#!/usr/bin/env python

"""
Shared utilities for Google Sheets link processing scripts.

Provides common functionality for downloading/uploading to Google Sheets
and working with CSV files.

Import as:

import dev_scripts_helpers.download.bookmark_utils as dshdbou
"""

import csv
import logging
import re
from typing import Any, Dict, List

import helpers.hdbg as hdbg
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.htable as htable

_LOG = logging.getLogger(__name__)


def get_tmp_file_path(filename: str, prefix: str) -> str:
    """
    Get the path for a temporary file with a given prefix.

    :param filename: Base filename
    :param prefix: Prefix for the temporary file (e.g., "download_link_articles")
    :return: Path to temporary file
    """
    _LOG.debug(hprint.to_str("filename prefix"))
    result = f"./tmp.{prefix}.{filename}"
    _LOG.debug(hprint.to_str("result"))
    return result


def read_csv(filepath: str) -> List[Dict[str, Any]]:
    """
    Read CSV file and return list of dictionaries.

    Each row becomes a dictionary with column names as keys.

    :param filepath: Path to CSV file
    :return: List of row dictionaries
    """
    _LOG.debug(hprint.to_str("filepath"))
    rows = []
    # Read each row into a dict keyed by column name.
    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    _LOG.debug("len(rows)=%d", len(rows))
    return rows


def write_csv(
    filepath: str,
    rows: List[Dict[str, Any]],
    *,
    fieldnames: List[str],
) -> None:
    """
    Write list of dictionaries to CSV file.

    :param filepath: Path to CSV file
    :param rows: List of row dictionaries
    :param fieldnames: Column names in order
    """
    _LOG.debug(hprint.to_str("filepath fieldnames"))
    # Write the header row followed by all data rows.
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    _LOG.debug("Wrote %d rows to '%s'", len(rows), filepath)


def is_hackernews_url(url: str) -> bool:
    """
    Check if URL is a Hacker News item URL.

    :param url: URL to check
    :return: True if URL is a HN item URL
    """
    _LOG.debug(hprint.to_str("url"))
    hdbg.dassert_isinstance(url, str)
    result = "news.ycombinator.com/item?id=" in url
    _LOG.debug(hprint.to_str("result"))
    return result


def extract_item_id(hn_url: str) -> str:
    """
    Extract the item ID from a Hacker News URL.

    :param hn_url: Hacker News item URL
    :return: Item ID
    """
    _LOG.debug(hprint.to_str("hn_url"))
    hdbg.dassert(is_hackernews_url(hn_url), "Not a Hacker News URL: %s", hn_url)
    # Extract the numeric item ID from the query string, e.g., `item?id=123`.
    match = re.search(r"item\?id=(\d+)", hn_url)
    hdbg.dassert(match, "Could not extract item ID from: %s", hn_url)
    result = match.group(1)  # type: ignore
    _LOG.debug(hprint.to_str("result"))
    return result


def download_from_gsheet(url: str, output_file: str) -> str:
    """
    Download data from Google Sheets and save to a CSV file.

    :param url: URL of the Google Sheets document
    :param output_file: Path where CSV will be saved
    :return: Path to the saved CSV file
    """
    _LOG.debug(hprint.to_str("url output_file"))
    _LOG.info("Downloading data from Google Sheets")
    # Build and run the command to export the sheet to a local CSV file.
    cmd = (
        f"from_gsheet.py --url '{url}' --output_file '{output_file}' --overwrite"
    )
    _LOG.debug("cmd=%s", cmd)
    hsystem.system(cmd, print_command=True)
    _LOG.debug("Downloaded from Google Sheets %s to %s", url, output_file)
    hdbg.dassert_path_exists(output_file)
    # Report basic stats to help spot obviously wrong downloads early.
    rows = read_csv(output_file)
    num_cols = len(rows[0].keys()) if rows else 0
    _LOG.info("Loaded %d rows and %d columns", len(rows), num_cols)
    # Log the first 3 rows of the downloaded file to spot obvious issues
    # (e.g., wrong sheet, malformed header) without dumping the whole file.
    _LOG.info(
        "First 3 rows of '%s':\n%s",
        output_file,
        htable.csv_to_str(output_file, max_rows=3),
    )
    _LOG.debug(hprint.to_str("output_file"))
    return output_file


def upload_to_gsheet(url: str, input_file: str, tabname: str) -> None:
    """
    Upload CSV data to Google Sheets.

    :param url: URL of the Google Sheets document
    :param input_file: Path to CSV file to upload
    :param tabname: Name of the tab to create/overwrite
    """
    _LOG.debug(hprint.to_str("url input_file tabname"))
    _LOG.info("Reading CSV file: '%s'", input_file)
    rows = read_csv(input_file)
    num_cols = len(rows[0].keys()) if rows else 0
    _LOG.info("Loaded %d rows and %d columns", len(rows), num_cols)
    _LOG.info("Writing data to tab '%s' in Google Sheet", tabname)
    # Build and run the command to import the CSV into the target tab.
    cmd = (
        f"to_gsheet.py --input_file '{input_file}' --url '{url}' "
        f"--tabname '{tabname}' --overwrite"
    )
    _LOG.debug("cmd=%s", cmd)
    hsystem.system(cmd, print_command=True)
    _LOG.info("Successfully wrote data to Google Sheet")
