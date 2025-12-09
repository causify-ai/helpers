#!/usr/bin/env python
"""
Fetch the Google sheet, authenticate it using OAuth service account and
download it and store it for future use. This removes the dependency of
fetching the file multiple times and enables faster re-use of the downloaded
version.

> ./download_gsheet.py \
    --sheet_url " " \
    --tab_name " " \
    --output_csv_name " " \
    --secret_path " "

Import as:

import dev_scripts_helpers.google.download_gsheet as d_gsheet
"""

import argparse
import logging

import helpers.hdbg as hdbg
import helpers.hgoogle_drive_api as hgodrapi
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

# #############################################################################


def _extract_sheet(
    sheet_url: str,
    tab_name: str,
    output_csv_name: str,
    *,
    service_key_path: str,
) -> None:
    """
    Fetch Google Sheet using OAuth service account and store it as CSV.

    :param sheet_url: Google Sheet URL
    :param tab_name: tab name inside Google Sheet
    :param output_csv_name: output CSV file path
    :param service_key_path: path to service account key JSON file
        (e.g., ~/.config/gspread_pandas/google_secret.json)
    """
    credentials = hgodrapi.get_credentials(service_key_path=service_key_path)
    _LOG.info("Using credentials from: %s", service_key_path)
    df = hgodrapi.read_google_file(
        credentials, sheet_url, tab_name=tab_name
    )
    df.to_csv(output_csv_name, index=False)
    _LOG.info("Sheet stored at: %s", output_csv_name)


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--sheet_url", required=True, help="URL of the Google Sheet."
    )
    parser.add_argument(
        "--tab_name", required=True, help="Tab name (default: first tab)."
    )
    parser.add_argument(
        "--output_csv_name", required=True, help="Output CSV file path."
    )
    parser.add_argument(
        "--secret_path",
        required=False,
        help="Path to service account key (optional).",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    _LOG.info("Reading sheet %s", args.sheet_url)
    _extract_sheet(
        args.sheet_url,
        args.tab_name,
        args.output_csv_name,
        service_key_path=args.secret_path,
    )


if __name__ == "__main__":
    _main(_parse())
