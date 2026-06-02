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
3. Summarizing articles and comments using LLM

Filenames are sanitized from the Title column with bash-unfriendly chars
replaced with underscores.

Example usage:

Download HN comments for rows 1-10 where the "Url" column is not empty:
> download_link_articles.py \
    --url "https://docs.google.com/spreadsheets/d/..." \
    --row_idx "1:10" \
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

Download from rows 1-5, skip downloading articles:
> download_link_articles.py \
    --url "https://docs.google.com/spreadsheets/d/..." \
    --row_idx "1:5" \
    --select_column "Url" \
    --skip-action download_article_url

Summarize articles for all rows:
> download_link_articles.py \
    --url "https://docs.google.com/spreadsheets/d/..." \
    --action summarize_article_url

Summarize HN comments for all rows:
> download_link_articles.py \
    --url "https://docs.google.com/spreadsheets/d/..." \
    --action summarize_url

Import as:

import dev_scripts_helpers.scraping.download_link_articles as dssdla
"""

import argparse
import html
import logging
import os
import re
from typing import Any, Dict, List, Optional

# TODO(gp): Consider using a different implementation and remove this
# dependency.
import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hcache_simple as hcacsimp
import helpers.hselect_action as hselacti
import helpers.hsystem as hsystem
import dev_scripts_helpers.scraping.link_gsheet_utils as dshslgsut

_LOG = logging.getLogger(__name__)

# #############################################################################
# Text Processing Utilities
# #############################################################################


def _sanitize_title_for_filename(title: str) -> str:
    """
    Sanitize a title for use in a filename.

    Replaces non-alphanumeric chars with underscores, collapses repeated
    underscores, and strips leading/trailing underscores.

    :param title: Title string
    :return: Sanitized filename slug
    """
    # Replace any non-alphanumeric character (except underscore) with underscore.
    sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", title)
    # Collapse consecutive underscores into a single underscore.
    sanitized = re.sub(r"_+", "_", sanitized)
    # Remove leading and trailing underscores for cleaner filenames.
    sanitized = sanitized.strip("_")
    return sanitized


def _simplify_html_links(text: str) -> str:
    """
    Simplify HTML links by extracting just the URL and unescaping entities.

    Converts: <a href="https:&#x2F;&#x2F;example.com">...</a>
    To: https://example.com

    :param text: Text containing HTML links
    :return: Text with simplified links
    """
    # Match <a> tags and extract href, then replace with just the URL
    def replace_link(match):
        href = match.group(1)
        # Unescape HTML entities (&#x2F; -> /)
        unescaped = html.unescape(href)
        return unescaped
    # Pattern: <a href="...">...</a> - captures the href attribute
    pattern = r'<a\s+[^>]*href=["\'](.*?)["\'][^>]*>.*?</a>'
    simplified = re.sub(pattern, replace_link, text, flags=re.IGNORECASE | re.DOTALL)
    return simplified

# #############################################################################
# HN API and Data Fetching
# #############################################################################


@hcacsimp.simple_cache(cache_type="json", write_through=True)
def _fetch_hn_item(item_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a Hacker News item from the API.

    :param item_id: HN item ID
    :return: Item data dict or None if fetch fails
    """
    try:
        # Query the official HN API for the item.
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
    # Stop recursion at max depth to limit API calls and processing time.
    if current_depth >= max_depth:
        return []
    # Fetch the item data from HN API.
    item_data = _fetch_hn_item(item_id)
    if not item_data:
        return []
    # Extract core comment metadata from the item data.
    comment = {
        "id": item_data.get("id"),
        "by": item_data.get("by"),
        "text": item_data.get("text", ""),
        "time": item_data.get("time"),
        "score": item_data.get("score"),
    }
    # Recursively fetch child comments (replies) if they exist.
    # Limit to first 10 children per comment to avoid excessive API calls.
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

# #############################################################################
# Content Processing and Formatting
# #############################################################################


@hcacsimp.simple_cache(cache_type="json", write_through=True)
def _download_article_content(url: str) -> Optional[str]:
    """
    Download and extract article content from a URL.

    :param url: Article URL
    :return: Article text or None if download fails
    """
    hdbg.dassert_is_not(url, None)
    _LOG.debug("Downloading article from: %s", url)
    # Use a realistic User-Agent to avoid being blocked by many web servers.
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        # Fetch the HTML from the URL with timeout to prevent hanging.
        response = requests.get(url, timeout=15, headers=headers)
        response.raise_for_status()
        html = response.text
        # Parse HTML and extract article text from paragraph elements.
        soup = BeautifulSoup(html, "html.parser")
        paragraphs = soup.find_all("p")
        if paragraphs:
            # Join paragraphs with blank lines for readability.
            text = "\n\n".join(str(p) for p in paragraphs)
        else:
            # Fallback to raw HTML if no paragraphs found.
            text = html
        # Simplify HTML links and extract just the URLs.
        text = _simplify_html_links(text)
        # Extract text after link simplification.
        text = BeautifulSoup(text, "html.parser").get_text()
        return text
    except Exception as e:
        _LOG.warning("Failed to download article from %s: %s", url, e)
        return None


def _add_comment_tree(
    comment_list: List[Dict[str, Any]], lines: List[str], depth: int = 0
) -> None:
    """
    Recursively add comments to output, preserving hierarchy.
    """
    for comment in comment_list:
        # Format comment metadata: author, score, and timestamp.
        indent = "  " * depth
        lines.append(f"{indent}By: {comment.get('by', 'unknown')}")
        lines.append(f"{indent}Score: {comment.get('score', 0)}")
        lines.append(f"{indent}Time: {comment.get('time', 'unknown')}")
        # Extract and format comment text, preserving line breaks.
        text = comment.get("text", "").strip()
        if text:
            # Simplify HTML links in comment text.
            text = _simplify_html_links(text)
            # Unescape HTML entities (&#x27; -> ', &quot; -> ", etc.)
            text = html.unescape(text)
            for text_line in text.split("\n"):
                lines.append(f"{indent}{text_line}")
        lines.append("")
        # Recursively process nested replies at increasing indentation depth.
        if "replies" in comment:
            _add_comment_tree(comment["replies"], lines, depth + 1)


def _format_hn_comments_as_text(comments: List[Dict[str, Any]]) -> str:
    """
    Format HN comments list as readable text.

    :param comments: List of comment dicts with nested replies
    :return: Formatted text representation of comments
    """
    lines = []
    _add_comment_tree(comments, lines)
    text = "\n".join(lines)
    # Simplify HTML links in comment text.
    text = _simplify_html_links(text)
    return text

# #############################################################################
# Row Index Parsing
# #############################################################################


def _parse_row_idx(row_idx_str: str, num_rows: int) -> List[int]:
    """
    Parse row_idx string and return list of 0-indexed row indices.

    Format: "1" (single 1-indexed row) or "1:10" (range, inclusive start and end).
    Internally converts from 1-indexed to 0-indexed.

    :param row_idx_str: Row index specification (1-indexed)
    :param num_rows: Total number of rows available
    :return: List of 0-indexed row indices to process
    """
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
        hdbg.dassert_lte(1, start, "Row index start must be >= 1 (1-indexed)")
        hdbg.dassert_lte(
            end,
            num_rows,
            "Row index end must be <= number of rows (%d)",
            num_rows,
        )
        # Convert to 0-indexed: range is inclusive on both ends.
        return list(range(start - 1, end))
    else:
        # Parse single index format (e.g., "1").
        try:
            idx = int(row_idx_str.strip())
        except ValueError:
            raise ValueError(f"Invalid row_idx: {row_idx_str}; expected integer")
        hdbg.dassert_lte(1, idx, "Row index must be >= 1 (1-indexed)")
        hdbg.dassert_lte(
            idx,
            num_rows,
            "Row index must be <= number of rows (%d)",
            num_rows,
        )
        # Convert to 0-indexed.
        return [idx - 1]

# #############################################################################
# Download Operations
# #############################################################################


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
        # Extract URL and title from the row.
        url = row.get("Url", "").strip()
        title = row.get("Title", "").strip()
        if not url or not title:
            _LOG.warning("Row %d missing Url or Title, skipping", idx)
            continue
        # Validate URL is from HN and extract the submission item ID.
        try:
            if not dshslgsut.is_hackernews_url(url):
                _LOG.info("Row %d: URL is not HN URL, skipping", idx)
                continue
            _LOG.debug("Processing row %d: %s", idx, title)
            item_id = dshslgsut.extract_item_id(url)
        except (AssertionError, AttributeError):
            _LOG.warning("Row %d: Could not extract item ID from: %s", idx, url)
            continue
        # Fetch comments from HN API and format as readable text.
        _LOG.info("Fetching HN comments for item: %s", item_id)
        hn_comments = _fetch_hn_comments(item_id, max_depth=3)
        # Generate filename from title and write comments to disk.
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
        # Extract article URL and title from the row.
        article_url = row.get("Article_url", "").strip()
        title = row.get("Title", "").strip()
        if not article_url or not title:
            _LOG.warning("Row %d missing Article_url or Title, skipping", idx)
            continue
        _LOG.debug("Processing row %d: %s", idx, title)
        # Download and parse article content from the URL.
        article_content = _download_article_content(article_url)
        if not article_content:
            _LOG.warning(
                "Row %d: Failed to download article from: %s", idx, article_url
            )
            continue
        # Generate filename from title and write article text to disk.
        sanitized_title = _sanitize_title_for_filename(title)
        output_file = f"{sanitized_title}.text.txt"
        _LOG.info("Writing article content to: %s", output_file)
        with open(output_file, "w") as f:
            f.write(article_content)
        _LOG.info("Successfully saved article for: %s", title)

# #############################################################################
# Summarization Operations
# #############################################################################


def _summarize_text_with_llm(
    input_file: str, output_file: str, *, prompt: str
) -> None:
    """
    Summarize text using llm_cli.py and lint the output.

    :param input_file: Path to input text file to summarize
    :param output_file: Path to save the summary
    :param prompt: System prompt to guide the summarization
    """
    _LOG.info("Summarizing: %s", input_file)
    # Save prompt to a temporary file.
    prompt_file = f"{output_file}.prompt.txt"
    # TODO(ai_gp): Use hio.to_file
    with open(prompt_file, "w") as f:
        f.write(prompt)
    _LOG.debug("Saved prompt to: %s", prompt_file)
    # Build command to call llm_cli.py with the given prompt file.
    llm_cli_path = "dev_scripts_helpers/llms/llm_cli.py"
    cmd_parts = [
        llm_cli_path,
        f"--input={input_file}",
        f"--output={output_file}",
        f"--pf={prompt_file}",
        # TODO(ai_gp): Pass this as a parameter.
        "--model=gpt-4o-mini",
        "--lint",
    ]
    cmd = " ".join(cmd_parts)
    _LOG.debug("Running command: %s", cmd)
    hsystem.system(cmd)
    _LOG.info("Summary saved to: %s", output_file)


def _summarize_articles(
    rows: List[Dict[str, Any]], *, indices: List[int]
) -> None:
    """
    Summarize article text using llm_cli.py.

    Creates a summary file per article:
    - title.text.summary.txt: Summary of the article

    :param rows: List of data rows
    :param indices: List of row indices to process
    """
    _LOG.info("Summarizing articles for %d rows", len(indices))
    article_prompt = (
        "Summarize the main article in 5 bullet points. "
        "Format as plain text without markdown."
    )
    for idx in tqdm(indices, desc="Summarizing articles"):
        row = rows[idx]
        title = row.get("Title", "").strip()
        hdbg.dassert(title)
        _LOG.debug("Processing row %d: %s", idx, title)
        # Generate sanitized filename from title.
        sanitized_title = _sanitize_title_for_filename(title)
        # Summarize article text if .text.txt file exists.
        article_file = f"{sanitized_title}.text.txt"
        hdbg.dassert_file_exists(article_file)
        article_summary_file = f"{sanitized_title}.text.summary.txt"
        _LOG.info("Summarizing article text for: %s", title)
        _summarize_text_with_llm(
            article_file, article_summary_file, prompt=article_prompt
        )


def _summarize_comments(
    rows: List[Dict[str, Any]], *, indices: List[int]
) -> None:
    """
    Summarize HN comments using llm_cli.py.

    Creates a summary file per article:
    - title.hn_comments.summary.txt: Summary of HN comments

    :param rows: List of data rows
    :param indices: List of row indices to process
    """
    _LOG.info("Summarizing comments for %d rows", len(indices))
    comments_prompt = (
        "Analyze the Hacker News comment section. "
        "From all comments, summarize the 5 most interesting ones based on: "
        "1. Thought-provoking or insightful content "
        "2. Unique perspective or uncommon knowledge "
        "3. Sparks discussion or debate "
        "4. Technically informative or educational "
        "5. Controversial but well-argued. "
        "Avoid comments that are: simple jokes, memes, very short reactions, "
        "repetitive or low-effort. "
        "Do not include commenter names. "
        "Format as plain text without markdown."
    )
    for idx in tqdm(indices, desc="Summarizing comments"):
        row = rows[idx]
        title = row.get("Title", "").strip()
        hdbg.dassert(title)
        _LOG.debug("Processing row %d: %s", idx, title)
        # Generate sanitized filename from title.
        sanitized_title = _sanitize_title_for_filename(title)
        # Summarize HN comments if .hn_comments.txt file exists.
        comments_file = f"{sanitized_title}.hn_comments.txt"
        hdbg.dassert_file_exists(comments_file)
        comments_summary_file = f"{sanitized_title}.hn_comments.summary.txt"
        _LOG.info("Summarizing HN comments for: %s", title)
        _summarize_text_with_llm(
            comments_file, comments_summary_file, prompt=comments_prompt
        )


# #############################################################################
# CLI and Entry Points
# #############################################################################


VALID_ACTIONS = [
    "download_url",
    "download_article_url",
    "summarize_url",
    "summarize_article_url",
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
    # Required: URL of the Google Sheets document containing article links.
    parser.add_argument(
        "--url",
        action="store",
        required=True,
        help="URL of the Google Sheets document",
    )
    # Optional: specify which rows to process (1-indexed).
    parser.add_argument(
        "--row_idx",
        action="store",
        default=None,
        help="Row index or range to process, 1-indexed (e.g., '1' for first row, '1:10' for rows 1-10)",
    )
    # Optional: filter rows by non-empty values in this column.
    parser.add_argument(
        "--select_column",
        action="store",
        default=None,
        help="Column name to use for filtering; only rows with non-empty cells in "
        "this column will be processed",
    )
    # Add action selection arguments (download_url, download_article_url, etc).
    hselacti.add_action_arg(parser, VALID_ACTIONS, DEFAULT_ACTIONS)
    # Add verbosity control argument.
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main entry point.
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    hdbg.dassert_is_not(args.url, None, "--url is required")
    # Determine which actions to execute based on command-line flags.
    actions = hselacti.select_actions(args, VALID_ACTIONS, DEFAULT_ACTIONS)
    _LOG.info(
        "Actions to execute:\n%s",
        hselacti.actions_to_string(actions, VALID_ACTIONS, add_frame=True),
    )
    # Phase 1: Download and parse the Google Sheets data.
    gsheet_csv = dshslgsut.get_tmp_file_path(
        "gsheet.csv", "download_link_articles"
    )
    dshslgsut.download_from_gsheet(args.url, gsheet_csv)
    rows = dshslgsut.read_csv(gsheet_csv)
    hdbg.dassert(len(rows) > 0, "No rows in downloaded CSV")
    _LOG.info("Processing %d rows from Google Sheets", len(rows))
    # Phase 2: Determine which rows to process based on row_idx argument.
    # Defaults to all rows if row_idx is not specified.
    if args.row_idx:
        indices = _parse_row_idx(args.row_idx, len(rows))
    else:
        indices = list(range(len(rows)))
    _LOG.info("Row indices to process: %s", indices)
    # Phase 3: Filter rows by non-empty values in the specified column.
    # This narrows down the set of rows to process further.
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
            # Handle both string and pandas NA values correctly.
            if isinstance(cell_value, str):
                is_nonempty = cell_value.strip() != ""
            else:
                is_nonempty = pd.notna(cell_value) and cell_value != ""
            if is_nonempty:
                filtered_indices.append(idx)
        indices = filtered_indices
        _LOG.info("After filtering: %d rows to process", len(indices))
    # Phase 4: Execute selected actions in sequence.
    # Each action processes the filtered set of rows independently.
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
        elif action == "summarize_url":
            _summarize_comments(rows, indices=indices)
        elif action == "summarize_article_url":
            _summarize_articles(rows, indices=indices)
    _LOG.info("Download and processing completed")


if __name__ == "__main__":
    _main(_parse())
