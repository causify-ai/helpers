#!/usr/bin/env -S uv run

# /// script
# dependencies = ["feedparser", "pymupdf", "requests", "pyyaml", "beautifulsoup4", "tqdm"]
# ///

"""
- Download academic papers from arXiv, DOI, and other sources
- Save the paper with a standardized base name, e.g.,
    `2016.Ribeiro_et_al.Why_Should_I_Trust_You_Explaining_the_Predictions_of_Any_Classifier`
- Convert them to Markdown
- Summarize the markdown text

- The output file name is shared across the `.pdf`, `.md`, and `.summary.md` outputs

# Examples
```
# Download from arXiv URL (runs download, convert, summarize by default)
> download_academic_paper_to_md.py --input "https://arxiv.org/abs/1706.03762"

# Download from DOI URL
> download_academic_paper_to_md.py --input "https://doi.org/10.1038/nature12373"

# Download from bare DOI
> download_academic_paper_to_md.py --input "10.1038/nature12373"

# Download from generic PDF URL
> download_academic_paper_to_md.py --input "https://example.com/paper.pdf"

# Save under a custom directory when --output is not passed, via $PAPERS_DIR
> PAPERS_DIR=./my_papers download_academic_paper_to_md.py --input "https://arxiv.org/abs/1706.03762"

# Specify an explicit output base name (produces mypaper.pdf, mypaper.md, ...)
> download_academic_paper_to_md.py --input "https://arxiv.org/abs/1706.03762" --output ./my_papers/mypaper

# Overwrite existing files
> download_academic_paper_to_md.py --input "10.1038/nature12373" --no_incremental

# Only download and convert, skip summarization
> download_academic_paper_to_md.py --input "10.1038/nature12373" -sa summarize
```

Import as:

import dev_scripts_helpers.download.download_academic_paper_to_md as dsdapt
"""

import argparse
import logging
import os
import re
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
import dev_scripts_helpers.download.download_utils as dsdlut

_LOG = logging.getLogger(__name__)

# API decorator configuration.
_RETRY_DELAY_SEC = 2
_API_TIMEOUT = 30
_DOWNLOAD_TIMEOUT = 300

# - Extracts metadata (year, authors, title) from arXiv API, CrossRef, or PDF
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


def _extract_arxiv_metadata(arxiv_id: str) -> Dict[str, Any]:
    """
    Extract metadata from arXiv API.

    :param arxiv_id: arXiv paper ID (e.g., "1706.03762")
    :return: dict with 'year', 'authors', 'title' keys
    """
    _LOG.debug(hprint.to_str("arxiv_id"))
    _ARXIV_API_URL = "http://export.arxiv.org/api/query?id_list={arxiv_id}"
    _LOG.debug("Extracting metadata from arXiv for ID: %s", arxiv_id)
    url = _ARXIV_API_URL.format(arxiv_id=arxiv_id)
    feed = feedparser.parse(url)
    hdbg.dassert(feed.entries, "No entries found for arXiv ID: %s", arxiv_id)
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


def detect_doi(url: str) -> Optional[str]:
    """
    Detect DOI from URL or bare DOI string.

    :param url: URL or bare DOI (e.g., "https://doi.org/10.xxx" or "10.xxx/yyy")
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
def _unpaywall_query(
    doi: str, *, email: str = "user@example.com"
) -> Dict[str, Any]:
    """
    Query Unpaywall API for open access PDF URL.

    :param doi: DOI string
    :param email: email for API (Unpaywall requests valid email)
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


def _resolve_doi_metadata(doi: str) -> Dict[str, Any]:
    """
    Resolve DOI to paper metadata.

    :param doi: DOI string
    :return: dict with 'year', 'authors', 'title', 'pdf_url' keys
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
    # Query Unpaywall for PDF URL.
    pdf_url = None
    uw_data = _unpaywall_query(doi)
    if uw_data.get("is_oa"):
        pdf_url = uw_data.get("best_oa_location", {}).get("url")
    metadata = {
        "year": str(year),
        "authors": authors,
        "title": title,
        "pdf_url": pdf_url,
    }
    _LOG.debug(hprint.to_str("metadata"))
    return metadata


# #############################################################################
# Non-arXiv metadata
# #############################################################################


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
        # Split by common delimiters.
        authors = [a.strip() for a in re.split(r"[,;and]", author_str)]
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
    url: str,
) -> Tuple[Dict[str, Any], Optional[bytes], Optional[str]]:
    """
    Resolve paper metadata for a URL.

    For generic (non-arXiv, non-DOI) PDF URLs, the PDF is downloaded as a
    side effect since there is no metadata API to query; the downloaded
    bytes are returned so callers can reuse them instead of downloading
    twice.

    :param url: URL to PDF, arXiv URL, or DOI
    :return: tuple of (metadata dict with 'year'/'authors'/'title', PDF
        content if already downloaded else None, resolved PDF URL to
        download from if known)
    """
    _LOG.debug(hprint.to_str("url"))
    _LOG.info("Resolving metadata for: %s", url)
    # Try to resolve via DOI first, then arXiv ID, falling back to
    # downloading the raw PDF and extracting metadata locally.
    doi = detect_doi(url)
    pdf_content = None
    pdf_url = None
    if doi:
        _LOG.debug("Detected DOI: %s", doi)
        metadata = _resolve_doi_metadata(doi)
        pdf_url = metadata.pop("pdf_url")
    else:
        arxiv_id = _detect_arxiv_id(url)
        if arxiv_id:
            _LOG.debug("Detected arXiv paper with ID: %s", arxiv_id)
            metadata = _extract_arxiv_metadata(arxiv_id)
            pdf_url = f"http://arxiv.org/pdf/{arxiv_id}.pdf"
        else:
            _LOG.debug("Non-arXiv paper, downloading and extracting metadata")
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


def _get_output_base_path(input_url: str, output_dir: str) -> str:
    """
    Derive the output base path (no extension) from the paper's metadata.

    :param input_url: URL to PDF, arXiv URL, or DOI
    :param output_dir: directory to save the base path under
    :return: base path, e.g. `<output_dir>/2017.Vaswani.Attention_Is_All_You_Need`
    """
    _LOG.debug(hprint.to_str("input_url output_dir"))
    metadata, _, _ = _resolve_metadata_and_content(input_url)
    # Normalize authors to a list since metadata may store a single string.
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


def _download(
    url: str,
    pdf_path: str,
    *,
    no_incremental: bool = False,
) -> None:
    """
    Download the PDF for `url` and save it to `pdf_path`.

    :param url: URL to PDF, arXiv URL, or DOI
    :param pdf_path: path to save the PDF to
    :param no_incremental: if True, overwrite existing files
    """
    _LOG.debug(hprint.to_str("url pdf_path no_incremental"))
    if os.path.exists(pdf_path) and not no_incremental:
        _LOG.info("PDF already exists, skipping: %s", pdf_path)
        return
    _, pdf_content, pdf_url = _resolve_metadata_and_content(url)
    # Download the PDF now if metadata resolution did not already fetch it
    # (the DOI/arXiv branches only resolve a URL, not the content).
    if pdf_content is None:
        download_url = pdf_url or url
        _LOG.debug("Downloading PDF from URL: %s", download_url)
        response = requests.get(download_url, timeout=_DOWNLOAD_TIMEOUT)
        response.raise_for_status()
        pdf_content = response.content
    # Save PDF.
    pdf_dir = os.path.dirname(pdf_path) or "."
    hio.create_dir(pdf_dir, incremental=True)
    _LOG.info("Saving PDF to: %s", pdf_path)
    with open(pdf_path, "wb") as f:
        f.write(pdf_content)
    _LOG.info("Successfully downloaded and saved: %s", pdf_path)


# #############################################################################
# Convert action
# #############################################################################


def _convert(pdf_path: str) -> None:
    """
    Convert the PDF to Markdown using `convert_pdf_to_md.py`.

    Writes `<pdf_stem>.md` next to `pdf_path`, i.e. `<base_path>.md`.

    :param pdf_path: path to the PDF file to convert
    """
    _LOG.debug(hprint.to_str("pdf_path"))
    hdbg.dassert_file_exists(pdf_path)
    _LOG.info("Converting PDF to markdown: %s", pdf_path)
    script_path = hgit.find_file_in_git_tree("convert_pdf_to_md.py")
    output_dir = os.path.dirname(pdf_path) or "."
    cmd = (
        f"{script_path} --input {pdf_path} --output {output_dir} --overwrite"
    )
    _LOG.debug("Running command: %s", cmd)
    hsystem.system(cmd)


# #############################################################################
# Summarize action
# #############################################################################


def _summarize(base_path: str) -> None:
    """
    Summarize the converted markdown content using an LLM.

    Reads `<base_path>.md` and writes `<base_path>.summary.md`.

    :param base_path: base path (no extension) shared by the pdf/md/summary
        files
    """
    _LOG.debug(hprint.to_str("base_path"))
    md_path = f"{base_path}.md"
    summary_path = f"{base_path}.summary.md"
    hdbg.dassert_file_exists(md_path)
    _LOG.info("Summarizing markdown file: '%s'...", md_path)
    dsdlut.summarize_text_with_llm(
        md_path,
        summary_path,
        dsdlut.ARTICLE_SUMMARY_PROMPT,
    )
    _LOG.info("Summary saved to: '%s'", summary_path)


# #############################################################################
# CLI
# #############################################################################

# Available and default actions.
_VALID_ACTIONS = ["download", "convert", "summarize"]
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
        help="URL to PDF paper, arXiv URL, or DOI (URL or bare DOI)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help=(
            "Output base path (no extension), shared by the generated "
            "<output>.pdf, <output>.md, <output>.summary.md files. If not "
            "specified, a standardized name is derived from the paper's "
            "metadata and saved under $PAPERS_DIR (or the current directory "
            "if unset)"
        ),
    )
    parser.add_argument(
        "--no_incremental",
        action="store_true",
        help="Overwrite existing files instead of skipping",
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
    # Determine the output base path.
    if args.output:
        base_path = args.output
        _LOG.debug("Using explicit --output base path: '%s'", base_path)
    else:
        output_dir = os.path.expanduser(os.getenv("PAPERS_DIR", "."))
        base_path = _get_output_base_path(args.input, output_dir)
        _LOG.info(
            "No --output specified, using derived base path: '%s'", base_path
        )
    pdf_path = f"{base_path}.pdf"
    # Get selected actions.
    actions = hselacti.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    _LOG.info("Selected actions: %s", actions)
    # Execute actions.
    while actions:
        action = actions[0]
        to_execute, actions = hselacti.mark_action(action, actions)
        if to_execute:
            if action == "download":
                _download(
                    args.input, pdf_path, no_incremental=args.no_incremental
                )
            elif action == "convert":
                _convert(pdf_path)
            elif action == "summarize":
                _summarize(base_path)
            else:
                raise ValueError("Invalid action='{action}'")


if __name__ == "__main__":
    parser = _parse()
    _main(parser)
