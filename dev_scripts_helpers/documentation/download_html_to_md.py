#!/usr/bin/env -S uv run

# /// script
# dependencies = ["readability-lxml", "markdownify", "requests", "beautifulsoup4"]
# ///

r"""
Download an HTML page and convert it to markdown.

Supports multiple converters:
  1. pandoc: Uses `pandoc` command (must be installed separately)
  2. bs: Uses BeautifulSoup to find main content, then markdownify to convert
  3. readability: Uses readability library for article extraction
  4. auto: Tries BeautifulSoup first, falls back to readability

Examples:

> download_html_to_md.py --input https://example.com --output output.md

> download_html_to_md.py --input https://example.com --output output.md --converter pandoc

> download_html_to_md.py --input https://example.com --output output.md --converter bs
"""

import argparse
import logging
import os
import re

import helpers.hdbg as hdbg
import helpers.hcache_simple as hcacsimp
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hselect_action as hselacti
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# #############################################################################
# Download action
# #############################################################################


@hcacsimp.simple_cache(write_through=True)
def _download_html(input_url: str, output_html_file: str) -> None:
    """
    Download HTML from URL and save to file.

    :param input_url: URL to download from
    :param output_html_file: Path to save the HTML file
    """
    # Lazy imports to run unit tests.
    import requests

    _LOG.info("Downloading HTML from '%s'...", input_url)
    response = requests.get(input_url)
    response.raise_for_status()
    hio.to_file(output_html_file, response.text)
    _LOG.info("Saved HTML to '%s'", output_html_file)


# #############################################################################
# Convert actions
# #############################################################################


def _convert_using_pandoc(
    input_html_file: str,
    output_md_file: str,
) -> str:
    """
    Convert HTML to markdown using pandoc.

    :param input_html_file: Path to input HTML file
    :param output_md_file: Path to output markdown file
    """
    _LOG.info("Converting HTML to markdown using pandoc...")
    cmd = [
        "pandoc",
        "-f html",
        "-t markdown",
        f"-i {input_html_file}",
        f"-o {output_md_file}",
    ]
    cmd = " ".join(cmd)
    hsystem.system(cmd)
    article_html = hio.from_file(output_md_file)
    return article_html


def _convert_using_bs(
    html_content: str,
) -> str:
    """
    Extract content using BeautifulSoup with common selectors.

    :param html_content: HTML content as string
    :return: Extracted HTML content
    """
    from bs4 import BeautifulSoup  # type: ignore

    soup = BeautifulSoup(html_content, "html.parser")
    content_selectors = [
        "main",
        "[data-content]",
        "[role='main']",
        "article",
        ".content",
        ".main-content",
        ".documentation",
        ".doc-content",
    ]
    for selector in content_selectors:
        element = soup.select_one(selector)
        if element:
            _LOG.info("Found content using selector: '%s'", selector)
            return str(element)
    _LOG.info("No content container found with BeautifulSoup")
    return ""


def _convert_using_readability(
    html_content: str,
) -> str:
    """
    Extract content using readability library.

    :param html_content: HTML content as string
    :return: Extracted HTML content
    """
    import readability  # type: ignore

    doc = readability.Document(html_content)
    article_html = doc.summary()
    _LOG.info("Extracted content using readability")
    return article_html


def _convert_html(
    input_html_file: str,
    output_md_file: str,
    *,
    converter: str = "auto",
) -> None:
    """
    Convert HTML to markdown using python libraries.

    :param input_html_file: Path to input HTML file
    :param output_md_file: Path to output markdown file
    :param converter:
        - If "pandoc": use pandoc
        - If "readability": use readability library only
        - If "bs": use BeautifulSoup with smart selectors only
        - If "auto": try BeautifulSoup first, fall back to readability
    """
    import markdownify  # type: ignore

    _LOG.info("Converting HTML to markdown using python libraries...")
    html_content = hio.from_file(input_html_file)
    hdbg.dassert_in(
        converter,
        ["readability", "bs", "auto"],
        "Invalid python converter specified",
    )
    if converter == "auto":
        article_html = _convert_using_bs(html_content)
        if not article_html:
            article_html = _convert_using_readability(html_content)
    elif converter == "pandoc":
        article_html = _convert_using_pandoc(input_html_file, output_md_file)
    elif converter == "bs":
        article_html = _convert_using_bs(html_content)
    elif converter == "readability":
        article_html = _convert_using_readability(html_content)
    else:
        raise ValueError(f"Unknown python converter: '{converter}'")
    markdown_content = markdownify.markdownify(
        article_html,
        heading_style="atx",
        escape_misc=False,
    )
    hio.to_file(output_md_file, markdown_content)
    _LOG.info("Saved markdown to '%s'", output_md_file)


# #############################################################################
# Cleanup action
# #############################################################################


def _remove_data_uri_images(content: str) -> str:
    """
    Remove markdown images with data URI sources.

    Removes image syntax `![...](data:...)` that embeds base64-encoded data,
    such as inline SVG icons, which are not needed in the final markdown output.

    :param content: Markdown content to clean
    :return: Markdown content with data URI images removed
    """
    # Remove image syntax with data URI sources: ![...](data:...) including
    # optional attributes.
    pattern = r"!\[[^\]]*\]\(data:[^)]*\)(?:{[^}]*})?"
    cleaned = re.sub(pattern, "", content)
    # Remove excess blank lines from image removal.
    cleaned = cleaned.strip()
    return cleaned


def _cleanup_markdown_file(md_file: str) -> None:
    """
    Clean up markdown file by removing unnecessary content.

    Removes data URI images (e.g., base64-encoded SVG icons) that are not
    needed in the final markdown output.

    :param md_file: Path to markdown file to clean
    """
    _LOG.info("Cleaning up markdown file: '%s'...", md_file)
    # Read markdown content.
    content = hio.from_file(md_file)
    # Remove data URI images.
    cleaned = _remove_data_uri_images(content)
    # Write cleaned content back.
    hio.to_file(md_file, cleaned)
    _LOG.info("Markdown file cleaned: '%s'", md_file)


def _cleanup(md_file: str) -> None:
    """
    Clean up markdown file by removing unnecessary content.

    :param md_file: Path to markdown file to clean
    """
    _cleanup_markdown_file(md_file)


# #############################################################################
# Lint action
# #############################################################################


def _lint(output_md_file: str) -> None:
    """
    Lint the markdown file using lint_txt.py.

    :param output_md_file: Path to markdown file to lint
    """
    _LOG.info("Linting markdown file: '%s'...", output_md_file)
    # Find lint_txt.py in the git tree.
    script_path = None
    script_path = hgit.find_file_in_git_tree("lint_txt.py")
    cmd = f"{script_path} --input {output_md_file} --output {output_md_file}"
    hsystem.system(cmd, abort_on_error=False)
    _LOG.info("Linting completed for '%s'", output_md_file)


# #############################################################################
# CLI
# #############################################################################

# Supported converters: pandoc, bs, readability, auto.
_CONVERTERS = ["pandoc", "bs", "readability", "auto"]

# Available and default actions.
_VALID_ACTIONS = ["download", "convert", "cleanup", "lint"]
_DEFAULT_ACTIONS = ["download", "convert", "cleanup", "lint"]


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments.

    :return: ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__,
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        required=True,
        help="Input: URL or HTML file path",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        required=True,
        help="Output markdown file path",
    )
    parser.add_argument(
        "--converter",
        type=str,
        default="auto",
        choices=_CONVERTERS,
        help="Converter to use for HTML to markdown conversion",
    )
    hselacti.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Execute the main workflow.

    :param parser: ArgumentParser instance
    """
    args = parser.parse_args()
    # Determine HTML file path.
    html_file = args.output.replace(".md", ".html")
    if html_file == args.output:
        # Add a tmp prefix before the basename.
        html_dir = os.path.dirname(args.output) or "."
        html_basename = os.path.basename(args.output)
        html_file = os.path.join(
            html_dir, f"tmp_{html_basename.replace('.md', '.html')}"
        )
    # Get selected actions.
    actions = hselacti.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    _LOG.info("Selected actions: %s", actions)
    # Execute actions.
    while actions:
        action = actions[0]
        to_execute, actions = hselacti.mark_action(action, actions)
        if to_execute:
            if action == "download":
                # If the file already exists skip downloading.
                _download_html(args.input, html_file)
            elif action == "convert":
                _convert_html(
                    html_file,
                    args.output,
                    converter=args.converter,
                )
            elif action == "cleanup":
                _cleanup(args.output)
            elif action == "lint":
                _lint(args.output)


if __name__ == "__main__":
    hdbg.init_logger(use_exec_path=True)
    parser = _parse()
    _main(parser)
