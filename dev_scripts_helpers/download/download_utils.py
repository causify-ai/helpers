"""
Shared utilities for downloading and summarizing article content.

Provides common functionality for fetching article titles, sanitizing
titles for use in filenames, and summarizing text via an LLM.

Import as:

import dev_scripts_helpers.download.download_utils as dsdlut
"""

import logging
import re
from typing import Optional

import bs4
import requests

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hcache_simple as hcacsimp
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


@hcacsimp.simple_cache(cache_type="json", write_through=True)
def fetch_article_title(url: str) -> Optional[str]:
    """
    Fetch a web page and extract the contents of its `<title>` tag.

    :param url: Article URL
    :return: Page title, or None if it can't be fetched or has no
        `<title>` tag
    """
    _LOG.debug(hprint.func_signature_to_str())
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
    try:
        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        _LOG.warning("Failed to fetch '%s': %s", url, e)
        return None
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    if not soup.title or not soup.title.string:
        _LOG.warning("No <title> tag found in '%s'", url)
        return None
    # BeautifulSoup already unescapes HTML entities; just collapse internal
    # whitespace/newlines.
    title = soup.title.string.strip()
    title = re.sub(r"\s+", " ", title)
    _LOG.debug(hprint.to_str("title"))
    return title


def sanitize_title_for_filename(title: str) -> str:
    """
    Sanitize a title for use in a filename.

    Replaces non-alphanumeric chars with underscores, collapses repeated
    underscores, and strips leading/trailing underscores.

    :param title: Title string
    :return: Sanitized filename slug
    """
    _LOG.debug(hprint.func_signature_to_str())
    # Replace any non-alphanumeric character (except underscore) with underscore.
    sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", title)
    # Collapse consecutive underscores into a single underscore.
    sanitized = re.sub(r"_+", "_", sanitized)
    # Remove leading and trailing underscores for cleaner filenames.
    sanitized = sanitized.strip("_")
    _LOG.debug(hprint.to_str("sanitized"))
    return sanitized


# Default model for LLM-based summarization. This is a direct model name
# passed to `llm` (not routed through OpenRouter, which uses an
# "openrouter/<provider>/<model>" prefix, e.g.
# "openrouter/anthropic/claude-haiku-4.5"; see `llm_cli.py`).
_SUMMARY_MODEL = "gpt-4o-mini"

# Shared prompt for summarizing article content into 5 bullet points; reused
# by `download_hn_article_to_md.py`, `download_html_to_md.py`, and
# `download_academic_paper_to_md.py` to avoid repeating the same prompt text.
ARTICLE_SUMMARY_PROMPT = hprint.dedent(
    """
    - Summarize the main article in 5 bullet points
    - Format as plain text without markdown following the conventions in:
      - @.claude/skills/markdown.rules.txt
      - @.claude/skills/text.rules.txt
    """
)


def summarize_text_with_llm(
    input_file: str,
    output_file: str,
    prompt: str,
    model: str = _SUMMARY_MODEL,
    *,
    dry_run: bool = False,
) -> None:
    """
    Summarize text using llm_cli.py and lint the output.

    :param input_file: Path to input text file to summarize
    :param output_file: Path to save the summary
    :param prompt: System prompt to guide the summarization
    :param model: LLM model to use for summarization
    :param dry_run: If True, show what would be done without executing
    """
    _LOG.debug(hprint.to_str("input_file output_file model"))
    _LOG.info("Summarizing: %s", input_file)
    if dry_run:
        _LOG.info(
            "[DRY RUN] Would summarize: %s -> %s (model: %s)",
            input_file,
            output_file,
            model,
        )
        return
    # Save prompt to a temporary file.
    prompt_file = "tmp.summarize_text_with_llm.prompt.txt"
    hio.to_file(prompt_file, prompt)
    _LOG.debug("Saved prompt to: %s", prompt_file)
    # Build command to call llm_cli.py with the given prompt file.
    llm_cli_path = "dev_scripts_helpers/llms/llm_cli.py"
    cmd_parts = [
        llm_cli_path,
        f"--input={input_file}",
        f"--output={output_file}",
        f"--pf={prompt_file}",
        f"--model={model}",
        "--lint",
    ]
    cmd = " ".join(cmd_parts)
    _LOG.debug("Running command: %s", cmd)
    hsystem.system(cmd)
    _LOG.info("Summary saved to: %s", output_file)


# #############################################################################
# Article download dispatch
# #############################################################################


def is_arxiv_url(url: str) -> bool:
    """
    Check if a URL points to an arXiv paper.

    :param url: Article URL
    :return: True if the URL is an arXiv link
    """
    _LOG.debug(hprint.to_str("url"))
    result = "arxiv.org" in url.lower()
    _LOG.debug(hprint.to_str("result"))
    return result


def download_website_article(url: str, output_file: str) -> None:
    """
    Download a normal website article and convert it to text via
    `download_html_to_md.py`.

    :param url: Article URL
    :param output_file: Path to save the article text to
    """
    _LOG.debug(hprint.to_str("url output_file"))
    script = hgit.find_file_in_git_tree("download_html_to_md.py")
    cmd = f'{script} --input "{url}" --output "{output_file}"'
    hsystem.system(cmd)
    hdbg.dassert_file_exists(output_file)


def download_arxiv_article(url: str, output_file: str) -> None:
    """
    Download an arXiv paper via `download_academic_paper_to_md.py` and use
    its converted markdown as the article text.

    The PDF and markdown are saved next to `output_file` (same basename,
    `.pdf`/`.md` extensions) and the markdown content is written to
    `output_file` so it can be consumed like any other article.

    :param url: arXiv URL
    :param output_file: Path to save the extracted article text to
    """
    _LOG.debug(hprint.to_str("url output_file"))
    # Base path (no extension) shared by the generated .pdf/.md files.
    base_path = re.sub(r"\.txt$", "", output_file)
    script = hgit.find_file_in_git_tree("download_academic_paper_to_md.py")
    # Only download + convert here: skip the script's own summarize action
    # since callers summarize the resulting article text themselves.
    cmd = (
        f'{script} --input "{url}" --output "{base_path}" '
        f'--no_incremental -sa summarize'
    )
    hsystem.system(cmd)
    pdf_output_file = f"{base_path}.pdf"
    md_output_file = f"{base_path}.md"
    hdbg.dassert_file_exists(pdf_output_file)
    hdbg.dassert_file_exists(md_output_file)
    _LOG.info("Saved PDF to: %s", pdf_output_file)
    # Use the converted markdown as the article text for downstream
    # summarization.
    text = hio.from_file(md_output_file)
    hio.to_file(output_file, text)


def download_article(url: str, output_file: str) -> None:
    """
    Download an article, dispatching to the arXiv or generic downloader.

    :param url: Article URL
    :param output_file: Path to save the article text to
    """
    _LOG.debug(hprint.to_str("url output_file"))
    if is_arxiv_url(url):
        download_arxiv_article(url, output_file)
    else:
        download_website_article(url, output_file)
