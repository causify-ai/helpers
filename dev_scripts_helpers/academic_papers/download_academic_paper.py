#!/usr/bin/env -S uv run

# /// script
# dependencies = ["feedparser", "pymupdf", "requests", "pyyaml"]
# ///

"""
Download academic papers from arXiv, DOI, and other sources with standardized
filenames.

# Download from arXiv URL
> download_academic_paper.py --input "https://arxiv.org/abs/1706.03762"

# Download from DOI URL
> download_academic_paper.py --input "https://doi.org/10.1038/nature12373"

# Download from bare DOI
> download_academic_paper.py --input "10.1038/nature12373"

# Download from generic PDF URL
> download_academic_paper.py --input "https://example.com/paper.pdf"

# Specify custom output directory
> download_academic_paper.py --input "https://arxiv.org/abs/1706.03762" --output_dir ./my_papers

# Overwrite existing files
> download_academic_paper.py --input "10.1038/nature12373" --no_incremental

Import as:

import download_academic_paper as dap
"""

# - Extracts metadata (year, authors, title) from arXiv API, CrossRef, or PDF
# - Formats filenames as: <year>.<FirstAuthorLastName>.[et_al.].<Title>.pdf
# - Checks if file already exists (skip unless --no_incremental)
# - Saves papers to $PAPERS_DIR (or ~/papers if not set)
#
# - Filename examples:
# - "2017.Vaswani.Attention_Is_All_You_Need.pdf"
# - "2019.Devlin.et_al.BERT_Pre-training_of_Deep_Bidirectional_Transformers.pdf"
# - "2020.Brown.et_al.Language_Models_are_Few-Shot_Learners.pdf"

import argparse
import logging
import os
import re
from typing import Any, Dict, List, Optional

import feedparser
import fitz
import requests

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hretry as hretry
import helpers.hstring as hstring

_LOG = logging.getLogger(__name__)

# API decorator configuration.
_MAX_RETRIES = 3
_RETRY_DELAY_SEC = 2
_API_TIMEOUT = 30


# #############################################################################
# ArXiv metadata
# #############################################################################


def _extract_arxiv_metadata(arxiv_id: str) -> Dict[str, Any]:
    """
    Extract metadata from arXiv API.

    :param arxiv_id: arXiv paper ID (e.g., "1706.03762")
    :return: dict with 'year', 'authors', 'title' keys
    """
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
    return {"year": year, "authors": authors, "title": title}


def _detect_arxiv_id(url: str) -> Optional[str]:
    """
    Detect arXiv ID from URL.

    :param url: input URL
    :return: arXiv ID if detected, None otherwise
    """
    _ARXIV_ID_PATTERN = r"(?:arxiv\.org/(?:abs|pdf)/)?(\d{4}\.\d{4,5})"
    match = re.search(_ARXIV_ID_PATTERN, url)
    return match.group(1) if match else None


# #############################################################################
# DOI metadata
# #############################################################################


def _detect_doi(url: str) -> Optional[str]:
    """
    Detect DOI from URL or bare DOI string.

    :param url: URL or bare DOI (e.g., "https://doi.org/10.xxx" or "10.xxx/yyy")
    :return: DOI if detected, None otherwise
    """
    _DOI_URL_PATTERN = r"(?:https?://)?(?:dx\.)?doi\.org/(.+)"
    _DOI_BARE_PATTERN = r"^(10\.\d{4,}/\S+)$"
    # Try URL pattern.
    match = re.search(_DOI_URL_PATTERN, url)
    if match:
        return match.group(1)
    # Try bare DOI pattern.
    match = re.search(_DOI_BARE_PATTERN, url)
    if match:
        return match.group(1)
    return None


@hretry.sync_retry(
    num_attempts=_MAX_RETRIES,
    exceptions=(requests.RequestException,),
    retry_delay_in_sec=_RETRY_DELAY_SEC,
)
def _crossref_query(doi: str) -> Dict[str, Any]:
    """
    Query CrossRef API for paper metadata.

    :param doi: DOI string
    :return: API response as dict
    """
    _CROSSREF_API = "https://api.crossref.org/works"
    url = f"{_CROSSREF_API}/{doi}"
    _LOG.debug("Querying CrossRef API: %s", url)
    resp = requests.get(url, timeout=_API_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


@hretry.sync_retry(
    num_attempts=_MAX_RETRIES,
    exceptions=(requests.RequestException,),
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
    _UNPAYWALL_API = "https://api.unpaywall.org/v2"
    url = f"{_UNPAYWALL_API}/{doi}"
    params = {"email": email}
    _LOG.debug("Querying Unpaywall API: %s", url)
    resp = requests.get(url, params=params, timeout=_API_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def _resolve_doi_metadata(doi: str) -> Dict[str, Any]:
    """
    Resolve DOI to paper metadata.

    :param doi: DOI string
    :return: dict with 'year', 'authors', 'title', 'pdf_url' keys
    """
    _LOG.info("Resolving DOI='%s'", doi)
    # Query CrossRef for metadata.
    cr_data = _crossref_query(doi)
    message = cr_data.get("message", {})
    title = (
        message.get("title", [""])[0]
        if isinstance(message.get("title"), list)
        else message.get("title", "")
    )
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
    return {
        "year": str(year),
        "authors": authors,
        "title": title,
        "pdf_url": pdf_url,
    }


# #############################################################################
# Non-arXiv metadata
# #############################################################################


def _extract_pdf_metadata_pymupdf(pdf_path: str) -> Dict[str, Any]:
    """
    Extract metadata from PDF using pymupdf.

    :param pdf_path: path to PDF file
    :return: dict with 'year', 'authors', 'title' keys
    """
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
        text = first_page.get_text("text")
        # Look for year pattern (1900-2099).
        year_match = re.search(r"\b(19|20)\d{2}\b", text)
        year = year_match.group(0) if year_match else None
    doc.close()
    return {
        "year": year,
        "authors": authors,
        "title": title,
    }


# #############################################################################
# Filename formatting
# #############################################################################


def _format_filename(
    year: Optional[str], authors: List[str], title: Optional[str]
) -> str:
    """
    Format filename according to spec with bash-safe formatting (spaces → underscores).

    Format: <year>.<First_author_last_name>.[et_al.].<Title>

    :param year: publication year
    :param authors: list of author names
    :param title: paper title
    :return: formatted filename with underscores instead of spaces
    """
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
    filename = ".".join(parts)
    # Remove invalid characters and replace spaces with underscores.
    filename = re.sub(r'[<>:"/\\|?*]', "", filename)
    filename = re.sub(r"\s+", "_", filename)
    filename = f"{filename}.pdf"
    return filename


# #############################################################################
# Download and save
# #############################################################################


def _download_paper(
    url: str, output_dir: str, *, no_incremental: bool = False
) -> None:
    """
    Download academic paper and save with standardized filename.

    :param url: URL to PDF, arXiv URL, or DOI
    :param output_dir: directory to save PDF
    :param no_incremental: if True, overwrite existing files
    """
    _DOWNLOAD_TIMEOUT = 300
    _LOG.info("Processing URL: %s", url)
    # Check if output directory exists.
    hdbg.dassert_dir_exists(
        output_dir, "Output directory does not exist: %s", output_dir
    )
    # Detect DOI.
    doi = _detect_doi(url)
    arxiv_id = None
    pdf_content = None
    pdf_url = None
    if doi:
        _LOG.debug("Detected DOI: %s", doi)
        metadata = _resolve_doi_metadata(doi)
        pdf_url = metadata.pop("pdf_url")
    else:
        # Detect arXiv paper.
        arxiv_id = _detect_arxiv_id(url)
        if arxiv_id:
            _LOG.debug("Detected arXiv paper with ID: %s", arxiv_id)
            metadata = _extract_arxiv_metadata(arxiv_id)
        else:
            _LOG.debug("Non-arXiv paper, downloading and extracting metadata")
            # Download PDF once for both extraction and saving.
            _LOG.debug("Downloading PDF from URL")
            response = requests.get(url, timeout=_DOWNLOAD_TIMEOUT)
            response.raise_for_status()
            pdf_content = response.content
            # Extract metadata from PDF.
            tmp_path = "tmp.download_academic_paper.metadata.pdf"
            with open(tmp_path, "wb") as f:
                f.write(pdf_content)
            metadata = _extract_pdf_metadata_pymupdf(tmp_path)
    # Format filename.
    authors = metadata.get("authors", [])
    if not isinstance(authors, list):
        authors = [authors] if authors else []
    year = metadata.get("year")
    title = metadata.get("title")
    filename = _format_filename(
        year,
        authors,
        title,
    )
    output_path = os.path.join(output_dir, filename)
    # Check if file already exists.
    if os.path.exists(output_path) and not no_incremental:
        _LOG.info("File already exists, skipping: %s", output_path)
        return
    # Download PDF if not already downloaded.
    if not pdf_content:
        # Determine PDF URL.
        if pdf_url:
            download_url = pdf_url
        elif arxiv_id:
            download_url = f"http://arxiv.org/pdf/{arxiv_id}.pdf"
        else:
            download_url = url
        _LOG.debug("Downloading PDF from URL: %s", download_url)
        response = requests.get(download_url, timeout=_DOWNLOAD_TIMEOUT)
        response.raise_for_status()
        pdf_content = response.content
    # Save PDF.
    _LOG.info("Saving PDF to: %s", output_path)
    with open(output_path, "wb") as f:
        f.write(pdf_content)
    _LOG.info("Successfully downloaded and saved: %s", filename)


# #############################################################################
# Main
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments.
    """
    _DEFAULT_OUTPUT_DIR = os.path.expanduser(os.getenv("PAPERS_DIR", "."))
    parser = argparse.ArgumentParser(
        description="Download academic papers with standardized filenames"
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="URL to PDF paper, arXiv URL, or DOI (URL or bare DOI)",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        default=_DEFAULT_OUTPUT_DIR,
        help="Output directory",
    )
    parser.add_argument(
        "--no_incremental",
        action="store_true",
        help="Overwrite existing files instead of skipping",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Execute the download paper script.
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    _download_paper(
        args.input,
        args.output_dir,
        no_incremental=args.no_incremental,
    )


if __name__ == "__main__":
    parser = _parse()
    _main(parser)
