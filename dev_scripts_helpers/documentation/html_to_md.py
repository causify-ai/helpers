#!/usr/bin/env -S uv run

# /// script
# dependencies = ["readability-lxml", "markdownify", "requests"]
# ///

r"""
Download an HTML page and convert it to markdown.

Supports two conversion engines:
  1. pandoc: Uses `pandoc` command (must be installed separately)
  2. python: Uses `readability-lxml` and `markdownify` libraries

Examples:

> html_to_md.py --input https://example.com --output output.md

> html_to_md.py --input https://example.com --output output.md --engine pandoc

> html_to_md.py --input https://example.com --output output.md --engine python
"""

import argparse
import logging
import os
import re

import requests
import readability  # type: ignore
import markdownify  # type: ignore

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hselect_action as hselect_action
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

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
    doc = readability.Document(html_content)
    article_html = doc.summary()
    # Convert to markdown with proper header handling.
    markdown_content = markdownify.markdownify(
        article_html,
        heading_style="atx",
        escape_misc=False,
    )
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
    if engine == "pandoc":
        _convert_using_pandoc(input_html_file, output_md_file)
    elif engine == "python":
        _convert_using_python(input_html_file, output_md_file)
    else:
        raise ValueError(f"Invalid engine '{engine}'")


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
    # Remove image syntax with data URI sources: ![...](data:...)
    # The pattern captures the entire markdown image including optional attributes.
    pattern = r"!\[[^\]]*\]\(data:[^)]*\)(?:{[^}]*})?"
    cleaned = re.sub(pattern, "", content)
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

# Supported conversion engines.
_ENGINES = ["pandoc", "python"]

# Available and default actions.
_VALID_ACTIONS = ["download", "convert", "cleanup", "lint"]
_DEFAULT_ACTIONS = ["download", "convert"]


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments.

    :return: ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Input: URL or HTML file path",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output markdown file path",
    )
    parser.add_argument(
        "--engine",
        type=str,
        default="python",
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
    # Determine HTML file path.
    html_file = args.output.replace(".md", ".html")
    if html_file == args.output:
        # Add a tmp prefix before the basename.
        html_dir = os.path.dirname(args.output) or "."
        html_basename = os.path.basename(args.output)
        html_file = os.path.join(html_dir, f"tmp_{html_basename.replace('.md', '.html')}")
    # Get selected actions.
    actions = hselect_action.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    _LOG.info("Selected actions: %s", actions)
    # Execute actions.
    while actions:
        action = actions[0]
        to_execute, actions = hselect_action.mark_action(action, actions)
        if to_execute:
            if action == "download":
                # If the file already exists skip downloading.
                if os.path.exists(html_file):
                    _LOG.info("HTML file already exists: '%s', skipping download", html_file)
                else:
                    _download_html(args.input, html_file)
            elif action == "convert":
                _convert_html(html_file, args.output, args.engine)
            elif action == "cleanup":
                _cleanup(args.output)
            elif action == "lint":
                _lint(args.output)


if __name__ == "__main__":
    hdbg.init_logger(use_exec_path=True)
    parser = _parse()
    _main(parser)
