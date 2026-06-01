#!/usr/bin/env -S uv run

# /// script
# dependencies = [
#   "beautifulsoup4",
#   "lxml",
#   "pandas",
#   "requests",
#   "tqdm",
# ]
# ///

r"""
Download article content and HN comments from links stored in Google Sheets.

This script downloads articles from a Google Sheets document and saves them
as text files. It supports:
1. Downloading HN comments from HackerNews submission URLs
2. Downloading article content from article URLs

Filenames are sanitized from the Title column with bash-unfriendly chars
replaced with underscores.

Example usage:

Download HN comments for rows 0-10 where the "Url" column is not empty:
> download_link_articles.py \
    --url "https://docs.google.com/spreadsheets/d/..." \
    --column_idx "0:10" \
    --select_column "Url" \
    --action download_url

Download all (both HN comments and articles):
> download_link_articles.py \
    --url "https://docs.google.com/spreadsheets/d/..." \
    --select_column "Article_url" \
    --all

Download article content from article URLs only:
> download_link_articles.py \
    --url "https://docs.google.com/spreadsheets/d/..." \
    --select_column "Article_url" \
    --action download_article_url

Download from rows 0-5, skip downloading articles:
> download_link_articles.py \
    --url "https://docs.google.com/spreadsheets/d/..." \
    --column_idx "0:5" \
    --select_column "Url" \
    --skip-action download_article_url

Import as:

import dev_scripts_helpers.scraping.download_link_articles as dssdla
"""

import argparse
import logging
import re
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hcache_simple as hcacsimp
import helpers.hselect_action as hselacti
import dev_scripts_helpers.scraping.link_gsheet_utils as dshslgsut

_LOG = logging.getLogger(__name__)


@hcacsimp.simple_cache(cache_type="json", write_through=True)
def _fetch_hn_item(item_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a Hacker News item from the API.

    :param item_id: HN item ID
    :return: Item data dict or None if fetch fails
    """
    try:
        api_url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
        _LOG.debug("Fetching HN item: %s", api_url)
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data:
            _LOG.warning("No data returned for item: %s", item_id)
            return None
        return data
    except requests.RequestException as e:
        _LOG.warning("API request failed for item %s: %s", item_id, e)
        return None
    except Exception as e:
        _LOG.warning("Error fetching item %s: %s", item_id, e)
        return None


def _fetch_hn_comments(
    item_id: str,
    *,
    max_depth: int = 3,
    current_depth: int = 0,
) -> List[Dict[str, Any]]:
    """
    Recursively fetch HN comments for an item.

    :param item_id: HN item ID
    :param max_depth: Maximum recursion depth
    :param current_depth: Current recursion depth (internal use)
    :return: List of comment dicts with nested replies
    """
    if current_depth >= max_depth:
        return []
    item_data = _fetch_hn_item(item_id)
    if not item_data:
        return []
    comment = {
        "id": item_data.get("id"),
        "by": item_data.get("by"),
        "text": item_data.get("text", ""),
        "time": item_data.get("time"),
        "score": item_data.get("score"),
    }
    kids = item_data.get("kids", [])
    if kids:
        replies = []
        for kid_id in kids[:10]:
            kid_comments = _fetch_hn_comments(
                str(kid_id),
                max_depth=max_depth,
                current_depth=current_depth + 1,
            )
            replies.extend(kid_comments)
        comment["replies"] = replies
    return [comment]


@hcacsimp.simple_cache(cache_type="json", write_through=True)
def _download_article_content(url: str) -> Optional[str]:
    """
    Download and extract article content from a URL.

    :param url: Article URL
    :return: Article text or None if download fails
    """
    if not url:
        return None
    _LOG.debug("Downloading article from: %s", url)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(url, timeout=15, headers=headers)
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        paragraphs = soup.find_all("p")
        if paragraphs:
            text = "\n\n".join(p.get_text() for p in paragraphs)
        else:
            text = html
        return text
    except Exception as e:
        _LOG.warning("Failed to download article from %s: %s", url, e)
        return None


def _sanitize_title_for_filename(title: str) -> str:
    """
    Sanitize a title for use in a filename.

    Replaces non-alphanumeric chars with underscores, collapses repeated
    underscores, and strips leading/trailing underscores.

    :param title: Title string
    :return: Sanitized filename slug
    """
    sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", title)
    sanitized = re.sub(r"_+", "_", sanitized)
    sanitized = sanitized.strip("_")
    return sanitized


def _format_hn_comments_as_text(comments: List[Dict[str, Any]]) -> str:
    """
    Format HN comments list as readable text.

    :param comments: List of comment dicts with nested replies
    :return: Formatted text representation of comments
    """
    lines = []

    def add_comment_tree(
        comment_list: List[Dict[str, Any]], depth: int = 0
    ) -> None:
        """
        Recursively add comments to output, preserving hierarchy.
        """
        for comment in comment_list:
            indent = "  " * depth
            lines.append(f"{indent}By: {comment.get('by', 'unknown')}")
            lines.append(f"{indent}Score: {comment.get('score', 0)}")
            lines.append(f"{indent}Time: {comment.get('time', 'unknown')}")
            text = comment.get("text", "").strip()
            if text:
                for text_line in text.split("\n"):
                    lines.append(f"{indent}{text_line}")
            lines.append("")
            if "replies" in comment:
                add_comment_tree(comment["replies"], depth + 1)

    add_comment_tree(comments)
    return "\n".join(lines)


def _parse_column_idx(column_idx_str: str, num_rows: int) -> List[int]:
    """
    Parse column_idx string and return list of row indices.

    Format: "0" (single index) or "0:10" (range, inclusive start, exclusive end).

    :param column_idx_str: Column index specification
    :param num_rows: Total number of rows available
    :return: List of row indices to process
    """
    if ":" in column_idx_str:
        parts = column_idx_str.split(":")
        hdbg.dassert_eq(
            len(parts),
            2,
            "Column index range must be in format START:END",
        )
        try:
            start = int(parts[0].strip())
            end = int(parts[1].strip())
        except ValueError:
            raise ValueError(
                f"Invalid column_idx range: {column_idx_str}; "
                "expected integers in format START:END"
            )
        hdbg.dassert_lte(
            start,
            end,
            "Column index start must be <= end",
        )
        hdbg.dassert_lte(0, start, "Column index start must be >= 0")
        hdbg.dassert_lte(
            end,
            num_rows,
            "Column index end must be <= number of rows (%d)",
            num_rows,
        )
        return list(range(start, end))
    else:
        try:
            idx = int(column_idx_str.strip())
        except ValueError:
            raise ValueError(
                f"Invalid column_idx: {column_idx_str}; expected integer"
            )
        hdbg.dassert_lte(0, idx, "Column index must be >= 0")
        hdbg.dassert_lt(
            idx,
            num_rows,
            "Column index must be < number of rows (%d)",
            num_rows,
        )
        return [idx]


def _download_hn_comments(
    rows: List[Dict[str, Any]], *, indices: List[int]
) -> None:
    """
    Download HN comments for selected rows and save to files.

    :param rows: List of data rows
    :param indices: List of row indices to process
    """
    _LOG.info("Downloading HN comments for %d rows", len(indices))
    for idx in tqdm(indices, desc="Downloading HN comments"):
        row = rows[idx]
        url = row.get("Url", "").strip()
        title = row.get("Title", "").strip()
        if not url or not title:
            _LOG.warning("Row %d missing Url or Title, skipping", idx)
            continue
        try:
            if not dshslgsut.is_hackernews_url(url):
                _LOG.info("Row %d: URL is not HN URL, skipping", idx)
                continue
            _LOG.debug("Processing row %d: %s", idx, title)
            item_id = dshslgsut.extract_item_id(url)
        except (AssertionError, AttributeError):
            _LOG.warning("Row %d: Could not extract item ID from: %s", idx, url)
            continue
        _LOG.info("Fetching HN comments for item: %s", item_id)
        hn_comments = _fetch_hn_comments(item_id, max_depth=3)
        sanitized_title = _sanitize_title_for_filename(title)
        output_file = f"{sanitized_title}.hn_comments.txt"
        _LOG.info("Writing HN comments to: %s", output_file)
        formatted_comments = _format_hn_comments_as_text(hn_comments)
        with open(output_file, "w") as f:
            f.write(formatted_comments)
        _LOG.info("Successfully saved HN comments for: %s", title)


def _download_article_urls(
    rows: List[Dict[str, Any]], *, indices: List[int]
) -> None:
    """
    Download article content from Article_url column and save to files.

    :param rows: List of data rows
    :param indices: List of row indices to process
    """
    _LOG.info("Downloading articles from Article_url for %d rows", len(indices))
    for idx in tqdm(indices, desc="Downloading articles"):
        row = rows[idx]
        article_url = row.get("Article_url", "").strip()
        title = row.get("Title", "").strip()
        if not article_url or not title:
            _LOG.warning("Row %d missing Article_url or Title, skipping", idx)
            continue
        _LOG.debug("Processing row %d: %s", idx, title)
        article_content = _download_article_content(article_url)
        if not article_content:
            _LOG.warning(
                "Row %d: Failed to download article from: %s", idx, article_url
            )
            continue
        sanitized_title = _sanitize_title_for_filename(title)
        output_file = f"{sanitized_title}.text.txt"
        _LOG.info("Writing article content to: %s", output_file)
        with open(output_file, "w") as f:
            f.write(article_content)
        _LOG.info("Successfully saved article for: %s", title)


VALID_ACTIONS = [
    "download_url",
    "download_article_url",
]
DEFAULT_ACTIONS = VALID_ACTIONS[:]


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments.
    """
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
        "--column_idx",
        action="store",
        default=None,
        help="Column/row index or range to process (e.g., '0' or '0:10')",
    )
    parser.add_argument(
        "--select_column",
        action="store",
        default=None,
        help="Column name to use for filtering; only rows with non-empty cells in "
        "this column will be processed",
    )
    hselacti.add_action_arg(parser, VALID_ACTIONS, DEFAULT_ACTIONS)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main entry point.
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    hdbg.dassert_is_not(args.url, None, "--url is required")
    actions = hselacti.select_actions(args, VALID_ACTIONS, DEFAULT_ACTIONS)
    _LOG.info(
        "Actions to execute:\n%s",
        hselacti.actions_to_string(actions, VALID_ACTIONS, add_frame=True),
    )
    gsheet_csv = dshslgsut.get_tmp_file_path("gsheet.csv", "download_link_articles")
    dshslgsut.download_from_gsheet(args.url, gsheet_csv)
    rows = dshslgsut.read_csv(gsheet_csv)
    hdbg.dassert(len(rows) > 0, "No rows in downloaded CSV")
    _LOG.info("Processing %d rows from Google Sheets", len(rows))
    if args.column_idx:
        indices = _parse_column_idx(args.column_idx, len(rows))
    else:
        indices = list(range(len(rows)))
    _LOG.info("Row indices to process: %s", indices)
    if args.select_column:
        hdbg.dassert_in(
            args.select_column,
            rows[0].keys() if rows else [],
            "Select column not found in CSV",
        )
        _LOG.info("Filtering rows by non-empty cells in: %s", args.select_column)
        filtered_indices = []
        for idx in indices:
            cell_value = rows[idx].get(args.select_column, "")
            if isinstance(cell_value, str):
                is_nonempty = cell_value.strip() != ""
            else:
                is_nonempty = pd.notna(cell_value) and cell_value != ""
            if is_nonempty:
                filtered_indices.append(idx)
        indices = filtered_indices
        _LOG.info("After filtering: %d rows to process", len(indices))
    actions_remaining = actions
    while actions_remaining:
        action = actions_remaining[0]
        to_execute, actions_remaining = hselacti.mark_action(
            action, actions_remaining
        )
        if not to_execute:
            continue
        if action == "download_url":
            _download_hn_comments(rows, indices=indices)
        elif action == "download_article_url":
            _download_article_urls(rows, indices=indices)
    _LOG.info("Download completed")


if __name__ == "__main__":
    _main(_parse())
