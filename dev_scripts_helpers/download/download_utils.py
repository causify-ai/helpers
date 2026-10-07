"""
Shared utilities for downloading and summarizing article content.

Provides common functionality for fetching article titles, sanitizing
titles for use in filenames, and summarizing text via an LLM.

Import as:

import dev_scripts_helpers.download.download_utils as dshddut
"""

import logging
import os
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
    # TODO(ai_gp): Remove try-except and let the exception propagate, or
    # restructure to avoid recovering from errors (coding.rules.md:## Do Not
    # Use `try-except`)
    # Not removed: this function's contract (see `:return:` above) is to
    # return `None` on fetch failure, and
    # `download_html_to_md.py::_get_output_md_file()` relies on that `None`
    # to gracefully fall back to the input's basename when the request
    # fails (e.g., network error, timeout, 404).
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
    # `BeautifulSoup` already unescapes HTML entities; just collapse internal
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


# Phrases (lowercase) found in the visible text of the pages that bot-protection
# systems (e.g., Cloudflare, Akamai, Imperva, Elsevier's content protection)
# return instead of the requested content.
BLOCKED_PAGE_MARKERS = [
    "just a moment",
    "attention required! | cloudflare",
    "enable javascript and cookies to continue",
    "checking your browser before accessing",
    "verify you are human",
    "performing security verification",
    "you may be using an automated script",
    "access denied",
    "unusual traffic from your computer",
    "pardon our interruption",
    "are you a robot",
    "captcha",
]

# A block page has only a few lines of text, while a real page has much more:
# a marker is only trusted on pages with less visible text than this, so that
# an article that merely mentions a "captcha" is not flagged.
BLOCKED_PAGE_MAX_TEXT_CHARS = 2000


def detect_blocked_page(html_content: str) -> str:
    """
    Detect a bot-protection page returned instead of the requested content.

    Such pages often come with a `200` status or are rendered by a browser, so
    the HTTP status alone does not reveal them. A page is flagged when its
    visible text is short and contains a known marker.

    :param html_content: HTML of the downloaded page
    :return: the matching marker, e.g., "just a moment", or "" if the page
        looks like real content
    """
    _LOG.debug(hprint.to_str("html_content"))
    # Keep only the text a person would see: drop scripts and styles, which are
    # large in block pages (e.g., 900 KB of HTML for 400 characters of text).
    soup = bs4.BeautifulSoup(html_content, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = re.sub(r"\s+", " ", soup.get_text(" ")).strip().lower()
    marker = ""
    if len(text) < BLOCKED_PAGE_MAX_TEXT_CHARS:
        matches = [m for m in BLOCKED_PAGE_MARKERS if m in text]
        marker = matches[0] if matches else ""
    _LOG.debug("return=%s", marker)
    return marker


# Shared prompt for summarizing article content into 5 bullet points; reused
# by `download_hn_article_to_md.py`, `download_html_to_md.py`, and
# `download_academic_paper_to_md.py` to avoid repeating the same prompt text.
ARTICLE_SUMMARY_PROMPT = hprint.dedent(
    """
    - Summarize the main article in 7-10 bullet points and fewer than about 250
      words
    - Format the result as plain text without markdown following the
      conventions in:
      - @.claude/skills/markdown.rules.md
      - @.claude/skills/text.rules.md
    """
)


def get_stat_file_path(summary_file: str) -> str:
    """
    Derive the stats JSON file path for a summary file.

    :param summary_file: path to a summary file produced by
        `summarize_text_with_llm()`, e.g., `*.summary.md` or `*.summary.txt`
    :return: path to the sibling stats file (e.g.,
        `foo.summary.md` -> `foo.summary.stat.json`)
    """
    stem, ext = os.path.splitext(summary_file)
    hdbg.dassert_ne(
        ext, "", "Summary file must have an extension: '%s'", summary_file
    )
    return stem + ".stat.json"


def _build_llm_cli_cmd(
    llm_cli_path: str,
    input_file: str,
    output_file: str,
    prompt_file: str,
    stat_file: str,
    *,
    model: str = "",
) -> str:
    """
    Build the `llm_cli.py` command line to summarize a file.

    :param llm_cli_path: path to `llm_cli.py`
    :param input_file: path to the input text file
    :param output_file: path to save the result
    :param prompt_file: path to the file with the system prompt
    :param stat_file: path to save the LLM usage stats
    :param model: LLM model name
        - Default: `""`, which omits `--model` so that `llm_cli.py` uses its
          own default model
    :return: command line
    """
    _LOG.debug(hprint.to_str("input_file output_file prompt_file model"))
    cmd_parts = [
        llm_cli_path,
        f"--input={input_file}",
        f"--output={output_file}",
        f"--pf={prompt_file}",
    ]
    # Without `--model`, `llm_cli.py` uses its default model: an OpenRouter one.
    if model:
        cmd_parts.append(f"--model={model}")
    cmd_parts += [f"--stat_file={stat_file}", "--lint"]
    cmd = " ".join(cmd_parts)
    return cmd


def summarize_text_with_llm(
    input_file: str,
    output_file: str,
    prompt: str,
    *,
    model: str = "",
    dry_run: bool = False,
) -> None:
    """
    Summarize text using `llm_cli.py` and lint the output.

    Also saves LLM usage stats (model, input/output/prompt char counts,
    wallclock time, cost) next to `output_file`; see `get_stat_file_path()`.

    :param input_file: Path to input text file to summarize
    :param output_file: Path to save the summary
    :param prompt: System prompt to guide the summarization
    :param model: LLM model to use for summarization
        - Default: `""`, which uses the default model of `llm_cli.py`, an
          OpenRouter one (it needs the `OPENROUTER_KEY` env var)
        - Use the `openrouter/<provider>/<model>` prefix for another
          OpenRouter model, e.g., `openrouter/anthropic/claude-haiku-4.5`
        - A direct model name, e.g., `gpt-4o-mini`, is not routed through
          OpenRouter and needs the key of its provider
    :param dry_run: If True, show what would be done without executing
    """
    _LOG.debug(hprint.to_str("input_file output_file model"))
    _LOG.info("Summarizing: '%s'", input_file)
    if dry_run:
        _LOG.info(
            "[DRY RUN] Would summarize: %s -> %s (model: %s)",
            input_file,
            output_file,
            model or "default",
        )
        return
    # Save prompt to a temporary file.
    prompt_file = "tmp.download_utils.summarize_text_with_llm.prompt.txt"
    hio.to_file(prompt_file, prompt)
    _LOG.debug("Saved prompt to: '%s'", prompt_file)
    # Build command to call `llm_cli.py` with the given prompt file.
    llm_cli_path = hsystem.find_file_in_repo("llm_cli.py")
    stat_file = get_stat_file_path(output_file)
    cmd = _build_llm_cli_cmd(
        llm_cli_path,
        input_file,
        output_file,
        prompt_file,
        stat_file,
        model=model,
    )
    _LOG.debug("Running command: '%s'", cmd)
    hsystem.system(cmd, print_command=True)
    _LOG.info("Summary saved to: '%s'", output_file)
    _LOG.info("Stats saved to: '%s'", stat_file)


# #############################################################################
# Article download dispatch
# #############################################################################


# TODO(ai_gp): Rename to `_is_arxiv_url()` since it is only used
# internally by `is_academic_paper_url()` (coding.rules.md:## Mark
# Private Functions)
# Not renamed: `is_arxiv_url()` is also called from
# `download_hn_article_to_md.py` (as `dshddut.is_arxiv_url()`), so it is
# part of the module's public interface, not internal-only.
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


# TODO(ai_gp): Rename to `_detect_doi()` since it is only used
# internally by `is_academic_paper_url()` (coding.rules.md:## Mark
# Private Functions)
# Not renamed: `detect_doi()` is also called from
# `download_academic_paper_to_md.py` (as `dshddut.detect_doi()`), so it is
# part of the module's public interface, not internal-only.
def detect_doi(url: str) -> Optional[str]:
    """
    Detect DOI from URL or bare DOI string.

    :param url: URL or bare DOI (e.g., "https://doi.org/10.xxx" or
        "10.xxx/yyy")
    :return: DOI if detected, None otherwise
    """
    _LOG.debug(hprint.to_str("url"))
    _DOI_URL_PATTERN = r"(?:https?://)?(?:dx\.)?doi\.org/(.+)"
    _DOI_BARE_PATTERN = r"^(10\.\d{4,}/\S+)$"
    # Try URL pattern.
    match = re.search(_DOI_URL_PATTERN, url)
    if match:
        doi = match.group(1)
        _LOG.debug(hprint.to_str("doi"))
        return doi
    # Try bare DOI pattern.
    match = re.search(_DOI_BARE_PATTERN, url)
    if match:
        doi = match.group(1)
        _LOG.debug(hprint.to_str("doi"))
        return doi
    _LOG.debug("return=None")
    return None


def get_ssrn_id(input_arg: str) -> str:
    """
    Extract the SSRN abstract id from an SSRN URL or DOI.

    E.g., all of these return "5277078":
    - `https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5277078`
    - `https://papers.ssrn.com/sol3/Delivery.cfm/5277078.pdf?abstractid=5277078`
    - `https://www.ssrn.com/abstract=5277078`
    - `10.2139/ssrn.5277078`

    :param input_arg: URL or DOI
    :return: the abstract id, or "" if the input is not an SSRN paper
    """
    _LOG.debug(hprint.to_str("input_arg"))
    ssrn_id = ""
    if "ssrn" in input_arg.lower():
        # Match the id after any of the forms SSRN uses for it.
        pattern = r"""
            (?:
                abstract_id=         # papers.cfm?abstract_id=<id>
              | abstractid=          # Delivery.cfm/<id>.pdf?abstractid=<id>
              | ssrn\.com/abstract=  # www.ssrn.com/abstract=<id>
              | 10\.2139/ssrn\.      # DOI
            )
            (\d+)
        """
        match = re.search(pattern, input_arg, re.VERBOSE)
        if match:
            ssrn_id = match.group(1)
    _LOG.debug("return=%s", ssrn_id)
    return ssrn_id


def _is_pdf_url(url: str) -> bool:
    """
    Check if a URL points directly to a PDF file.

    :param url: input URL
    :return: True if the URL path (ignoring query string/fragment) ends
        in `.pdf`
    """
    _LOG.debug(hprint.to_str("url"))
    # Strip query string and fragment before checking the file extension.
    path = url.split("?")[0].split("#")[0]
    result = path.lower().endswith(".pdf")
    _LOG.debug("return='%s'", result)
    return result


def is_academic_paper_url(url: str) -> bool:
    """
    Check if a URL points to an academic paper (arXiv, DOI, PDF, or SSRN).

    Single source of truth for what counts as an "academic paper" URL,
    shared by `download_to_md.py`'s input-type detection and
    `download_article()`'s dispatch below, so the two stay consistent.

    A path to a local `.pdf` file also counts, like a PDF URL. An SSRN
    abstract page counts too: it is not a PDF, but
    `download_academic_paper_to_md.py` downloads its paper through Chrome.

    :param url: Article URL, bare DOI, or local file path
    :return: True if the URL should be routed to
        `download_academic_paper_to_md.py`
    """
    _LOG.debug(hprint.to_str("url"))
    result = bool(
        is_arxiv_url(url)
        or detect_doi(url)
        or _is_pdf_url(url)
        or get_ssrn_id(url)
    )
    _LOG.debug(hprint.to_str("result"))
    return result


def download_website_article(url: str, output_file: str) -> None:
    """
    Download a normal website article and convert it to markdown via
    `download_html_to_md.py`.

    :param url: Article URL
    :param output_file: Path to save the article markdown to; should end
        in `.md`
    """
    _LOG.debug(hprint.to_str("url output_file"))
    script = hgit.find_file_in_git_tree("download_html_to_md.py")
    cmd = [
        script,
        f'--input "{url}"',
        f'--output "{output_file}"',
    ]
    cmd = " ".join(cmd)
    hsystem.system(cmd, print_command=True)
    hdbg.dassert_file_exists(output_file)


def download_arxiv_article(url: str, output_file: str) -> None:
    """
    Download an arXiv paper via `download_academic_paper_to_md.py` and use
    its converted markdown as the article content.

    `output_file` must end in `.md`: `download_academic_paper_to_md.py`
    writes its converted markdown directly to it (and the downloaded PDF to
    the sibling `.pdf`), so no separate copy step is needed.

    Figures are not extracted from the PDF since only the article text is
    needed downstream (e.g., for summarization).

    :param url: arXiv URL
    :param output_file: Path to save the extracted article markdown to;
        must end in `.md`
    """
    _LOG.debug(hprint.to_str("url output_file"))
    hdbg.dassert(
        output_file.endswith(".md"),
        "output_file must end in '.md': %s",
        output_file,
    )
    # Base path (no extension) shared by the generated .pdf/.md files.
    base_path = output_file[: -len(".md")]
    script = hgit.find_file_in_git_tree("download_academic_paper_to_md.py")
    # Only download + convert here: skip the script's own summarize action
    # since callers summarize the resulting article text themselves. Skip
    # figures too, since only the text is consumed downstream.
    cmd = [
        script,
        f'--input "{url}"',
        f'--output "{base_path}"',
        "--no_incremental",
        "--skip_action summarize",
        "--skip_figures",
    ]
    cmd = " ".join(cmd)
    hsystem.system(cmd, print_command=True)
    pdf_output_file = f"{base_path}.pdf"
    hdbg.dassert_file_exists(pdf_output_file)
    hdbg.dassert_file_exists(output_file)
    _LOG.info("Saved PDF to: '%s'", pdf_output_file)
    _LOG.info("Saved article markdown to: '%s'", output_file)


def download_article(url: str, output_file: str) -> None:
    """
    Download an article, dispatching to the academic-paper or generic
    downloader.

    :param url: Article URL
    :param output_file: Path to save the article text to
    """
    _LOG.debug(hprint.to_str("url output_file"))
    if is_academic_paper_url(url):
        download_arxiv_article(url, output_file)
    else:
        download_website_article(url, output_file)
