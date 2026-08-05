"""
Shared utilities for downloading and summarizing article content.

Provides common functionality for fetching article titles, sanitizing
titles for use in filenames, and summarizing text via an LLM.

Import as:

import dev_scripts_helpers.download.download_utils as dsdlut
"""

import html
import logging
import re
from typing import Any, Dict, List, Optional

import bs4
import requests
from tqdm import tqdm

import helpers.hdbg as hdbg
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


# TODO(ai_gp): Use _SUMMARY_MODEL = "gpt-4o-mini" as default value for model
def summarize_text_with_llm(
    input_file: str,
    output_file: str,
    prompt: str,
    model: str,
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
    # TODO(ai_gp): Use hgit.find_in_repo
    script = "dev_scripts_helpers/download/download_html_to_md.py"
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
    # TODO(ai_gp): Use hgit.find_in_repo
    script = "dev_scripts_helpers/download/download_academic_paper_to_md.py"
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


# #############################################################################
# Hacker News comments
# #############################################################################

# TODO(ai_gp): Move all the functions for hackernews that are used only by
# ./dev_scripts_helpers/download/download_hn_article_to_md.py to that file
# and make them private

@hcacsimp.simple_cache(cache_type="json", write_through=True)
def fetch_hn_item(item_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a Hacker News item from the API.

    :param item_id: HN item ID
    :return: Item data dict or None if fetch fails
    """
    _LOG.debug(hprint.func_signature_to_str())
    # Query the official HN API for the item.
    api_url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
    _LOG.debug("Fetching HN item: %s", api_url)
    response = requests.get(api_url, timeout=10)
    response.raise_for_status()
    data = response.json()
    if data:
        result = data
    else:
        _LOG.warning("No data returned for item: %s", item_id)
        result = None
    _LOG.debug("return=%s", result is not None)
    return result


def fetch_hn_comments(
    item_id: str,
    *,
    max_depth: int = -1,
    current_depth: int = 0,
) -> List[Dict[str, Any]]:
    """
    Recursively fetch HN comments for an item.

    :param item_id: HN item ID
    :param max_depth: Maximum recursion depth
    :param current_depth: Current recursion depth (internal use)
    :return: List of comment dicts with nested replies
    """
    _LOG.debug(hprint.to_str("item_id current_depth"))
    # Guard: stop recursion at max depth to limit API calls and processing time.
    if max_depth >= 0 and current_depth >= max_depth:
        result = []
    else:
        # Fetch the item data from HN API.
        item_data = fetch_hn_item(item_id)
        if not item_data:
            result = []
        else:
            # Extract core comment metadata from the item data.
            comment = {
                "id": item_data.get("id"),
                "by": item_data.get("by"),
                "text": item_data.get("text", ""),
                "time": item_data.get("time"),
                "score": item_data.get("score"),
            }
            # Recursively fetch all child comments (replies) if they exist.
            kids = item_data.get("kids", [])
            if kids:
                replies = []
                for kid_id in kids:
                    kid_comments = fetch_hn_comments(
                        str(kid_id),
                        max_depth=max_depth,
                        current_depth=current_depth + 1,
                    )
                    replies.extend(kid_comments)
                comment["replies"] = replies
            result = [comment]
    _LOG.debug(hprint.to_str("len(result)"))
    return result


def count_comments(comments: List[Dict[str, Any]]) -> int:
    """
    Recursively count total comments including nested replies.

    :param comments: List of comment dicts with nested replies
    :return: Total comment count
    """
    _LOG.debug(hprint.to_str("len(comments)"))
    count = len(comments)
    # Recurse into each comment's replies to include nested comments in the
    # total.
    for comment in comments:
        if "replies" in comment:
            count += count_comments(comment["replies"])
    _LOG.debug(hprint.to_str("count"))
    return count


def _simplify_html_links(text: str) -> str:
    """
    Simplify HTML links by extracting just the URL and unescaping entities.

    Converts: `<a href="https:&#x2F;&#x2F;example.com">...</a>`
    to: `https://example.com`

    :param text: Text containing HTML links
    :return: Text with simplified links
    """
    _LOG.debug(hprint.func_signature_to_str())

    def replace_link(match):
        """
        Match <a> tags and extract href, then replace with just the URL.
        """
        href = match.group(1)
        # Unescape HTML entities (&#x2F; -> /).
        unescaped = html.unescape(href)
        return unescaped

    # Pattern: <a href="...">...</a>: captures the href attribute.
    pattern = r'<a\s+[^>]*href=["\'](.*?)["\'][^>]*>.*?</a>'
    simplified = re.sub(
        pattern, replace_link, text, flags=re.IGNORECASE | re.DOTALL
    )
    _LOG.debug("simplified=%d chars", len(simplified))
    return simplified


def _add_comment_tree(
    comment_list: List[Dict[str, Any]], lines: List[str], depth: int = 0
) -> None:
    """
    Recursively add comments to output, preserving hierarchy.
    """
    _LOG.debug(hprint.func_signature_to_str())
    for comment in comment_list:
        # Format comment metadata: author, score, and timestamp.
        indent = "  " * depth
        lines.append(f"{indent}By: {comment.get('by', 'unknown')}")
        lines.append(f"{indent}Score: {comment.get('score', 0)}")
        lines.append(f"{indent}Time: {comment.get('time', 'unknown')}")
        # Extract and format comment text, preserving line breaks.
        text = comment.get("text", "").strip()
        if text:
            # Simplify HTML links in comment text.
            text = _simplify_html_links(text)
            # Unescape HTML entities (&#x27; -> ', &quot; -> ", etc.)
            text = html.unescape(text)
            for text_line in text.split("\n"):
                lines.append(f"{indent}{text_line}")
        lines.append("")
        # Recursively process nested replies at increasing indentation depth.
        if "replies" in comment:
            _add_comment_tree(comment["replies"], lines, depth + 1)


def format_hn_comments_as_text(comments: List[Dict[str, Any]]) -> str:
    """
    Format HN comments list as readable text.

    :param comments: List of comment dicts with nested replies
    :return: Formatted text representation of comments
    """
    _LOG.debug(hprint.func_signature_to_str())
    lines: List[str] = []
    _add_comment_tree(comments, lines)
    text = "\n".join(lines)
    # Simplify HTML links in comment text.
    text = _simplify_html_links(text)
    total_comments = count_comments(comments)
    _LOG.info("Total comments downloaded: %d", total_comments)
    _LOG.debug(hprint.to_str("len(text)"))
    return text
