#!/usr/bin/env -S uv run

# /// script
# dependencies = [
#   "requests",
# ]
# ///

r"""
Download Raindrop.io links and sync with Google Sheets.

This script manages four actions:
1. download_hn_gsheet: Download data from Google Sheets to CSV
2. download_raindrop_data: Fetch links from Raindrop.io after the latest
   timestamp and save to CSV
3. combine: Transform and combine Raindrop data with gsheet structure
4. upload_hn_gsheet: Upload the combined CSV to a new tab in Google Sheets

Example usage:

# Download data from Google Sheets
> update_hn_gsheet_from_raindrop.py \
    --url "https://docs.google.com/spreadsheets/d/1i6Z7v2..." \
    -a download_hn_gsheet

# Run all actions
> update_hn_gsheet_from_raindrop.py \
    --url "https://docs.google.com/spreadsheets/d/1i6Z7v2..." \
    --all

# Skip upload action
> update_hn_gsheet_from_raindrop.py \
    --url "https://docs.google.com/spreadsheets/d/1i6Z7v2..." \
    -sa upload_hn_gsheet

Import as:

import dev_scripts_helpers.scraping.update_hn_gsheet_from_raindrop as dshshufr
"""

import argparse
import csv
import logging
import os
from datetime import datetime
from typing import List, Dict, Any

import requests

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hsystem as hsystem
import helpers.hselect_action as hselacti

_LOG = logging.getLogger(__name__)

# #############################################################################
# Constants
# #############################################################################

GSHEET_CSV_FILE = "hn_gsheet.csv"
RAINDROP_CSV_FILE = "raindrop_data.csv"
COMBINED_CSV_FILE = "combined_data.csv"


# #############################################################################
# Helper functions
# #############################################################################


def _get_tmp_file_path(filename: str) -> str:
    """
    Get the path for a temporary file.
    """
    return "./tmp.update_hn_gsheet_from_raindrop." + filename


def _read_csv(filepath: str) -> List[Dict[str, Any]]:
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


def _write_csv(
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


def _download_from_gsheet(url: str) -> str:
    """
    Download data from Google Sheets and save to a temporary CSV file.

    Retrieves data from the 'All' tab and saves it to a temporary CSV
    for later processing and combination with Raindrop data.

    :param url: URL of the Google Sheets document
    :return: Path to the saved CSV file
    """
    _LOG.info("Downloading data from Google Sheets")
    output_file = _get_tmp_file_path(GSHEET_CSV_FILE)
    cmd = (
        f"from_gsheet.py --url '{url}' --tabname 'All' "
        f"--output_file '{output_file}' --overwrite"
    )
    hsystem.system(cmd, print_command=True)
    hdbg.dassert_path_exists(output_file)
    rows = _read_csv(output_file)
    num_cols = len(rows[0].keys()) if rows else 0
    _LOG.info("Loaded %d rows and %d columns", len(rows), num_cols)
    _LOG.info("Successfully downloaded and saved data")
    return output_file


def _download_from_raindrop() -> str:
    """
    Download links from Raindrop.io after the latest timestamp from the
    gsheet CSV.

    Fetches all bookmarks from the Raindrop API that were created after the
    most recent timestamp in the existing gsheet data, then combines them.

    :return: Path to the CSV file with combined data
    """
    gsheet_csv = _get_tmp_file_path(GSHEET_CSV_FILE)
    hdbg.dassert_path_exists(
        gsheet_csv, "Must download from gsheet first"
    )
    _LOG.info("Loading gsheet CSV to find latest timestamp")
    rows_gsheet = _read_csv(gsheet_csv)
    if rows_gsheet and "timestamp" in rows_gsheet[0]:
        latest_timestamp = max(
            float(row.get("timestamp", 0)) for row in rows_gsheet
        )
        _LOG.info("Latest timestamp in gsheet: %s", latest_timestamp)
    else:
        latest_timestamp = None
        _LOG.info("No timestamp column found, fetching all bookmarks")
    raindrop_token = os.environ.get("RAINDROP_API_TOKEN")
    hdbg.dassert_is_not(
        raindrop_token,
        None,
        "RAINDROP_API_TOKEN environment variable not set"
    )
    _LOG.info("Downloading bookmarks from Raindrop.io")
    headers = {"Authorization": f"Bearer {raindrop_token}"}
    url = "https://api.raindrop.io/rest/v1/raindrops/0"
    all_bookmarks = []
    count = 0
    while url:
        response = requests.get(url, headers=headers)
        hdbg.dassert_eq(
            response.status_code,
            200,
            "Raindrop API returned %s",
            response.status_code,
        )
        data = response.json()
        items = data.get("items", [])
        _LOG.info("Fetched %d items from Raindrop", len(items))
        for item in items:
            if "created" in item:
                if latest_timestamp is None or float(item["created"]) > latest_timestamp:
                    all_bookmarks.append(item)
                    count += 1
        url = data.get("pagination", {}).get("nextLink")
    _LOG.info("Downloaded %d new bookmarks after timestamp", count)
    raindrop_csv = _get_tmp_file_path(RAINDROP_CSV_FILE)
    _LOG.info("Writing Raindrop data to CSV file: '%s'", raindrop_csv)
    if all_bookmarks:
        fields_to_keep = ["id", "title", "url", "created"]
        rows_to_write = []
        for item in all_bookmarks:
            row = {
                "id": item.get("_id", ""),
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "created": item.get("created", ""),
            }
            rows_to_write.append(row)
        _write_csv(raindrop_csv, rows_to_write, fieldnames=fields_to_keep)
    else:
        _write_csv(raindrop_csv, [], fieldnames=[])
    return raindrop_csv


def _combine_raindrop_with_gsheet() -> str:
    """
    Transform and combine Raindrop data with gsheet structure.

    Maps Raindrop fields to gsheet columns:
    - title -> Title
    - url -> Url
    - created -> Timestamp (converted from ISO 8601 to YYYY-MM-DD HH:MM:SS)
    - id -> discarded
    - Other gsheet columns left empty for Raindrop rows

    Raindrop data is prepended to gsheet data in the combined CSV.

    :return: Path to the combined CSV file
    """
    gsheet_csv = _get_tmp_file_path(GSHEET_CSV_FILE)
    raindrop_csv = _get_tmp_file_path(RAINDROP_CSV_FILE)
    hdbg.dassert_path_exists(gsheet_csv, "gsheet CSV file not found")
    hdbg.dassert_path_exists(raindrop_csv, "raindrop CSV file not found")
    _LOG.info("Loading gsheet CSV to get schema")
    rows_gsheet = _read_csv(gsheet_csv)
    gsheet_columns = list(rows_gsheet[0].keys()) if rows_gsheet else []
    _LOG.info("Gsheet schema: %s", gsheet_columns)
    _LOG.info("Loading Raindrop CSV data")
    rows_raindrop = _read_csv(raindrop_csv)
    rows_combined = []
    for row in rows_raindrop:
        combined_row = {col: "" for col in gsheet_columns}
        if "title" in row:
            combined_row["Title"] = row["title"]
        if "url" in row:
            combined_row["Url"] = row["url"]
        if "created" in row:
            try:
                iso_str = row["created"].replace('Z', '+00:00')
                dt = datetime.fromisoformat(iso_str)
                combined_row["Timestamp"] = dt.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, AttributeError) as e:
                _LOG.warning(
                    "Failed to parse timestamp '%s': %s",
                    row["created"],
                    e,
                )
                combined_row["Timestamp"] = row["created"]
        rows_combined.append(combined_row)
    rows_combined.extend(rows_gsheet)
    combined_csv = _get_tmp_file_path(COMBINED_CSV_FILE)
    _LOG.info(
        "Combining data: %d raindrop items, %d gsheet items",
        len(rows_raindrop),
        len(rows_gsheet),
    )
    _LOG.info("Writing combined data to CSV file: '%s'", combined_csv)
    if rows_combined:
        _write_csv(combined_csv, rows_combined, fieldnames=gsheet_columns)
    else:
        _write_csv(combined_csv, [], fieldnames=gsheet_columns)
    _LOG.info("Combined CSV created with %d rows", len(rows_combined))
    return combined_csv


def _upload_to_gsheet(url: str, *, tabname: str = None) -> None:
    """
    Upload combined CSV data to a new tab in Google Sheets.

    Reads the combined CSV file and uploads it to the specified tab in the
    Google Sheet, creating the tab if it doesn't exist or overwriting it.

    :param url: URL of the Google Sheets document
    :param tabname: Name of the tab to create/overwrite (defaults to today's date)
    """
    if tabname is None:
        tabname = datetime.now().strftime("%Y-%m-%d")
    combined_csv = _get_tmp_file_path(COMBINED_CSV_FILE)
    hdbg.dassert_path_exists(combined_csv, "combined CSV file not found")
    _LOG.info("Reading combined CSV file: '%s'", combined_csv)
    rows = _read_csv(combined_csv)
    num_cols = len(rows[0].keys()) if rows else 0
    _LOG.info("Loaded %d rows and %d columns", len(rows), num_cols)
    _LOG.info("Writing data to tab '%s' in Google Sheet", tabname)
    cmd = (
        f"to_gsheet.py --input_file '{combined_csv}' --url '{url}' "
        f"--tabname '{tabname}' --overwrite"
    )
    hsystem.system(cmd, print_command=True)
    _LOG.info("Successfully wrote data to Google Sheet")


# #############################################################################
# Argument parsing
# #############################################################################

VALID_ACTIONS = [
    "download_hn_gsheet",
    "download_raindrop_data",
    "combine",
    "upload_hn_gsheet",
]
DEFAULT_ACTIONS = [
    "download_hn_gsheet",
    "download_raindrop_data",
    "combine",
    "upload_hn_gsheet",
]


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--url",
        action="store",
        default=None,
        help="URL of the Google Sheets document (required for "
        "download_hn_gsheet and upload_hn_gsheet actions)",
    )
    hselacti.add_action_arg(parser, VALID_ACTIONS, DEFAULT_ACTIONS)
    hparser.add_verbosity_arg(parser)
    return parser


# #############################################################################
# Main
# #############################################################################


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    actions = hselacti.select_actions(
        args, VALID_ACTIONS, DEFAULT_ACTIONS
    )
    _LOG.info(
        "Actions to execute:\n%s",
        hselacti.actions_to_string(actions, VALID_ACTIONS, add_frame=True),
    )
    actions_remaining = actions
    while actions_remaining:
        action = actions_remaining[0]
        to_execute, actions_remaining = hselacti.mark_action(
            action, actions_remaining
        )
        if not to_execute:
            continue
        if action == "download_hn_gsheet":
            hdbg.dassert_is_not(
                args.url,
                None,
                "--url is required for download_hn_gsheet action",
            )
            _download_from_gsheet(args.url)
        elif action == "download_raindrop_data":
            _download_from_raindrop()
        elif action == "combine":
            _combine_raindrop_with_gsheet()
        elif action == "upload_hn_gsheet":
            hdbg.dassert_is_not(
                args.url,
                None,
                "--url is required for upload_hn_gsheet action",
            )
            _upload_to_gsheet(args.url)


if __name__ == "__main__":
    _main(_parse())
