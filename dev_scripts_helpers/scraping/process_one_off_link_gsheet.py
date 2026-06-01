#!/usr/bin/env -S uv run

# /// script
# dependencies = [
#   "pandas",
#   "pyyaml",
# ]
# ///

"""
Process links and articles from Google Sheets with topic tag replacement.

This script performs a one-off data processing pipeline:
1. download_gsheet_links: Download data from Google Sheets to CSV
2. replace_article_tags: Replace old topic names with simplified names
3. upload_gsheet_links: Upload the processed CSV back to Google Sheets

Example usage:

# Run complete pipeline
> process_one_off_link_gsheet.py \
    --url "https://docs.google.com/spreadsheets/d/1i6Z7v2..."

Import as:

import dev_scripts_helpers.scraping.process_one_off_link_gsheet as dsolg
"""

import argparse
import datetime
import logging

import pandas as pd

import helpers.hdbg as hdbg
import helpers.hlogging as hloggin
import helpers.hparser as hparser
import dev_scripts_helpers.scraping.link_gsheet_utils as dslgu

_LOG = logging.getLogger(__name__)

HN_CSV_FILE = "hn_gsheet.csv"

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


def _download_from_gsheet(url: str) -> str:
    """
    Download data from Google Sheets and save to a temporary CSV file.

    :param url: URL of the Google Sheets document
    :return: Path to the saved CSV file
    """
    output_file = dslgu.get_tmp_file_path(HN_CSV_FILE, "process_one_off_link_gsheet")
    dslgu.download_from_gsheet(url, output_file)
    return output_file


def _replace_article_tags(csv_file: str) -> str:
    """
    Replace old topic names with new simplified topic names in Article_tag column.

    Updates the CSV file with renamed topics using the old_topic_to_new_topic mapping.

    :param csv_file: Path to the CSV file to process
    :return: Path to the updated CSV file
    """
    hdbg.dassert_path_exists(csv_file, "CSV file not found")
    _LOG.info("Loading CSV '%s' to replace topic names", csv_file)
    df = pd.read_csv(csv_file)
    hdbg.dassert_isinstance(df, pd.DataFrame, "Failed to load CSV as DataFrame")
    hdbg.dassert_in("Article_tag", df.columns, "CSV must have 'Article_tag' column")
    _LOG.info(
        "Loaded %d rows and %d columns from '%s'",
        len(df),
        len(df.columns),
        csv_file,
    )
    # Replace old topic names with new simplified names.
    replacements_made = 0
    for idx, row in df.iterrows():
        tag_val = row["Article_tag"]
        old_tag = ""
        if pd.notna(tag_val):
            old_tag = str(tag_val).strip()
        if old_tag in old_topic_to_new_topic:
            new_tag = old_topic_to_new_topic[old_tag]
            df.at[idx, "Article_tag"] = new_tag
            replacements_made += 1
            _LOG.debug("Replaced '%s' with '%s'", old_tag, new_tag)
    _LOG.info("Made %d topic name replacements", replacements_made)
    df.to_csv(csv_file, index=False)
    _LOG.info(
        "Wrote %d rows with %d columns to '%s'",
        len(df),
        len(df.columns),
        csv_file,
    )
    return csv_file


def _upload_to_gsheet(url: str, csv_file: str) -> None:
    """
    Upload processed CSV data to Google Sheets.

    :param url: URL of the Google Sheets document
    :param csv_file: Path to the CSV file to upload
    """
    hdbg.dassert_path_exists(csv_file, "CSV file not found")
    tabname = "process_one_off_link_gsheet." + datetime.datetime.now().strftime(
        "%Y-%m-%d"
    )
    dslgu.upload_to_gsheet(url, csv_file, tabname)


def _parse() -> argparse.ArgumentParser:
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
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    hloggin.shutup_chatty_modules(verbosity=logging.ERROR)
    _LOG.info("Starting one-off link gsheet processing pipeline")
    # Phase 1: Download from Google Sheets.
    _LOG.info("Phase 1: Downloading data from Google Sheets")
    csv_file = _download_from_gsheet(args.url)
    _LOG.info("Downloaded data to: %s", csv_file)
    # Phase 2: Replace article tags.
    _LOG.info("Phase 2: Replacing article tags")
    csv_file = _replace_article_tags(csv_file)
    _LOG.info("Replaced tags in: %s", csv_file)
    # Phase 3: Upload to Google Sheets.
    _LOG.info("Phase 3: Uploading processed data to Google Sheets")
    _upload_to_gsheet(args.url, csv_file)
    _LOG.info("Pipeline completed successfully")


if __name__ == "__main__":
    _main(_parse())
