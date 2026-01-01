#!/usr/bin/env python

"""
Extract article information from Hacker News submissions using the HN API.

This script processes Hacker News item URLs from CSV files and uses the
Firebase API to extract selected fields:
- The submission title (--extract_title)
- The original article URL that the submission links to (--extract_url)
- The submission timestamp converted to date format YYYY-MM-DD in UTC (--extract_timestamp)
- Optionally, classify articles into categories using LLM (--tag_articles, requires --extract_title)

All extraction options are opt-in and must be explicitly enabled.

The script uses the official HN API: https://hacker-news.firebaseio.com/v0/

Examples:
> ./extract_hn_article.py --input_file input.csv --output_file output.csv --extract_title --extract_url

> ./extract_hn_article.py --input_file input.csv --output_file output.csv --extract_title --extract_timestamp

> ./extract_hn_article.py --input_file input.csv --output_file output.csv --extract_title --extract_url --extract_timestamp

> ./extract_hn_article.py --input_file input.csv --output_file output.csv --extract_title --tag_articles

> ./extract_hn_article.py --input_file input.csv --output_file output.csv --extract_title --tag_articles --batch_size 5

Import as:

import dev_scripts_helpers.scraping_script.extract_hn_article as dsscehar
"""

import argparse
import datetime
import logging
import os
import re
from typing import List, Optional, Tuple

import pandas as pd
import requests
from tqdm import tqdm

import helpers.hdbg as hdbg
import helpers.hllm_cli as hllmcli
import helpers.hparser as hparser
import helpers.hcache_simple as hcacsimp

_LOG = logging.getLogger(__name__)

# Classification prompt for article tagging.
_CLASSIFICATION_PROMPT = """
Given the title and URL of an article, emit the tag among the ones below that represents
the article best. Consider both the title and URL when making your classification.

AI Agents & Tool-Using Systems
Automated Theorem Proving
Causal Inference
Diffusion Models
Knowledge Graphs
LLM Reasoning
Multi-Agent Systems
Probabilistic Programming
Prompt Engineering
Self-Supervised Learning
Uncertainty & Belief Modeling
AI Infrastructure
Data Engineering & Pipelines
High-Performance Computing
Developer Tools
Git and GitHub
Open Source
Python Ecosystem
Rust and C++
Quant Finance
Trading Strategies
Complex Systems & Network Dynamics
Mathematical Concepts
Simulation & Agent-Based Modeling
Time Series
Unconventional Computing
Careers & Professional Growth
Marketing and Sales
Organizational Behavior & Incentives
Psychology & Well-Being
Cybersecurity & Privacy
Risk Management & Compliance
Code Refactoring
Dev Productivity
Software Architecture
Software Project Management
System Reliability & Fault Tolerance
"""


# #############################################################################


def _convert_timestamp_to_date(timestamp_val) -> Optional[str]:
    """
    Convert a timestamp value to date string (YYYY-MM-DD in UTC).

    :param timestamp_val: Unix timestamp (int/float) or date string
    :return: Date string in YYYY-MM-DD format or None if conversion fails
    """
    if pd.isna(timestamp_val):
        return None
    # If already a string in YYYY-MM-DD format, return as is.
    if isinstance(timestamp_val, str):
        if len(timestamp_val) == 10 and timestamp_val.count("-") == 2:
            return timestamp_val
        # Try to parse ISO 8601 datetime string (e.g., '2025-10-17T21:53:18.487Z').
        try:
            dt = datetime.datetime.fromisoformat(timestamp_val.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
        # Try to parse datetime string (e.g., '2019-10-31 11:49:06').
        try:
            dt = datetime.datetime.strptime(timestamp_val, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
    # Try to convert numeric timestamp.
    try:
        timestamp_unix = float(timestamp_val)
        dt = datetime.datetime.fromtimestamp(timestamp_unix, tz=datetime.timezone.utc)
        return dt.strftime("%Y-%m-%d")
    except (ValueError, OSError) as e:
        _LOG.warning("Could not convert timestamp %s: %s", timestamp_val, e)
        return None


def _is_hackernews_url(url: str) -> bool:
    """
    Check if URL is a Hacker News item URL.

    :param url: URL to check
    :return: True if URL is a HN item URL
    """
    if not isinstance(url, str):
        return False
    return "news.ycombinator.com/item?id=" in url


def _extract_item_id(hn_url: str) -> Optional[str]:
    """
    Extract the item ID from a Hacker News URL.

    :param hn_url: Hacker News item URL
    :return: Item ID or None if not found
    """
    # Match pattern: item?id=12345
    match = re.search(r"item\?id=(\d+)", hn_url)
    if match:
        return match.group(1)
    return None


@hcacsimp.simple_cache(cache_type="json", write_through=True)
def _extract_article_info(hn_url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extract article title, URL, and timestamp from a Hacker News submission using the API.

    Uses the HN Firebase API: https://hacker-news.firebaseio.com/v0/

    :param hn_url: Hacker News item URL
    :return: Tuple of (article_title, article_url, timestamp_date)
    """
    # Handle non-string inputs (e.g., NaN from pandas).
    if not isinstance(hn_url, str):
        _LOG.warning("Invalid URL type: %s (type: %s)", hn_url, type(hn_url))
        return None, None, None
    if not _is_hackernews_url(hn_url):
        _LOG.warning("Not a Hacker News URL: %s", hn_url)
        return None, None, None
    # Extract item ID from URL.
    item_id = _extract_item_id(hn_url)
    if not item_id:
        _LOG.warning("Could not extract item ID from: %s", hn_url)
        return None, None, None
    try:
        # Fetch data from HN API.
        api_url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
        _LOG.debug("Fetching from API: %s", api_url)
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        # Parse JSON response.
        data = response.json()
        if not data:
            _LOG.warning("No data returned for item: %s", item_id)
            return None, None, None
        # Extract title, URL, and timestamp.
        article_title = data.get("title")
        article_url = data.get("url")
        timestamp_unix = data.get("time")
        if not article_title:
            _LOG.warning("No title found for item: %s", item_id)
            return None, None, None
        # Convert Unix timestamp to date string (YYYY-MM-DD in UTC).
        timestamp_date = None
        if timestamp_unix:
            dt = datetime.datetime.fromtimestamp(timestamp_unix, tz=datetime.timezone.utc)
            timestamp_date = dt.strftime("%Y-%m-%d")
            _LOG.debug("Converted timestamp %s to date: %s", timestamp_unix, timestamp_date)
        _LOG.debug("Extracted title: %s", article_title)
        _LOG.debug("Extracted URL: %s", article_url)
        _LOG.debug("Extracted date: %s", timestamp_date)
        return article_title, article_url, timestamp_date
    except requests.RequestException as e:
        _LOG.warning("API request failed for %s: %s", hn_url, e)
        return None, None, None
    except Exception as e:
        _LOG.warning("Error processing %s: %s", hn_url, e)
        return None, None, None


def _tag_articles_with_llm(
    df: pd.DataFrame,
    output_file: str,
    tag_col_idx: int,
    *,
    batch_size: int = 10,
    model: Optional[str] = None,
) -> None:
    """
    Tag articles using LLM classification and update output file after each batch.

    Uses Article_title (from HN API) or title column (from input CSV), plus URL.

    :param df: DataFrame containing Article_title or title column, and url column
    :param output_file: Path to output CSV file
    :param tag_col_idx: Index position for inserting Article_tag column
    :param batch_size: Number of articles to process in each batch
    :param model: Optional LLM model name to use
    """
    hdbg.dassert_isinstance(df, pd.DataFrame)
    hdbg.dassert_lt(0, batch_size)
    # Determine which title column to use.
    has_article_title = "Article_title" in df.columns
    has_title = "title" in df.columns
    if not has_article_title and not has_title:
        _LOG.warning("Neither Article_title nor title column found, skipping tagging")
        return
    # Build list of items (title + URL) for classification.
    valid_indices = []
    valid_items = []
    for idx, row in df.iterrows():
        # Get title from Article_title or fall back to title column.
        title = ""
        if has_article_title and pd.notna(row["Article_title"]) and row["Article_title"]:
            title = row["Article_title"]
        elif has_title and pd.notna(row["title"]) and row["title"]:
            title = row["title"]
        # Get URL.
        url = row.get("url", "")
        if not title:
            continue
        # Format as "Title: <title>\nURL: <url>".
        item_text = f"Title: {title}\nURL: {url}" if url else f"Title: {title}"
        valid_indices.append(idx)
        valid_items.append(item_text)
    _LOG.info("Tagging %d articles using LLM in batches of %d", len(valid_items), batch_size)
    if not valid_items:
        _LOG.warning("No valid items to tag")
        return
    # Initialize Article_tag column if it doesn't exist.
    if "Article_tag" not in df.columns:
        df.insert(tag_col_idx, "Article_tag", "")
    # Process items in batches with progress bar for entire workload.
    num_batches = (len(valid_items) + batch_size - 1) // batch_size
    _LOG.info("Processing %d items in %d batches", len(valid_items), num_batches)
    for batch_num in tqdm(range(num_batches), desc="Tagging articles"):
        # Get batch indices.
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(valid_items))
        batch_items = valid_items[start_idx:end_idx]
        batch_indices = valid_indices[start_idx:end_idx]
        _LOG.debug("Processing batch %d/%d (%d items)", batch_num + 1, num_batches, len(batch_items))
        # Call LLM for this batch.
        batch_tags = hllmcli.apply_llm_batch(
            prompt=_CLASSIFICATION_PROMPT,
            input_list=batch_items,
            model=model,
        )
        # Update dataframe with batch results.
        for idx, tag in zip(batch_indices, batch_tags):
            df.at[idx, "Article_tag"] = tag.strip()
        # Update output file after each batch.
        _LOG.debug("Updating output file: %s", output_file)
        df.to_csv(output_file, index=False)
    _LOG.info("Finished tagging %d articles", len(valid_items))


def _process_csv_file(
    input_file: str,
    output_file: str,
    *,
    extract_title: bool = False,
    extract_url: bool = False,
    extract_timestamp: bool = False,
    tag_articles: bool = False,
    url_batch_size: int = 10,
    batch_size: int = 10,
    model: Optional[str] = None,
) -> None:
    """
    Process CSV file with HN URLs and add article info columns.

    Extracts selected fields: Article_title, Article_url, and/or Timestamp.

    :param input_file: Path to input CSV file with 'url' column
    :param output_file: Path to output CSV file
    :param extract_title: Whether to extract article title
    :param extract_url: Whether to extract article URL
    :param extract_timestamp: Whether to extract timestamp (date in YYYY-MM-DD format)
    :param tag_articles: Whether to tag articles using LLM classification
    :param url_batch_size: Batch size for URL extraction (default: 10)
    :param batch_size: Batch size for LLM processing (used when tag_articles=True)
    :param model: Optional LLM model name to use for tagging
    """
    hdbg.dassert(os.path.exists(input_file), "Input file does not exist:", input_file)
    hdbg.dassert_lt(0, url_batch_size)
    hdbg.dassert_lt(0, batch_size)
    # Log info if tagging without title extraction.
    if tag_articles and not extract_title:
        _LOG.info("--tag_articles enabled without --extract_title, will use existing title column if available")
    # Read the CSV file.
    _LOG.info("Reading input file: %s", input_file)
    df = pd.read_csv(input_file)
    # Check that url column exists.
    hdbg.dassert_in("url", df.columns, "CSV must have 'url' column")
    # Convert existing Timestamp column to date format if present.
    if "Timestamp" in df.columns:
        _LOG.info("Converting Timestamp column to date format")
        df["Timestamp"] = df["Timestamp"].apply(_convert_timestamp_to_date)
    # Check if any extraction is requested.
    extract_any = extract_title or extract_url or extract_timestamp
    if not extract_any and not tag_articles:
        _LOG.warning("No extraction options enabled, output will be same as input")
        df.to_csv(output_file, index=False)
        return
    # Get url column index for inserting new columns.
    url_col_idx = df.columns.get_loc("url")
    col_offset = 1
    # Initialize columns based on extraction flags.
    if extract_title and "Article_title" not in df.columns:
        df.insert(url_col_idx + col_offset, "Article_title", "")
        col_offset += 1
    if extract_url and "Article_url" not in df.columns:
        df.insert(url_col_idx + col_offset, "Article_url", "")
        col_offset += 1
    if extract_timestamp and "Timestamp" not in df.columns:
        df.insert(url_col_idx + col_offset, "Timestamp", "")
        col_offset += 1
    # Process URLs in batches with progress bar for entire workload.
    num_urls = len(df)
    num_batches = (num_urls + url_batch_size - 1) // url_batch_size
    _LOG.info("Processing %d URLs in %d batches of size %d", num_urls, num_batches, url_batch_size)
    for batch_num in tqdm(range(num_batches), desc="Extracting articles"):
        # Get batch indices.
        start_idx = batch_num * url_batch_size
        end_idx = min(start_idx + url_batch_size, num_urls)
        _LOG.debug("Processing batch %d/%d (rows %d-%d)", batch_num + 1, num_batches, start_idx, end_idx - 1)
        # Process URLs in this batch.
        for idx in range(start_idx, end_idx):
            url = df.at[idx, "url"]
            _LOG.debug("Processing row %d: %s", idx, url)
            article_title, article_url, timestamp_date = _extract_article_info(url)
            # Update columns based on extraction flags.
            if extract_title:
                df.at[idx, "Article_title"] = article_title if article_title else ""
            if extract_url:
                df.at[idx, "Article_url"] = article_url if article_url else ""
            if extract_timestamp and timestamp_date:
                # Only overwrite timestamp if we extracted one from HN API.
                # This preserves existing timestamps for non-HN URLs.
                df.at[idx, "Timestamp"] = timestamp_date
        # Update output file after each batch.
        _LOG.debug("Updating output file: %s", output_file)
        df.to_csv(output_file, index=False)
    _LOG.info("Finished extracting %d articles", num_urls)
    # Optionally tag articles with LLM.
    if tag_articles:
        _LOG.info("Tagging articles using LLM")
        _tag_articles_with_llm(
            df,
            output_file,
            url_col_idx + col_offset,
            batch_size=batch_size,
            model=model,
        )
    _LOG.info("Done processing %d URLs", len(df))


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # CSV mode.
    parser.add_argument(
        "--input_file",
        action="store",
        required=True,
        help="Input CSV file with 'url' column",
    )
    parser.add_argument(
        "--output_file",
        action="store",
        required=True,
        help="Output CSV file with selected columns based on extraction flags",
    )
    # URL extraction options.
    parser.add_argument(
        "--url_batch_size",
        action="store",
        type=int,
        default=10,
        help="Batch size for URL extraction (default: 10)",
    )
    # Field extraction options.
    parser.add_argument(
        "--extract_title",
        action="store_true",
        help="Extract article title from HN submissions",
    )
    parser.add_argument(
        "--extract_url",
        action="store_true",
        help="Extract article URL from HN submissions",
    )
    parser.add_argument(
        "--extract_timestamp",
        action="store_true",
        help="Extract submission timestamp (converted to date YYYY-MM-DD in UTC)",
    )
    # LLM tagging options.
    parser.add_argument(
        "--tag_articles",
        action="store_true",
        help="Tag articles using LLM classification",
    )
    parser.add_argument(
        "--batch_size",
        action="store",
        type=int,
        default=10,
        help="Batch size for LLM processing (default: 10)",
    )
    parser.add_argument(
        "--model",
        action="store",
        help="LLM model name to use for tagging (e.g., gpt-4, claude-3-opus)",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Process CSV file.
    _process_csv_file(
        args.input_file,
        args.output_file,
        extract_title=args.extract_title,
        extract_url=args.extract_url,
        extract_timestamp=args.extract_timestamp,
        tag_articles=args.tag_articles,
        url_batch_size=args.url_batch_size,
        batch_size=args.batch_size,
        model=args.model,
    )


if __name__ == "__main__":
    _main(_parse())
