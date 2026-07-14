#!/usr/bin/env -S uv run

# /// script
# dependencies = ["readability-lxml", "markdownify", "requests"]
# ///

# TODO(ai_gp): Rename this file html_to_md.py

r"""
Download an HTML page and convert it to markdown.

Supports two conversion engines:
  1. pandoc: Uses `pandoc` command (must be installed separately)
  2. python: Uses `readability-lxml` and `markdownify` libraries

Examples:

> html_to_markdown.py --input https://example.com --output output.md

> html_to_markdown.py --input https://example.com --output output.md --engine pandoc

> html_to_markdown.py --input https://example.com --output output.md --engine python
"""

import argparse
import logging
import os
import requests

# TODO(ai_gp): Use import instead of from import
from readability import Document
from markdownify import markdownify as md

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hselect_action as hselect_action
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# #############################################################################
# Constants
# #############################################################################

# Supported conversion engines.
# TODO(ai_gp): Inline this vars
_ENGINE_PANDOC = "pandoc"
_ENGINE_PYTHON = "python"

_ENGINES = [_ENGINE_PANDOC, _ENGINE_PYTHON]

# Available and default actions.
_VALID_ACTIONS = ["download", "convert", "cleanup"]
_DEFAULT_ACTIONS = ["download", "convert"]

# #############################################################################
# Download action
# #############################################################################


def _download_html(input_url: str, output_html_file: str) -> None:
    """
    Download HTML from URL and save to file.

    :param input_url: URL to download from
    :param output_html_file: Path to save the HTML file
    """
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
) -> None:
    """
    Convert HTML to markdown using pandoc.

    :param input_html_file: Path to input HTML file
    :param output_md_file: Path to output markdown file
    """
    _LOG.info("Converting HTML to markdown using pandoc...")
    cmd = [
        "pandoc",
        f"-f html",
        f"-t markdown",
        f"-i {input_html_file}",
        f"-o {output_md_file}",
    ]
    cmd = " ".join(cmd)
    hsystem.system(cmd)
    _LOG.info("Saved markdown to '%s'", output_md_file)


def _convert_using_python(
    input_html_file: str,
    output_md_file: str,
) -> None:
    """
    Convert HTML to markdown using readability + markdownify.

    :param input_html_file: Path to input HTML file
    :param output_md_file: Path to output markdown file
    """
    _LOG.info("Converting HTML to markdown using python libraries...")
    # Read HTML file.
    html_content = hio.from_file(input_html_file)
    # Extract article content.
    doc = Document(html_content)
    article_html = doc.summary()
    # Convert to markdown.
    markdown_content = md(article_html)
    # Save markdown file.
    hio.to_file(output_md_file, markdown_content)
    _LOG.info("Saved markdown to '%s'", output_md_file)


def _convert_html(
    input_html_file: str,
    output_md_file: str,
    engine: str,
) -> None:
    """
    Convert HTML to markdown using the specified engine.

    :param input_html_file: Path to input HTML file
    :param output_md_file: Path to output markdown file
    :param engine: Conversion engine to use ('pandoc' or 'python')
    """
    hdbg.dassert_in(engine, _ENGINES, "Invalid engine specified")
    if engine == _ENGINE_PANDOC:
        _convert_using_pandoc(input_html_file, output_md_file)
    elif engine == _ENGINE_PYTHON:
        _convert_using_python(input_html_file, output_md_file)


# #############################################################################
# Cleanup action
# #############################################################################


def _cleanup(html_file: str) -> None:
    """
    Clean up temporary HTML file.

    :param html_file: Path to HTML file to remove
    """
    _LOG.info("Cleaning up markdown file...")


# #############################################################################
# CLI
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments.

    :return: ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
    )
    # TODO(ai_gp): Make it mandatory
    parser.add_argument(
        "--input",
        type=str,
        default="",
        help="Input: URL or HTML file path",
    )
    # TODO(ai_gp): Make it mandatory
    parser.add_argument(
        "--output",
        type=str,
        default="",
        help="Output markdown file path",
    )
    parser.add_argument(
        "--engine",
        type=str,
        default=_ENGINE_PYTHON,
        choices=_ENGINES,
        help="Conversion engine to use",
    )
    hselect_action.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Execute the main workflow.

    :param parser: ArgumentParser instance
    """
    args = parser.parse_args()
    hdbg.dassert_ne(
        args.input,
        "",
        "Input URL or file path must be specified with --input",
    )
    hdbg.dassert_ne(
        args.output,
        "",
        "Output file path must be specified with --output",
    )
    # Determine HTML file path.
    html_file = args.output.replace(".md", ".html")
    if html_file == args.output:
        # TODO(ai_gp): Add a tmp before the basename.
        html_file = args.output + ".html"
    # Get selected actions.
    actions = hselect_action.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    # TODO(ai_gp): Print actions.
    # Execute actions.
    while actions:
        action = actions[0]
        to_execute, actions = hselect_action.mark_action(action, actions)
        if to_execute:
            if action == "download":
                # TODO(ai_gp): If the file already exists skip downloading.
                if args.input.startswith("http://") or args.input.startswith(
                    "https://"
                ):
                    _download_html(args.input, html_file)
                else:
                    # Input is a file path, use it directly.
                    _LOG.info("Using existing HTML file: '%s'", args.input)
                    html_file = args.input
            elif action == "convert":
                _convert_html(html_file, args.output, args.engine)
            elif action == "cleanup":
                _cleanup(html_file)


if __name__ == "__main__":
    hdbg.init_logger(use_exec_path=True)
    parser = _parse()
    _main(parser)
