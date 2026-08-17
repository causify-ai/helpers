#!/usr/bin/env -S uv run

# /// script
# dependencies = [
#   "requests",
# ]
# ///

r"""
Update Google Sheets data with Raindrop.io data.

This script manages four actions:
- Download_gsheet_links: Download data from Google Sheets to CSV
- Download_raindrop_data: Fetch links from Raindrop.io after the latest
  timestamp and save to CSV
- Combine_data: Transform and combine Raindrop data with gsheet structure
- Upload_gsheet_links: Upload the combined CSV to a new tab in Google Sheets

# Usage Example

- Download data from Google Sheets (only that action):
> update_gsheet_links_from_raindrop.py \
    --url "https://docs.google.com/spreadsheets/d/1i6Z7v2..." \
    --clear_actions --action download_gsheet_links

- Run all actions:
> update_gsheet_links_from_raindrop.py \
    --url "https://docs.google.com/spreadsheets/d/1i6Z7v2..." \
    --all_actions

- Skip the upload action:
> update_gsheet_links_from_raindrop.py \
    --url "https://docs.google.com/spreadsheets/d/1i6Z7v2..." \
    --skip_action upload_gsheet_links

Each action (other than `upload_gsheet_links`, which has no local output
file) is skipped automatically if its output file already exists. Pass
`--no_incremental` to force every selected action to re-run:
> update_gsheet_links_from_raindrop.py \
    --url "https://docs.google.com/spreadsheets/d/1i6Z7v2..." \
    --all_actions --no_incremental

Import as:

import dev_scripts_helpers.download.update_gsheet_links_from_raindrop as dsglfr
"""

import argparse
import logging
import os
from datetime import datetime
from typing import Optional

import requests

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hselect_action as hselacti
import helpers.htable as htable
import dev_scripts_helpers.download.bookmark_utils as dshdbou

_LOG = logging.getLogger(__name__)

# #############################################################################
# Constants
# #############################################################################

# Filenames for temporary CSV files used in the synchronization pipeline.
GSHEET_CSV_FILE = "hn_gsheet.csv"
RAINDROP_CSV_FILE = "raindrop_data.csv"
COMBINED_CSV_FILE = "combined_data.csv"


# #############################################################################
# Helper functions
# #############################################################################


def _log_first_rows(csv_file: str, *, action_desc: str) -> None:
    """
    Log the first 3 rows of a CSV file right after it was read, written, or
    combined, to spot obvious issues (wrong sheet, malformed header) early.

    :param csv_file: path to the CSV file to preview
    :param action_desc: short description of what just happened to the file
        (e.g., "Read", "Wrote"), used in the log message
    """
    _LOG.info(
        "%s '%s', first 3 rows:\n%s",
        action_desc,
        csv_file,
        htable.csv_to_str(csv_file, max_rows=3),
    )


def _resolve_gsheet_url(url: str) -> str:
    """
    Resolve the Google Sheets URL from the CLI arg or the `LINKS_GSHEET` env
    variable.

    :param url: URL passed via `--url` (empty string if not passed)
    :return: resolved, non-empty URL
    """
    if not url:
        url = os.environ.get("LINKS_GSHEET", "")
    hdbg.dassert_ne(
        url,
        "",
        "Specify --url or set the LINKS_GSHEET environment variable",
    )
    return url


def _download_gsheet_links(url: str) -> str:
    """
    Download data from Google Sheets and save to a temporary CSV file.

    :param url: URL of the Google Sheets document
    :return: Path to the saved CSV file
    """
    _LOG.debug(hprint.func_signature_to_str())
    # Compute the shared temporary path used by the rest of the pipeline.
    output_file = dshdbou.get_tmp_file_path(
        GSHEET_CSV_FILE, "update_gsheet_links_from_raindrop"
    )
    dshdbou.download_from_gsheet(url, output_file)
    _LOG.debug("return=%s", output_file)
    return output_file


def _parse_timestamp(ts_str: str) -> datetime:
    """
    Parse a timestamp string in either ISO 8601 (Raindrop) or gsheet format.

    :param ts_str: timestamp string, e.g. "2021-05-01T12:00:00.000Z" (Raindrop
        `created` field) or "2021-05-01 12:00:00" (gsheet `Timestamp` column)
    :return: parsed, timezone-naive datetime (in UTC)
    """
    try:
        iso_str = ts_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(iso_str).replace(tzinfo=None)
    except ValueError:
        dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
    return dt


def _get_latest_timestamp_from_file(gsheet_csv: str) -> datetime:
    """
    Get the latest `Timestamp` value from a gsheet CSV file.

    :param gsheet_csv: path to the gsheet CSV file
    :return: latest timestamp found in the file
    """
    _LOG.debug(hprint.to_str("gsheet_csv"))
    hdbg.dassert_path_exists(gsheet_csv, "Must download from gsheet first")
    _LOG.info("Loading gsheet CSV to find latest timestamp")
    rows_gsheet = dshdbou.read_csv(gsheet_csv)
    _log_first_rows(gsheet_csv, action_desc="Read")
    _LOG.debug(hprint.to_str("len(rows_gsheet)"))
    # The gsheet CSV must have a `Timestamp` column to compute the cutoff.
    hdbg.dassert(
        bool(rows_gsheet) and "Timestamp" in rows_gsheet[0],
        "gsheet CSV '%s' is missing the required 'Timestamp' column",
        gsheet_csv,
    )
    # Determine the latest timestamp in existing data to avoid re-downloading duplicates.
    latest_timestamp = max(
        _parse_timestamp(row["Timestamp"])
        for row in rows_gsheet
        if row.get("Timestamp")
    )
    _LOG.info("Latest timestamp in gsheet: '%s'", latest_timestamp)
    _LOG.debug("return=%s", latest_timestamp)
    return latest_timestamp


def _download_raindrop_data() -> str:
    """
    Download links from Raindrop.io after the latest timestamp from the
    gsheet CSV.

    Fetches all bookmarks from the Raindrop API that were created after the
    most recent timestamp in the existing gsheet data, then combines them.

    :return: Path to the CSV file with combined data
    """
    _LOG.debug(hprint.func_signature_to_str())
    # Load the gsheet CSV to find the cutoff timestamp for filtering new bookmarks.
    gsheet_csv = dshdbou.get_tmp_file_path(
        GSHEET_CSV_FILE, "update_gsheet_links_from_raindrop"
    )
    latest_timestamp = _get_latest_timestamp_from_file(gsheet_csv)

    # Retrieve Raindrop API token from environment and validate it exists.
    raindrop_token = os.environ.get("RAINDROP_API_TOKEN")
    hdbg.dassert_is_not(
        raindrop_token, None, "RAINDROP_API_TOKEN environment variable not set"
    )
    _LOG.info("Downloading bookmarks from Raindrop.io")
    headers = {"Authorization": f"Bearer {raindrop_token}"}
    # The Raindrop API paginates via `page`/`perpage` query params (max
    # `perpage` is 50); it does not return a `pagination.nextLink` field.
    url = "https://api.raindrop.io/rest/v1/raindrops/0"
    perpage = 50
    page = 0
    all_bookmarks = []
    count = 0
    # Paginate through all Raindrop bookmarks, newest first, until a short
    # page (fewer than `perpage` items) signals the last page.
    while True:
        _LOG.debug("Fetching Raindrop page %d", page)
        params = {"sort": "-created", "page": page, "perpage": perpage}
        response = requests.get(url, headers=headers, params=params)
        hdbg.dassert_eq(
            response.status_code,
            200,
            "Raindrop API returned %s",
            response.status_code,
        )
        data = response.json()
        items = data.get("items", [])
        _LOG.info("Fetched %d items from Raindrop (page %d)", len(items), page)
        # Filter bookmarks: keep only those created after the latest gsheet timestamp.
        for item in items:
            if (
                "created" in item
                and _parse_timestamp(item["created"]) > latest_timestamp
            ):
                all_bookmarks.append(item)
                count += 1
        # Stop once we hit a short page (last page) or an empty page.
        if len(items) < perpage:
            break
        page += 1
    _LOG.info("Downloaded %d new bookmarks after timestamp", count)
    _LOG.debug(hprint.to_str("len(all_bookmarks) count"))
    # Extract relevant fields and write bookmarks to CSV.
    raindrop_csv = dshdbou.get_tmp_file_path(
        RAINDROP_CSV_FILE, "update_gsheet_links_from_raindrop"
    )
    _LOG.info("Writing Raindrop data to CSV file: '%s'", raindrop_csv)
    if all_bookmarks:
        fields_to_keep = ["id", "title", "url", "created"]
        rows_to_write = []
        # Transform each Raindrop item: map fields to standard column names.
        for item in all_bookmarks:
            row = {
                "id": item.get("_id", ""),
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "created": item.get("created", ""),
            }
            rows_to_write.append(row)
        _LOG.debug(hprint.to_str("len(rows_to_write)"))
        dshdbou.write_csv(
            raindrop_csv, rows_to_write, fieldnames=fields_to_keep
        )
    else:
        # If no new bookmarks, write empty CSV with appropriate structure.
        dshdbou.write_csv(raindrop_csv, [], fieldnames=[])
    if all_bookmarks:
        _log_first_rows(raindrop_csv, action_desc="Wrote")
    _LOG.debug("return=%s", raindrop_csv)
    return raindrop_csv


def _combine_raindrop_with_gsheet_links() -> str:
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
    _LOG.debug(hprint.func_signature_to_str())
    # Load both CSV files and extract the gsheet column schema.
    gsheet_csv = dshdbou.get_tmp_file_path(
        GSHEET_CSV_FILE, "update_gsheet_links_from_raindrop"
    )
    raindrop_csv = dshdbou.get_tmp_file_path(
        RAINDROP_CSV_FILE, "update_gsheet_links_from_raindrop"
    )
    hdbg.dassert_path_exists(gsheet_csv, "gsheet CSV file not found")
    hdbg.dassert_path_exists(raindrop_csv, "raindrop CSV file not found")
    _LOG.info("Loading gsheet CSV to get schema")
    rows_gsheet = dshdbou.read_csv(gsheet_csv)
    _log_first_rows(gsheet_csv, action_desc="Read")
    gsheet_columns = list(rows_gsheet[0].keys()) if rows_gsheet else []
    _LOG.info("Gsheet schema: %s", gsheet_columns)
    _LOG.info("Loading Raindrop CSV data")
    rows_raindrop = dshdbou.read_csv(raindrop_csv)
    if rows_raindrop:
        _log_first_rows(raindrop_csv, action_desc="Read")
    _LOG.debug(hprint.to_str("len(rows_raindrop)"))
    # Transform Raindrop rows to match gsheet structure: map fields and convert timestamps.
    rows_combined = []
    for row in rows_raindrop:
        # Initialize combined row with empty strings for all gsheet columns.
        combined_row = {col: "" for col in gsheet_columns}
        # Map Raindrop title field: strip "| Hacker News" suffix if present.
        if "title" in row:
            title = row["title"]
            # Remove "| Hacker News" suffix from the title.
            if title.endswith("| Hacker News"):
                title = title[: -len("| Hacker News")].strip()
            combined_row["Title"] = title
        # Raindrop's "url" is the HN item link (e.g., these bookmarks are of
        # the HN discussion page, not the linked article), so it maps to the
        # gsheet's "Hn_url" column; "Article_url" is left empty (unknown).
        if "url" in row:
            combined_row["Hn_url"] = row["url"]
        # Convert Raindrop ISO 8601 timestamp to gsheet format: YYYY-MM-DD HH:MM:SS.
        if "created" in row:
            try:
                iso_str = row["created"].replace("Z", "+00:00")
                dt = datetime.fromisoformat(iso_str)
                combined_row["Timestamp"] = dt.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, AttributeError) as e:
                _LOG.warning(
                    "Failed to parse timestamp '%s': %s",
                    row["created"],
                    e,
                )
                # Use original timestamp string if parsing fails.
                combined_row["Timestamp"] = row["created"]
        rows_combined.append(combined_row)
    # Prepend Raindrop data (newest first) and append existing gsheet data.
    rows_combined.extend(rows_gsheet)
    _LOG.debug(hprint.to_str("len(rows_combined)"))
    combined_csv = dshdbou.get_tmp_file_path(
        COMBINED_CSV_FILE, "update_gsheet_links_from_raindrop"
    )
    _LOG.info(
        "Combining data: %d raindrop items, %d gsheet items",
        len(rows_raindrop),
        len(rows_gsheet),
    )
    _LOG.info("Writing combined data to CSV file: '%s'", combined_csv)
    # Write combined data preserving gsheet column order.
    if rows_combined:
        dshdbou.write_csv(
            combined_csv, rows_combined, fieldnames=gsheet_columns
        )
    else:
        dshdbou.write_csv(combined_csv, [], fieldnames=gsheet_columns)
    if rows_combined:
        _log_first_rows(combined_csv, action_desc="Combined into")
    _LOG.info("Combined CSV created with %d rows", len(rows_combined))
    _LOG.debug("return=%s", combined_csv)
    return combined_csv


def _upload_to_gsheet(url: str) -> None:
    """
    Upload combined CSV data to a new tab in Google Sheets.

    Reads the combined CSV file and uploads it to the specified tab in the
    Google Sheet, creating the tab if it doesn't exist or overwriting it.

    :param url: URL of the Google Sheets document
    """
    _LOG.debug(hprint.to_str("url"))
    # Build a dated tab name so re-runs on the same day overwrite the same tab.
    tabname = "update_gsheet_links_from_raindrop." + datetime.now().strftime(
        "%Y-%m-%d"
    )
    combined_csv = dshdbou.get_tmp_file_path(
        COMBINED_CSV_FILE, "update_gsheet_links_from_raindrop"
    )
    hdbg.dassert_path_exists(combined_csv, "combined CSV file not found")
    _LOG.debug(hprint.to_str("tabname combined_csv"))
    dshdbou.upload_to_gsheet(url, combined_csv, tabname)


def _get_action_output_file(action: str) -> Optional[str]:
    """
    Get the output file that an action produces, if any.

    Used to support incremental runs: an action is skipped when its output
    file already exists (unless `--no_incremental` is passed).

    :param action: name of the action
    :return: path to the action's output file, or `None` if the action has
        no local output file to check against (e.g., `upload_gsheet_links`,
        which only has a side effect on the remote gsheet)
    """
    action_to_filename = {
        "download_gsheet_links": GSHEET_CSV_FILE,
        "download_raindrop_data": RAINDROP_CSV_FILE,
        "combine_data": COMBINED_CSV_FILE,
    }
    filename = action_to_filename.get(action)
    if filename is None:
        return None
    return dshdbou.get_tmp_file_path(
        filename, "update_gsheet_links_from_raindrop"
    )


# #############################################################################
# Argument parsing
# #############################################################################

# Define the four-step pipeline: download gsheet, download raindrop, combine, and upload.
_VALID_ACTIONS = [
    "download_gsheet_links",
    "download_raindrop_data",
    "combine_data",
    "upload_gsheet_links",
]
# By default, execute all actions in order.
_DEFAULT_ACTIONS = _VALID_ACTIONS[:]


def _parse() -> argparse.ArgumentParser:
    _LOG.debug(hprint.func_signature_to_str())
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    parser.add_argument(
        "--url",
        action="store",
        default="",
        help="URL of the Google Sheets document (required for "
        "download_gsheet_links and upload_gsheet_links actions); falls back "
        "to the LINKS_GSHEET environment variable if not specified",
    )
    parser.add_argument(
        "--no_incremental",
        action="store_true",
        help="Force re-execution of every selected action even if its "
        "output file already exists (by default, an action is skipped "
        "when its output file is already present)",
    )
    hselacti.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    hparser.add_verbosity_arg(parser)
    return parser


# #############################################################################
# Main
# #############################################################################


def _main(parser: argparse.ArgumentParser) -> None:
    _LOG.debug(hprint.func_signature_to_str())
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Determine which actions to execute based on command-line arguments.
    actions = hselacti.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    _LOG.info(
        "Actions to execute:\n%s",
        hselacti.actions_to_string(actions, _VALID_ACTIONS, add_frame=True),
    )
    # Execute actions sequentially in the order specified by the user.
    while actions:
        action = actions[0]
        to_execute, actions = hselacti.mark_action(action, actions)
        if not to_execute:
            continue
        _LOG.debug("Executing action: '%s'", action)
        # Skip the action if its output file already exists (incremental
        # mode), unless the caller forced a full re-run.
        if not args.no_incremental:
            output_file = _get_action_output_file(action)
            if output_file is not None and os.path.exists(output_file):
                _LOG.warning(
                    "Skipping action '%s': output file '%s' already exists "
                    "(use --no_incremental to force)",
                    action,
                    output_file,
                )
                continue
        # Execute each action with required argument validation.
        if action == "download_gsheet_links":
            url = _resolve_gsheet_url(args.url)
            _download_gsheet_links(url)
        elif action == "download_raindrop_data":
            _download_raindrop_data()
        elif action == "combine_data":
            _combine_raindrop_with_gsheet_links()
        elif action == "upload_gsheet_links":
            url = _resolve_gsheet_url(args.url)
            _upload_to_gsheet(url)
        else:
            raise ValueError(f"Invalid action='{action}'")
    hdbg.dassert_eq(
        len(actions), 0, "There are unprocessed actions: %s", str(actions)
    )


if __name__ == "__main__":
    _main(_parse())
