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
Load a CSV file to a Google Sheets document.

Tab Selection:
- By default, the gid in the URL is ignored. Use --tabname to specify which tab
  to write to (default: 'new_data').
- With --use_gid flag, the tab name is extracted from the gid in the URL and the
  --tabname argument is ignored. The URL must contain a gid for this to work.

Example usage:

# Load CSV to a new tab (default tab name: 'new_data')
> to_gsheet.py \
    --input_file data.csv \
    --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit"

# Load CSV to a specific tab
> to_gsheet.py \
    --input_file data.csv \
    --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit" \
    --tabname "my_data"

# Overwrite existing tab
> to_gsheet.py \
    --input_file data.csv \
    --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit" \
    --tabname "my_data" \
    --overwrite

# Extract tab name from gid in URL (ignores --tabname)
> to_gsheet.py \
    --input_file data.csv \
    --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit?gid=123#gid=123" \
    --use_gid

Import as:

import dev_scripts_helpers.google.to_gsheet as dshgotgs
"""

import argparse
import logging

import pandas as pd

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
        "--input_file",
        action="store",
        required=True,
        help="Path to input CSV file",
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
        default="new_data",
        help="Name of the tab to write to (default: 'new_data')",
    )
    parser.add_argument(
        "--use_gid",
        action="store_true",
        default=False,
        help="Extract tab name from gid in the URL instead of using --tabname",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite the tab if it already exists",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Validate input file exists.
    hdbg.dassert_path_exists(args.input_file)
    _LOG.info("Reading CSV file: '%s'", args.input_file)
    # Read CSV file.
    df = pd.read_csv(args.input_file)
    _LOG.info("Loaded %d rows and %d columns", len(df), len(df.columns))
    # Get credentials.
    _LOG.info("Loading Google API credentials")
    credentials = hgodrapi.get_credentials()
    # Print information about the Google Sheet.
    _LOG.info("Google Sheet information:")
    hgodrapi.print_info_about_google_url(args.url, credentials=credentials)
    # Determine tab name: if --use_gid is provided, extract from URL.
    tab_name = args.tabname
    if args.use_gid:
        gid = hgodrapi._extract_gid_from_url(args.url)
        hdbg.dassert_is_not(
            gid,
            None,
            "No gid found in URL. Cannot use --use_gid flag without gid in URL: %s",
            args.url,
        )
        spreadsheet_id = hgodrapi._extract_file_id_from_url(args.url)
        tab_name = hgodrapi.get_tab_name_from_gid(
            spreadsheet_id, gid, credentials=credentials
        )
        _LOG.info(
            "Using --use_gid flag, extracted tab name '%s' from gid '%s'",
            tab_name,
            gid,
        )
    # Check if the tab already exists.
    existing_tabs = hgodrapi.get_tabs_from_gsheet(
        args.url, credentials=credentials
    )
    tab_exists = tab_name in existing_tabs
    hdbg.dassert_imply(
        tab_exists,
        args.overwrite,
        f"Tab '{tab_name}' already exists in the Google Sheet. Use --overwrite to replace it.",
    )
    # Write data to Google Sheet.
    _LOG.info("Writing data to tab '%s' in Google Sheet", tab_name)
    hgodrapi.to_gsheet(
        df,
        args.url,
        tab_name=tab_name,
        freeze_rows=True,
        credentials=credentials,
    )
    _LOG.info("Successfully wrote data to Google Sheet")


if __name__ == "__main__":
    _main(_parse())
