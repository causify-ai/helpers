#!/usr/bin/env -S uv run

# /// script
# dependencies = ["feedparser", "pymupdf", "requests", "pyyaml", "beautifulsoup4", "tqdm"]
# ///

"""
- Download academic papers from arXiv, DOI, SSRN, and other sources
- Save the paper with a standardized base name, e.g.,
    `2016.Ribeiro_et_al.Why_Should_I_Trust_You_Explaining_the_Predictions_of_Any_Classifier`
- Convert them to Markdown
- Summarize the markdown text

- The output file name is shared across the `.pdf`, `.md`, and `.summary.md` outputs

# Usage Example

- Download from arXiv URL (runs download, convert, summarize by default):
> download_academic_paper_to_md.py --input "https://arxiv.org/abs/1706.03762"

- Download from DOI URL:
> download_academic_paper_to_md.py --input "https://doi.org/10.1038/nature12373"

- Download from bare DOI:
> download_academic_paper_to_md.py --input "10.1038/nature12373"

- Download from bare DOI, looking up an open-access PDF with Unpaywall (which
  requires a valid contact email):
> download_academic_paper_to_md.py --input "10.1038/nature12373" --email me@example.org

- Download from an SSRN URL (SSRN blocks scripted clients, so the PDF is
  downloaded through Chrome with `download_with_chrome.py`: a Chrome is started
  and closed by the script):
> download_academic_paper_to_md.py --input "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5277078"

- Download from generic PDF URL:
> download_academic_paper_to_md.py --input "https://example.com/paper.pdf"

- Use a PDF already saved locally (e.g., from a site that blocks scripted
  downloads): copy it under the standardized name, convert it, and summarize
  it:
> download_academic_paper_to_md.py --input ~/Downloads/ssrn_5277078.pdf

- Use a local PDF with an explicit base name (produces mypaper.pdf, mypaper.md, ...):
> download_academic_paper_to_md.py --input ~/Downloads/ssrn_5277078.pdf --output ./my_papers/mypaper

- Save under a custom directory when --output is not passed, via $PAPERS_DIR:
> PAPERS_DIR=./my_papers download_academic_paper_to_md.py --input "https://arxiv.org/abs/1706.03762"

- Specify an explicit output base name (produces mypaper.pdf, mypaper.md, ...):
> download_academic_paper_to_md.py --input "https://arxiv.org/abs/1706.03762" --output ./my_papers/mypaper

- Overwrite existing files:
> download_academic_paper_to_md.py --input "10.1038/nature12373" --no_incremental

- Summarize with a specific LLM model (by default the OpenRouter model of
  `llm_cli.py`, which needs the `OPENROUTER_KEY` env var):
> download_academic_paper_to_md.py --input "10.1038/nature12373" --model openrouter/anthropic/claude-haiku-4.5

- Only download and convert, skip summarization:
> download_academic_paper_to_md.py --input "10.1038/nature12373" --skip_action summarize

- Also copy the PDF and the summary to the papers dir (by default
  `/Users/saggese/src/notes1/papers`):
> download_academic_paper_to_md.py --input "https://arxiv.org/abs/1706.03762" --action save_to_papers_dir

- Copy the PDF and the summary to a custom papers dir:
> download_academic_paper_to_md.py --input "https://arxiv.org/abs/1706.03762" --action save_to_papers_dir --papers_dir ./my_papers

- Convert without extracting figures/images from the PDF:
> download_academic_paper_to_md.py --input "10.1038/nature12373" --skip_figures

- Show what would be done without downloading, converting, or summarizing:
> download_academic_paper_to_md.py --input "10.1038/nature12373" --dry_run

Import as:

import dev_scripts_helpers.download.download_academic_paper_to_md as dsdapt
"""

import argparse
import logging
import os
import re
import shutil
from typing import Any, Dict, List, Optional, Tuple

import feedparser
import fitz
import requests

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hretry as hretry
import helpers.hselect_action as hselacti
import helpers.hstring as hstring
import helpers.hsystem as hsystem
import dev_scripts_helpers.download.download_utils as dshddut

_LOG = logging.getLogger(__name__)

# API decorator configuration.
_RETRY_DELAY_SEC = 2
_API_TIMEOUT = 30
_DOWNLOAD_TIMEOUT = 300

# Default dir where the `save_to_papers_dir` action copies the PDF and the
# summary of a paper. It is different from `$PAPERS_DIR`, the dir where the
# files are generated.
_DEFAULT_PAPERS_DIR = "/Users/saggese/src/notes1/papers"

# - Extracts metadata (year, authors, title) from arXiv API, CrossRef, or PDF
#   (including a local PDF file passed as `--input`)
# - Formats base name as: <year>.<FirstAuthorLastName>.[et_al.].<Title>
# - Checks if file already exists (skip unless --no_incremental)
# - Saves papers to $PAPERS_DIR (or "." if not set)
#
# - Base name examples:
# - "2017.Vaswani.Attention_Is_All_You_Need"
# - "2019.Devlin.et_al.BERT_Pre-training_of_Deep_Bidirectional_Transformers"
# - "2020.Brown.et_al.Language_Models_are_Few-Shot_Learners"


# #############################################################################
# ArXiv metadata
# #############################################################################


@hretry.sync_retry(
    (requests.RequestException,),
    retry_delay_in_sec=_RETRY_DELAY_SEC,
)
def _extract_arxiv_metadata(arxiv_id: str) -> Dict[str, Any]:
    """
    Extract metadata from arXiv API.

    :param arxiv_id: arXiv paper ID (e.g., "1706.03762")
    :return: dict with 'year', 'authors', 'title' keys
    """
    _LOG.debug(hprint.to_str("arxiv_id"))
    # Use https directly: the plain `http://` endpoint 301-redirects and
    # `feedparser.parse()` fetches the URL itself with no timeout, so a
    # slow/failed redirect can silently yield an empty feed instead of
    # raising.
    _ARXIV_API_URL = "https://export.arxiv.org/api/query?id_list={arxiv_id}"
    _LOG.debug("Extracting metadata from arXiv for ID: %s", arxiv_id)
    url = _ARXIV_API_URL.format(arxiv_id=arxiv_id)
    # Fetch via `requests` (with a timeout and retry, like the other API
    # calls in this file) and hand the raw bytes to `feedparser`, instead of
    # letting `feedparser.parse()` do its own un-timed, un-retried fetch.
    resp = requests.get(url, timeout=_API_TIMEOUT)
    resp.raise_for_status()
    feed = feedparser.parse(resp.content)
    hdbg.dassert(
        feed.entries,
        "No entries found for arXiv ID: %s (bozo=%s, bozo_exception=%s)",
        arxiv_id,
        feed.get("bozo"),
        feed.get("bozo_exception"),
    )
    entry = feed.entries[0]
    # Extract year from published date (format: YYYY-MM-DDTHH:MM:SSZ).
    year = entry.published[:4]
    # Extract authors.
    authors = [author.name for author in entry.authors]
    title = entry.title
    metadata = {"year": year, "authors": authors, "title": title}
    _LOG.debug(hprint.to_str("metadata"))
    return metadata


def _detect_arxiv_id(url: str) -> str:
    """
    Detect arXiv ID from URL.

    :param url: input URL
        Example: "https://arxiv.org/abs/1706.03762"
    :return: arXiv ID if detected, empty string otherwise
        Example: "1706.03762"
    """
    _LOG.debug(hprint.to_str("url"))
    # Match the arXiv ID with or without a leading `arxiv.org/abs|pdf/` prefix.
    _ARXIV_ID_PATTERN = r"(?:arxiv\.org/(?:abs|pdf)/)?(\d{4}\.\d{4,5})"
    match = re.search(_ARXIV_ID_PATTERN, url)
    arxiv_id = match.group(1) if match else ""
    _LOG.debug(hprint.to_str("arxiv_id"))
    return arxiv_id


# #############################################################################
# DOI metadata
# #############################################################################


@hretry.sync_retry(
    (requests.RequestException,),
    retry_delay_in_sec=_RETRY_DELAY_SEC,
)
def _crossref_query(doi: str) -> Dict[str, Any]:
    """
    Query CrossRef API for paper metadata.

    :param doi: DOI string
    :return: API response as dict
    """
    _LOG.debug(hprint.to_str("doi"))
    _CROSSREF_API = "https://api.crossref.org/works"
    url = f"{_CROSSREF_API}/{doi}"
    _LOG.debug("Querying CrossRef API: %s", url)
    resp = requests.get(url, timeout=_API_TIMEOUT)
    resp.raise_for_status()
    result = resp.json()
    _LOG.debug("return keys=%s", list(result.keys()))
    return result


@hretry.sync_retry(
    (requests.RequestException,),
    retry_delay_in_sec=_RETRY_DELAY_SEC,
)
def _unpaywall_query(doi: str, *, email: str) -> Dict[str, Any]:
    """
    Query Unpaywall API for open access PDF URL.

    :param doi: DOI string
    :param email: contact email for the API
        - Unpaywall rejects placeholder emails (e.g., `user@example.com`)
          with a `422` error, so it must be a real address
    :return: API response as dict
    """
    _LOG.debug(hprint.to_str("doi email"))
    _UNPAYWALL_API = "https://api.unpaywall.org/v2"
    url = f"{_UNPAYWALL_API}/{doi}"
    params = {"email": email}
    _LOG.debug("Querying Unpaywall API: %s", url)
    resp = requests.get(url, params=params, timeout=_API_TIMEOUT)
    resp.raise_for_status()
    result = resp.json()
    _LOG.debug("return keys=%s", list(result.keys()))
    return result


def _resolve_crossref_metadata(doi: str) -> Dict[str, Any]:
    """
    Resolve DOI to paper metadata with CrossRef.

    :param doi: DOI string
    :return: dict with 'year', 'authors', 'title' keys
    """
    _LOG.debug(hprint.to_str("doi"))
    _LOG.info("Resolving DOI='%s'", doi)
    # Query CrossRef for metadata.
    cr_data = _crossref_query(doi)
    message = cr_data.get("message", {})
    title = (
        message.get("title", [""])[0]
        if isinstance(message.get("title"), list)
        else message.get("title", "")
    )
    # Build author names from CrossRef's given/family name fields.
    authors = []
    for author in message.get("author", []):
        name_parts = []
        if "given" in author:
            name_parts.append(author["given"])
        if "family" in author:
            name_parts.append(author["family"])
        if name_parts:
            authors.append(" ".join(name_parts))
    year = message.get("issued", {}).get("date-parts", [[2000]])[0][0]
    metadata = {"year": str(year), "authors": authors, "title": title}
    _LOG.debug(hprint.to_str("metadata"))
    return metadata


def _resolve_doi_metadata(doi: str, *, email: str = "") -> Dict[str, Any]:
    """
    Resolve DOI to paper metadata and to the URL of an open-access PDF.

    :param doi: DOI string
    :param email: contact email for the Unpaywall API
        - Default: `""`, which skips the Unpaywall lookup so 'pdf_url' is
          `None`
    :return: dict with 'year', 'authors', 'title', 'pdf_url' keys
    """
    _LOG.debug(hprint.to_str("doi email"))
    metadata = _resolve_crossref_metadata(doi)
    # Query Unpaywall for PDF URL. Unpaywall rejects requests without a valid
    # contact email, so skip the lookup (instead of failing) when none is given:
    # CrossRef is enough to name the paper.
    pdf_url = None
    if email:
        uw_data = _unpaywall_query(doi, email=email)
        # Use only `url_for_pdf`, a direct link to a PDF: `url` can be a
        # landing page (e.g., an SSRN abstract page, which blocks scripts with
        # a `403`), and saving it as a PDF would fail or save HTML. Prefer the
        # best location, then any other location with a direct PDF link.
        locations = [uw_data.get("best_oa_location") or {}]
        locations += uw_data.get("oa_locations") or []
        pdf_urls = [
            loc["url_for_pdf"] for loc in locations if loc.get("url_for_pdf")
        ]
        pdf_url = pdf_urls[0] if pdf_urls else None
        _LOG.debug(hprint.to_str("pdf_url"))
        if pdf_url is None:
            _LOG.warning("Unpaywall has no direct PDF link for DOI '%s'", doi)
    else:
        _LOG.warning(
            "Skipping the Unpaywall lookup for DOI '%s': pass --email to find "
            "an open-access PDF",
            doi,
        )
    metadata["pdf_url"] = pdf_url
    _LOG.debug(hprint.to_str("metadata"))
    return metadata


# #############################################################################
# Non-arXiv metadata
# #############################################################################


def _is_local_file(input_arg: str) -> bool:
    """
    Check if the input is the path to an existing local file.

    :param input_arg: URL, DOI, or path (a leading `~` is expanded)
    :return: True if it is an existing file, e.g., `~/Downloads/paper.pdf`
    """
    _LOG.debug(hprint.to_str("input_arg"))
    result = os.path.isfile(os.path.expanduser(input_arg))
    _LOG.debug("return=%s", result)
    return result


def _extract_pdf_metadata_pymupdf(pdf_path: str) -> Dict[str, Any]:
    """
    Extract metadata from PDF using `pymupdf`.

    :param pdf_path: path to PDF file
    :return: dict with 'year', 'authors', 'title' keys
    """
    _LOG.debug(hprint.to_str("pdf_path"))
    _LOG.debug("Extracting metadata from PDF: %s", pdf_path)
    doc = fitz.open(pdf_path)
    metadata = doc.metadata
    # Extract title.
    title = metadata.get("title", None) if metadata else None
    title = title.strip() if title else None
    # Extract author.
    author_str = metadata.get("author", None) if metadata else None
    author_str = author_str.strip() if author_str else None
    authors = []
    if author_str:
        # Split on commas, semicolons, and the word "and" (not on the letters
        # a, n, d, which a `[,;and]` character class would match).
        authors = [a.strip() for a in re.split(r",|;|\band\b", author_str)]
        authors = [a for a in authors if a]
    # Extract year from creation date or text content (best effort).
    year = None
    if metadata:
        creation_date = metadata.get("creationDate", None)
        if creation_date:
            # Extract year from date string.
            year_match = re.search(r"(\d{4})", str(creation_date))
            year = year_match.group(1) if year_match else None
    # If no year from metadata, try extracting from first page text.
    if not year:
        first_page = doc[0]
        text = first_page.get_text("text")  # type: ignore
        # Look for year pattern (1900-2099).
        year_match = re.search(r"\b(19|20)\d{2}\b", text)
        year = year_match.group(0) if year_match else None
    doc.close()
    result = {
        "year": year,
        "authors": authors,
        "title": title,
    }
    _LOG.debug(hprint.to_str("result"))
    return result


# #############################################################################
# Filename formatting
# #############################################################################


def _format_base_filename(
    year: Optional[str], authors: List[str], title: Optional[str]
) -> str:
    """
    Format the base filename (no extension) according to spec, with
    bash-safe formatting (spaces -> underscores).

    Format: <year>.<First_author_last_name>.[et_al.].<Title>

    :param year: publication year
    :param authors: list of author names
    :param title: paper title
    :return: formatted base filename (without extension)
    """
    _LOG.debug(hprint.to_str("year authors title"))
    parts = []
    # Add year.
    if year:
        parts.append(year)
    else:
        parts.append("UnknownYear")
    # Add author(s).
    if authors:
        first_author = authors[0]
        # Extract last name (assume "First Last" format).
        last_name_parts = first_author.strip().split()
        last_name = last_name_parts[-1] if last_name_parts else "Unknown"
        last_name = hstring.to_ascii(last_name)
        if len(authors) > 1:
            author_part = f"{last_name}_et_al"
        else:
            author_part = last_name
    else:
        author_part = "None"
    parts.append(author_part)
    # Add title.
    if title:
        title = title.strip()
        title = hstring.to_ascii(title)
        title_part = title
    else:
        title_part = "UnknownTitle"
    parts.append(title_part)
    # Join parts with dot.
    base_filename = ".".join(parts)
    # Remove invalid characters and replace spaces with underscores.
    base_filename = re.sub(r'[<>:"/\\|?*]', "", base_filename)
    base_filename = re.sub(r"\s+", "_", base_filename)
    _LOG.debug(hprint.to_str("base_filename"))
    return base_filename


# #############################################################################
# Metadata / base path resolution
# #############################################################################


def _resolve_metadata_and_content(
    url: str, *, email: str = ""
) -> Tuple[Dict[str, Any], Optional[bytes], Optional[str]]:
    """
    Resolve paper metadata for a URL.

    For a local PDF file, the metadata is extracted from the file itself.

    For an SSRN paper, the metadata comes from CrossRef (SSRN papers have the
    DOI `10.2139/ssrn.<id>`) and there is no PDF URL, since SSRN blocks scripted
    downloads: the PDF is downloaded through Chrome by `_download()`.

    For generic (non-arXiv, non-DOI) PDF URLs, the PDF is downloaded as a
    side effect since there is no metadata API to query; the downloaded
    bytes are returned so callers can reuse them instead of downloading
    twice.

    :param url: path to a local PDF file, URL to PDF, arXiv URL, SSRN URL, or
        DOI
    :param email: contact email for the Unpaywall API, used to find an
        open-access PDF for a DOI
    :return: tuple of (metadata dict with 'year'/'authors'/'title', PDF
        content if already downloaded else None, resolved PDF URL to
        download from if known)
    """
    _LOG.debug(hprint.to_str("url email"))
    _LOG.info("Resolving metadata for: %s", url)
    # Try to resolve a local file first, then an SSRN paper, then via DOI, then
    # arXiv ID, falling back to downloading the raw PDF and extracting metadata
    # locally.
    doi = dshddut.detect_doi(url)
    ssrn_id = dshddut.get_ssrn_id(url)
    pdf_content = None
    pdf_url = None
    if _is_local_file(url):
        _LOG.debug("Detected local PDF file")
        metadata = _extract_pdf_metadata_pymupdf(os.path.expanduser(url))
    elif ssrn_id:
        _LOG.debug("Detected SSRN paper with ID: %s", ssrn_id)
        metadata = _resolve_crossref_metadata(f"10.2139/ssrn.{ssrn_id}")
    elif doi:
        _LOG.debug("Detected DOI: %s", doi)
        metadata = _resolve_doi_metadata(doi, email=email)
        pdf_url = metadata.pop("pdf_url")
    else:
        arxiv_id = _detect_arxiv_id(url)
        if arxiv_id:
            _LOG.debug("Detected arXiv paper with ID: %s", arxiv_id)
            metadata = _extract_arxiv_metadata(arxiv_id)
            pdf_url = f"http://arxiv.org/pdf/{arxiv_id}.pdf"
        else:
            _LOG.debug("Non-arXiv paper, downloading and extracting metadata")
            # A path to a missing file would otherwise fail in `requests` with
            # an obscure "No scheme supplied" error.
            hdbg.dassert_in(
                "://",
                url,
                "Input is not an existing file, an arXiv URL, a DOI, or a URL",
            )
            # Download PDF once for both extraction and saving.
            response = requests.get(url, timeout=_DOWNLOAD_TIMEOUT)
            response.raise_for_status()
            pdf_content = response.content
            # Extract metadata from PDF.
            tmp_path = "tmp.download_academic_paper_to_md.metadata.pdf"
            with open(tmp_path, "wb") as f:
                f.write(pdf_content)
            metadata = _extract_pdf_metadata_pymupdf(tmp_path)
    _LOG.debug(
        "return metadata=%s pdf_content_len=%s pdf_url=%s",
        metadata,
        len(pdf_content) if pdf_content else None,
        pdf_url,
    )
    return metadata, pdf_content, pdf_url


def _get_output_base_path(
    input_url: str, output_dir: str, *, email: str = ""
) -> str:
    """
    Derive the output base path (no extension) from the paper's metadata.

    :param input_url: path to a local PDF file, URL to PDF, arXiv URL, or DOI
    :param output_dir: directory to save the base path under
    :param email: contact email for the Unpaywall API
    :return: base path, e.g. `<output_dir>/2017.Vaswani.Attention_Is_All_You_Need`
    """
    _LOG.debug(hprint.to_str("input_url output_dir email"))
    metadata, _, _ = _resolve_metadata_and_content(input_url, email=email)
    if _is_local_file(input_url) and not metadata.get("title"):
        # A local PDF often has no embedded title (e.g., PDFs from SSRN): a
        # name like `UnknownYear.None.UnknownTitle` would be useless, so keep
        # the name the user gave to the file.
        base_filename = os.path.splitext(os.path.basename(input_url))[0]
    else:
        # Normalize authors to a list since metadata may store a single
        # string.
        authors = metadata.get("authors", [])
        if not isinstance(authors, list):
            authors = [authors] if authors else []
        base_filename = _format_base_filename(
            metadata.get("year"), authors, metadata.get("title")
        )
    base_path = os.path.join(output_dir, base_filename)
    _LOG.debug(hprint.to_str("base_path"))
    return base_path


# #############################################################################
# Download action
# #############################################################################


def _download_ssrn_with_chrome(
    url: str, pdf_path: str, *, log_level: str
) -> None:
    """
    Download the PDF of an SSRN paper through Chrome with
    `download_with_chrome.py`.

    SSRN blocks scripted clients, including headless browsers, so the PDF is
    fetched by a real Chrome. The script starts a Chrome if none is running and
    closes it after the download.

    :param url: SSRN abstract URL, delivery URL, or DOI
    :param pdf_path: path to save the PDF to
    :param log_level: logging level to forward to the called script
    """
    _LOG.debug(hprint.to_str("url pdf_path log_level"))
    script_path = hgit.find_file_in_git_tree("download_with_chrome.py")
    # `--no_incremental` since the caller already decided that `pdf_path`
    # has to be (over)written.
    cmd = [
        script_path,
        "--launch_chrome",
        "--mode file",
        f'--input "{url}"',
        f'--output "{pdf_path}"',
        "--no_incremental",
        f"-v {log_level}",
    ]
    cmd = " ".join(cmd)
    _LOG.info("Downloading the SSRN paper '%s' through Chrome", url)
    hsystem.system(cmd, print_command=True)
    hdbg.dassert_file_exists(pdf_path)


def _download(
    url: str,
    pdf_path: str,
    *,
    email: str = "",
    log_level: str = "INFO",
    no_incremental: bool = False,
    dry_run: bool = False,
) -> None:
    """
    Download the PDF for `url` and save it to `pdf_path`.

    A local PDF file is copied to `pdf_path` instead, so that the `.pdf`,
    `.md`, and `.summary.md` outputs share the same base name.

    An SSRN paper is downloaded through Chrome, since SSRN blocks scripted
    clients.

    :param url: path to a local PDF file, URL to PDF, arXiv URL, SSRN URL, or
        DOI
    :param pdf_path: path to save the PDF to
    :param email: contact email for the Unpaywall API
    :param log_level: logging level to forward to the called scripts
    :param no_incremental: if True, overwrite existing files
    :param dry_run: if True, show what would be done without executing
    """
    _LOG.debug(
        hprint.to_str("url pdf_path email log_level no_incremental dry_run")
    )
    is_local_file = _is_local_file(url)
    is_ssrn = bool(dshddut.get_ssrn_id(url)) and not is_local_file
    if dry_run:
        if is_local_file:
            _LOG.warning(
                "[DRY_RUN] Would copy local PDF '%s' to '%s'", url, pdf_path
            )
        elif is_ssrn:
            _LOG.warning(
                "[DRY_RUN] Would download SSRN paper '%s' through Chrome to "
                "'%s'",
                url,
                pdf_path,
            )
        else:
            _LOG.warning("[DRY_RUN] Would download PDF from '%s'", url)
            _LOG.warning("[DRY_RUN] Would save PDF to: '%s'", pdf_path)
        _LOG.debug("return: dry run, nothing written")
        return
    if is_local_file and os.path.abspath(pdf_path) == os.path.abspath(url):
        # Copying a file onto itself fails, and there is nothing to do.
        _LOG.info("PDF is already at '%s', nothing to copy", pdf_path)
        return
    if os.path.exists(pdf_path) and not no_incremental:
        _LOG.warning("PDF already exists, skipping: '%s'", pdf_path)
        return
    pdf_dir = os.path.dirname(pdf_path) or "."
    if is_local_file:
        # Copy the local PDF to the standardized path.
        hio.create_dir(pdf_dir, incremental=True)
        _LOG.info("Copying local PDF '%s' to '%s'", url, pdf_path)
        shutil.copyfile(os.path.expanduser(url), pdf_path)
        _LOG.info("Successfully copied: '%s'", pdf_path)
    elif is_ssrn:
        # SSRN blocks scripted clients: download through Chrome.
        hio.create_dir(pdf_dir, incremental=True)
        _download_ssrn_with_chrome(url, pdf_path, log_level=log_level)
        _LOG.info("Successfully downloaded and saved: '%s'", pdf_path)
    else:
        _, pdf_content, pdf_url = _resolve_metadata_and_content(url, email=email)
        # Download the PDF now if metadata resolution did not already fetch it
        # (the DOI/arXiv branches only resolve a URL, not the content).
        if pdf_content is None:
            # A DOI resolves to a landing page, not to a PDF: without a direct
            # open-access PDF URL there is nothing to download.
            hdbg.dassert(
                pdf_url or not dshddut.detect_doi(url),
                "No direct open-access PDF link found for DOI '%s' (Unpaywall "
                "is queried only if --email is passed): download the PDF "
                "manually and pass the local file with --input",
                url,
            )
            download_url = pdf_url or url
            _LOG.debug("Downloading PDF from URL: %s", download_url)
            response = requests.get(download_url, timeout=_DOWNLOAD_TIMEOUT)
            response.raise_for_status()
            pdf_content = response.content
        # Save PDF.
        hio.create_dir(pdf_dir, incremental=True)
        _LOG.info("Saving PDF to: '%s'", pdf_path)
        with open(pdf_path, "wb") as f:
            f.write(pdf_content)
        _LOG.info("Successfully downloaded and saved: '%s'", pdf_path)


# #############################################################################
# Convert action
# #############################################################################


def _convert(
    pdf_path: str, *, skip_figures: bool = False, dry_run: bool = False
) -> None:
    """
    Convert the PDF to Markdown using `convert_pdf_to_md.py`.

    Writes `<pdf_stem>.md` next to `pdf_path`, i.e. `<base_path>.md`.

    :param pdf_path: path to the PDF file to convert
    :param skip_figures: if True, do not extract images/figures from the
        PDF
    :param dry_run: if True, show what would be done without executing
    """
    _LOG.debug(hprint.to_str("pdf_path skip_figures dry_run"))
    if dry_run:
        _LOG.info("[DRY RUN] Would convert PDF to markdown: %s", pdf_path)
        _LOG.debug("return: dry run, nothing written")
        return
    hdbg.dassert_file_exists(pdf_path)
    _LOG.info("Converting PDF to markdown: %s", pdf_path)
    script_path = hgit.find_file_in_git_tree("convert_pdf_to_md.py")
    output_dir = os.path.dirname(pdf_path) or "."
    cmd = f"{script_path} --input {pdf_path} --output {output_dir} --overwrite"
    if skip_figures:
        cmd += " --skip_figures"
    _LOG.debug("Running command: %s", cmd)
    hsystem.system(cmd, print_command=True)


# #############################################################################
# Summarize action
# #############################################################################


def _summarize(
    base_path: str, *, model: str = "", dry_run: bool = False
) -> None:
    """
    Summarize the converted markdown content using an LLM.

    Reads `<base_path>.md` and writes `<base_path>.summary.md`.

    :param base_path: base path (no extension) shared by the pdf/md/summary
        files
    :param model: LLM model name
        - Default: `""`, which uses the default model of `llm_cli.py`, an
          OpenRouter one
    :param dry_run: if True, show what would be done without executing
    """
    _LOG.debug(hprint.to_str("base_path model dry_run"))
    md_path = f"{base_path}.md"
    summary_path = f"{base_path}.summary.md"
    if not dry_run:
        hdbg.dassert_file_exists(md_path)
    _LOG.info("Summarizing markdown file: '%s'...", md_path)
    dshddut.summarize_text_with_llm(
        md_path,
        summary_path,
        dshddut.ARTICLE_SUMMARY_PROMPT,
        model=model,
        dry_run=dry_run,
    )
    if not dry_run:
        _LOG.info("Summary saved to: '%s'", summary_path)


# #############################################################################
# Save to papers dir action
# #############################################################################


def _save_to_papers_dir(
    base_path: str,
    papers_dir: str,
    *,
    no_incremental: bool = False,
    dry_run: bool = False,
) -> None:
    """
    Copy the PDF and the summary of a paper to the papers dir.

    Copies `<base_path>.pdf` and `<base_path>.summary.md` to
    `<papers_dir>/<base_name>.pdf` and `<papers_dir>/<base_name>.summary.md`.

    A missing summary (e.g., the `summarize` action was skipped) is not an
    error: only the PDF is copied, with a warning.

    :param base_path: base path (no extension) shared by the pdf/md/summary
        files
    :param papers_dir: dir to copy the files to (e.g.,
        `/Users/saggese/src/notes1/papers`)
    :param no_incremental: if True, overwrite existing files in the
        papers dir
    :param dry_run: if True, show what would be done without executing
    """
    _LOG.debug(hprint.to_str("base_path papers_dir no_incremental dry_run"))
    papers_dir = os.path.expanduser(papers_dir)
    pdf_path = f"{base_path}.pdf"
    summary_path = f"{base_path}.summary.md"
    # Select the files to copy. In a dry run nothing was generated yet, so
    # assume both files will exist.
    src_paths = [pdf_path, summary_path]
    if not dry_run:
        hdbg.dassert_file_exists(pdf_path)
        if not os.path.exists(summary_path):
            _LOG.warning(
                "Summary '%s' not found, saving only the PDF", summary_path
            )
            src_paths = [pdf_path]
        hio.create_dir(papers_dir, incremental=True)
    for src_path in src_paths:
        dst_path = os.path.join(papers_dir, os.path.basename(src_path))
        if dry_run:
            _LOG.warning("[DRY_RUN] Would copy '%s' to '%s'", src_path, dst_path)
        elif os.path.abspath(src_path) == os.path.abspath(dst_path):
            # Copying a file onto itself fails, and there is nothing to do.
            _LOG.info("File is already at '%s', nothing to copy", dst_path)
        elif os.path.exists(dst_path) and not no_incremental:
            _LOG.warning("File already exists, skipping: '%s'", dst_path)
        else:
            _LOG.info("Copying '%s' to '%s'", src_path, dst_path)
            shutil.copyfile(src_path, dst_path)
            _LOG.info("Saved to papers dir: '%s'", dst_path)


# #############################################################################
# CLI
# #############################################################################

# Available and default actions.
# `save_to_papers_dir` is opt-in: enable it with `--action save_to_papers_dir`.
_VALID_ACTIONS = ["download", "convert", "summarize", "save_to_papers_dir"]
_DEFAULT_ACTIONS = ["download", "convert", "summarize"]


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments.
    """
    _LOG.debug("Building the argument parser.")
    parser = argparse.ArgumentParser(
        formatter_class=hparser.CustomHelpFormatter,
        description=__doc__,
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help=(
            "URL to PDF paper, arXiv URL, SSRN URL (downloaded through "
            "Chrome), DOI (URL or bare DOI), or path to a local PDF file"
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help=(
            "Output base path (no extension), shared by the generated "
            "<output>.pdf, <output>.md, <output>.summary.md files. If not "
            "specified, a standardized name is derived from the paper's "
            "metadata (or from the file name, for a local PDF without an "
            "embedded title) and saved under $PAPERS_DIR (or the current "
            "directory if unset)"
        ),
    )
    parser.add_argument(
        "--model",
        default="",
        help=(
            "LLM model for the `summarize` action, e.g., "
            "`openrouter/anthropic/claude-haiku-4.5`. If not specified, the "
            "default model of `llm_cli.py` is used, an OpenRouter one (it "
            "needs the `OPENROUTER_KEY` env var)"
        ),
    )
    parser.add_argument(
        "--email",
        default="",
        help=(
            "Contact email sent to the Unpaywall API to find an open-access "
            "PDF for a DOI. If not specified, the Unpaywall lookup is skipped "
            "since Unpaywall rejects placeholder emails"
        ),
    )
    parser.add_argument(
        "--papers_dir",
        default=_DEFAULT_PAPERS_DIR,
        help=(
            "Dir where the `save_to_papers_dir` action copies the PDF and the "
            "summary (enable it with `--action save_to_papers_dir`). It is "
            "independent of $PAPERS_DIR, the dir where the files are "
            "generated"
        ),
    )
    parser.add_argument(
        "--no_incremental",
        action="store_true",
        help="Overwrite existing files instead of skipping",
    )
    parser.add_argument(
        "--skip_figures",
        action="store_true",
        help="Skip extracting figures/images when converting the PDF to markdown",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Dry run mode: show what would be done without actually executing actions",
    )
    hselacti.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    hparser.add_verbosity_arg(parser)
    _LOG.debug("return=parser")
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Execute the download paper script.
    """
    _LOG.debug(hprint.func_signature_to_str())
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Make a local input path absolute, so it does not depend on the current
    # directory and can be compared with the output path.
    input_arg = args.input
    if _is_local_file(input_arg):
        input_arg = os.path.abspath(os.path.expanduser(input_arg))
        hdbg.dassert(
            input_arg.lower().endswith(".pdf"),
            "A local input must be a PDF file: '%s'",
            input_arg,
        )
    # Determine the output base path.
    if args.output:
        base_path = args.output
        _LOG.debug("Using explicit --output base path: '%s'", base_path)
    else:
        output_dir = os.path.expanduser(os.getenv("PAPERS_DIR", "."))
        base_path = _get_output_base_path(
            input_arg, output_dir, email=args.email
        )
        _LOG.info(
            "No --output specified, using derived base path: '%s'", base_path
        )
    pdf_path = f"{base_path}.pdf"
    # Get selected actions.
    actions = hselacti.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    _LOG.info("Selected actions: %s", actions)
    if args.dry_run:
        _LOG.info("DRY RUN MODE: showing what would be done without executing")
    # Execute actions.
    while actions:
        action = actions[0]
        to_execute, actions = hselacti.mark_action(action, actions)
        if to_execute:
            if action == "download":
                _download(
                    input_arg,
                    pdf_path,
                    email=args.email,
                    log_level=args.log_level,
                    no_incremental=args.no_incremental,
                    dry_run=args.dry_run,
                )
            elif action == "convert":
                _convert(
                    pdf_path,
                    skip_figures=args.skip_figures,
                    dry_run=args.dry_run,
                )
            elif action == "summarize":
                _summarize(base_path, model=args.model, dry_run=args.dry_run)
            elif action == "save_to_papers_dir":
                _save_to_papers_dir(
                    base_path,
                    args.papers_dir,
                    no_incremental=args.no_incremental,
                    dry_run=args.dry_run,
                )
            else:
                raise ValueError("Invalid action='{action}'")


if __name__ == "__main__":
    parser = _parse()
    _main(parser)
