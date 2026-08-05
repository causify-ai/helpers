#!/usr/bin/env -S uv run

# /// script
# dependencies = [
#   "beautifulsoup4",
#   "pandas",
#   "requests",
#   "tqdm",
# ]
# ///

r"""
Download article content and HN comments from links stored in Google Sheets.

For detailed documentation on the link workflow, see:
`dev_scripts_helpers/download/download_link_articles.README.md`

This script processes a Google Sheets document containing article links,
downloads article content and Hacker News comments, and optionally summarizes
them using LLMs.

To download a single HN submission (comments + linked article) without a
Google Sheet, use `dev_scripts_helpers/download/download_hn_article_to_md.py`
instead.

## Supported Actions

- **download_article_url**: Download article content from direct URLs
- **download_hn_url**: Fetch HN comments from submission URLs and save to files
- **summarize_article_url**: Summarize article content using Claude
- **summarize_hn_url**: Summarize HN comments using Claude (requires prior download)

## Output Files

Each action delegates to `download_hn_article_to_md.py` for the row's
`Hn_url`, which derives the output filename from the submission title fetched
fresh from the HN API (normally identical to the Title column):

- `{title}.1.article_url.txt` - Article content (from download_article_url)
- `{title}.2.hn_url.txt` - Raw HN comments (from download_hn_url)
- `{title}.3.article_url.summary.txt` - Summarized article (from summarize_article_url)
- `{title}.4.hn_url.summary.txt` - Summarized HN comments (from summarize_hn_url)

## Example Usage

Download HN comments for rows 0-9 where the "Hn_url" column is not empty:
> download_link_articles.py \
    --url "https://docs.google.com/spreadsheets/d/..." \
    --row_idx "0:10" \
    --action download_hn_url

Download all actions (both HN comments and articles):
> download_link_articles.py \
    --url "https://docs.google.com/spreadsheets/d/..." \
    --all

Download article content only:
> download_link_articles.py \
    --url "https://docs.google.com/spreadsheets/d/..." \
    --action download_article_url

Download from rows 0-4, skip article downloads:
> download_link_articles.py \
    --url "https://docs.google.com/spreadsheets/d/..." \
    --row_idx "0:5" \
    --skip_action download_article_url

Summarize articles (requires prior download_article_url):
> download_link_articles.py \
    --url "https://docs.google.com/spreadsheets/d/..." \
    --action summarize_article_url

Summarize HN comments (requires prior download_hn_url):
> download_link_articles.py \
    --url "https://docs.google.com/spreadsheets/d/..." \
    --action summarize_hn_url

Import as:

import dev_scripts_helpers.download.download_link_articles as dssdla
"""

import argparse
import logging
from typing import Any, Dict, List

from tqdm import tqdm

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hcache_simple as hcacsimp
import helpers.hselect_action as hselacti
import helpers.hsystem as hsystem
import dev_scripts_helpers.download.link_gsheet_utils as dshslgsut

_LOG = logging.getLogger(__name__)


# #############################################################################
# Phase 1: Download Gsheet
# #############################################################################


def _load_rows_from_gsheet(url: str) -> List[Dict[str, Any]]:
    """
    Download and parse data from a Google Sheets document.

    :param url: URL of the Google Sheets document
    :return: List of data rows
    """
    _LOG.debug(hprint.func_signature_to_str())
    # Download the Google Sheets document to a local CSV file, then parse it.
    gsheet_csv = dshslgsut.get_tmp_file_path(
        "gsheet.csv", "download_link_articles"
    )
    _LOG.debug("Downloading from Google Sheets '%s' to '%s'", url, gsheet_csv)
    dshslgsut.download_from_gsheet(url, gsheet_csv)
    rows = dshslgsut.read_csv(gsheet_csv)
    hdbg.dassert_lt(0, len(rows), "No rows in downloaded CSV")
    # Verify expected columns exist.
    expected_columns = {
        "Title",
        "Article_url",
        "Hn_url",
        "Timestamp",
        "Article_tag",
        "Article_cluster",
    }
    actual_columns = list(rows[0].keys())
    hdbg.dassert_is_subset(
        expected_columns,
        actual_columns,
    )
    _LOG.info("Retrieved %d rows from Google Sheets", len(rows))
    _LOG.debug("return=%d rows", len(rows))
    return rows


# #############################################################################
# Phase 2: Parsing of Indices
# #############################################################################


def _parse_row_idx(row_idx_str: str, num_rows: int) -> List[int]:
    """
    Parse row_idx string and return list of 0-indexed row indices.

    Format: "N" (single 0-indexed row) or "START:END" (range, 0-based with
    exclusive end like Python slicing, e.g., "1:10" returns [1, 2, ..., 9]).

    :param row_idx_str: Row index specification (0-indexed, exclusive end)
    :param num_rows: Total number of rows available
    :return: List of 0-indexed row indices to process
    """
    _LOG.debug(hprint.to_str("row_idx_str num_rows"))
    # Parse range format (e.g., "1:10").
    if ":" in row_idx_str:
        parts = row_idx_str.split(":")
        hdbg.dassert_eq(
            len(parts),
            2,
            "Row index range must be in format START:END",
        )
        try:
            start = int(parts[0].strip())
            end = int(parts[1].strip())
        except ValueError:
            raise ValueError(
                f"Invalid row_idx range: {row_idx_str}; "
                "expected integers in format START:END"
            )
        hdbg.dassert_lte(
            start,
            end,
            "Row index start must be <= end",
        )
        hdbg.dassert_lte(0, start, "Row index start must be >= 0 (0-indexed)")
        hdbg.dassert_lte(
            end,
            num_rows,
            "Row index end must be <= number of rows (%d)",
            num_rows,
        )
        # Use 0-based indexing with exclusive end (Python range convention).
        indices = list(range(start, end))
    else:
        # Parse single index format (e.g., "5").
        try:
            idx = int(row_idx_str.strip())
        except ValueError:
            raise ValueError(f"Invalid row_idx: {row_idx_str}; expected integer")
        hdbg.dassert_lte(0, idx, "Row index must be >= 0 (0-indexed)")
        hdbg.dassert_lte(
            idx,
            num_rows - 1,
            "Row index must be < number of rows (%d)",
            num_rows,
        )
        # Return single 0-indexed row.
        indices = [idx]
    _LOG.debug(hprint.to_str("indices"))
    return indices


# #############################################################################
# Phase 3: Download
# #############################################################################

_DOWNLOAD_HN_ARTICLE_SCRIPT = (
    "dev_scripts_helpers/download/download_hn_article_to_md.py"
)


def _run_hn_article_action(
    hn_url: str, action: str, *, dry_run: bool = False
) -> None:
    """
    Run a single action of `download_hn_article_to_md.py` for one HN URL.

    The action names of the two scripts match 1:1 (`download_hn_url`,
    `download_article_url`, `summarize_hn_url`, `summarize_article_url`), so
    the action is simply forwarded.

    :param hn_url: Hacker News item URL
    :param action: action name to run, e.g. "download_hn_url"
    :param dry_run: If True, show what would be done without executing
    """
    _LOG.debug(hprint.to_str("hn_url action dry_run"))
    # Build the command that forwards the action to `download_hn_article_to_md.py`.
    cmd = f'{_DOWNLOAD_HN_ARTICLE_SCRIPT} --hn_url "{hn_url}" -a {action}'
    if dry_run:
        cmd += " --dry_run"
    _LOG.debug("Running command: '%s'", cmd)
    hsystem.system(cmd)


def _download_hn_urls(
    rows: List[Dict[str, Any]], indices: List[int], *, dry_run: bool = False
) -> None:
    """
    Download HN comments for selected rows via `download_hn_article_to_md.py`.

    :param rows: List of data rows
    :param indices: List of row indices to process
    :param dry_run: If True, show what would be done without executing
    """
    _LOG.debug(hprint.to_str("len(indices)"))
    _LOG.info(
        "Downloading HN comments for %d rows%s",
        len(indices),
        " (DRY RUN)" if dry_run else "",
    )
    for idx in tqdm(indices, desc="Downloading HN comments"):
        row = rows[idx]
        # Extract URL and title from the row.
        hn_url = row.get("Hn_url", "").strip()
        title = row.get("Title", "").strip()
        if not hn_url or not title:
            _LOG.warning("Row %d missing Url or Title, skipping", idx)
            continue
        # Validate URL is from HN.
        if not dshslgsut.is_hackernews_url(hn_url):
            _LOG.info("Row %d: URL is not HN URL, skipping", idx)
            continue
        _LOG.debug("Processing row %d: %s", idx, title)
        _run_hn_article_action(hn_url, "download_hn_url", dry_run=dry_run)


def _download_article_urls(
    rows: List[Dict[str, Any]], *, indices: List[int], dry_run: bool = False
) -> None:
    """
    Download article content for selected rows via
    `download_hn_article_to_md.py`.

    :param rows: List of data rows
    :param indices: List of row indices to process
    :param dry_run: If True, show what would be done without executing
    """
    _LOG.debug(hprint.to_str("len(indices)"))
    _LOG.info(
        "Downloading articles from Article_url for %d rows%s",
        len(indices),
        " (DRY RUN)" if dry_run else "",
    )
    for idx in tqdm(indices, desc="Downloading articles"):
        row = rows[idx]
        # Extract article URL, HN URL, and title from the row.
        article_url = row.get("Article_url", "").strip()
        hn_url = row.get("Hn_url", "").strip()
        title = row.get("Title", "").strip()
        if not article_url or not title:
            _LOG.warning("Row %d missing Article_url or Title, skipping", idx)
            continue
        # download_hn_article_to_md.py requires --hn_url, so skip rows without one.
        if not hn_url or not dshslgsut.is_hackernews_url(hn_url):
            _LOG.warning(
                "Row %d has Article_url but no valid Hn_url, skipping "
                "(download_hn_article_to_md.py requires --hn_url)",
                idx,
            )
            continue
        _LOG.debug("Processing row %d: %s", idx, title)
        _run_hn_article_action(hn_url, "download_article_url", dry_run=dry_run)


# #############################################################################
# Phase 4: Summarization
# #############################################################################


def _summarize_hn_url(
    rows: List[Dict[str, Any]], *, indices: List[int], dry_run: bool = False
) -> None:
    """
    Summarize HN comments for selected rows via `download_hn_article_to_md.py`.

    Creates a summary file per article:
    - title.4.hn_url.summary.txt: Summary of HN comments

    :param rows: List of data rows
    :param indices: List of row indices to process
    :param dry_run: If True, show what would be done without executing
    """
    _LOG.debug(hprint.to_str("len(indices)"))
    _LOG.info(
        "Summarizing comments for %d rows%s",
        len(indices),
        " (DRY RUN)" if dry_run else "",
    )
    for idx in tqdm(indices, desc="Summarizing comments"):
        row = rows[idx]
        # Extract HN URL and title from the row.
        hn_url = row.get("Hn_url", "").strip()
        title = row.get("Title", "").strip()
        hdbg.dassert(title)
        if not hn_url or not dshslgsut.is_hackernews_url(hn_url):
            _LOG.warning("Row %d missing a valid Hn_url, skipping", idx)
            continue
        _LOG.debug("Processing row %d: %s", idx, title)
        _run_hn_article_action(hn_url, "summarize_hn_url", dry_run=dry_run)


def _summarize_articles(
    rows: List[Dict[str, Any]], *, indices: List[int], dry_run: bool = False
) -> None:
    """
    Summarize article text for selected rows via `download_hn_article_to_md.py`.

    Creates a summary file per article:
    - title.text.summary.txt: Summary of the article

    :param rows: List of data rows
    :param indices: List of row indices to process
    :param dry_run: If True, show what would be done without executing
    """
    _LOG.debug(hprint.to_str("len(indices)"))
    _LOG.info(
        "Summarizing articles for %d rows%s",
        len(indices),
        " (DRY RUN)" if dry_run else "",
    )
    for idx in tqdm(indices, desc="Summarizing articles"):
        row = rows[idx]
        # Extract HN URL and title from the row.
        hn_url = row.get("Hn_url", "").strip()
        title = row.get("Title", "").strip()
        hdbg.dassert(title)
        if not hn_url or not dshslgsut.is_hackernews_url(hn_url):
            _LOG.warning("Row %d missing a valid Hn_url, skipping", idx)
            continue
        _LOG.debug("Processing row %d: %s", idx, title)
        _run_hn_article_action(hn_url, "summarize_article_url", dry_run=dry_run)


# #############################################################################
# CLI and Entry Points
# #############################################################################


VALID_ACTIONS = [
    "download_article_url",
    "download_hn_url",
    "summarize_article_url",
    "summarize_hn_url",
]
DEFAULT_ACTIONS = VALID_ACTIONS[:]


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments.
    """
    _LOG.debug(hprint.func_signature_to_str())
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    parser.add_argument(
        "--url",
        action="store",
        required=True,
        help="URL of the Google Sheets document",
    )
    # Optional: specify which rows to process (0-indexed).
    parser.add_argument(
        "--row_idx",
        action="store",
        required=False,
        default="",
        help="Row index or range to process, 1-indexed (e.g., '1' for first row, '1:10' for rows 1-10)",
    )
    # Add action selection arguments (download_hn_url, download_article_url, etc).
    hselacti.add_action_arg(parser, VALID_ACTIONS, DEFAULT_ACTIONS)
    # Add cache control argument.
    hcacsimp.add_cache_control_arg(parser)
    # Dry run mode: show what would happen without executing.
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Dry run mode: show what would be done without actually executing actions",
    )
    # Add verbosity control argument.
    hparser.add_verbosity_arg(parser)
    _LOG.debug("return=%s", parser.prog)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main entry point.
    """
    _LOG.debug(hprint.func_signature_to_str())
    # Parse CLI arguments and initialize logging and cache control.
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    hcacsimp.parse_cache_control_args(args)
    # Phase 1: Download the rows from the Google Sheets document.
    rows = _load_rows_from_gsheet(args.url)
    # Phase 2: Determine which rows to process based on `row_idx` argument.
    indices = _parse_row_idx(args.row_idx, len(rows))
    _LOG.info("Row indices to process: %s", indices)
    actions = hselacti.select_actions(args, VALID_ACTIONS, DEFAULT_ACTIONS)
    _LOG.info(
        "Actions to execute:\n%s",
        hselacti.actions_to_string(actions, VALID_ACTIONS, add_frame=True),
    )
    # Execute selected actions in sequence.
    # Each action processes the filtered set of rows independently.
    if args.dry_run:
        _LOG.info("DRY RUN MODE: showing what would be done without executing")
    actions_remaining = actions
    while actions_remaining:
        action = actions_remaining[0]
        # Pop the action off the remaining list; mark_action() decides whether
        # it should actually run (e.g., some actions may be grouped together).
        to_execute, actions_remaining = hselacti.mark_action(
            action, actions_remaining
        )
        if not to_execute:
            continue
        _LOG.debug("Executing action='%s'", action)
        # Phase 3: Download article.
        if action == "download_article_url":
            _download_article_urls(rows, indices=indices, dry_run=args.dry_run)
        elif action == "download_hn_url":
            _download_hn_urls(rows, indices=indices, dry_run=args.dry_run)
        elif action == "summarize_article_url":
            # Phase 4: Summarization.
            _summarize_articles(rows, indices=indices, dry_run=args.dry_run)
        elif action == "summarize_hn_url":
            _summarize_hn_url(rows, indices=indices, dry_run=args.dry_run)
    _LOG.info("Download and processing completed")


if __name__ == "__main__":
    _main(_parse())
