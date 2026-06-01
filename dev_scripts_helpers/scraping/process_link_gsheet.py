#!/usr/bin/env -S uv run

# /// script
# dependencies = [
#   "beautifulsoup4",
#   "google",
#   "googleapi",
#   "gspread",
#   "llm",
#   "lxml",
#   "pandas",
#   "pyyaml",
#   "requests",
#   "tokencost",
#   "tqdm",
# ]
# ///

"""
Process links and articles from a Google Sheets document.

This script manages the following actions:
1. download_link_gsheet: Download data from Google Sheets to CSV (alias)
2. update_article_url: Extract article URLs from HN links using HN API
3. update_article_tag: Tag articles using LLM-based classification
4. update_article_cluster: Map topics to clusters
5. replace_article_tags: Replace old topic names with simplified names
6. upload_link_gsheet: Upload the processed CSV back to Google Sheets

Example usage:

# Download data from Google Sheets
> process_link_gsheet.py \
    --url "https://docs.google.com/spreadsheets/d/1i6Z7v2..." \
    --action download_link_gsheet

# Run all actions
> process_link_gsheet.py \
    --url "https://docs.google.com/spreadsheets/d/1i6Z7v2..." \
    --all

# Replace topic names and upload
> process_link_gsheet.py \
    --url "https://docs.google.com/spreadsheets/d/1i6Z7v2..." \
    --action replace_article_tags \
    --action upload_link_gsheet

Import as:

import dev_scripts_helpers.scraping.process_link_gsheet as dslg
"""

import argparse
import datetime
import logging

import pandas as pd
import requests
from tqdm import tqdm

import helpers.hdbg as hdbg
import helpers.hllm_cli as hllmcli
import helpers.hlogging as hloggin
import helpers.hparser as hparser
import helpers.hselect_action as hselacti
import helpers.hcache_simple as hcacsimp
import dev_scripts_helpers.scraping.link_gsheet_utils as dshslgsut

_LOG = logging.getLogger(__name__)

HN_CSV_FILE = "hn_gsheet.csv"
URLS_CSV_FILE = "processed_data.urls.csv"
TAGS_CSV_FILE = "processed_data.tags.csv"
CLUSTERS_CSV_FILE = "processed_data.clusters.csv"

# Map article topics to high-level cluster categories for grouping and analysis.
topic_to_cluster = {
    "AI Agents": "AI",
    "Automated Theorem Proving": "AI",
    "Causal Inference": "AI",
    "Diffusion Models": "AI",
    "Knowledge Graphs": "AI",
    "LLM Reasoning": "AI",
    "Multi-Agent Systems": "AI",
    "Probabilistic Programming": "AI",
    "Prompt Engineering": "AI",
    "Self-Supervised Learning": "AI",
    "Uncertainty Modeling": "AI",
    #
    "AI Infrastructure": "Data/Infra",
    "Data Engineering": "Data/Infra",
    "High-Performance Computing": "Data/Infra",
    #
    "Developer Tools": "Dev tools",
    "Git": "Dev tools",
    "Open Source": "Dev tools",
    "Python Ecosystem": "Dev tools",
    "Rust and C++": "Dev tools",
    #
    "Quant Finance": "Finance",
    "Trading Strategies": "Finance",
    #
    "Complex Systems": "Math",
    "Mathematical Concepts": "Math",
    "Simulation": "Math",
    "Time Series": "Math",
    "Unconventional Computing": "Math",
    #
    "Careers": "Business",
    "Marketing and Sales": "Business",
    "Organizational Behavior": "Business",
    "Psychology": "Business",
    #
    "Cybersecurity": "CyberSec",
    "Risk Management": "CyberSec",
    #
    "Code Refactoring": "SwEng",
    "Dev Productivity": "SwEng",
    "Software Architecture": "SwEng",
    "Software Project Management": "SwEng",
    "System Reliability": "SwEng",
}

# Map old topic names to new simplified names for data migration.
old_topic_to_new_topic = {
    "AI Agents & Tool-Using Systems": "AI Agents",
    "Uncertainty & Belief Modeling": "Uncertainty Modeling",
    "Data Engineering & Pipelines": "Data Engineering",
    "Git and GitHub": "Git",
    "Complex Systems & Network Dynamics": "Complex Systems",
    "Simulation & Agent-Based Modeling": "Simulation",
    "Careers & Professional Growth": "Careers",
    "Organizational Behavior & Incentives": "Organizational Behavior",
    "Psychology & Well-Being": "Psychology",
    "Cybersecurity & Privacy": "Cybersecurity",
    "Risk Management & Compliance": "Risk Management",
    "System Reliability & Fault Tolerance": "System Reliability",
}


_CLASSIFICATION_PROMPT = """
Given the title and URL of an article, emit the tag among the ones below that represents
the article best. Consider both the title and URL when making your classification.
"""


@hcacsimp.simple_cache(cache_type="json", write_through=True)
def _extract_article_url(hn_url: str) -> str:
    """
    Extract article URL from a Hacker News submission using the HN API.

    :param hn_url: Hacker News item URL
    :return: Article URL or the HN URL if no article URL exists
    """
    hdbg.dassert_isinstance(hn_url, str)
    hdbg.dassert(
        dshslgsut.is_hackernews_url(hn_url), "Not a Hacker News URL: %s", hn_url
    )
    _LOG.debug("Processing HN URL: %s", hn_url)
    # Extract the numeric item ID from the HN URL.
    item_id = dshslgsut.extract_item_id(hn_url)
    _LOG.debug("Extracted item ID: %s", item_id)
    # Query the HN API for the item details which includes the actual article URL.
    api_url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
    _LOG.debug("Fetching from API: %s", api_url)
    response = requests.get(api_url, timeout=10)
    response.raise_for_status()
    data = response.json()
    hdbg.dassert(data, "No data returned for item: %s", item_id)
    _LOG.debug("API response received for item %s", item_id)
    article_url = data.get("url")
    if not article_url:
        _LOG.debug(
            "No URL found for item %s (type: %s), using HN URL instead",
            item_id,
            data.get("type", "unknown"),
        )
        return hn_url
    _LOG.debug("Successfully extracted article URL: %s", article_url)
    return article_url


def _download_from_gsheet(url: str) -> str:
    """
    Download data from Google Sheets and save to a temporary CSV file.

    :param url: URL of the Google Sheets document
    :return: Path to the saved CSV file
    """
    output_file = dshslgsut.get_tmp_file_path(HN_CSV_FILE, "process_link_gsheet")
    dshslgsut.download_from_gsheet(url, output_file)
    return output_file


def _update_article_urls() -> str:
    """
    Extract article URLs from HN links and update CSV.

    For HN links, extracts Article_url using HN API.
    For non-HN links, uses the URL as-is.
    Only processes rows where Article_url is empty; skips rows with existing values.

    :return: Path to the updated CSV file
    """
    # Load and validate the HN CSV from the previous download step.
    hn_csv = dshslgsut.get_tmp_file_path(HN_CSV_FILE, "process_link_gsheet")
    hdbg.dassert_path_exists(hn_csv, "Must download from gsheet first")
    _LOG.info("Loading CSV '%s' to extract article URLs", hn_csv)
    rows = dshslgsut.read_csv(hn_csv)
    num_cols = len(rows[0].keys()) if rows else 0
    _LOG.info(
        "Loaded %d rows and %d columns from '%s'", len(rows), num_cols, hn_csv
    )
    hdbg.dassert(rows, "No rows in CSV: %s", hn_csv)
    columns = list(rows[0].keys()) if rows else []
    hdbg.dassert_in("Url", columns, "CSV must have 'Url' column")
    hdbg.dassert_in("Article_url", columns, "CSV must have 'Article_url' column")
    # Create a mask of rows with empty Article_url cells.
    rows_to_process = []
    row_indices = []
    for idx, row in enumerate(rows):
        article_url = row.get("Article_url")
        if not isinstance(article_url, str) or article_url.strip() == "":
            rows_to_process.append(row)
            row_indices.append(idx)
    _LOG.info("Found %d empty Article_url cells to fill", len(rows_to_process))
    # Process only rows with empty Article_url cells.
    for idx, row in tqdm(
        enumerate(rows_to_process),
        total=len(rows_to_process),
        desc="Extracting article URLs",
    ):
        url = row["Url"]
        if dshslgsut.is_hackernews_url(url):
            _LOG.debug(
                "Processing row %d: Extracting from HN URL", row_indices[idx]
            )
            article_url = _extract_article_url(url)
            row["Article_url"] = article_url
        else:
            _LOG.debug(
                "Processing row %d: Non-HN URL, using as-is", row_indices[idx]
            )
            row["Article_url"] = url
    # Write the updated rows with extracted article URLs to a new CSV file for the next processing stage.
    urls_csv = dshslgsut.get_tmp_file_path(URLS_CSV_FILE, "process_link_gsheet")
    _LOG.info("Writing updated data to CSV file: '%s'", urls_csv)
    dshslgsut.write_csv(urls_csv, rows, fieldnames=columns)
    _LOG.info(
        "Wrote %d rows with %d columns to '%s'",
        len(rows),
        len(columns),
        urls_csv,
    )
    return urls_csv


def _update_article_tags(
    model: str,
    *,
    batch_size: int = 10,
) -> str:
    """
    Tag articles using LLM classification and update output file after each batch.

    Uses Title column plus Article_url for classification.
    Only processes rows where Article_tag is empty; skips rows with existing values.

    :param batch_size: Number of articles to process in each batch
    :param model: Optional LLM model name to use
    :return: Path to the updated CSV file
    """
    hdbg.dassert_lt(0, batch_size)
    urls_csv = dshslgsut.get_tmp_file_path(URLS_CSV_FILE, "process_link_gsheet")
    hdbg.dassert_path_exists(urls_csv, "Must update article URLs first")
    _LOG.info("Loading CSV '%s' for tagging", urls_csv)
    df = pd.read_csv(urls_csv)
    _LOG.info(
        "Loaded %d rows and %d columns from '%s'",
        len(df),
        len(df.columns),
        urls_csv,
    )
    hdbg.dassert_in("Title", df.columns)
    hdbg.dassert_in("Article_tag", df.columns)
    # Create a mask of rows with empty Article_tag cells.
    valid_indices = []
    valid_items = []
    for idx, row in df.iterrows():
        tag_val = row["Article_tag"]
        if pd.isna(tag_val) or str(tag_val).strip() == "":
            # Get title from Title column.
            title = ""
            title_val = row["Title"]
            if bool(pd.notna(title_val)):
                title = str(title_val)
            # Get URL.
            url_val = row.get("Article_url")
            url = ""
            if bool(pd.notna(url_val)):
                url = str(url_val)
            # Format as "Title: <title>\nURL: <url>".
            item_text = (
                f"Title: {title}\nURL: {url}" if url else f"Title: {title}"
            )
            valid_indices.append(idx)
            valid_items.append(item_text)
    _LOG.info(
        "Tagging %d articles using LLM in batches of %d",
        len(valid_items),
        batch_size,
    )
    if not valid_items:
        _LOG.warning("No valid items to tag")
        return urls_csv
    # Process items in batches with progress bar for entire workload.
    num_batches = (len(valid_items) + batch_size - 1) // batch_size
    _LOG.info(
        "Processing %d items in %d batches (batch size: %d)",
        len(valid_items),
        num_batches,
        batch_size,
    )
    tags_csv = dshslgsut.get_tmp_file_path(TAGS_CSV_FILE, "process_link_gsheet")
    prompt = _CLASSIFICATION_PROMPT
    prompt += "\n".join(topic_to_cluster.keys())
    for batch_num in tqdm(range(num_batches), desc="Tagging articles"):
        # Get batch indices.
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(valid_items))
        batch_items = valid_items[start_idx:end_idx]
        batch_indices = valid_indices[start_idx:end_idx]
        _LOG.info(
            "Processing batch %d/%d (%d items)",
            batch_num + 1,
            num_batches,
            len(batch_items),
        )
        # Call LLM for this batch.
        batch_tags, _ = hllmcli.apply_llm_batch_with_shared_prompt(
            prompt=prompt, input_list=batch_items, model=model
        )
        # Update dataframe with batch results.
        for idx, tag in zip(batch_indices, batch_tags):
            df.at[idx, "Article_tag"] = tag.strip()
        # Update output file after each batch.
        _LOG.info("Writing batch results to: %s", tags_csv)
        df.to_csv(tags_csv, index=False)
    _LOG.info("Finished tagging and wrote %d rows to '%s'", len(df), tags_csv)
    return tags_csv


def _update_article_clusters() -> str:
    """
    Map article tags to clusters using topic-to-cluster mapping.

    Only processes rows where Article_cluster is empty; skips rows with existing values.

    :return: Path to the updated CSV file
    """
    # Load the CSV from the previous tagging step.
    tags_csv = dshslgsut.get_tmp_file_path(TAGS_CSV_FILE, "process_link_gsheet")
    hdbg.dassert_path_exists(tags_csv, "Must update article tags first")
    _LOG.info("Loading CSV to assign clusters from: %s", tags_csv)
    rows = dshslgsut.read_csv(tags_csv)
    hdbg.dassert(rows, "No rows in CSV: %s", tags_csv)
    columns = list(rows[0].keys()) if rows else []
    _LOG.info(
        "Loaded %d rows and %d columns from '%s'",
        len(rows),
        len(columns),
        tags_csv,
    )
    hdbg.dassert_in("Article_tag", columns, "CSV must have 'Article_tag' column")
    hdbg.dassert_in(
        "Article_cluster", columns, "CSV must have 'Article_cluster' column"
    )
    # Create a mask of rows with empty Article_cluster cells.
    rows_to_process = []
    row_indices = []
    for idx, row in enumerate(rows):
        cluster = row.get("Article_cluster")
        if not cluster or cluster.strip() == "":
            rows_to_process.append(row)
            row_indices.append(idx)
    _LOG.info(
        "Found %d empty Article_cluster cells to fill", len(rows_to_process)
    )
    _LOG.info("Mapping %d unique topics to clusters", len(topic_to_cluster))
    # Map each article's tag to its corresponding cluster using the predefined topic_to_cluster dictionary.
    for idx, row in tqdm(
        enumerate(rows_to_process),
        total=len(rows_to_process),
        desc="Assigning clusters",
    ):
        tag = row["Article_tag"].strip()
        hdbg.dassert_isinstance(tag, str)
        if tag in topic_to_cluster:
            cluster = topic_to_cluster[tag]
            row["Article_cluster"] = cluster
        else:
            _LOG.warning(f"Tag '{tag}' not found in topic_to_cluster mapping")
            row["Article_cluster"] = ""
    # Write the clustered data to a new CSV file for final upload.
    clusters_csv = dshslgsut.get_tmp_file_path(
        CLUSTERS_CSV_FILE, "process_link_gsheet"
    )
    _LOG.info("Writing clustered data to CSV file: '%s'", clusters_csv)
    dshslgsut.write_csv(clusters_csv, rows, fieldnames=columns)
    _LOG.info(
        "Assigned clusters to %d rows and %d columns, wrote to '%s'",
        len(rows_to_process),
        len(columns),
        clusters_csv,
    )
    return clusters_csv


def _replace_article_tags() -> str:
    """
    Replace old topic names with new simplified topic names in Article_tag column.

    Updates the CSV file with renamed topics using the old_topic_to_new_topic mapping.

    :return: Path to the updated CSV file
    """
    clusters_csv = dshslgsut.get_tmp_file_path(
        CLUSTERS_CSV_FILE, "process_link_gsheet"
    )
    hdbg.dassert_path_exists(clusters_csv, "Must update article clusters first")
    _LOG.info("Loading CSV '%s' to replace topic names", clusters_csv)
    rows = dshslgsut.read_csv(clusters_csv)
    hdbg.dassert(rows, "No rows in CSV: %s", clusters_csv)
    columns = list(rows[0].keys()) if rows else []
    hdbg.dassert_in("Article_tag", columns, "CSV must have 'Article_tag' column")
    _LOG.info(
        "Loaded %d rows and %d columns from '%s'",
        len(rows),
        len(columns),
        clusters_csv,
    )
    replacements_made = 0
    for row in rows:
        old_tag = row.get("Article_tag", "").strip()
        if old_tag in old_topic_to_new_topic:
            new_tag = old_topic_to_new_topic[old_tag]
            row["Article_tag"] = new_tag
            replacements_made += 1
            _LOG.debug("Replaced '%s' with '%s'", old_tag, new_tag)
    _LOG.info("Made %d topic name replacements", replacements_made)
    dshslgsut.write_csv(clusters_csv, rows, fieldnames=columns)
    _LOG.info(
        "Wrote %d rows with %d columns to '%s'",
        len(rows),
        len(columns),
        clusters_csv,
    )
    return clusters_csv


def _upload_to_gsheet(url: str) -> None:
    """
    Upload processed CSV data to Google Sheets.

    :param url: URL of the Google Sheets document
    """
    tabname = "process_link_gsheet." + datetime.datetime.now().strftime(
        "%Y-%m-%d"
    )
    clusters_csv = dshslgsut.get_tmp_file_path(
        CLUSTERS_CSV_FILE, "process_link_gsheet"
    )
    hdbg.dassert_path_exists(clusters_csv, "clusters CSV file not found")
    dshslgsut.upload_to_gsheet(url, clusters_csv, tabname)


# List of available pipeline actions; executed in order when --all is used.
VALID_ACTIONS = [
    "download_link_gsheet",
    "update_article_url",
    "update_article_tag",
    "update_article_cluster",
    "replace_article_tags",
    "upload_link_gsheet",
]
DEFAULT_ACTIONS = [
    "download_link_gsheet",
    "update_article_url",
    "update_article_tag",
    "update_article_cluster",
    # "replace_article_tags",
    "upload_link_gsheet",
]


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--url",
        action="store",
        default=None,
        help="URL of the Google Sheets document (required for download_link_gsheet and upload_link_gsheet actions)",
    )
    parser.add_argument(
        "--model",
        action="store",
        default="gpt-4o-mini",
        help="LLM model name to use for tagging (default: gpt-4o-mini)",
    )
    hselacti.add_action_arg(parser, VALID_ACTIONS, DEFAULT_ACTIONS)
    hcacsimp.add_cache_control_arg(parser)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    hloggin.shutup_chatty_modules(verbosity=logging.ERROR)
    for module_name in ["httpcore", "httpx", "_base_client", "_trace", "openai"]:
        logger = logging.getLogger(module_name)
        logger.setLevel(logging.CRITICAL)
    hcacsimp.parse_cache_control_args(args)
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
        if action == "download_link_gsheet":
            hdbg.dassert_is_not(
                args.url,
                None,
                f"--url is required for {action} action",
            )
            _download_from_gsheet(args.url)
        elif action == "update_article_url":
            _update_article_urls()
        elif action == "update_article_tag":
            _update_article_tags(args.model)
        elif action == "update_article_cluster":
            _update_article_clusters()
        elif action == "replace_article_tags":
            _replace_article_tags()
        elif action == "upload_link_gsheet":
            hdbg.dassert_is_not(
                args.url,
                None,
                f"--url is required for {action} action",
            )
            _upload_to_gsheet(args.url)


if __name__ == "__main__":
    _main(_parse())
