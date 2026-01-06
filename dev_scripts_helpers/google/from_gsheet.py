#!/usr/bin/env python

"""
Download data from a Google Sheets document and save it as a CSV file.

Example usage:
    # Download first tab to CSV
    > from_gsheet.py \\
        --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit" \\
        --output_file data.csv

    # Download specific tab to CSV
    > from_gsheet.py \\
        --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit" \\
        --tabname "my_data" \\
        --output_file data.csv

    # Overwrite existing file
    > from_gsheet.py \\
        --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit" \\
        --tabname "my_data" \\
        --output_file data.csv \\
        --overwrite

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
        default=None,
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
            "Output file '%s' already exists. Use --overwrite to replace it.",
            args.output_file,
        )
    # Get credentials.
    _LOG.info("Loading Google API credentials")
    credentials = hgodrapi.get_credentials()
    # Print information about the Google Sheet.
    _LOG.info("Google Sheet information:")
    hgodrapi.print_info_about_google_url(args.url, credentials=credentials)
    # Read data from Google Sheet.
    if args.tabname:
        _LOG.info("Reading data from tab '%s'", args.tabname)
    else:
        _LOG.info("Reading data from first tab")
    df = hgodrapi.from_gsheet(
        args.url,
        tab_name=args.tabname,
        credentials=credentials,
    )
    _LOG.info("Loaded %d rows and %d columns", len(df), len(df.columns))
    # Save to CSV.
    _LOG.info("Writing data to CSV file: '%s'", args.output_file)
    df.to_csv(args.output_file, index=False)
    _LOG.info("Successfully saved data to CSV file")


if __name__ == "__main__":
    _main(_parse())
