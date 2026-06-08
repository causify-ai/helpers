#!/usr/bin/env -S uv run

# /// script
# dependencies = [
#   "google",
#   "googleapi",
#   "gspread",
#   "pandas",
#   "pyyaml",
#   "tqdm",
# ]
# ///

r"""
Download data from a Google Sheets document and save it as a CSV file.

Tab Selection:
- If the URL contains a gid (e.g., ?gid=123#gid=123), the script automatically
  downloads that specific tab, even if --tabname is not specified.
- Use --tabname to override the gid and download a different tab.
- If no gid is in the URL and no --tabname is provided, downloads the first tab.

Example usage:

# Download first tab to CSV
> from_gsheet.py \
    --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit" \
    --output_file data.csv

# Download specific tab by name
> from_gsheet.py \
    --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit" \
    --tabname "my_data" \
    --output_file data.csv

# Automatically download tab from gid in URL (no --tabname needed)
> from_gsheet.py \
    --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit?gid=123#gid=123" \
    --output_file data.csv

# Override gid with explicit tab name
> from_gsheet.py \
    --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit?gid=123#gid=123" \
    --tabname "different_tab" \
    --output_file data.csv

Import as:

import dev_scripts_helpers.google.from_gsheet as dshgofrgs
"""

import argparse
import logging
import os

import helpers.hdbg as hdbg
import helpers.hgoogle_drive_api as hgodrapi
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--url",
        action="store",
        required=True,
        help="URL of the Google Sheets document",
    )
    parser.add_argument(
        "--tabname",
        action="store",
        default="",
        help="Name of the tab to read from (default: first tab)",
    )
    parser.add_argument(
        "--output_file",
        action="store",
        required=True,
        help="Path to output CSV file",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite the output file if it already exists",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Check if output file already exists.
    if os.path.exists(args.output_file) and not args.overwrite:
        hdbg.dfatal(
            f"Output file '{args.output_file}' already exists. Use --overwrite to replace it."
        )
    # Get credentials.
    _LOG.info("Loading Google API credentials")
    credentials = hgodrapi.get_credentials()
    # Print information about the Google Sheet.
    _LOG.info("Google Sheet information:")
    hgodrapi.print_info_about_google_url(args.url, credentials=credentials)
    # Determine tab name
    tab_name = args.tabname
    if not tab_name:
        # If not provided, check if URL has a gid.
        gid = hgodrapi._extract_gid_from_url(args.url)
        if gid:
            spreadsheet_id = hgodrapi._extract_file_id_from_url(args.url)
            tab_name = hgodrapi.get_tab_name_from_gid(
                spreadsheet_id, gid, credentials=credentials
            )
            _LOG.info(
                "Found gid '%s' in URL, using tab name '%s'", gid, tab_name
            )
    # Read data from Google Sheet.
    if tab_name:
        _LOG.info("Reading data from tab '%s'", tab_name)
    else:
        _LOG.warning("Reading data from first tab")
    df = hgodrapi.from_gsheet(
        args.url,
        tab_name=tab_name,
        credentials=credentials,
    )
    _LOG.info("Loaded %d rows and %d columns", len(df), len(df.columns))
    # Save to CSV.
    _LOG.info("Writing data to CSV file: '%s'", args.output_file)
    df.to_csv(args.output_file, index=False)
    _LOG.info("Successfully saved data to CSV file")


if __name__ == "__main__":
    _main(_parse())
