#!/usr/bin/env python

"""
Extract article title and URL from Hacker News submissions using the HN API.

This script processes Hacker News item URLs from CSV files and uses the Firebase API to extract:
- The submission title
- The original article URL that the submission links to
- Optionally, classify articles into categories using LLM

The script uses the official HN API: https://hacker-news.firebaseio.com/v0/

Examples:
> ./extract_hn_article.py --input_file input.csv --output_file output.csv

> ./extract_hn_article.py --input_file input.csv --output_file output.csv --tag_articles

> ./extract_hn_article.py --input_file input.csv --output_file output.csv --tag_articles --batch_size 5

Import as:

import dev_scripts_helpers.scraping_script.extract_hn_article as dsscehar
"""

import argparse
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
Given the title of an article emit the tag among the ones below that represent
the article best

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
def _extract_article_info(hn_url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract article title and URL from a Hacker News submission using the API.

    Uses the HN Firebase API: https://hacker-news.firebaseio.com/v0/

    :param hn_url: Hacker News item URL
    :return: Tuple of (article_title, article_url)
    """
    # Handle non-string inputs (e.g., NaN from pandas).
    if not isinstance(hn_url, str):
        _LOG.warning("Invalid URL type: %s (type: %s)", hn_url, type(hn_url))
        return None, None
    if not _is_hackernews_url(hn_url):
        _LOG.warning("Not a Hacker News URL: %s", hn_url)
        return None, None
    # Extract item ID from URL.
    item_id = _extract_item_id(hn_url)
    if not item_id:
        _LOG.warning("Could not extract item ID from: %s", hn_url)
        return None, None
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
            return None, None
        # Extract title and URL.
        article_title = data.get("title")
        article_url = data.get("url")
        if not article_title:
            _LOG.warning("No title found for item: %s", item_id)
            return None, None
        _LOG.debug("Extracted title: %s", article_title)
        _LOG.debug("Extracted URL: %s", article_url)
        return article_title, article_url
    except requests.RequestException as e:
        _LOG.warning("API request failed for %s: %s", hn_url, e)
        return None, None
    except Exception as e:
        _LOG.warning("Error processing %s: %s", hn_url, e)
        return None, None


def _tag_articles_with_llm(
    df: pd.DataFrame,
    output_file: str,
    url_col_idx: int,
    *,
    batch_size: int = 10,
    model: Optional[str] = None,
) -> None:
    """
    Tag articles using LLM classification and update output file after each batch.

    :param df: DataFrame containing Article_title column
    :param output_file: Path to output CSV file
    :param url_col_idx: Index of url column (for inserting Article_tag column)
    :param batch_size: Number of titles to process in each batch
    :param model: Optional LLM model name to use
    """
    hdbg.dassert_isinstance(df, pd.DataFrame)
    hdbg.dassert_in("Article_title", df.columns)
    hdbg.dassert_lt(0, batch_size)
    # Get article titles from dataframe.
    article_titles = df["Article_title"].tolist()
    _LOG.info("Tagging %d articles using LLM in batches of %d", len(article_titles), batch_size)
    # Filter out empty titles and track their indices.
    valid_indices = [i for i, title in enumerate(article_titles) if title]
    valid_titles = [article_titles[i] for i in valid_indices]
    if not valid_titles:
        _LOG.warning("No valid titles to tag")
        return
    # Initialize Article_tag column if it doesn't exist.
    if "Article_tag" not in df.columns:
        df.insert(url_col_idx + 3, "Article_tag", "")
    # Process titles in batches with progress bar for entire workload.
    num_batches = (len(valid_titles) + batch_size - 1) // batch_size
    _LOG.info("Processing %d titles in %d batches", len(valid_titles), num_batches)
    for batch_num in tqdm(range(num_batches), desc="Tagging articles"):
        # Get batch indices.
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(valid_titles))
        batch_titles = valid_titles[start_idx:end_idx]
        batch_indices = valid_indices[start_idx:end_idx]
        _LOG.debug("Processing batch %d/%d (%d titles)", batch_num + 1, num_batches, len(batch_titles))
        # Call LLM for this batch.
        batch_tags = hllmcli.apply_llm_batch(
            prompt=_CLASSIFICATION_PROMPT,
            input_list=batch_titles,
            model=model,
        )
        # Update dataframe with batch results.
        for idx, tag in zip(batch_indices, batch_tags):
            df.at[idx, "Article_tag"] = tag.strip()
        # Update output file after each batch.
        _LOG.debug("Updating output file: %s", output_file)
        df.to_csv(output_file, index=False)
    _LOG.info("Finished tagging %d articles", len(valid_titles))


def _process_csv_file(
    input_file: str,
    output_file: str,
    *,
    tag_articles: bool = False,
    batch_size: int = 10,
    model: Optional[str] = None,
) -> None:
    """
    Process CSV file with HN URLs and add article info columns.

    :param input_file: Path to input CSV file with 'url' column
    :param output_file: Path to output CSV file
    :param tag_articles: Whether to tag articles using LLM classification
    :param batch_size: Batch size for LLM processing (used when tag_articles=True)
    :param model: Optional LLM model name to use for tagging
    """
    hdbg.dassert(os.path.exists(input_file), "Input file does not exist:", input_file)
    # Read the CSV file.
    _LOG.info("Reading input file: %s", input_file)
    df = pd.read_csv(input_file)
    # Check that url column exists.
    hdbg.dassert_in("url", df.columns, "CSV must have 'url' column")
    # Process each URL.
    _LOG.info("Processing %d URLs", len(df))
    article_titles = []
    article_urls = []
    for idx, url in enumerate(tqdm(df["url"], desc="Processing URLs")):
        _LOG.debug("Processing row %d: %s", idx, url)
        article_title, article_url = _extract_article_info(url)
        article_titles.append(article_title if article_title else "")
        article_urls.append(article_url if article_url else "")
    # Add new columns after url column.
    url_col_idx = df.columns.get_loc("url")
    df.insert(url_col_idx + 1, "Article_title", article_titles)
    df.insert(url_col_idx + 2, "Article_url", article_urls)
    # Write output file with article info.
    _LOG.info("Writing output file: %s", output_file)
    df.to_csv(output_file, index=False)
    # Optionally tag articles with LLM.
    if tag_articles:
        _LOG.info("Tagging articles using LLM")
        _tag_articles_with_llm(
            df,
            output_file,
            url_col_idx,
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
        help="Output CSV file with Article_title and Article_url columns",
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
        tag_articles=args.tag_articles,
        batch_size=args.batch_size,
        model=args.model,
    )


if __name__ == "__main__":
    _main(_parse())
