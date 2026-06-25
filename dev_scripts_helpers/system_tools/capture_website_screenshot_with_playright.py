#!/usr/bin/env -S uv run

# /// script
# dependencies = ["playwright"]
# ///

"""
Take a screenshot of a website using Playwright.

> website_screenshot.py --url https://example.com --output screenshot.png
"""

import argparse
import logging
import os

import helpers.hdbg as hdbg
import helpers.hparser as hparser
from playwright.sync_api import sync_playwright

_LOG = logging.getLogger(__name__)

# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--url",
        action="store",
        type=str,
        required=True,
        help="URL of the website to screenshot",
    )
    parser.add_argument(
        "--output",
        action="store",
        type=str,
        required=True,
        help="Path to save the screenshot PNG file",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Ensure the URL is a string.
    url: str = args.url
    output_path: str = args.output
    # Validate that the output path ends with .png.
    hdbg.dassert(
        output_path.endswith(".png"),
        "Output file '%s' must have a .png extension",
        output_path,
    )
    # Create output directory if it doesn't exist.
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    _LOG.info("Taking screenshot of '%s' -> '%s'", url, output_path)
    # Launch browser and take screenshot.
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        page.screenshot(path=output_path, full_page=True)
        browser.close()
    _LOG.info("Screenshot saved to '%s'", output_path)


if __name__ == "__main__":
    _main(_parse())
