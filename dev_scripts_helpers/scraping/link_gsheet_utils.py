#!/usr/bin/env python

"""
Shared utilities for Google Sheets link processing scripts.

Provides common functionality for downloading/uploading to Google Sheets
and working with CSV files.

Import as:

import dev_scripts_helpers.scraping.link_gsheet_utils as dslgu
"""

import csv
import logging
import re
from typing import Any, Dict, List

import helpers.hdbg as hdbg
import helpers.hcache_simple as hcacsimp
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


def get_tmp_file_path(filename: str, prefix: str) -> str:
    """
    Get the path for a temporary file with a given prefix.

    :param filename: Base filename
    :param prefix: Prefix for the temporary file (e.g., "download_link_articles")
    :return: Path to temporary file
    """
    return f"./tmp.{prefix}.{filename}"


def read_csv(filepath: str) -> List[Dict[str, Any]]:
    """
    Read CSV file and return list of dictionaries.

    Each row becomes a dictionary with column names as keys.

    :param filepath: Path to CSV file
    :return: List of row dictionaries
    """
    rows = []
    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
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
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def is_hackernews_url(url: str) -> bool:
    """
    Check if URL is a Hacker News item URL.

    :param url: URL to check
    :return: True if URL is a HN item URL
    """
    hdbg.dassert_isinstance(url, str)
    return "news.ycombinator.com/item?id=" in url


def extract_item_id(hn_url: str) -> str:
    """
    Extract the item ID from a Hacker News URL.

    :param hn_url: Hacker News item URL
    :return: Item ID
    """
    hdbg.dassert(is_hackernews_url(hn_url), "Not a Hacker News URL: %s", hn_url)
    match = re.search(r"item\?id=(\d+)", hn_url)
    hdbg.dassert(match, "Could not extract item ID from: %s", hn_url)
    return match.group(1)  # type: ignore


@hcacsimp.simple_cache(cache_type="json", write_through=True)
def download_from_gsheet(url: str, output_file: str) -> str:
    """
    Download data from Google Sheets and save to a CSV file.

    Results are cached to avoid redundant downloads of the same sheet.

    :param url: URL of the Google Sheets document
    :param output_file: Path where CSV will be saved
    :return: Path to the saved CSV file
    """
    _LOG.info("Downloading data from Google Sheets")
    cmd = (
        f"from_gsheet.py --url '{url}' --output_file '{output_file}' --overwrite"
    )
    _LOG.debug("cmd=%s", cmd)
    hsystem.system(cmd, print_command=True)
    _LOG.debug("Downloaded from Google Sheets %s to %s", url, output_file)
    hdbg.dassert_path_exists(output_file)
    rows = read_csv(output_file)
    num_cols = len(rows[0].keys()) if rows else 0
    _LOG.info("Loaded %d rows and %d columns", len(rows), num_cols)
    return output_file


def upload_to_gsheet(url: str, input_file: str, tabname: str) -> None:
    """
    Upload CSV data to Google Sheets.

    :param url: URL of the Google Sheets document
    :param input_file: Path to CSV file to upload
    :param tabname: Name of the tab to create/overwrite
    """
    _LOG.info("Reading CSV file: '%s'", input_file)
    rows = read_csv(input_file)
    num_cols = len(rows[0].keys()) if rows else 0
    _LOG.info("Loaded %d rows and %d columns", len(rows), num_cols)
    _LOG.info("Writing data to tab '%s' in Google Sheet", tabname)
    cmd = (
        f"to_gsheet.py --input_file '{input_file}' --url '{url}' "
        f"--tabname '{tabname}' --overwrite"
    )
    hsystem.system(cmd, print_command=True)
    _LOG.info("Successfully wrote data to Google Sheet")
