#!/usr/bin/env python

"""
Load a CSV file to a Google Sheets document.

Example usage:
    # Load CSV to a new tab
    > to_gsheet.py \\
        --input_file data.csv \\
        --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit" \\
        --tabname "my_data"

    # Overwrite existing tab
    > to_gsheet.py \\
        --input_file data.csv \\
        --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit" \\
        --tabname "my_data" \\
        --overwrite

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
    # Check if the tab already exists.
    existing_tabs = hgodrapi.get_tabs_from_gsheet(
        args.url, credentials=credentials
    )
    tab_exists = args.tabname in existing_tabs
    if tab_exists and not args.overwrite:
        hdbg.dfatal(
            f"Tab '{args.tabname}' already exists in the Google Sheet. Use --overwrite to replace it."
        )
    # Write data to Google Sheet.
    _LOG.info("Writing data to tab '%s' in Google Sheet", args.tabname)
    hgodrapi.to_gsheet(
        df,
        args.url,
        tab_name=args.tabname,
        freeze_rows=True,
        credentials=credentials,
    )
    _LOG.info("Successfully wrote data to Google Sheet")


if __name__ == "__main__":
    _main(_parse())
