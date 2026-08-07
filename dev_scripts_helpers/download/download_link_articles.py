#!/usr/bin/env -S uv run

# /// script
# dependencies = [
#   "beautifulsoup4",
#   "pandas",
#   "pymupdf",
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

## Supported Actions

- **download_article_url**: Download article content from direct URLs
- **download_hn_url**: Fetch HN comments from submission URLs and save to files
- **summarize_article_url**: Summarize article content using Claude
- **summarize_hn_url**: Summarize HN comments using Claude (requires prior download)

## Output Files

Output filenames are derived from the Title column with bash-unfriendly
characters replaced with underscores:

- `{title}.1.article_url.txt` - Article content (from download_article_url)
- `{title}.2.hn_url.txt` - Raw HN comments (from download_hn_url)
- `{title}.3.article_url.summary.txt` - Summarized article (from summarize_article_url)
- `{title}.4.hn_url.summary.txt` - Summarized HN comments (from summarize_hn_url)

# Usage Example

- Download HN comments (and its linked article, if any) for a single submission
  directly, bypassing Google Sheets; the input type (HN submission vs. generic
  article) is auto-detected:
> download_link_articles.py \
    --input "https://news.ycombinator.com/item?id=12345"

- Download a single article directly, bypassing Google Sheets; the title is
  extracted from the page's <title> tag:
> download_link_articles.py \
    --input "https://queue.acm.org/detail.cfm?id=3807963"

- Use an explicit output base name instead of the derived title:
> download_link_articles.py \
    --input "https://news.ycombinator.com/item?id=12345" \
    --output my_submission

- Overwrite existing output files instead of skipping:
> download_link_articles.py \
    --input "https://news.ycombinator.com/item?id=12345" \
    --no_incremental

- Download HN comments for rows 0-9 where the "Hn_url" column is not empty:
> download_link_articles.py \
    --url "https://docs.google.com/spreadsheets/d/..." \
    --row_idx "0:10" \
    --action download_hn_url

- Download all actions (both HN comments and articles):
> download_link_articles.py \
    --url "https://docs.google.com/spreadsheets/d/..." \
    --all_actions

- Download article content only:
> download_link_articles.py \
    --url "https://docs.google.com/spreadsheets/d/..." \
    --action download_article_url

- Download from rows 0-4, skip article downloads:
> download_link_articles.py \
    --url "https://docs.google.com/spreadsheets/d/..." \
    --row_idx "0:5" \
    --skip_action download_article_url

- Summarize articles (requires prior download_article_url):
> download_link_articles.py \
    --url "https://docs.google.com/spreadsheets/d/..." \
    --action summarize_article_url

- Summarize HN comments (requires prior download_hn_url):
> download_link_articles.py \
    --url "https://docs.google.com/spreadsheets/d/..." \
    --action summarize_hn_url

- Show what would be done without downloading or summarizing:
> download_link_articles.py \
    --url "https://docs.google.com/spreadsheets/d/..." \
    --dry_run

Import as:

import dev_scripts_helpers.download.download_link_articles as dssdla
"""

import argparse
import html
import logging
import os
import re
from typing import Any, Dict, List, Optional

import bs4
import requests
from tqdm import tqdm

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hcache_simple as hcacsimp
import helpers.hselect_action as hselacti
import helpers.hsystem as hsystem
import dev_scripts_helpers.download.download_to_md as dshddtm
import dev_scripts_helpers.download.download_utils as dshddut
import dev_scripts_helpers.download.link_gsheet_utils as dshdlgsut

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
    gsheet_csv = dshdlgsut.get_tmp_file_path(
        "gsheet.csv", "download_link_articles"
    )
    _LOG.debug("Downloading from Google Sheets '%s' to '%s'", url, gsheet_csv)
    dshdlgsut.download_from_gsheet(url, gsheet_csv)
    rows = dshdlgsut.read_csv(gsheet_csv)
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
    return rows


# #############################################################################
# Phase 3: Download
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


def _build_row_from_hn_url(hn_url: str) -> List[Dict[str, Any]]:
    """
    Build a single synthetic row from a directly-provided HN URL.

    Bypasses the Google Sheets download by fetching the submission title
    directly from the HN API, so `--input` can be used standalone with a HN
    submission URL.

    :param hn_url: Hacker News item URL
    :return: List containing a single row with Title, Article_url, Hn_url
    """
    _LOG.debug(hprint.func_signature_to_str())
    hdbg.dassert(
        dshdlgsut.is_hackernews_url(hn_url), "Not a Hacker News URL: %s", hn_url
    )
    item_id = dshdlgsut.extract_item_id(hn_url)
    item_data = _fetch_hn_item(item_id)
    title = item_id
    # Link posts have a "url" field pointing to the external article; Show
    # HN / Ask HN / text posts have no "url" (only "text"), so Article_url
    # stays empty and article download/summarize is skipped for those.
    article_url = ""
    if item_data:
        title = item_data.get("title", item_id)
        article_url = item_data.get("url", "")
    row = {"Title": title, "Article_url": article_url, "Hn_url": hn_url}
    _LOG.info(
        "Built row from --input: title='%s' article_url='%s'",
        title,
        article_url,
    )
    return [row]


@hcacsimp.simple_cache(cache_type="json", write_through=True)
def _fetch_article_title(url: str) -> Optional[str]:
    """
    Fetch a web page and extract the contents of its `<title>` tag.

    :param url: Article URL
    :return: Page title, or None if it can't be fetched or has no
        `<title>` tag
    """
    _LOG.debug(hprint.func_signature_to_str())
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;"
            "q=0.9,image/webp,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        _LOG.warning("Failed to fetch '%s': %s", url, e)
        return None
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    if not soup.title or not soup.title.string:
        _LOG.warning("No <title> tag found in '%s'", url)
        return None
    # BeautifulSoup already unescapes HTML entities; just collapse internal
    # whitespace/newlines.
    title = soup.title.string.strip()
    title = re.sub(r"\s+", " ", title)
    _LOG.debug(hprint.to_str("title"))
    return title


def _build_row_from_article_url(article_url: str) -> List[Dict[str, Any]]:
    """
    Build a single synthetic row from a directly-provided article URL.

    Bypasses the Google Sheets download by fetching the page's `<title>`
    tag directly, so `--input` can be used standalone with a generic
    article URL.

    :param article_url: Article URL
    :return: List containing a single row with Title, Article_url, Hn_url
    """
    _LOG.debug(hprint.func_signature_to_str())
    title = _fetch_article_title(article_url)
    if not title:
        _LOG.warning(
            "Could not extract title from '%s', using URL as title",
            article_url,
        )
        title = article_url
    row = {"Title": title, "Article_url": article_url, "Hn_url": ""}
    _LOG.info(
        "Built row from --input: title='%s' article_url='%s'",
        title,
        article_url,
    )
    return [row]


def _build_row_from_input(input_arg: str) -> List[Dict[str, Any]]:
    """
    Build a single synthetic row from a directly-provided URL, bypassing
    Google Sheets.

    The input type (Hacker News submission vs. generic article) is
    auto-detected, mirroring `download_to_md.py`'s `detect_input_type()`.

    :param input_arg: HN submission URL or generic article URL
    :return: List containing a single row with Title, Article_url, Hn_url
    """
    _LOG.debug(hprint.func_signature_to_str())
    if dshdlgsut.is_hackernews_url(input_arg):
        rows = _build_row_from_hn_url(input_arg)
    else:
        rows = _build_row_from_article_url(input_arg)
    _LOG.debug(hprint.to_str("rows"))
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


def _fetch_hn_url(
    item_id: str,
    *,
    max_depth: int = -1,
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
    if max_depth >= 0 and current_depth >= max_depth:
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
            # Recursively fetch all child comments (replies) if they exist.
            kids = item_data.get("kids", [])
            if kids:
                replies = []
                for kid_id in kids:
                    kid_comments = _fetch_hn_url(
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


def _count_comments(comments: List[Dict[str, Any]]) -> int:
    """
    Recursively count total comments including nested replies.

    :param comments: List of comment dicts with nested replies
    :return: Total comment count
    """
    count = len(comments)
    for comment in comments:
        if "replies" in comment:
            count += _count_comments(comment["replies"])
    return count


def _format_hn_url_as_text(comments: List[Dict[str, Any]]) -> str:
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
    total_comments = _count_comments(comments)
    _LOG.info("Total comments downloaded: %d", total_comments)
    _LOG.debug(hprint.to_str("len(text)"))
    return text


def _download_hn_urls(
    rows: List[Dict[str, Any]],
    indices: List[int],
    *,
    dry_run: bool = False,
    no_incremental: bool = False,
) -> None:
    """
    Download HN comments for selected rows and save to files.

    :param rows: List of data rows
    :param indices: List of row indices to process
    :param dry_run: If True, show what would be done without executing
    :param no_incremental: If True, overwrite output files even if they
        already exist
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
        url = row.get("Hn_url", "").strip()
        title = row.get("Title", "").strip()
        if not url or not title:
            _LOG.warning("Row %d missing Url or Title, skipping", idx)
            continue
        # Validate URL is from HN and extract the submission item ID.
        if not dshdlgsut.is_hackernews_url(url):
            _LOG.info("Row %d: URL is not HN URL, skipping", idx)
            continue
        _LOG.debug("Processing row %d: %s", idx, title)
        item_id = dshdlgsut.extract_item_id(url)
        # Generate filename from title and check if it already exists.
        sanitized_title = _sanitize_title_for_filename(title)
        output_file = f"{sanitized_title}.3.hn_url.txt"
        # Fetch comments from HN API and format as readable text.
        _LOG.info("Fetching HN comments for item: %s", item_id)
        if dry_run:
            _LOG.info("[DRY RUN] Would fetch HN comments for item: %s", item_id)
            _LOG.info("[DRY RUN] Would write HN comments to: %s", output_file)
        elif os.path.exists(output_file) and not no_incremental:
            _LOG.info("HN comments already exist, skipping: %s", output_file)
        else:
            hn_comments = _fetch_hn_url(item_id, max_depth=10)
            total_comments = _count_comments(hn_comments)
            _LOG.info("Fetched %d total comments", total_comments)
            # Write comments to disk.
            _LOG.info("Writing HN comments to: %s", output_file)
            formatted_comments = _format_hn_url_as_text(hn_comments)
            hio.to_file(output_file, formatted_comments)
            _LOG.info("Successfully saved HN comments for: %s", title)


def _download_article_urls(
    rows: List[Dict[str, Any]],
    *,
    indices: List[int],
    dry_run: bool = False,
    no_incremental: bool = False,
) -> None:
    """
    Download article content from Article_url column and save to files.

    :param rows: List of data rows
    :param indices: List of row indices to process
    :param dry_run: If True, show what would be done without executing
    :param no_incremental: If True, overwrite output files even if they
        already exist
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
        output_file = f"{sanitized_title}.1.article_url.txt"
        # TODO(ai_gp): Consider using directly
        # dev_scripts_helpers/download/download_to_md.py
        # Use `download_to_md.py`'s shared, already-correct URL-type detection
        # (arXiv/DOI/PDF) instead of maintaining a separate, narrower check
        # here; the actual download still dispatches via
        # `dshddut.download_article()` below.
        input_type = dshddtm.detect_input_type(article_url)
        downloader = (
            "download_academic_paper_to_md.py"
            if input_type == "academic_paper"
            else "download_html_to_md.py"
        )
        if dry_run:
            _LOG.info(
                "[DRY RUN] Would download article from '%s' via %s",
                article_url,
                downloader,
            )
            _LOG.info(
                "[DRY RUN] Would write article content to: %s", output_file
            )
        elif os.path.exists(output_file) and not no_incremental:
            _LOG.info(
                "Article content already exists, skipping: %s", output_file
            )
        else:
            _LOG.info(
                "Downloading article from '%s' via %s", article_url, downloader
            )
            try:
                dshddut.download_article(article_url, output_file)
            except Exception as e:
                _LOG.warning(
                    "Row %d: Failed to download article from '%s': %s",
                    idx,
                    article_url,
                    e,
                )
                continue
            _LOG.info("Successfully saved article for: %s", title)


# #############################################################################
# Phase 4: Summarization
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
    hsystem.system(cmd, print_command=True)
    _LOG.info("Summary saved to: %s", output_file)


def _summarize_hn_url(
    rows: List[Dict[str, Any]],
    *,
    indices: List[int],
    dry_run: bool = False,
    no_incremental: bool = False,
) -> None:
    """
    Summarize HN comments using llm_cli.py.

    Creates a summary file per article:
    - title.4.hn_url.summary.txt: Summary of HN comments

    :param rows: List of data rows
    :param indices: List of row indices to process
    :param dry_run: If True, show what would be done without executing
    :param no_incremental: If True, overwrite the summary even if it
        already exists
    """
    _LOG.debug(hprint.to_str("len(indices)"))
    _LOG.info(
        "Summarizing comments for %d rows%s",
        len(indices),
        " (DRY RUN)" if dry_run else "",
    )
    comments_prompt = """
        Analyze the Hacker News comment section.
        From all comments, summarize the 5 most interesting ones based on:
        1. Thought-provoking or insightful content
        2. Unique perspective or uncommon knowledge
        3. Sparks discussion or debate
        4. Technically informative or educational
        5. Controversial but well-argued.
        Avoid comments that are: simple jokes, memes, very short reactions,
        repetitive or low-effort.
        Do not include commenter names.
        Format as plain text without markdown.
    """
    comments_prompt = hprint.dedent(comments_prompt)
    for idx in tqdm(indices, desc="Summarizing comments"):
        row = rows[idx]
        title = row.get("Title", "").strip()
        hdbg.dassert(title)
        _LOG.debug("Processing row %d: %s", idx, title)
        # Generate sanitized filename from title.
        sanitized_title = _sanitize_title_for_filename(title)
        # Summarize HN comments if .hn_url.txt file exists.
        comments_file = f"{sanitized_title}.3.hn_url.txt"
        if not dry_run:
            hdbg.dassert_file_exists(comments_file)
        comments_summary_file = f"{sanitized_title}.4.hn_url.summary.txt"
        if (
            not dry_run
            and os.path.exists(comments_summary_file)
            and not no_incremental
        ):
            _LOG.info(
                "HN comments summary already exists, skipping: %s",
                comments_summary_file,
            )
            continue
        _LOG.info("Summarizing HN comments for: %s", title)
        _summarize_text_with_llm(
            comments_file,
            comments_summary_file,
            comments_prompt,
            "gpt-4o-mini",
            dry_run=dry_run,
        )


def _summarize_articles(
    rows: List[Dict[str, Any]],
    *,
    indices: List[int],
    dry_run: bool = False,
    no_incremental: bool = False,
) -> None:
    """
    Summarize article text using llm_cli.py.

    Creates a summary file per article:
    - title.text.summary.txt: Summary of the article

    :param rows: List of data rows
    :param indices: List of row indices to process
    :param dry_run: If True, show what would be done without executing
    :param no_incremental: If True, overwrite the summary even if it
        already exists
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
        # Summarize article text.
        article_file = f"{sanitized_title}.1.article_url.txt"
        if not dry_run:
            hdbg.dassert_file_exists(article_file)
        article_summary_file = f"{sanitized_title}.2.article_url.summary.txt"
        if (
            not dry_run
            and os.path.exists(article_summary_file)
            and not no_incremental
        ):
            _LOG.info(
                "Article summary already exists, skipping: %s",
                article_summary_file,
            )
            continue
        _LOG.info("Summarizing article text for: %s", title)
        _summarize_text_with_llm(
            article_file,
            article_summary_file,
            article_prompt,
            "gpt-4o-mini",
            dry_run=dry_run,
        )


# #############################################################################
# CLI and Entry Points
# #############################################################################


_VALID_ACTIONS = [
    "download_article_url",
    "download_hn_url",
    "summarize_article_url",
    "summarize_hn_url",
]
_DEFAULT_ACTIONS = _VALID_ACTIONS[:]


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments.
    """
    _LOG.debug(hprint.func_signature_to_str())
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    # Exactly one data source is required: a Google Sheets document, or a
    # single HN submission/article URL processed directly (bypassing Google
    # Sheets), with the input type auto-detected.
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--url",
        action="store",
        help="URL of the Google Sheets document",
    )
    source_group.add_argument(
        "-i",
        "--input",
        action="store",
        help="Directly download a single HN submission URL or article URL, "
        "bypassing Google Sheets (type auto-detected)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="",
        help=(
            "Output base name (no extension) shared by the generated files, "
            "used with --input only (ignored with --url). If not "
            "specified, the sanitized page/submission title is used"
        ),
    )
    # Optional: specify which rows to process (0-indexed). Ignored when
    # --input is used, since it processes a single synthetic row.
    parser.add_argument(
        "--row_idx",
        action="store",
        required=False,
        default="",
        help="Row index or range to process, 1-indexed (e.g., '1' for first row, '1:10' for rows 1-10); ignored with --input",
    )
    # Add action selection arguments (download_hn_url, download_article_url, etc).
    hselacti.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    # Add cache control argument.
    hcacsimp.add_cache_control_arg(parser)
    # Dry run mode: show what would happen without executing.
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Dry run mode: show what would be done without actually executing actions",
    )
    parser.add_argument(
        "--no_incremental",
        action="store_true",
        help="Overwrite existing output files instead of skipping",
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
    hcacsimp.parse_cache_control_args(args)
    # Phase 1: Determine the rows to process, either from a single --input
    # (type auto-detected) or from the full Google Sheets document.
    is_hn_input = False
    if args.input:
        is_hn_input = dshdlgsut.is_hackernews_url(args.input)
        rows = _build_row_from_input(args.input)
        if args.output:
            # Override the derived title so downstream filenames use the
            # explicit --output base name instead of the sanitized
            # page/submission title.
            rows[0]["Title"] = args.output
        indices = [0]
    else:
        rows = _load_rows_from_gsheet(args.url)
        # Phase 2: Determine which rows to process based on `row_idx` argument.
        indices = _parse_row_idx(args.row_idx, len(rows))
    _LOG.info("Row indices to process: %s", indices)
    # Determine which actions to execute based on command-line flags. When
    # processing a single --input directly that resolves to an HN
    # submission with no linked article (e.g., Show HN / Ask HN / text
    # posts have no Article_url), restrict the defaults to HN-only actions.
    # Likewise, a generic article --input has no Hn_url, so restrict to
    # article-only actions. Both are overridable explicitly via
    # --action/--skip_action/--enable.
    default_actions = _DEFAULT_ACTIONS
    if is_hn_input and not rows[0]["Article_url"]:
        default_actions = ["download_hn_url", "summarize_hn_url"]
    elif args.input and not is_hn_input:
        default_actions = ["download_article_url", "summarize_article_url"]
    actions = hselacti.select_actions(args, _VALID_ACTIONS, default_actions)
    _LOG.info(
        "Actions to execute:\n%s",
        hselacti.actions_to_string(actions, _VALID_ACTIONS, add_frame=True),
    )
    # Execute selected actions in sequence.
    # Each action processes the filtered set of rows independently.
    if args.dry_run:
        _LOG.info("DRY RUN MODE: showing what would be done without executing")
    while actions:
        action = actions[0]
        to_execute, actions = hselacti.mark_action(action, actions)
        if not to_execute:
            continue
        # Phase 3: Download article.
        if action == "download_article_url":
            _download_article_urls(
                rows,
                indices=indices,
                dry_run=args.dry_run,
                no_incremental=args.no_incremental,
            )
        elif action == "download_hn_url":
            _download_hn_urls(
                rows,
                indices,
                dry_run=args.dry_run,
                no_incremental=args.no_incremental,
            )
        elif action == "summarize_article_url":
            # Phase 4: Summarization.
            _summarize_articles(
                rows,
                indices=indices,
                dry_run=args.dry_run,
                no_incremental=args.no_incremental,
            )
        elif action == "summarize_hn_url":
            _summarize_hn_url(
                rows,
                indices=indices,
                dry_run=args.dry_run,
                no_incremental=args.no_incremental,
            )
        else:
            raise ValueError(f"Invalid action='{action}'")
    hdbg.dassert_eq(
        len(actions), 0, "There are unprocessed actions: %s", str(actions)
    )
    _LOG.info("Download and processing completed")


if __name__ == "__main__":
    _main(_parse())
