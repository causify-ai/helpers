#!/usr/bin/env -S uv run

# /// script
# dependencies = ["arxiv", "requests", "pyyaml", "pandas", "numpy", "tqdm"]
# ///

"""
Fetch and download academic papers from arXiv, Unpaywall (via DOI), and optionally LibGen.

Examples:

# Search arXiv and download papers
python retrieve_academic_paper.py --query "causal inference" --max_results 5 --output_dir ./papers

# Fetch specific arXiv paper
python retrieve_academic_paper.py --arxiv_id 2109.11415 --metadata_only

# Resolve DOI and fetch metadata
python retrieve_academic_paper.py --doi "10.1038/nature12373" --metadata_only

# Batch fetch from file
python retrieve_academic_paper.py --file paper_ids.txt --output_dir ./papers

Import as:

import retrieve_academic_paper as retacpap
"""

import argparse
import dataclasses
import logging
import os
from typing import List, Optional, Dict, Any

import requests

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hretry as hretry

_LOG = logging.getLogger(__name__)

# #############################################################################
# Constants
# #############################################################################

API_TIMEOUT = 30
DOWNLOAD_TIMEOUT = 300
CROSSREF_API = "https://api.crossref.org/works"
UNPAYWALL_API = "https://api.unpaywall.org/v2"
MAX_RETRIES = 3
RETRY_DELAY_SEC = 2


# #############################################################################
# Paper Metadata
# #############################################################################


@dataclasses.dataclass
class Paper:
    """
    Metadata for an academic paper.
    """

    title: str
    authors: List[str]
    year: int
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    pdf_url: Optional[str] = None
    source: str = "unknown"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert paper to dictionary.
        """
        return dataclasses.asdict(self)


# #############################################################################
# arXiv Client
# #############################################################################


def _arxiv_search(query: str, *, max_results: int = 10) -> List[Paper]:
    """
    Search arXiv for papers matching query.

    :param query: search query
    :param max_results: maximum number of results
    :return: list of Paper objects
    """
    try:
        import arxiv
    except ImportError:
        hdbg.dfatal(
            "arxiv library not installed; run: pip install arxiv"
        )
    _LOG.info("Searching arXiv for query='%s'", query)
    papers = []
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )
    for result in client.results(search):
        author_names = [author.name for author in result.authors]
        paper = Paper(
            title=result.title,
            authors=author_names,
            year=result.published.year,
            arxiv_id=result.entry_id.split("/abs/")[-1],
            pdf_url=result.pdf_url,
            source="arxiv",
        )
        papers.append(paper)
    _LOG.info("Found %d papers from arXiv", len(papers))
    return papers


def _arxiv_get_by_id(arxiv_id: str) -> Paper:
    """
    Fetch a specific arXiv paper by ID.

    :param arxiv_id: arXiv ID (e.g., "2301.00001")
    :return: Paper object
    """
    try:
        import arxiv
    except ImportError:
        hdbg.dfatal(
            "arxiv library not installed; run: pip install arxiv"
        )
    _LOG.info("Fetching arXiv paper with ID='%s'", arxiv_id)
    client = arxiv.Client()
    search = arxiv.Search(id_list=[arxiv_id])
    try:
        result = next(client.results(search))
    except StopIteration:
        hdbg.dfatal(f"arXiv paper not found: {arxiv_id}")
    except Exception as e:
        hdbg.dfatal(f"Failed to fetch arXiv paper: {e}")
    author_names = [author.name for author in result.authors]
    paper = Paper(
        title=result.title,
        authors=author_names,
        year=result.published.year,
        arxiv_id=result.entry_id.split("/abs/")[-1],
        pdf_url=result.pdf_url,
        source="arxiv",
    )
    return paper


# #############################################################################
# DOI Client
# #############################################################################


@hretry.sync_retry(
    num_attempts=MAX_RETRIES,
    exceptions=(requests.RequestException,),
    retry_delay_in_sec=RETRY_DELAY_SEC,
)
def _crossref_query(doi: str) -> Dict[str, Any]:
    """
    Query CrossRef API for paper metadata.

    :param doi: DOI string
    :return: API response as dict
    """
    url = f"{CROSSREF_API}/{doi}"
    _LOG.debug("Querying CrossRef API: %s", url)
    resp = requests.get(url, timeout=API_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


@hretry.sync_retry(
    num_attempts=MAX_RETRIES,
    exceptions=(requests.RequestException,),
    retry_delay_in_sec=RETRY_DELAY_SEC,
)
def _unpaywall_query(doi: str, email: str) -> Dict[str, Any]:
    """
    Query Unpaywall API for open access PDF URL.

    :param doi: DOI string
    :param email: email for API (Unpaywall requests valid email)
    :return: API response as dict
    """
    url = f"{UNPAYWALL_API}/{doi}"
    params = {"email": email}
    _LOG.debug("Querying Unpaywall API: %s", url)
    resp = requests.get(url, params=params, timeout=API_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def _resolve_doi(doi: str, *, email: str = "user@example.com") -> Paper:
    """
    Resolve DOI to paper metadata.

    :param doi: DOI string
    :param email: email for Unpaywall API
    :return: Paper object
    """
    _LOG.info("Resolving DOI='%s'", doi)
    # Query CrossRef for metadata.
    cr_data = _crossref_query(doi)
    message = cr_data.get("message", {})
    title = message.get("title", [""])[0] if isinstance(
        message.get("title"), list
    ) else message.get("title", "")
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
    try:
        uw_data = _unpaywall_query(doi, email=email)
        if uw_data.get("is_oa"):
            pdf_url = uw_data.get("best_oa_location", {}).get("url")
    except Exception as e:
        _LOG.warning("Unpaywall query failed: %s", e)
    paper = Paper(
        title=title,
        authors=authors,
        year=year,
        doi=doi,
        pdf_url=pdf_url,
        source="doi",
    )
    return paper


# #############################################################################
# Downloader
# #############################################################################


def _safe_filename(paper: Paper) -> str:
    """
    Generate safe filename from paper metadata.

    :param paper: Paper object
    :return: safe filename (e.g., "Author_2020_Title.pdf")
    """
    author = paper.authors[0] if paper.authors else "Unknown"
    author = author.split()[-1]
    title = paper.title[:40]
    filename = f"{author}_{paper.year}_{title}.pdf"
    filename = hio.purify_file_name(filename)
    return filename


@hretry.sync_retry(
    num_attempts=MAX_RETRIES,
    exceptions=(requests.RequestException,),
    retry_delay_in_sec=RETRY_DELAY_SEC,
)
def _download_pdf_url(url: str, output_path: str) -> None:
    """
    Download PDF from URL to file.

    :param url: PDF URL
    :param output_path: output file path
    """
    _LOG.info("Downloading PDF from %s", url)
    with requests.get(
        url, stream=True, timeout=DOWNLOAD_TIMEOUT
    ) as resp:
        resp.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 512):
                if chunk:
                    f.write(chunk)
    _LOG.info("Saved PDF to %s", output_path)


def _download_paper(
    paper: Paper, output_dir: str
) -> Optional[str]:
    """
    Download PDF for a paper.

    :param paper: Paper object
    :param output_dir: output directory
    :return: output file path if successful, None otherwise
    """
    if not paper.pdf_url:
        _LOG.warning("No PDF URL for paper: %s", paper.title)
        return None
    filename = _safe_filename(paper)
    output_path = os.path.join(output_dir, filename)
    if os.path.exists(output_path):
        _LOG.info("File already exists: %s", output_path)
        return output_path
    try:
        _download_pdf_url(paper.pdf_url, output_path)
        return output_path
    except Exception as e:
        _LOG.error("Failed to download paper: %s", e)
        return None


def _save_metadata(papers: List[Paper], output_dir: str) -> None:
    """
    Save paper metadata to JSON file.

    :param papers: list of Paper objects
    :param output_dir: output directory
    """
    metadata = [paper.to_dict() for paper in papers]
    metadata_file = os.path.join(output_dir, "metadata.json")
    hio.to_json(metadata_file, metadata)
    _LOG.info("Saved metadata to %s", metadata_file)


# #############################################################################
# LibGen Client (Optional)
# #############################################################################


def _libgen_search(query: str) -> Optional[str]:
    """
    Search LibGen for paper (optional fallback).

    :param query: search query (title or DOI)
    :return: mirror URL if found, None otherwise
    """
    _LOG.debug("LibGen search not yet implemented (disabled by default)")
    return None


# #############################################################################
# Input Handler
# #############################################################################


def _detect_input_type(
    query: Optional[str],
    doi: Optional[str],
    arxiv_id: Optional[str],
    file: Optional[str],
) -> str:
    """
    Detect input type from arguments.

    :param query: search query
    :param doi: DOI string
    :param arxiv_id: arXiv ID
    :param file: input file path
    :return: input type string
    """
    if query:
        return "query"
    if doi:
        return "doi"
    if arxiv_id:
        return "arxiv"
    if file:
        return "file"
    hdbg.dfatal("No input provided; use --query, --doi, --arxiv-id, or --file")


def _process_input(
    input_type: str,
    query: Optional[str],
    doi: Optional[str],
    arxiv_id: Optional[str],
    file: Optional[str],
    max_results: int,
) -> List[Paper]:
    """
    Process input and fetch papers.

    :param input_type: type of input
    :param query: search query
    :param doi: DOI string
    :param arxiv_id: arXiv ID
    :param file: input file path
    :param max_results: max results for search
    :return: list of Paper objects
    """
    papers = []
    if input_type == "query":
        papers = _arxiv_search(query, max_results=max_results)
    elif input_type == "doi":
        papers = [_resolve_doi(doi)]
    elif input_type == "arxiv":
        papers = [_arxiv_get_by_id(arxiv_id)]
    elif input_type == "file":
        lines = hio.from_file(file).strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("10."):
                papers.append(_resolve_doi(line))
            else:
                papers.append(_arxiv_get_by_id(line))
    return papers


# #############################################################################
# CLI
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    """
    Parse command line arguments.

    :return: argument parser
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Search query for arXiv",
    )
    parser.add_argument(
        "--doi",
        type=str,
        default=None,
        help="DOI to resolve",
    )
    parser.add_argument(
        "--arxiv_id",
        type=str,
        default=None,
        help="arXiv ID (e.g., 2109.11415)",
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Input file with DOIs or arXiv IDs (one per line)",
    )
    parser.add_argument(
        "--max_results",
        type=int,
        default=10,
        help="Max results for search (default: 10)",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./papers",
        help="Output directory for PDFs (default: ./papers)",
    )
    parser.add_argument(
        "--libgen",
        action="store_true",
        help="Enable LibGen fallback (disabled by default)",
    )
    parser.add_argument(
        "--metadata_only",
        action="store_true",
        help="Fetch metadata only, do not download PDFs",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main entry point.

    :param parser: argument parser
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    _LOG.info("Starting retrieve_academic_paper")
    # Detect input type.
    input_type = _detect_input_type(
        args.query, args.doi, args.arxiv_id, args.file
    )
    _LOG.info("Input type: %s", input_type)
    # Fetch papers.
    papers = _process_input(
        input_type,
        args.query,
        args.doi,
        args.arxiv_id,
        args.file,
        args.max_results,
    )
    _LOG.info("Fetched %d papers", len(papers))
    # Download PDFs if not metadata_only.
    if not args.metadata_only:
        hio.create_dir(args.output_dir, incremental=True)
        for paper in papers:
            _download_paper(paper, args.output_dir)
    # Save metadata.
    if not args.metadata_only:
        _save_metadata(papers, args.output_dir)
    else:
        _LOG.info("Metadata-only mode; not saving to file")
        for paper in papers:
            _LOG.info(
                "Paper: title=%s, authors=%s, year=%d, source=%s",
                paper.title,
                ", ".join(paper.authors[:2]),
                paper.year,
                paper.source,
            )
    _LOG.info("Done")


if __name__ == "__main__":
    _main(_parse())
