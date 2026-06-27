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

This script processes a Google Sheets document containing article links,
downloads article content and Hacker News comments, and optionally summarizes
them using LLMs.

## Supported Actions

1. **download_url**: Fetch HN comments from submission URLs and save to files
2. **download_article_url**: Download article content from direct URLs
3. **summarize_url**: Summarize HN comments using Claude (requires prior download)
4. **summarize_article_url**: Summarize article content using Claude

## Output Files

Output filenames are derived from the Title column with bash-unfriendly
characters replaced with underscores:

- `{title}.hn_comments.txt` - Raw HN comments (from download_url)
- `{title}.hn_comments.summary.txt` - Summarized HN comments (from summarize_url)
- `{title}.text.txt` - Article content (from download_article_url)
- `{title}.text.summary.txt` - Summarized article (from summarize_article_url)

## Example Usage

Download HN comments for rows 0-9 where the "Url" column is not empty:
> download_link_articles.py \
    --url "https://docs.google.com/spreadsheets/d/..." \
    --row_idx "0:10" \
    --select_column "Url" \
    --action download_url

Download all actions (both HN comments and articles):
> download_link_articles.py \
    --url "https://docs.google.com/spreadsheets/d/..." \
    --all

Download article content only:
> download_link_articles.py \
    --url "https://docs.google.com/spreadsheets/d/..." \
    --select_column "Article_url" \
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

Summarize HN comments (requires prior download_url):
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

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hcache_simple as hcacsimp
import helpers.hselect_action as hselacti
import helpers.hsystem as hsystem
import dev_scripts_helpers.scraping.link_gsheet_utils as dshslgsut

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
    gsheet_csv = dshslgsut.get_tmp_file_path(
        "gsheet.csv", "download_link_articles"
    )
    _LOG.debug("Downloading from Google Sheets '%s' to '%s'", url, gsheet_csv)
    dshslgsut.download_from_gsheet(url, gsheet_csv)
    rows = dshslgsut.read_csv(gsheet_csv)
    hdbg.dassert_lt(0, len(rows), "No rows in downloaded CSV")
    _LOG.info("Retrieved %d rows from Google Sheets", len(rows))
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
    _LOG.debug(hprint.func_signature_to_str())
    # Replace any non-alphanumeric character (except underscore) with underscore.
    sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", title)
    # Collapse consecutive underscores into a single underscore.
    sanitized = re.sub(r"_+", "_", sanitized)
    # Remove leading and trailing underscores for cleaner filenames.
    sanitized = sanitized.strip("_")
    _LOG.debug(hprint.to_str("sanitized"))
    return sanitized


def _simplify_html_links(text: str) -> str:
    """
    Simplify HTML links by extracting just the URL and unescaping entities.

    Converts: `<a href="https:&#x2F;&#x2F;example.com">...</a>`
    to: `https://example.com`

    :param text: Text containing HTML links
    :return: Text with simplified links
    """
    _LOG.debug(hprint.func_signature_to_str())

    def replace_link(match):
        """
        Match <a> tags and extract href, then replace with just the URL.
        """
        href = match.group(1)
        # Unescape HTML entities (&#x2F; -> /).
        unescaped = html.unescape(href)
        return unescaped

    # Pattern: <a href="...">...</a>: captures the href attribute.
    pattern = r'<a\s+[^>]*href=["\'](.*?)["\'][^>]*>.*?</a>'
    simplified = re.sub(
        pattern, replace_link, text, flags=re.IGNORECASE | re.DOTALL
    )
    _LOG.debug("simplified=%d chars", len(simplified))
    return simplified


# #############################################################################
# Download HN comments
# #############################################################################


@hcacsimp.simple_cache(cache_type="json", write_through=True)
def _fetch_hn_item(item_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a Hacker News item from the API.

    :param item_id: HN item ID
    :return: Item data dict or None if fetch fails
    """
    _LOG.debug(hprint.func_signature_to_str())
    # Query the official HN API for the item.
    api_url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
    _LOG.debug("Fetching HN item: %s", api_url)
    response = requests.get(api_url, timeout=10)
    response.raise_for_status()
    data = response.json()
    if data:
        result = data
    else:
        _LOG.warning("No data returned for item: %s", item_id)
        result = None
    _LOG.debug("return=%s", result is not None)
    return result


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
    _LOG.debug(hprint.to_str("item_id current_depth"))
    # Guard: stop recursion at max depth to limit API calls and processing time.
    if current_depth >= max_depth:
        result = []
    else:
        # Fetch the item data from HN API.
        item_data = _fetch_hn_item(item_id)
        if not item_data:
            result = []
        else:
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
            result = [comment]
    _LOG.debug(hprint.to_str("len(result)"))
    return result


# #############################################################################
# Content Processing and Formatting
# #############################################################################


def _add_comment_tree(
    comment_list: List[Dict[str, Any]], lines: List[str], depth: int = 0
) -> None:
    """
    Recursively add comments to output, preserving hierarchy.
    """
    _LOG.debug(hprint.func_signature_to_str())
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
    _LOG.debug(hprint.func_signature_to_str())
    lines = []
    _add_comment_tree(comments, lines)
    text = "\n".join(lines)
    # Simplify HTML links in comment text.
    text = _simplify_html_links(text)
    _LOG.debug(hprint.to_str("len(text)"))
    return text


@hcacsimp.simple_cache(cache_type="json", write_through=True)
def _download_article_content(url: str) -> str:
    """
    Download and extract article content from a URL.

    :param url: Article URL
    :return: Article text or empty string if download fails
    """
    hdbg.dassert_is_not(url, None)
    _LOG.debug(hprint.func_signature_to_str())
    # Use a realistic User-Agent to avoid being blocked by many web servers.
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    result = ""
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
        result = BeautifulSoup(text, "html.parser").get_text()
    except Exception as e:
        _LOG.warning("Failed to download article from %s: %s", url, e)
    _LOG.debug(hprint.to_str("len(result)"))
    return result


# #############################################################################
# Download Operations
# #############################################################################


def _download_hn_comments(
    rows: List[Dict[str, Any]], indices: List[int], *, dry_run: bool = False
) -> None:
    """
    Download HN comments for selected rows and save to files.

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
        url = row.get("Url", "").strip()
        title = row.get("Title", "").strip()
        if not url or not title:
            _LOG.warning("Row %d missing Url or Title, skipping", idx)
            continue
        # Validate URL is from HN and extract the submission item ID.
        if not dshslgsut.is_hackernews_url(url):
            _LOG.info("Row %d: URL is not HN URL, skipping", idx)
            continue
        _LOG.debug("Processing row %d: %s", idx, title)
        item_id = dshslgsut.extract_item_id(url)
        # Generate filename from title and check if it already exists.
        sanitized_title = _sanitize_title_for_filename(title)
        output_file = f"{sanitized_title}.hn_comments.txt"
        if os.path.exists(output_file):
            _LOG.warning("File already exists, skipping: %s", output_file)
            continue
        # Fetch comments from HN API and format as readable text.
        _LOG.info("Fetching HN comments for item: %s", item_id)
        if dry_run:
            _LOG.info("[DRY RUN] Would fetch HN comments for item: %s", item_id)
            _LOG.info("[DRY RUN] Would write HN comments to: %s", output_file)
        else:
            hn_comments = _fetch_hn_comments(item_id, max_depth=3)
            # Write comments to disk.
            _LOG.info("Writing HN comments to: %s", output_file)
            formatted_comments = _format_hn_comments_as_text(hn_comments)
            with open(output_file, "w") as f:
                f.write(formatted_comments)
            _LOG.info("Successfully saved HN comments for: %s", title)


def _download_article_urls(
    rows: List[Dict[str, Any]], *, indices: List[int], dry_run: bool = False
) -> None:
    """
    Download article content from Article_url column and save to files.

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
        # Extract article URL and title from the row.
        article_url = row.get("Article_url", "").strip()
        title = row.get("Title", "").strip()
        if not article_url or not title:
            _LOG.warning("Row %d missing Article_url or Title, skipping", idx)
            continue
        _LOG.debug("Processing row %d: %s", idx, title)
        # Generate filename from title and check if it already exists.
        sanitized_title = _sanitize_title_for_filename(title)
        output_file = f"{sanitized_title}.text.txt"
        if os.path.exists(output_file):
            _LOG.warning("File already exists, skipping: %s", output_file)
            continue
        # Download and parse article content from the URL.
        if dry_run:
            _LOG.info("[DRY RUN] Would download article from: %s", article_url)
            _LOG.info(
                "[DRY RUN] Would write article content to: %s", output_file
            )
        else:
            article_content = _download_article_content(article_url)
            if not article_content:
                _LOG.warning(
                    "Row %d: Failed to download article from: %s",
                    idx,
                    article_url,
                )
                continue
            # Write article text to disk.
            _LOG.info("Writing article content to: %s", output_file)
            with open(output_file, "w") as f:
                f.write(article_content)
            _LOG.info("Successfully saved article for: %s", title)


# #############################################################################
# Summarization Operations
# #############################################################################


def _summarize_text_with_llm(
    input_file: str,
    output_file: str,
    prompt: str,
    model: str,
    dry_run: bool = False,
) -> None:
    """
    Summarize text using llm_cli.py and lint the output.

    :param input_file: Path to input text file to summarize
    :param output_file: Path to save the summary
    :param prompt: System prompt to guide the summarization
    :param model: LLM model to use for summarization
    :param dry_run: If True, show what would be done without executing
    """
    _LOG.debug(hprint.to_str("input_file output_file model"))
    _LOG.info("Summarizing: %s", input_file)
    if dry_run:
        _LOG.info(
            "[DRY RUN] Would summarize: %s -> %s (model: %s)",
            input_file,
            output_file,
            model,
        )
        return
    # Save prompt to a temporary file.
    prompt_file = "tmp.summarize_text_with_llm.prompt.txt"
    hio.to_file(prompt_file, prompt)
    _LOG.debug("Saved prompt to: %s", prompt_file)
    # Build command to call llm_cli.py with the given prompt file.
    llm_cli_path = "dev_scripts_helpers/llms/llm_cli.py"
    cmd_parts = [
        llm_cli_path,
        f"--input={input_file}",
        f"--output={output_file}",
        f"--pf={prompt_file}",
        f"--model={model}",
        "--lint",
    ]
    cmd = " ".join(cmd_parts)
    _LOG.debug("Running command: %s", cmd)
    hsystem.system(cmd)
    _LOG.info("Summary saved to: %s", output_file)


def _summarize_articles(
    rows: List[Dict[str, Any]], *, indices: List[int], dry_run: bool = False
) -> None:
    """
    Summarize article text using llm_cli.py.

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
        if not dry_run:
            hdbg.dassert_file_exists(article_file)
        article_summary_file = f"{sanitized_title}.text.summary.txt"
        _LOG.info("Summarizing article text for: %s", title)
        _summarize_text_with_llm(
            article_file,
            article_summary_file,
            article_prompt,
            "gpt-4o-mini",
            dry_run=dry_run,
        )


def _summarize_hn_comments(
    rows: List[Dict[str, Any]], *, indices: List[int], dry_run: bool = False
) -> None:
    """
    Summarize HN comments using llm_cli.py.

    Creates a summary file per article:
    - title.hn_comments.summary.txt: Summary of HN comments

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
        if not dry_run:
            hdbg.dassert_file_exists(comments_file)
        comments_summary_file = f"{sanitized_title}.hn_comments.summary.txt"
        _LOG.info("Summarizing HN comments for: %s", title)
        _summarize_text_with_llm(
            comments_file,
            comments_summary_file,
            comments_prompt,
            "gpt-4o-mini",
            dry_run=dry_run,
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
    _LOG.debug(hprint.func_signature_to_str())
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
    # Optional: specify which rows to process (0-indexed).
    parser.add_argument(
        "--row_idx",
        action="store",
        required=False,
        default="",
        help="Row index or range to process, 1-indexed (e.g., '1' for first row, '1:10' for rows 1-10)",
    )
    # Optional: filter rows by non-empty values in this column.
    parser.add_argument(
        "--select_column",
        action="store",
        default="",
        help="Column name to use for filtering; only rows with non-empty cells in "
        "this column will be processed",
    )
    # Add action selection arguments (download_url, download_article_url, etc).
    hselacti.add_action_arg(parser, VALID_ACTIONS, DEFAULT_ACTIONS)
    # Dry run mode: show what would happen without executing
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Dry run mode: show what would be done without actually executing actions",
    )
    # Add verbosity control argument.
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main entry point.
    """
    _LOG.debug(hprint.func_signature_to_str())
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
    rows = _load_rows_from_gsheet(args.url)
    # Phase 2: Determine which rows to process based on `row_idx` argument.
    indices = _parse_row_idx(args.row_idx, len(rows))
    _LOG.info("Row indices to process: %s", indices)
    # Phase 3: Execute selected actions in sequence.
    # Each action processes the filtered set of rows independently.
    if args.dry_run:
        _LOG.info("DRY RUN MODE: showing what would be done without executing")
    actions_remaining = actions
    while actions_remaining:
        action = actions_remaining[0]
        to_execute, actions_remaining = hselacti.mark_action(
            action, actions_remaining
        )
        if not to_execute:
            continue
        if action == "download_url":
            _download_hn_comments(rows, indices=indices, dry_run=args.dry_run)
        elif action == "download_article_url":
            _download_article_urls(rows, indices=indices, dry_run=args.dry_run)
        elif action == "summarize_url":
            _summarize_hn_comments(rows, indices=indices, dry_run=args.dry_run)
        elif action == "summarize_article_url":
            _summarize_articles(rows, indices=indices, dry_run=args.dry_run)
    _LOG.info("Download and processing completed")


if __name__ == "__main__":
    _main(_parse())
