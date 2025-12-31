#!/usr/bin/env python

"""
Extract article title and URL from Hacker News discussion pages.

This script processes Hacker News item URLs and extracts:
- The submission title (discussion title)
- The original article URL that the submission links to

Examples:
> ./extract_hn_article.py --hn_url "https://news.ycombinator.com/item?id=45619537"
Claude Skills are awesome, maybe a bigger deal than MCP
https://simonwillison.net/2025/Oct/16/claude-skills/

> ./extract_hn_article.py --input_file input.csv --output_file output.csv

Import as:

import dev_scripts_helpers.scraping_script.extract_hn_article as dsscehar
"""

import argparse
import logging
from typing import Optional, Tuple

import pandas as pd
import requests
from bs4 import BeautifulSoup

import helpers.hcsv as hcsv
import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


# #############################################################################


def _is_hackernews_url(url: str) -> bool:
    """
    Check if URL is a Hacker News item URL.

    :param url: URL to check
    :return: True if URL is a HN item URL
    """
    return "news.ycombinator.com/item?id=" in url


def _extract_article_info(hn_url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract article title and URL from a Hacker News discussion page.

    :param hn_url: Hacker News item URL
    :return: Tuple of (article_title, article_url)
    """
    if not _is_hackernews_url(hn_url):
        _LOG.warning("Not a Hacker News URL: %s", hn_url)
        return None, None
    try:
        # Fetch the HN page.
        _LOG.debug("Fetching URL: %s", hn_url)
        response = requests.get(hn_url, timeout=10)
        response.raise_for_status()
        # Parse the HTML.
        soup = BeautifulSoup(response.text, "html.parser")
        # Find the submission title - it's in a span with class "titleline".
        titleline = soup.find("span", class_="titleline")
        if not titleline:
            _LOG.warning("Could not find titleline in: %s", hn_url)
            return None, None
        # The link is inside the titleline span.
        link = titleline.find("a")
        if not link:
            _LOG.warning("Could not find link in titleline: %s", hn_url)
            return None, None
        # Extract title and URL.
        article_title = link.get_text().strip()
        article_url = link.get("href")
        _LOG.debug("Extracted title: %s", article_title)
        _LOG.debug("Extracted URL: %s", article_url)
        return article_title, article_url
    except requests.RequestException as e:
        _LOG.warning("Request failed for %s: %s", hn_url, e)
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
    hdbg.dassert(hio.file_exists(input_file), "Input file does not exist:", input_file)
    # Read the CSV file.
    _LOG.info("Reading input file: %s", input_file)
    df = pd.read_csv(input_file)
    # Check that url column exists.
    hdbg.dassert_in("url", df.columns, "CSV must have 'url' column")
    # Process each URL.
    _LOG.info("Processing %d URLs", len(df))
    article_titles = []
    article_urls = []
    for idx, url in enumerate(df["url"]):
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
    hcsv.to_csv(df, output_file)
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
