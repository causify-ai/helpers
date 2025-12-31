#!/usr/bin/env python

"""
Extract article title and URL from Hacker News submissions using the HN API.

This script processes Hacker News item URLs and uses the Firebase API to extract:
- The submission title
- The original article URL that the submission links to

The script uses the official HN API: https://hacker-news.firebaseio.com/v0/

Examples:
> ./extract_hn_article.py --hn_url "https://news.ycombinator.com/item?id=45148180"
A Software Development Methodology for Disciplined LLM Collaboration
https://github.com/...

> ./extract_hn_article.py --input_file input.csv --output_file output.csv

Import as:

import dev_scripts_helpers.scraping_script.extract_hn_article as dsscehar
"""

import argparse
import logging
import os
import re
from typing import Optional, Tuple

import pandas as pd
import requests
from tqdm import tqdm

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hcache_simple as hcacsimp

_LOG = logging.getLogger(__name__)


# #############################################################################


def _is_hackernews_url(url: str) -> bool:
    """
    Check if URL is a Hacker News item URL.

    :param url: URL to check
    :return: True if URL is a HN item URL
    """
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


def _process_single_url(hn_url: str) -> None:
    """
    Process a single HN URL and print results.

    :param hn_url: Hacker News URL to process
    """
    article_title, article_url = _extract_article_info(hn_url)
    if article_title and article_url:
        _LOG.info("Title: %s", article_title)
        _LOG.info("URL: %s", article_url)
    else:
        _LOG.warning("Could not extract article info from: %s", hn_url)


def _process_csv_file(input_file: str, output_file: str) -> None:
    """
    Process CSV file with HN URLs and add article info columns.

    :param input_file: Path to input CSV file with 'url' column
    :param output_file: Path to output CSV file
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
    # Write output file.
    _LOG.info("Writing output file: %s", output_file)
    df.to_csv(output_file, index=False)
    _LOG.info("Done processing %d URLs", len(df))


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # Single URL mode.
    parser.add_argument(
        "--hn_url",
        action="store",
        help="Single Hacker News URL to process",
    )
    # Batch CSV mode.
    parser.add_argument(
        "--input_file",
        action="store",
        help="Input CSV file with 'url' column",
    )
    parser.add_argument(
        "--output_file",
        action="store",
        help="Output CSV file with Article_title and Article_url columns",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Validate arguments.
    if args.hn_url:
        # Single URL mode.
        hdbg.dassert_is(
            args.input_file,
            None,
            "Cannot specify both --hn_url and --input_file",
        )
        hdbg.dassert_is(
            args.output_file,
            None,
            "Cannot specify both --hn_url and --output_file",
        )
        _process_single_url(args.hn_url)
    elif args.input_file:
        # Batch CSV mode.
        hdbg.dassert_is_not(
            args.output_file,
            None,
            "Must specify --output_file when using --input_file",
        )
        _process_csv_file(args.input_file, args.output_file)
    else:
        parser.print_help()
        hdbg.dfatal("Must specify either --hn_url or --input_file")


if __name__ == "__main__":
    _main(_parse())
