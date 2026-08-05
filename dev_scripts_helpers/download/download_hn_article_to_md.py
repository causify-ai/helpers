#!/usr/bin/env -S uv run

# /// script
# dependencies = [
#   "beautifulsoup4",
#   "requests",
#   "tqdm",
# ]
# ///

r"""
- Download an Hacker News link (both comments, the article it points to)
- Save the files
- Summarize both

Output filenames share a base name, with

- `{base}.1.article_url.txt`: Article content
- `{base}.2.article_url.summary.txt`: Summarized article
- `{base}.3.hn_url.txt`: Raw HN comments
- `{base}.4.hn_url.summary.txt`: Summarized HN comments

where `{base}` is `--output` if specified, otherwise the submission title with
bash-unfriendly characters replaced with underscores.

# Usage Example

- Download and summarize everything for a submission (default actions):
> download_hn_article_to_md.py --hn_url "https://news.ycombinator.com/item?id=12345"

- Only fetch HN comments, skip the linked article:
> download_hn_article_to_md.py \
    --hn_url "https://news.ycombinator.com/item?id=12345" \
    --action download_hn_url \
    --action summarize_hn_url

- Download without summarizing:
> download_hn_article_to_md.py \
    --hn_url "https://news.ycombinator.com/item?id=12345" \
    --skip_action summarize_hn_url \
    --skip_action summarize_article_url

- Use an explicit output base name instead of the derived title:
> download_hn_article_to_md.py \
    --hn_url "https://news.ycombinator.com/item?id=12345" \
    --output my_submission

Import as:

import dev_scripts_helpers.download.download_hn_article_to_md as dsdhatm
"""

import argparse
import html
import logging
import re
from typing import Any, Dict, List, Optional

import requests

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hcache_simple as hcacsimp
import helpers.hselect_action as hselacti
import dev_scripts_helpers.download.download_utils as dsdlut
import dev_scripts_helpers.download.link_gsheet_utils as dshslgsut

_LOG = logging.getLogger(__name__)


# #############################################################################
# HN item + comments fetching
# #############################################################################


@hcacsimp.simple_cache(cache_type="json", write_through=True)
def _fetch_hn_item(item_id: str) -> Optional[Dict[str, Any]]:
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


def _fetch_hn_comments(
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
        item_data = _fetch_hn_item(item_id)
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
                    kid_comments = _fetch_hn_comments(
                        str(kid_id),
                        max_depth=max_depth,
                        current_depth=current_depth + 1,
                    )
                    replies.extend(kid_comments)
                comment["replies"] = replies
            result = [comment]
    _LOG.debug(hprint.to_str("len(result)"))
    return result


def _count_comments(comments: List[Dict[str, Any]]) -> int:
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
            count += _count_comments(comment["replies"])
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


def _format_hn_comments_as_text(comments: List[Dict[str, Any]]) -> str:
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
    total_comments = _count_comments(comments)
    _LOG.info("Total comments downloaded: %d", total_comments)
    _LOG.debug(hprint.to_str("len(text)"))
    return text


# #############################################################################
# Submission lookup
# #############################################################################


def _fetch_submission(hn_url: str) -> Dict[str, str]:
    """
    Fetch a HN submission's title and linked article URL (if any).

    :param hn_url: Hacker News item URL
    :return: dict with 'item_id', 'title', 'article_url' keys; 'article_url'
        is empty for Show HN / Ask HN / text posts (no linked article)
    """
    _LOG.debug(hprint.func_signature_to_str())
    hdbg.dassert(
        dshslgsut.is_hackernews_url(hn_url), "Not a Hacker News URL: %s", hn_url
    )
    item_id = dshslgsut.extract_item_id(hn_url)
    _LOG.debug(hprint.to_str("item_id"))
    item_data = _fetch_hn_item(item_id)
    title = item_id
    # Link posts have a "url" field pointing to the external article; Show
    # HN / Ask HN / text posts have no "url" (only "text"), so article_url
    # stays empty and article download/summarize is skipped for those.
    article_url = ""
    if item_data:
        title = item_data.get("title", item_id)
        article_url = item_data.get("url", "")
    _LOG.info(
        "Fetched submission: title='%s' article_url='%s'", title, article_url
    )
    _LOG.debug(hprint.to_str("item_id title article_url"))
    return {"item_id": item_id, "title": title, "article_url": article_url}


# #############################################################################
# Download actions
# #############################################################################


def _download_hn_url(
    item_id: str, output_file: str, *, dry_run: bool = False
) -> None:
    """
    Fetch HN comments for a submission and save them to a file.

    :param item_id: HN item ID
    :param output_file: Path to save the formatted comments to
    :param dry_run: If True, show what would be done without executing
    """
    _LOG.debug(hprint.to_str("item_id output_file dry_run"))
    if dry_run:
        _LOG.info("[DRY RUN] Would fetch HN comments for item: %s", item_id)
        _LOG.info("[DRY RUN] Would write HN comments to: %s", output_file)
        _LOG.debug("return: dry run, nothing written")
        return
    _LOG.info("Fetching HN comments for item: %s", item_id)
    hn_comments = _fetch_hn_comments(item_id, max_depth=10)
    total_comments = _count_comments(hn_comments)
    _LOG.info("Fetched %d total comments", total_comments)
    formatted_comments = _format_hn_comments_as_text(hn_comments)
    hio.to_file(output_file, formatted_comments)
    _LOG.info("Successfully saved HN comments to: %s", output_file)


def _download_article_url(
    article_url: str, output_file: str, *, dry_run: bool = False
) -> None:
    """
    Download the article content for a submission's linked URL.

    :param article_url: Article URL
    :param output_file: Path to save the article content to
    :param dry_run: If True, show what would be done without executing
    """
    _LOG.debug(hprint.to_str("article_url output_file dry_run"))
    # Pick the downloader based on the URL: arXiv links go through the
    # dedicated paper pipeline, everything else through the generic
    # HTML-to-markdown converter.
    downloader = (
        "download_academic_paper_to_md.py"
        if dsdlut.is_arxiv_url(article_url)
        else "download_html_to_md.py"
    )
    _LOG.debug(hprint.to_str("downloader"))
    if dry_run:
        _LOG.info(
            "[DRY RUN] Would download article from '%s' via %s",
            article_url,
            downloader,
        )
        _LOG.info("[DRY RUN] Would write article content to: %s", output_file)
        _LOG.debug("return: dry run, nothing written")
        return
    _LOG.info("Downloading article from '%s' via %s", article_url, downloader)
    dsdlut.download_article(article_url, output_file)
    _LOG.info("Successfully saved article to: %s", output_file)


# #############################################################################
# Summarize actions
# #############################################################################

_HN_COMMENTS_PROMPT = hprint.dedent("""
    - Analyze the Hacker News comment section.
    - From all comments, summarize the 5-10 most interesting comments based on:
      1. Thought-provoking or insightful content
      2. Unique perspective or uncommon knowledge
      3. Sparks discussion or debate
      4. Technically informative or educational
      5. Controversial but well-argued
    - Avoid comments that are: simple jokes, memes, very short reactions,
      repetitive or low-effort
    - Do not include commenter names

    - Format as plain text without markdown following the conventions in:
      - @.claude/skills/markdown.rules.txt
      - @.claude/skills/text.rules.txt
    """)


def _summarize_hn_url(
    comments_file: str, summary_file: str, *, dry_run: bool = False
) -> None:
    """
    Summarize HN comments using an LLM.

    :param comments_file: Path to the raw HN comments file
    :param summary_file: Path to save the summary to
    :param dry_run: If True, show what would be done without executing
    """
    _LOG.debug(hprint.to_str("comments_file summary_file dry_run"))
    if not dry_run:
        hdbg.dassert_file_exists(comments_file)
    dsdlut.summarize_text_with_llm(
        comments_file,
        summary_file,
        _HN_COMMENTS_PROMPT,
        dry_run=dry_run,
    )


def _summarize_article_url(
    article_file: str, summary_file: str, *, dry_run: bool = False
) -> None:
    """
    Summarize article text using an LLM.

    :param article_file: Path to the raw article content file
    :param summary_file: Path to save the summary to
    :param dry_run: If True, show what would be done without executing
    """
    _LOG.debug(hprint.to_str("article_file summary_file dry_run"))
    if not dry_run:
        hdbg.dassert_file_exists(article_file)
    dsdlut.summarize_text_with_llm(
        article_file,
        summary_file,
        dsdlut.ARTICLE_SUMMARY_PROMPT,
        dry_run=dry_run,
    )


# #############################################################################
# CLI and Entry Point
# #############################################################################


VALID_ACTIONS = [
    "download_article_url",
    "download_hn_url",
    "summarize_article_url",
    "summarize_hn_url",
]
DEFAULT_ACTIONS = VALID_ACTIONS[:]


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments.
    """
    _LOG.debug(hprint.func_signature_to_str())
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    parser.add_argument(
        "--hn_url",
        action="store",
        required=True,
        help="Hacker News submission URL, e.g. "
        "'https://news.ycombinator.com/item?id=12345'",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="",
        help=(
            "Output base name (no extension) shared by the generated files. "
            "If not specified, the sanitized submission title is used"
        ),
    )
    # Add action selection arguments (download_hn_url, download_article_url, etc).
    hselacti.add_action_arg(parser, VALID_ACTIONS, DEFAULT_ACTIONS)
    # Add cache control argument.
    hcacsimp.add_cache_control_arg(parser)
    # Dry run mode: show what would happen without executing.
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Dry run mode: show what would be done without actually executing actions",
    )
    # Add verbosity control argument.
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main entry point.
    """
    _LOG.debug(hprint.func_signature_to_str())
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    hcacsimp.parse_cache_control_args(args)
    # Fetch the submission to get its title and (optional) linked article URL.
    submission = _fetch_submission(args.hn_url)
    title = submission["title"]
    article_url = submission["article_url"]
    item_id = submission["item_id"]
    _LOG.debug(hprint.to_str("item_id title article_url"))
    # Restrict the defaults to HN-only actions when the submission has no
    # linked article (e.g., Show HN / Ask HN / text posts); overridable
    # explicitly via --action/--skip_action/--enable.
    default_actions = DEFAULT_ACTIONS
    if not article_url:
        _LOG.info("Submission has no linked article, restricting to HN-only actions")
        default_actions = ["download_hn_url", "summarize_hn_url"]
    actions = hselacti.select_actions(args, VALID_ACTIONS, default_actions)
    _LOG.info(
        "Actions to execute:\n%s",
        hselacti.actions_to_string(actions, VALID_ACTIONS, add_frame=True),
    )
    # Compute output filenames from `--output` if specified, otherwise from
    # the sanitized title.
    base_name = args.output or dsdlut.sanitize_title_for_filename(title)
    article_file = f"{base_name}.1.article_url.txt"
    article_summary_file = f"{base_name}.2.article_url.summary.txt"
    hn_file = f"{base_name}.3.hn_url.txt"
    hn_summary_file = f"{base_name}.4.hn_url.summary.txt"
    _LOG.debug(hprint.to_str("base_name"))
    if args.dry_run:
        _LOG.info("DRY RUN MODE: showing what would be done without executing")
    # Execute selected actions in sequence.
    actions_remaining = actions
    while actions_remaining:
        action = actions_remaining[0]
        to_execute, actions_remaining = hselacti.mark_action(
            action, actions_remaining
        )
        if not to_execute:
            continue
        _LOG.debug("Executing action='%s'", action)
        if action == "download_article_url":
            if not article_url:
                _LOG.warning(
                    "Submission has no linked article, skipping download_article_url"
                )
                continue
            _download_article_url(
                article_url, article_file, dry_run=args.dry_run
            )
        elif action == "download_hn_url":
            _download_hn_url(item_id, hn_file, dry_run=args.dry_run)
        elif action == "summarize_article_url":
            if not article_url:
                _LOG.warning(
                    "Submission has no linked article, skipping summarize_article_url"
                )
                continue
            _summarize_article_url(
                article_file, article_summary_file, dry_run=args.dry_run
            )
        elif action == "summarize_hn_url":
            _summarize_hn_url(hn_file, hn_summary_file, dry_run=args.dry_run)
    _LOG.info("Download and processing completed")


if __name__ == "__main__":
    _main(_parse())
