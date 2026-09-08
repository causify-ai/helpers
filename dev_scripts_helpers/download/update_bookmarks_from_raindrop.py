#!/usr/bin/env -S uv run

# /// script
# dependencies = [
#   "requests",
# ]
# ///

r"""
Sync new Raindrop.io bookmarks into a Google Sheet or a local CSV.

- `--target` selects the sync destination (default: `gsheet`):
    - `gsheet`: the original four-action pipeline, unchanged
      - Download_gsheet_links: Download data from Google Sheets to CSV
      - Download_raindrop_data: Fetch links from Raindrop.io after the latest
        timestamp and save to CSV
      - Combine_data: Transform and combine Raindrop data with gsheet structure
      - Upload_gsheet_links: Upload the combined CSV to a new tab in Google
        Sheets
    - `local_csv` (requires `--local_csv <path>`): only `download_raindrop_data`
      and `combine_data` apply; the latest-`Timestamp` cutoff is read directly
      from `--local_csv`, and `combine_data` prepends newly-fetched rows into
      that same file in place, leaving every existing row untouched

# Usage Example

- Download data from Google Sheets (only that action):
> update_bookmarks_from_raindrop.py \
    --url "https://docs.google.com/spreadsheets/d/1i6Z7v2..." \
    --clear_actions --action download_gsheet_links

- Run all gsheet actions:
> update_bookmarks_from_raindrop.py \
    --url "https://docs.google.com/spreadsheets/d/1i6Z7v2..." \
    --all_actions

- Skip the upload action:
> update_bookmarks_from_raindrop.py \
    --url "https://docs.google.com/spreadsheets/d/1i6Z7v2..." \
    --skip_action upload_gsheet_links

Each action (other than `upload_gsheet_links`, which has no local output
file) is skipped automatically if its output file already exists. Pass
`--no_incremental` to force every selected action to re-run:
> update_bookmarks_from_raindrop.py \
    --url "https://docs.google.com/spreadsheets/d/1i6Z7v2..." \
    --all_actions --no_incremental

- Sync new bookmarks directly into a local CSV instead of a Google Sheet:
> update_bookmarks_from_raindrop.py \
    --target local_csv --local_csv bookmarks/combined_data.csv \
    --action download_raindrop_data --action combine_data

Import as:

import dev_scripts_helpers.download.update_bookmarks_from_raindrop as dsbfr
"""

import argparse
import csv
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
import dev_scripts_helpers.download.bookmark_utils as dshdbout

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
    with open(csv_file) as f:
        rows = list(csv.reader(f))
    _LOG.info(
        "%s '%s', first 3 rows:\n%s",
        action_desc,
        csv_file,
        htable.csv_to_str(rows, max_rows=3),
    )


def _download_gsheet_links(url: str) -> str:
    """
    Download data from Google Sheets and save to a temporary CSV file.

    :param url: URL of the Google Sheets document
    :return: Path to the saved CSV file
    """
    _LOG.debug(hprint.func_signature_to_str())
    # Compute the shared temporary path used by the rest of the pipeline.
    output_file = dshdbout.get_tmp_file_path(
        GSHEET_CSV_FILE, "update_bookmarks_from_raindrop"
    )
    dshdbout.download_from_gsheet(url, output_file)
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


def _get_latest_timestamp_from_file(base_csv: str) -> datetime:
    """
    Get the latest `Timestamp` value from a CSV file.

    `base_csv` is the gsheet-downloaded CSV for `--target gsheet`, or the
    user's local CSV directly for `--target local_csv`.

    :param base_csv: path to the CSV file to scan
    :return: latest timestamp found in the file
    """
    _LOG.debug(hprint.to_str("base_csv"))
    hdbg.dassert_path_exists(base_csv, "Base CSV file not found")
    _LOG.info("Loading base CSV to find latest timestamp")
    rows_base = dshdbout.read_csv(base_csv)
    _log_first_rows(base_csv, action_desc="Read")
    _LOG.debug(hprint.to_str("len(rows_base)"))
    # The base CSV must have a `Timestamp` column to compute the cutoff.
    hdbg.dassert(
        bool(rows_base) and "Timestamp" in rows_base[0],
        "Base CSV '%s' is missing the required 'Timestamp' column",
        base_csv,
    )
    # Determine the latest timestamp in existing data to avoid re-downloading duplicates.
    latest_timestamp = max(
        _parse_timestamp(row["Timestamp"])
        for row in rows_base
        if row.get("Timestamp")
    )
    _LOG.info("Latest timestamp in base CSV: '%s'", latest_timestamp)
    _LOG.debug("return=%s", latest_timestamp)
    return latest_timestamp


def _download_raindrop_data(base_csv: str) -> str:
    """
    Download links from Raindrop.io after the latest timestamp in
    `base_csv`.

    Fetches all bookmarks from the Raindrop API that were created after the
    most recent timestamp in `base_csv` (the gsheet-downloaded CSV for
    `--target gsheet`, or the local CSV directly for `--target local_csv`).

    :param base_csv: path to the CSV file to read the latest-`Timestamp`
        cutoff from
    :return: Path to the CSV file with the newly-fetched Raindrop data
    """
    _LOG.debug(hprint.func_signature_to_str())
    # Find the cutoff timestamp for filtering new bookmarks.
    latest_timestamp = _get_latest_timestamp_from_file(base_csv)

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
    raindrop_csv = dshdbout.get_tmp_file_path(
        RAINDROP_CSV_FILE, "update_bookmarks_from_raindrop"
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
        dshdbout.write_csv(
            raindrop_csv, rows_to_write, fieldnames=fields_to_keep
        )
    else:
        # If no new bookmarks, write empty CSV with appropriate structure.
        dshdbout.write_csv(raindrop_csv, [], fieldnames=[])
    if all_bookmarks:
        _log_first_rows(raindrop_csv, action_desc="Wrote")
    _LOG.debug("return=%s", raindrop_csv)
    return raindrop_csv


def _combine_raindrop_with_gsheet_links(base_csv: str, output_csv: str) -> str:
    """
    Transform and combine Raindrop data with `base_csv`'s structure, writing
    the result to `output_csv`.

    Maps Raindrop fields to `base_csv` columns:
    - title -> Title
    - url -> Url
    - created -> Timestamp (converted from ISO 8601 to YYYY-MM-DD HH:MM:SS)
    - id -> discarded
    - Other `base_csv` columns left empty for Raindrop rows

    Raindrop data is prepended to `base_csv`'s existing rows.
    - For `--target gsheet`, `output_csv` is a separate combined tmp CSV
    - For `--target local_csv`, `output_csv` is the same path as `base_csv`,
      so this call merges the new rows into it in place, leaving every
      existing row (`Done` included) untouched

    :param base_csv: path to the CSV file providing existing rows and the
        column schema
    :param output_csv: path to write the combined CSV to (may be the same
        path as `base_csv` for an in-place merge)
    :return: Path to the combined CSV file (== `output_csv`)
    """
    _LOG.debug(hprint.func_signature_to_str())
    # Load both CSV files and extract the column schema from `base_csv`.
    raindrop_csv = dshdbout.get_tmp_file_path(
        RAINDROP_CSV_FILE, "update_bookmarks_from_raindrop"
    )
    hdbg.dassert_path_exists(base_csv, "Base CSV file not found")
    hdbg.dassert_path_exists(raindrop_csv, "raindrop CSV file not found")
    _LOG.info("Loading base CSV to get schema")
    rows_gsheet = dshdbout.read_csv(base_csv)
    _log_first_rows(base_csv, action_desc="Read")
    gsheet_columns = list(rows_gsheet[0].keys()) if rows_gsheet else []
    _LOG.info("Base CSV schema: %s", gsheet_columns)
    _LOG.info("Loading Raindrop CSV data")
    rows_raindrop = dshdbout.read_csv(raindrop_csv)
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
    # Prepend Raindrop data (newest first) and append existing base rows.
    rows_combined.extend(rows_gsheet)
    _LOG.debug(hprint.to_str("len(rows_combined)"))
    _LOG.info(
        "Combining data: %d raindrop items, %d existing items",
        len(rows_raindrop),
        len(rows_gsheet),
    )
    _LOG.info("Writing combined data to CSV file: '%s'", output_csv)
    # Write combined data preserving the base CSV's column order.
    if rows_combined:
        dshdbout.write_csv(
            output_csv, rows_combined, fieldnames=gsheet_columns
        )
    else:
        dshdbout.write_csv(output_csv, [], fieldnames=gsheet_columns)
    if rows_combined:
        _log_first_rows(output_csv, action_desc="Combined into")
    _LOG.info("Combined CSV created with %d rows", len(rows_combined))
    _LOG.debug("return=%s", output_csv)
    return output_csv


def _upload_to_gsheet(url: str) -> None:
    """
    Upload combined CSV data to a new tab in Google Sheets.

    Reads the combined CSV file and uploads it to the specified tab in the
    Google Sheet, creating the tab if it doesn't exist or overwriting it.

    :param url: URL of the Google Sheets document
    """
    _LOG.debug(hprint.to_str("url"))
    # Build a dated tab name so re-runs on the same day overwrite the same tab.
    tabname = "update_bookmarks_from_raindrop." + datetime.now().strftime(
        "%Y-%m-%d"
    )
    combined_csv = dshdbout.get_tmp_file_path(
        COMBINED_CSV_FILE, "update_bookmarks_from_raindrop"
    )
    hdbg.dassert_path_exists(combined_csv, "combined CSV file not found")
    _LOG.debug(hprint.to_str("tabname combined_csv"))
    dshdbout.upload_to_gsheet(url, combined_csv, tabname)


def _get_action_output_file(action: str, target: str) -> Optional[str]:
    """
    Get the output file that an action produces, if any.

    Used to support incremental runs: an action is skipped when its output
    file already exists (unless `--no_incremental` is passed).

    :param action: name of the action
    :param target: `--target` value (`gsheet` or `local_csv`)
    :return: path to the action's output file, or `None` if the action has
        no local output file to check against. This is the case for
        `upload_gsheet_links` (only a side effect on the remote gsheet) and,
        for `--target local_csv`, `combine_data` (it prepends into
        `--local_csv` in place, which always already exists, so an
        existence check would wrongly skip it every run)
    """
    if target == "local_csv":
        action_to_filename = {
            "download_raindrop_data": RAINDROP_CSV_FILE,
        }
    else:
        action_to_filename = {
            "download_gsheet_links": GSHEET_CSV_FILE,
            "download_raindrop_data": RAINDROP_CSV_FILE,
            "combine_data": COMBINED_CSV_FILE,
        }
    filename = action_to_filename.get(action)
    if filename is None:
        return None
    return dshdbout.get_tmp_file_path(
        filename, "update_bookmarks_from_raindrop"
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
# `--target local_csv` only supports fetching and merging: there's no
# separate gsheet to download from or upload to.
_LOCAL_CSV_ACTIONS = ["download_raindrop_data", "combine_data"]


def _parse() -> argparse.ArgumentParser:
    _LOG.debug(hprint.func_signature_to_str())
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    parser.add_argument(
        "--target",
        action="store",
        choices=["gsheet", "local_csv"],
        default="gsheet",
        help="Sync destination: 'gsheet' (default, unchanged behavior) "
        "syncs into a live Google Sheet via --url; 'local_csv' syncs "
        "directly into the file passed via --local_csv, merging new rows "
        "in place",
    )
    parser.add_argument(
        "--local_csv",
        action="store",
        default="",
        help="Path to the local CSV to sync into (required for "
        "--target local_csv; ignored for --target gsheet)",
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
    # Resolve the base CSV (source of the latest-`Timestamp` cutoff and, for
    # `combine_data`, of the existing rows/schema) for the selected target.
    if args.target == "local_csv":
        hdbg.dassert_ne(
            args.local_csv,
            "",
            "--local_csv is required when --target local_csv",
        )
        base_csv = args.local_csv
        valid_actions = _LOCAL_CSV_ACTIONS
        default_actions = _LOCAL_CSV_ACTIONS
    else:
        base_csv = dshdbout.get_tmp_file_path(
            GSHEET_CSV_FILE, "update_bookmarks_from_raindrop"
        )
        valid_actions = _VALID_ACTIONS
        default_actions = _DEFAULT_ACTIONS
    # Determine which actions to execute based on command-line arguments.
    # `select_actions()` rejects, with a clear error, any action outside
    # `valid_actions` (e.g., `download_gsheet_links`/`upload_gsheet_links`
    # when `--target local_csv`).
    actions = hselacti.select_actions(args, valid_actions, default_actions)
    _LOG.info(
        "Actions to execute:\n%s",
        hselacti.actions_to_string(actions, valid_actions, add_frame=True),
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
            output_file = _get_action_output_file(action, args.target)
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
            url = dshdbout.resolve_gsheet_url(args.url)
            _download_gsheet_links(url)
        elif action == "download_raindrop_data":
            _download_raindrop_data(base_csv)
        elif action == "combine_data":
            if args.target == "local_csv":
                # Merge new rows into the same file in place.
                output_csv = base_csv
            else:
                output_csv = dshdbout.get_tmp_file_path(
                    COMBINED_CSV_FILE, "update_bookmarks_from_raindrop"
                )
            _combine_raindrop_with_gsheet_links(base_csv, output_csv)
        elif action == "upload_gsheet_links":
            url = dshdbout.resolve_gsheet_url(args.url)
            _upload_to_gsheet(url)
        else:
            raise ValueError(f"Invalid action='{action}'")
    hdbg.dassert_eq(
        len(actions), 0, "There are unprocessed actions: %s", str(actions)
    )


if __name__ == "__main__":
    _main(_parse())
