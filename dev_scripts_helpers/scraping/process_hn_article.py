#!/usr/bin/env -S uv run

# /// script
# dependencies = [
#   "beautifulsoup4",
#   "google",
#   "googleapi",
#   "gspread",
#   "lxml",
#   "pandas",
#   "pyyaml",
#   "requests",
#   "tqdm",
# ]
# ///

"""
Process HN articles from a Google Sheets document.

This script manages four actions:
1. download: Download data from Google Sheets to CSV
2. update_article_url: Extract article URLs from HN links using HN API
3. update_article_tag: Tag articles using topics
4. update_article_cluster: Map topics to clusters
5. upload: Upload the processed CSV back to Google Sheets

Example usage:

# Download data from Google Sheets
> process_hn_article.py \
    --url "https://docs.google.com/spreadsheets/d/1i6Z7v2..." \
    --action download

# Run all actions
> process_hn_article.py \
    --url "https://docs.google.com/spreadsheets/d/1i6Z7v2..." \
    --all

# Skip upload action
> process_hn_article.py \
    --url "https://docs.google.com/spreadsheets/d/1i6Z7v2..." \
    --skip-action upload

Import as:

import dev_scripts_helpers.scraping.process_hn_article as dssprar
"""

import argparse
import csv
import datetime
import logging
import re
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from tqdm import tqdm

import helpers.hdbg as hdbg
import helpers.hllm_cli as hllmcli
import helpers.hparser as hparser
import helpers.hsystem as hsystem
import helpers.hselect_action as hselacti
import helpers.hcache_simple as hcacsimp

_LOG = logging.getLogger(__name__)

_CLASSIFICATION_PROMPT = """
Given the title and URL of an article, emit the tag among the ones below that represents
the article best. Consider both the title and URL when making your classification.
"""

HN_CSV_FILE = "hn_gsheet.csv"
PROCESSED_CSV_FILE = "processed_data.csv"

# Map article topics to high-level cluster categories for grouping and analysis.
topic_to_cluster = {
    "AI Agents & Tool-Using Systems": "AI",
    "Automated Theorem Proving": "AI",
    "Causal Inference": "AI",
    "Diffusion Models": "AI",
    "Knowledge Graphs": "AI",
    "LLM Reasoning": "AI",
    "Multi-Agent Systems": "AI",
    "Probabilistic Programming": "AI",
    "Prompt Engineering": "AI",
    "Self-Supervised Learning": "AI",
    "Uncertainty & Belief Modeling": "AI",
    #
    "AI Infrastructure": "Data/Infra",
    "Data Engineering & Pipelines": "Data/Infra",
    "High-Performance Computing": "Data/Infra",
    #
    "Developer Tools": "Dev tools",
    "Git and GitHub": "Dev tools",
    "Open Source": "Dev tools",
    "Python Ecosystem": "Dev tools",
    "Rust and C++": "Dev tools",
    #
    "Quant Finance": "Finance",
    "Trading Strategies": "Finance",
    #
    "Complex Systems & Network Dynamics": "Math",
    "Mathematical Concepts": "Math",
    "Simulation & Agent-Based Modeling": "Math",
    "Time Series": "Math",
    "Unconventional Computing": "Math",
    #
    "Careers & Professional Growth": "Business",
    "Marketing and Sales": "Business",
    "Organizational Behavior & Incentives": "Business",
    "Psychology & Well-Being": "Business",
    #
    "Cybersecurity & Privacy": "CyberSec",
    "Risk Management & Compliance": "CyberSec",
    #
    "Code Refactoring": "SwEng",
    "Dev Productivity": "SwEng",
    "Software Architecture": "SwEng",
    "Software Project Management": "SwEng",
    "System Reliability & Fault Tolerance": "SwEng",
}


def _get_tmp_file_path(filename: str) -> str:
    """
    Get the path for a temporary file.
    """
    return "./tmp.process_hn_article." + filename


# TODO(gp): Factor out this.
def _read_csv(filepath: str) -> List[Dict[str, Any]]:
    """
    Read CSV file and return list of dictionaries.

    Each row becomes a dictionary with column names as keys.

    :param filepath: Path to CSV file
    :return: List of row dictionaries
    """
    rows = []
    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def _write_csv(
    filepath: str,
    rows: List[Dict[str, Any]],
    *,
    fieldnames: List[str],
) -> None:
    """
    Write list of dictionaries to CSV file.

    :param filepath: Path to CSV file
    :param rows: List of row dictionaries
    :param fieldnames: Column names in order
    """
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _is_hackernews_url(url: str) -> bool:
    """
    Check if URL is a Hacker News item URL.

    :param url: URL to check
    :return: True if URL is a HN item URL
    """
    hdbg.dassert_isinstance(url, str)
    return "news.ycombinator.com/item?id=" in url


def _extract_item_id(hn_url: str) -> str:
    """
    Extract the item ID from a Hacker News URL.

    :param hn_url: Hacker News item URL
    :return: Item ID
    """
    hdbg.dassert(_is_hackernews_url(hn_url), "Not a Hacker News URL: %s", hn_url)
    match = re.search(r"item\?id=(\d+)", hn_url)
    hdbg.dassert(match, "Could not extract item ID from: %s", hn_url)
    return match.group(1)  # type: ignore


@hcacsimp.simple_cache(cache_type="json", write_through=True)
def _extract_article_url(hn_url: str) -> str:
    """
    Extract article URL from a Hacker News submission using the HN API.

    :param hn_url: Hacker News item URL
    :return: Article URL
    """
    hdbg.dassert_isinstance(hn_url, str)
    hdbg.dassert(_is_hackernews_url(hn_url), "Not a Hacker News URL: %s", hn_url)
    # Extract the numeric item ID from the HN URL.
    item_id = _extract_item_id(hn_url)
    # Query the HN API for the item details which includes the actual article URL.
    api_url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
    _LOG.debug("Fetching from API: %s", api_url)
    response = requests.get(api_url, timeout=10)
    response.raise_for_status()
    data = response.json()
    hdbg.dassert(data, "No data returned for item: %s", item_id)
    article_url = data.get("url")
    hdbg.dassert(article_url, "No URL found for item: %s", item_id)
    _LOG.debug("Extracted URL: %s", article_url)
    return article_url


def _download_from_gsheet(url: str) -> str:
    """
    Download data from Google Sheets and save to a temporary CSV file.

    :param url: URL of the Google Sheets document
    :return: Path to the saved CSV file
    """
    _LOG.info("Downloading data from Google Sheets")
    # Invoke from_gsheet.py to export the 'All' sheet to a temporary CSV file.
    output_file = _get_tmp_file_path(HN_CSV_FILE)
    cmd = (
        f"from_gsheet.py --url '{url}' "
        f"--output_file '{output_file}' --overwrite"
    )
    hsystem.system(cmd, print_command=True)
    hdbg.dassert_path_exists(output_file)
    # Validate the download: read the CSV and verify it has content.
    rows = _read_csv(output_file)
    num_cols = len(rows[0].keys()) if rows else 0
    _LOG.info(
        "Loaded %d rows and %d columns from Google Sheets '%s' into '%s'",
        len(rows),
        num_cols,
        url,
        output_file,
    )
    return output_file


def _update_article_urls() -> str:
    """
    Extract article URLs from HN links and update CSV.

    For HN links, extracts Article_url using HN API.
    For non-HN links, uses the URL as-is.

    :return: Path to the updated CSV file
    """
    # Load and validate the HN CSV from the previous download step.
    hn_csv = _get_tmp_file_path(HN_CSV_FILE)
    hdbg.dassert_path_exists(hn_csv, "Must download from gsheet first")
    _LOG.debug("Loading CSV to extract article URLs")
    rows = _read_csv(hn_csv)
    hdbg.dassert(rows, "No rows in CSV: %s", hn_csv)
    columns = list(rows[0].keys()) if rows else []
    hdbg.dassert_in("Url", columns, "CSV must have 'Url' column")
    hdbg.dassert_in("Article_url", columns, "CSV must have 'Article_url' column")
    # Iterate through rows: for HN links, fetch the actual article URL via the HN API; for other URLs, use them as-is.
    for idx, row in enumerate(rows):
        url = row["Url"]
        if _is_hackernews_url(url):
            _LOG.debug("Row %d: Extracting from HN URL", idx)
            article_url = _extract_article_url(url)
            row["Article_url"] = article_url
        else:
            _LOG.debug("Row %d: Non-HN URL, using as-is", idx)
            row["Article_url"] = url
    # Write the updated rows with extracted article URLs to a new CSV file for the next processing stage.
    processed_csv = _get_tmp_file_path(PROCESSED_CSV_FILE)
    _LOG.debug("Writing updated data to CSV file: '%s'", processed_csv)
    _write_csv(processed_csv, rows, fieldnames=columns)
    _LOG.info(
        "Updated %d rows with article URLs to '%s'", len(rows), processed_csv
    )
    return processed_csv


def _update_article_tags(
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
    hdbg.dassert_lt(0, batch_size)
    #
    processed_csv = _get_tmp_file_path(PROCESSED_CSV_FILE)
    hdbg.dassert_path_exists(processed_csv, "Must update article URLs first")
    _LOG.debug("Loading CSV for tagging")
    df = pd.read_csv(processed_csv)
    # Determine which title column to use.
    hdbg.dassert_in("Article_title", df.columns)
    hdbg.dassert_in("title", df.columns)
    # Build list of items (title + URL) for classification.
    valid_indices = []
    valid_items = []
    for idx, row in df.iterrows():
        # Get title from Article_title or fall back to title column.
        title = ""
        # Get URL.
        url = row["url"]
        # Format as "Title: <title>\nURL: <url>".
        item_text = f"Title: {title}\nURL: {url}" if url else f"Title: {title}"
        valid_indices.append(idx)
        valid_items.append(item_text)
    _LOG.info(
        "Tagging %d articles using LLM in batches of %d",
        len(valid_items),
        batch_size,
    )
    if not valid_items:
        _LOG.warning("No valid items to tag")
        return
    # Initialize Article_tag column if it doesn't exist.
    hdbg.dassert_is_in("Article_tag", df.columns)
    tag_col_idx = df.columns.get_loc("Article_tag")
    # Process items in batches with progress bar for entire workload.
    num_batches = (len(valid_items) + batch_size - 1) // batch_size
    _LOG.info("Processing %d items in %d batches", len(valid_items), num_batches)
    for batch_num in tqdm(range(num_batches), desc="Tagging articles"):
        # Get batch indices.
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(valid_items))
        batch_items = valid_items[start_idx:end_idx]
        batch_indices = valid_indices[start_idx:end_idx]
        _LOG.debug(
            "Processing batch %d/%d (%d items)",
            batch_num + 1,
            num_batches,
            len(batch_items),
        )
        # Call LLM for this batch.
        batch_tags, _ = hllmcli.apply_llm_batch_with_shared_prompt(
            prompt=_CLASSIFICATION_PROMPT,
            input_list=batch_items,
            model=model or "gpt-4o-mini",
        )
        # Update dataframe with batch results.
        for idx, tag in zip(batch_indices, batch_tags):
            df.at[idx, "Article_tag"] = tag.strip()
        # Update output file after each batch.
        _LOG.debug("Updating output file: %s", output_file)
        df.to_csv(output_file, index=False)
    _LOG.info("Finished tagging %d articles", len(valid_items))


def _update_article_clusters() -> str:
    """
    Map article tags to clusters using topic-to-cluster mapping.

    :return: Path to the updated CSV file
    """
    # Load the CSV from the previous tagging step.
    processed_csv = _get_tmp_file_path(PROCESSED_CSV_FILE)
    hdbg.dassert_path_exists(processed_csv, "Must update article tags first")
    _LOG.debug("Loading CSV to assign clusters")
    rows = _read_csv(processed_csv)
    hdbg.dassert(rows, "No rows in CSV: %s", processed_csv)
    columns = list(rows[0].keys()) if rows else []
    hdbg.dassert_in("Article_tag", columns, "CSV must have 'Article_tag' column")
    hdbg.dassert_in(
        "Article_cluster", columns, "CSV must have 'Article_cluster' column"
    )
    # Map each article's tag to its corresponding cluster using the predefined topic_to_cluster dictionary.
    for idx, row in enumerate(rows):
        tag = row["Article_tag"].strip()
        hdbg.dassert_isinstance(tag, str)
        hdbg.dassert_is_in(tag, topic_to_cluster)
        cluster = topic_to_cluster[tag]
        _LOG.debug("Row %d: Tag '%s' maps to cluster '%s'", idx, tag, cluster)
        row["Article_cluster"] = cluster
    # Write the clustered data back to the CSV for final upload.
    _LOG.debug("Writing clustered data to CSV file: '%s'", processed_csv)
    _write_csv(processed_csv, rows, fieldnames=columns)
    _LOG.info("Assigned clusters to %d rows to '%s'", len(rows), processed_csv)
    return processed_csv


# TODO(gp): Share with update_hn_gsheet_from_raindrop.py.
def _upload_to_gsheet(url: str) -> None:
    """
    Upload processed CSV data to Google Sheets.

    :param url: URL of the Google Sheets document
    :param tabname: Name of the tab to create/overwrite (defaults to today's date)
    """
    # Use today's date as the sheet name.
    tabname = "process_hn_article." + datetime.datetime.now().strftime("%Y-%m-%d")
    # Load and validate the fully processed CSV that includes article URLs and clusters.
    processed_csv = _get_tmp_file_path(PROCESSED_CSV_FILE)
    hdbg.dassert_path_exists(processed_csv, "processed CSV file not found")
    _LOG.info("Reading processed CSV file: '%s'", processed_csv)
    rows = _read_csv(processed_csv)
    num_cols = len(rows[0].keys()) if rows else 0
    _LOG.info("Loaded %d rows and %d columns", len(rows), num_cols)
    # Invoke to_gsheet.py to upload the processed data as a new sheet.
    _LOG.info("Writing data to tab '%s' in Google Sheet", tabname)
    cmd = (
        f"to_gsheet.py --input_file '{processed_csv}' --url '{url}' "
        f"--tabname '{tabname}' --overwrite"
    )
    hsystem.system(cmd, print_command=True)
    _LOG.info("Successfully wrote data to Google Sheet")


# List of available pipeline actions; executed in order when --all is used.
VALID_ACTIONS = [
    "download",
    "update_article_url",
    "update_article_tag",
    "update_article_cluster",
    "upload",
]
DEFAULT_ACTIONS = VALID_ACTIONS[:]


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--url",
        action="store",
        default=None,
        help="URL of the Google Sheets document (required for download and upload actions)",
    )
    hselacti.add_action_arg(parser, VALID_ACTIONS, DEFAULT_ACTIONS)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Resolve which actions to run based on command-line flags (--action, --all, --skip-action).
    actions = hselacti.select_actions(args, VALID_ACTIONS, DEFAULT_ACTIONS)
    _LOG.info(
        "Actions to execute:\n%s",
        hselacti.actions_to_string(actions, VALID_ACTIONS, add_frame=True),
    )
    # Execute actions in sequence: each action depends on outputs from previous stages.
    actions_remaining = actions
    while actions_remaining:
        action = actions_remaining[0]
        to_execute, actions_remaining = hselacti.mark_action(
            action, actions_remaining
        )
        if not to_execute:
            continue
        # Dispatch to the appropriate handler based on the current action.
        if action == "download":
            hdbg.dassert_is_not(
                args.url,
                None,
                "--url is required for download action",
            )
            _download_from_gsheet(args.url)
        elif action == "update_article_url":
            _update_article_urls()
        elif action == "update_article_tag":
            _update_article_tags(
                url_col_idx + 1,
                batch_size=10,
            )
        elif action == "update_article_cluster":
            _update_article_clusters()
        elif action == "upload":
            hdbg.dassert_is_not(
                args.url,
                None,
                "--url is required for upload action",
            )
            _upload_to_gsheet(args.url)


if __name__ == "__main__":
    _main(_parse())
