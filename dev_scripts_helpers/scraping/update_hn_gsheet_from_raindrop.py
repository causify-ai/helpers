#!/usr/bin/env -S uv run

# /// script
# dependencies = [
#   "pandas",
#   "requests",
# ]
# ///

r"""
Download Raindrop.io links and sync with Google Sheets.

This script manages three actions:
1. download_hn_gsheet: Download data from Google Sheets to CSV
2. download_raindrop_data: Fetch links from Raindrop.io after the latest
   timestamp and prepend them to the CSV
3. upload_hn_gsheet: Upload the combined CSV to a new tab in Google Sheets

Example usage:

# Download data from Google Sheets
> update_hn_gsheet_from_raindrop.py \
    --url "https://docs.google.com/spreadsheets/d/1i6Z7v2..." \
    --action download_hn_gsheet

# Download new links from Raindrop
> update_hn_gsheet_from_raindrop.py \
    --action download_raindrop_data

# Upload combined data back to Google Sheets
> update_hn_gsheet_from_raindrop.py \
    --url "https://docs.google.com/spreadsheets/d/1i6Z7v2..." \
    --action upload_hn_gsheet

Import as:

import dev_scripts_helpers.scraping.update_hn_gsheet_from_raindrop as dshshufr
"""

import argparse
import logging
import os

import pandas as pd
import requests

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# #############################################################################
# Constants
# #############################################################################

DEFAULT_TMP_DIR = "/tmp"
GSHEET_CSV_FILE = "hn_gsheet.csv"
RAINDROP_CSV_FILE = "raindrop_data.csv"
COMBINED_CSV_FILE = "combined_data.csv"


# #############################################################################
# Helper functions
# #############################################################################


def _get_tmp_file_path(filename: str, *, tmp_dir: str = DEFAULT_TMP_DIR) -> str:
    """Get the path for a temporary file."""
    return os.path.join(tmp_dir, filename)


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
    df = pd.read_csv(output_file)
    _LOG.info("Loaded %d rows and %d columns", len(df), len(df.columns))
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
    df_gsheet = pd.read_csv(gsheet_csv)
    if "timestamp" in df_gsheet.columns:
        latest_timestamp = df_gsheet["timestamp"].max()
        _LOG.info("Latest timestamp in gsheet: %s", latest_timestamp)
    else:
        latest_timestamp = 0
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
            if "created" in item and item["created"] > latest_timestamp:
                all_bookmarks.append(item)
                count += 1
        url = data.get("pagination", {}).get("nextLink")
    _LOG.info("Downloaded %d new bookmarks after timestamp", count)
    df_raindrop = pd.DataFrame(all_bookmarks)
    raindrop_csv = _get_tmp_file_path(RAINDROP_CSV_FILE)
    _LOG.info("Writing Raindrop data to CSV file: '%s'", raindrop_csv)
    df_raindrop.to_csv(raindrop_csv, index=False)
    return raindrop_csv


def _combine_csv_files() -> str:
    """
    Combine Raindrop data with gsheet data, prepending Raindrop data.

    Reads the gsheet CSV and Raindrop CSV files, concatenates them with
    Raindrop data first, and saves the result to a combined CSV file.

    :return: Path to the combined CSV file
    """
    gsheet_csv = _get_tmp_file_path(GSHEET_CSV_FILE)
    raindrop_csv = _get_tmp_file_path(RAINDROP_CSV_FILE)
    hdbg.dassert_path_exists(gsheet_csv, "gsheet CSV file not found")
    hdbg.dassert_path_exists(raindrop_csv, "raindrop CSV file not found")
    _LOG.info("Loading gsheet CSV data")
    df_gsheet = pd.read_csv(gsheet_csv)
    _LOG.info("Loading Raindrop CSV data")
    df_raindrop = pd.read_csv(raindrop_csv)
    _LOG.info(
        "Combining data: %d raindrop items, %d gsheet items",
        len(df_raindrop),
        len(df_gsheet),
    )
    df_combined = pd.concat(
        [df_raindrop, df_gsheet], ignore_index=True
    )
    combined_csv = _get_tmp_file_path(COMBINED_CSV_FILE)
    _LOG.info("Writing combined data to CSV file: '%s'", combined_csv)
    df_combined.to_csv(combined_csv, index=False)
    _LOG.info(
        "Combined CSV created with %d rows", len(df_combined)
    )
    return combined_csv


def _upload_to_gsheet(url: str, *, tabname: str = "raindrop_sync") -> None:
    """
    Upload combined CSV data to a new tab in Google Sheets.

    Reads the combined CSV file and uploads it to the specified tab in the
    Google Sheet, creating the tab if it doesn't exist or overwriting it.

    :param url: URL of the Google Sheets document
    :param tabname: Name of the tab to create/overwrite
    """
    combined_csv = _get_tmp_file_path(COMBINED_CSV_FILE)
    hdbg.dassert_path_exists(combined_csv, "combined CSV file not found")
    _LOG.info("Reading combined CSV file: '%s'", combined_csv)
    df = pd.read_csv(combined_csv)
    _LOG.info("Loaded %d rows and %d columns", len(df), len(df.columns))
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
    parser.add_argument(
        "--action",
        action="store",
        required=True,
        choices=[
            "download_hn_gsheet",
            "download_raindrop_data",
            "upload_hn_gsheet",
        ],
        help="Action to perform",
    )
    hparser.add_verbosity_arg(parser)
    return parser


# #############################################################################
# Main
# #############################################################################


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    if args.action in ["download_hn_gsheet", "upload_hn_gsheet"]:
        hdbg.dassert_is_not(
            args.url,
            None,
            "--url is required for this action"
        )
    if args.action == "download_hn_gsheet":
        _download_from_gsheet(args.url)
    elif args.action == "download_raindrop_data":
        _download_from_raindrop()
        _combine_csv_files()
    elif args.action == "upload_hn_gsheet":
        _upload_to_gsheet(args.url)


if __name__ == "__main__":
    _main(_parse())
