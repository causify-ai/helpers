#!/usr/bin/env -S uv run

# /// script
# dependencies = ["readability-lxml", "markdownify", "requests", "beautifulsoup4", "tqdm"]
# ///

r"""
- Download an HTML page
- Convert it to markdown with multiple converters:
  - auto: Tries BeautifulSoup first, falls back to readability
  - pandoc: Uses `pandoc` command (must be installed separately)
  - bs: Uses BeautifulSoup to find main content, then markdownify to convert
  - readability: Uses readability library for article extraction
- Summarize the content

# Usage Example

- Download a page and convert it using the default "auto" converter (tries
  BeautifulSoup first, falls back to readability):
> download_html_to_md.py --input https://example.com --output output.md

- Convert using the `pandoc` command-line tool instead:
> download_html_to_md.py --input https://example.com --output output.md --converter pandoc

- Convert using BeautifulSoup with common content selectors only:
> download_html_to_md.py --input https://example.com --output output.md --converter bs

- If --output is omitted, the page title is used to generate the filename:
> download_html_to_md.py --input https://example.com

- Enable the `summarize` action on top of the default actions to also
  generate `<output>.summary.md`:
> download_html_to_md.py --input https://example.com --output output.md -e summarize

- Show what would be done without downloading, converting, or summarizing:
> download_html_to_md.py --input https://example.com --output output.md --dry_run

- Overwrite existing output files instead of skipping:
> download_html_to_md.py --input https://example.com --output output.md --no_incremental
"""

import argparse
import logging
import os
import re

import helpers.hdbg as hdbg
import helpers.hcache_simple as hcacsimp
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hselect_action as hselacti
import helpers.hsystem as hsystem
import dev_scripts_helpers.download.download_utils as dshddut

_LOG = logging.getLogger(__name__)

# #############################################################################
# Download action
# #############################################################################


@hcacsimp.simple_cache(write_through=True)
def _download_html(
    input_url: str,
    output_html_file: str,
    *,
    dry_run: bool = False,
    no_incremental: bool = False,
) -> None:
    """
    Download HTML from URL or read from local file and save to file.

    :param input_url: URL to download from or local file path
    :param output_html_file: Path to save the HTML file
    :param dry_run: if True, show what would be done without executing
    :param no_incremental: if True, overwrite `output_html_file` even if it
        already exists
    """
    _LOG.debug(
        hprint.to_str("input_url output_html_file dry_run no_incremental")
    )
    if dry_run:
        _LOG.info("[DRY RUN] Would download HTML from '%s'", input_url)
        _LOG.info("[DRY RUN] Would save HTML to: '%s'", output_html_file)
        _LOG.debug("return: dry run, nothing written")
        return
    if os.path.exists(output_html_file) and not no_incremental:
        _LOG.warning("HTML already exists, skipping: '%s'", output_html_file)
        return
    # Lazy imports to run unit tests.
    import requests

    _LOG.info("Downloading HTML from '%s'...", input_url)
    # Check if input is a local file path.
    if os.path.isfile(input_url):
        html_content = hio.from_file(input_url)
        _LOG.info("Read local HTML file from '%s'", input_url)
    else:
        # Spoof a common desktop browser user agent to avoid sites blocking
        # bot-like requests.
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;"
                "q=0.9,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }
        _LOG.debug("Sending HTTP GET request to '%s'", input_url)
        response = requests.get(input_url, headers=headers, timeout=30)
        response.raise_for_status()
        html_content = response.text
        _LOG.debug("Received response: status_code=%s", response.status_code)
    hio.to_file(output_html_file, html_content)
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
    _LOG.debug(hprint.to_str("input_html_file output_md_file"))
    _LOG.info("Converting HTML to markdown using pandoc...")
    cmd = [
        "pandoc",
        "-f html",
        "-t markdown",
        f"-i {input_html_file}",
        f"-o {output_md_file}",
    ]
    cmd = " ".join(cmd)
    _LOG.debug("Running pandoc command: '%s'", cmd)
    hsystem.system(cmd, print_command=True)
    article_html = hio.from_file(output_md_file)
    _LOG.debug("return: len(article_html)=%d", len(article_html))
    return article_html


def _convert_using_bs(
    html_content: str,
) -> str:
    """
    Extract content using BeautifulSoup with common selectors.

    :param html_content: HTML content as string
    :return: Extracted HTML content
    """
    _LOG.debug(hprint.to_str("len(html_content)"))
    from bs4 import BeautifulSoup  # type: ignore

    soup = BeautifulSoup(html_content, "html.parser")
    # Try common content container selectors, in order of specificity.
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
            _LOG.debug("return: len(element)=%d", len(str(element)))
            return str(element)
    _LOG.info("No content container found with BeautifulSoup")
    _LOG.debug("return=''")
    return ""


def _convert_using_readability(
    html_content: str,
) -> str:
    """
    Extract content using readability library.

    :param html_content: HTML content as string
    :return: Extracted HTML content
    """
    _LOG.debug(hprint.to_str("len(html_content)"))
    import readability  # type: ignore

    doc = readability.Document(html_content)
    article_html = doc.summary()
    _LOG.info("Extracted content using readability")
    _LOG.debug("return: len(article_html)=%d", len(article_html))
    return article_html


def _convert_html(
    input_html_file: str,
    output_md_file: str,
    *,
    converter: str = "auto",
    dry_run: bool = False,
    no_incremental: bool = False,
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
    :param dry_run: if True, show what would be done without executing
    :param no_incremental: if True, overwrite `output_md_file` even if it
        already exists
    """
    _LOG.debug(
        hprint.to_str(
            "input_html_file output_md_file converter dry_run no_incremental"
        )
    )
    if dry_run:
        _LOG.info(
            "[DRY RUN] Would convert '%s' to markdown using '%s' converter",
            input_html_file,
            converter,
        )
        _LOG.info("[DRY RUN] Would save markdown to: '%s'", output_md_file)
        _LOG.debug("return: dry run, nothing written")
        return
    if os.path.exists(output_md_file) and not no_incremental:
        _LOG.warning("Markdown already exists, skipping: '%s'", output_md_file)
        return
    import markdownify  # type: ignore

    _LOG.info("Converting HTML to markdown using python libraries...")
    html_content = hio.from_file(input_html_file)
    hdbg.dassert_in(
        converter,
        ["readability", "bs", "auto"],
        "Invalid python converter specified",
    )
    # Dispatch to the selected converter.
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
    _LOG.debug("len(article_html)=%d", len(article_html))
    markdown_content = markdownify.markdownify(
        article_html,
        heading_style="atx",
        escape_misc=False,
    )
    _LOG.debug("len(markdown_content)=%d", len(markdown_content))
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
    _LOG.debug(hprint.to_str("len(content)"))
    # Remove image syntax with data URI sources: ![...](data:...) including
    # optional attributes.
    pattern = r"!\[[^\]]*\]\(data:[^)]*\)(?:{[^}]*})?"
    cleaned = re.sub(pattern, "", content)
    # Remove excess blank lines from image removal.
    cleaned = cleaned.strip()
    _LOG.debug("return: len(cleaned)=%d", len(cleaned))
    return cleaned


def _cleanup_markdown_file(md_file: str) -> None:
    """
    Clean up markdown file by removing unnecessary content.

    Removes data URI images (e.g., base64-encoded SVG icons) that are not
    needed in the final markdown output.

    :param md_file: Path to markdown file to clean
    """
    _LOG.debug(hprint.to_str("md_file"))
    _LOG.info("Cleaning up markdown file: '%s'...", md_file)
    # Read markdown content.
    content = hio.from_file(md_file)
    # Remove data URI images.
    cleaned = _remove_data_uri_images(content)
    _LOG.debug("len(content)=%d len(cleaned)=%d", len(content), len(cleaned))
    # Write cleaned content back.
    hio.to_file(md_file, cleaned)
    _LOG.info("Markdown file cleaned: '%s'", md_file)


def _cleanup(md_file: str, *, dry_run: bool = False) -> None:
    """
    Clean up markdown file by removing unnecessary content.

    :param md_file: Path to markdown file to clean
    :param dry_run: if True, show what would be done without executing
    """
    _LOG.debug(hprint.to_str("md_file dry_run"))
    if dry_run:
        _LOG.info("[DRY RUN] Would clean up markdown file: '%s'", md_file)
        _LOG.debug("return: dry run, nothing written")
        return
    _cleanup_markdown_file(md_file)


# #############################################################################
# Lint action
# #############################################################################


# TODO(gp): Consider using the library and a faster lib to lint.
def _lint(output_md_file: str, *, dry_run: bool = False) -> None:
    """
    Lint the markdown file using lint_text.py.

    :param output_md_file: Path to markdown file to lint
    :param dry_run: if True, show what would be done without executing
    """
    _LOG.debug(hprint.to_str("output_md_file dry_run"))
    if dry_run:
        _LOG.info("[DRY RUN] Would lint markdown file: '%s'", output_md_file)
        _LOG.debug("return: dry run, nothing written")
        return
    _LOG.info("Linting markdown file: '%s'...", output_md_file)
    # Find lint_text.py in the git tree.
    script_path = None
    script_path = hgit.find_file_in_git_tree("lint_text.py")
    _LOG.debug("script_path='%s'", script_path)
    cmd = f"{script_path} --input {output_md_file} --output {output_md_file}"
    _LOG.debug("Running command: '%s'", cmd)
    hsystem.system(cmd, abort_on_error=False, print_command=True)
    _LOG.info("Linting completed for '%s'", output_md_file)


# #############################################################################
# Summarize action
# #############################################################################


def _summarize(
    output_md_file: str,
    *,
    dry_run: bool = False,
    no_incremental: bool = False,
) -> None:
    """
    Summarize the markdown content using an LLM.

    :param output_md_file: Path to markdown file to summarize
    :param dry_run: if True, show what would be done without executing
    :param no_incremental: if True, overwrite the summary even if it
        already exists
    """
    _LOG.debug(hprint.to_str("output_md_file dry_run no_incremental"))
    summary_file = f"{output_md_file}.summary.md"
    if not dry_run and os.path.exists(summary_file) and not no_incremental:
        _LOG.warning("Summary already exists, skipping: '%s'", summary_file)
        return
    _LOG.info("Summarizing markdown file: '%s'...", output_md_file)
    dshddut.summarize_text_with_llm(
        output_md_file,
        summary_file,
        dshddut.ARTICLE_SUMMARY_PROMPT,
        dry_run=dry_run,
    )
    if not dry_run:
        _LOG.info("Summary saved to: '%s'", summary_file)


# #############################################################################
# Output filename
# #############################################################################


def _get_output_md_file(input_arg: str) -> str:
    """
    Derive an output markdown filename from the page title.

    Fetches the page title for the given URL and sanitizes it for use as a
    filename. Falls back to the input's basename if the title can't be
    fetched (e.g., local file input, request failure).

    :param input_arg: URL or local file path used as input
    :return: Output markdown filename, e.g. `The_Page_Title.md`
    """
    _LOG.debug(hprint.to_str("input_arg"))
    title = dshddut.fetch_article_title(input_arg)
    if not title:
        _LOG.warning(
            "Could not extract title from '%s', using input name instead",
            input_arg,
        )
        title = os.path.splitext(os.path.basename(input_arg))[0]
    sanitized_title = dshddut.sanitize_title_for_filename(title)
    output_md_file = f"{sanitized_title}.md"
    _LOG.debug(hprint.to_str("output_md_file"))
    return output_md_file


# #############################################################################
# CLI
# #############################################################################

# Supported converters: pandoc, bs, readability, auto.
_CONVERTERS = ["pandoc", "bs", "readability", "auto"]

# Available and default actions.
_VALID_ACTIONS = ["download", "convert", "cleanup", "lint", "summarize"]
_DEFAULT_ACTIONS = ["download", "convert", "cleanup", "lint"]


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments.

    :return: ArgumentParser instance
    """
    _LOG.debug("Building CLI argument parser")
    parser = argparse.ArgumentParser(
        formatter_class=hparser.CustomHelpFormatter,
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
        default=None,
        help=(
            "Output markdown file path. If not specified, the page title "
            "is used to generate the filename"
        ),
    )
    parser.add_argument(
        "--converter",
        type=str,
        default="auto",
        choices=_CONVERTERS,
        help="Converter to use for HTML to markdown conversion",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Dry run mode: show what would be done without actually executing actions",
    )
    parser.add_argument(
        "--no_incremental",
        action="store_true",
        help="Overwrite existing output files instead of skipping",
    )
    hselacti.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    _LOG.debug("return: parser built")
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Execute the main workflow.

    :param parser: ArgumentParser instance
    """
    _LOG.debug("Starting main workflow")
    args = parser.parse_args()
    _LOG.debug(hprint.to_str("args"))
    # Determine the output markdown file path.
    if args.output:
        output_md_file = args.output
    else:
        output_md_file = _get_output_md_file(args.input)
        _LOG.info(
            "No --output specified, using derived filename: '%s'",
            output_md_file,
        )
    _LOG.debug(hprint.to_str("output_md_file"))
    # Determine HTML file path.
    html_file = output_md_file.replace(".md", ".html")
    # If the output path doesn't end in .md, replace() above is a no-op, so
    # guard against the HTML and markdown files colliding.
    if html_file == output_md_file:
        # Add a tmp prefix before the basename.
        html_dir = os.path.dirname(output_md_file) or "."
        html_basename = os.path.basename(output_md_file)
        html_file = os.path.join(
            html_dir, f"tmp_{html_basename.replace('.md', '.html')}"
        )
    _LOG.debug(hprint.to_str("html_file"))
    # Get selected actions.
    actions = hselacti.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    _LOG.info(
        "\n%s",
        hselacti.actions_to_string(actions, _VALID_ACTIONS, add_frame=True),
    )
    if args.dry_run:
        _LOG.info("DRY RUN MODE: showing what would be done without executing")
    # Execute actions.
    while actions:
        action = actions[0]
        to_execute, actions = hselacti.mark_action(action, actions)
        if not to_execute:
            continue
        if action == "download":
            # If the file already exists skip downloading.
            _download_html(
                args.input,
                html_file,
                dry_run=args.dry_run,
                no_incremental=args.no_incremental,
            )
        elif action == "convert":
            _convert_html(
                html_file,
                output_md_file,
                converter=args.converter,
                dry_run=args.dry_run,
                no_incremental=args.no_incremental,
            )
        elif action == "cleanup":
            _cleanup(output_md_file, dry_run=args.dry_run)
        elif action == "lint":
            _lint(output_md_file, dry_run=args.dry_run)
        elif action == "summarize":
            _summarize(
                output_md_file,
                dry_run=args.dry_run,
                no_incremental=args.no_incremental,
            )
        else:
            raise ValueError(f"Invalid action='{action}'")
    hdbg.dassert_eq(
        len(actions), 0, "There are unprocessed actions: %s", str(actions)
    )


if __name__ == "__main__":
    hdbg.init_logger(use_exec_path=True)
    parser = _parse()
    _main(parser)
