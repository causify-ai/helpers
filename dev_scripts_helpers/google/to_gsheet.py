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

Temporary Sheet:
- If --url is not specified, a new Google Sheet named `tmp_file_<timestamp>` is
  created in the temporary Google Drive folder and the CSV is written to its
  first tab (unless --tabname is specified).

# Usage Example

- Load CSV to a new temporary Google Sheet and open it in the browser:
> to_gsheet.py --input_file data.csv --open

- Load CSV to a new tab (default tab name: 'new_data'):
> to_gsheet.py \
    --input_file data.csv \
    --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit"

- Load CSV to a specific tab:
> to_gsheet.py \
    --input_file data.csv \
    --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit" \
    --tabname "my_data"

- Overwrite an existing tab:
> to_gsheet.py \
    --input_file data.csv \
    --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit" \
    --tabname "my_data" \
    --overwrite

- Extract tab name from gid in URL (ignores --tabname):
> to_gsheet.py \
    --input_file data.csv \
    --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit?gid=123#gid=123" \
    --use_gid

- Open the tab in the browser after the upload:
> to_gsheet.py \
    --input_file data.csv \
    --url "https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit" \
    --tabname "my_data" \
    --open

Import as:

import dev_scripts_helpers.google.to_gsheet as dshgotgs
"""

import argparse
import logging
import webbrowser

import pandas as pd

import helpers.hdbg as hdbg
import helpers.hgoogle_drive_api as hgodrapi
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
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
        default="",
        help="URL of the Google Sheets document (default: create a new "
        "temporary Google Sheet)",
    )
    parser.add_argument(
        "--tabname",
        action="store",
        default="",
        help="Name of the tab to write to (default: 'new_data' for an "
        "existing Google Sheet, the first tab for a new temporary Google "
        "Sheet)",
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
    parser.add_argument(
        "--open",
        action="store_true",
        default=False,
        help="Open the tab in the browser after writing the data",
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
    # Without a URL, create a new temporary Google Sheet.
    url = args.url
    is_tmp_gsheet = url == ""
    hdbg.dassert_imply(
        args.use_gid,
        not is_tmp_gsheet,
        "Cannot use --use_gid flag without --url",
    )
    if is_tmp_gsheet:
        url = hgodrapi.create_tmp_gsheet(credentials=credentials)
        _LOG.info("Created temporary Google Sheet: '%s'", url)
    # Print information about the Google Sheet.
    _LOG.info("Google Sheet information:")
    hgodrapi.print_info_about_google_url(url, credentials=credentials)
    existing_tabs = hgodrapi.get_tabs_from_gsheet(url, credentials=credentials)
    # Determine tab name: if --use_gid is provided, extract from URL.
    tab_name = args.tabname
    if args.use_gid:
        gid = hgodrapi._extract_gid_from_url(url)
        hdbg.dassert_is_not(
            gid,
            None,
            "No gid found in URL. Cannot use --use_gid flag without gid in URL: %s",
            url,
        )
        spreadsheet_id = hgodrapi._extract_file_id_from_url(url)
        tab_name = hgodrapi.get_tab_name_from_gid(
            spreadsheet_id, gid, credentials=credentials
        )
        _LOG.info(
            "Using --use_gid flag, extracted tab name '%s' from gid '%s'",
            tab_name,
            gid,
        )
    elif tab_name == "":
        if is_tmp_gsheet:
            # Use the empty first tab of the new Google Sheet.
            tab_name = existing_tabs[0]
        else:
            tab_name = "new_data"
    # Check if the tab already exists. A new temporary Google Sheet has nothing
    # to lose, so its first tab can always be written.
    overwrite = args.overwrite or is_tmp_gsheet
    tab_exists = tab_name in existing_tabs
    hdbg.dassert_imply(
        tab_exists,
        overwrite,
        f"Tab '{tab_name}' already exists in the Google Sheet. Use --overwrite to replace it.",
    )
    # Write data to Google Sheet.
    _LOG.info("Writing data to tab '%s' in Google Sheet", tab_name)
    hgodrapi.to_gsheet(
        df,
        url,
        tab_name=tab_name,
        freeze_rows=True,
        credentials=credentials,
    )
    _LOG.info("Successfully wrote data to Google Sheet")
    if args.open:
        tab_url = hgodrapi.get_gsheet_tab_url(
            url, tab_name, credentials=credentials
        )
        _LOG.info("Opening '%s' in the browser", tab_url)
        webbrowser.open(tab_url)


if __name__ == "__main__":
    _main(_parse())
