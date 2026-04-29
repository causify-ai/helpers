#!/usr/bin/env python3

"""
Crawl a running MkDocs server and report all broken links.

The script:
- starts from --base_url (default http://localhost:8002)
- follows every internal <a href> found on each page
- checks that each URL returns HTTP 2xx/3xx
- reports 4xx/5xx responses as broken
- also checks external links when --check_external is passed
- exits with code 1 if any broken links are found (CI-friendly)

Usage:
> check_mkdocs_links.py
> check_mkdocs_links.py --base_url http://localhost:8003
> check_mkdocs_links.py --check_external

Import as:

import helpers_root.docs_mkdocs.check_mkdocs_links as hrdmchli
"""

import argparse
import logging
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from html.parser import HTMLParser
from typing import List, Set, Tuple

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


# #############################################################################
# _LinkExtractor
# #############################################################################


class _LinkExtractor(HTMLParser):
    """
    Extract all href values from <a> tags in an HTML page.
    """

    def __init__(self) -> None:
        super().__init__()
        self.links: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str]]) -> None:
        if tag == "a":
            for attr, val in attrs:
                if attr == "href" and val:
                    self.links.append(val)


def _extract_links(html: str) -> List[str]:
    """
    Return all href values from HTML content.

    :param html: raw HTML string
    :return: list of href values
    """
    parser = _LinkExtractor()
    parser.feed(html)
    return parser.links


# #############################################################################
# Crawler
# #############################################################################


def _fetch(url: str, timeout: int = 15) -> Tuple[int, str]:
    """
    Fetch a URL and return (status_code, body).

    Returns (0, "") on connection error.

    :param url: URL to fetch
    :param timeout: socket timeout in seconds
    :return: (http_status, response_body)
    """
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (MkDocs Link Checker/1.0)"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.getcode(), body
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        _LOG.debug("Connection error fetching %s: %s", url, e)
        return 0, ""


def crawl(
    base_url: str,
    *,
    check_external: bool = False,
    timeout: int = 15,
) -> List[dict]:
    """
    Crawl the site starting from base_url and return broken links.

    :param base_url: root URL of the running MkDocs server
    :param check_external: if True, also check external links (HEAD
        request)
    :param timeout: per-request timeout in seconds
    :return: list of dicts with keys: page, link, status
    """
    base = base_url.rstrip("/")
    visited: Set[str] = set()
    # Queue holds (url_to_check, page_it_was_found_on).
    queue: deque = deque()
    queue.append((base + "/", base + "/"))
    broken = []
    ok_count = 0
    skip_count = 0
    while queue:
        url, referrer = queue.popleft()
        # Normalise: strip fragment.
        url = urllib.parse.urldefrag(url)[0]
        if url in visited:
            continue
        visited.add(url)
        is_internal = url.startswith(base)
        if not is_internal and not check_external:
            skip_count += 1
            continue
        _LOG.debug("Checking %s (from %s)", url, referrer)
        status, body = _fetch(url, timeout=timeout)
        if status == 0 or status >= 400:
            broken.append({"page": referrer, "link": url, "status": status})
            _LOG.warning("BROKEN [%s]  %s  (found on %s)", status, url, referrer)
        else:
            ok_count += 1
            _LOG.debug("OK [%s]  %s", status, url)
        # Only follow links on internal HTML pages.
        if is_internal and body:
            for href in _extract_links(body):
                # Skip anchors, mailto, javascript, etc.
                if not href or href.startswith(
                    ("#", "mailto:", "javascript:", "data:")
                ):
                    continue
                resolved = urllib.parse.urljoin(url, href)
                resolved = urllib.parse.urldefrag(resolved)[0]
                if resolved not in visited:
                    queue.append((resolved, url))
    _LOG.info(
        "Crawl done: %d ok, %d broken, %d skipped (external)",
        ok_count,
        len(broken),
        skip_count,
    )
    return broken


# #############################################################################
# CLI
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--base_url",
        default="http://localhost:8002",
        help="Root URL of the running MkDocs server (default: http://localhost:8002).",
    )
    parser.add_argument(
        "--check_external",
        action="store_true",
        default=False,
        help="Also check external HTTP/HTTPS links.",
    )
    parser.add_argument(
        "--cfile",
        default="tmp.check_mkdocs_links.cfile",
        help="Output file for broken links in vim cfile format.",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    _LOG.info("Crawling %s ...", args.base_url)
    broken = crawl(args.base_url, check_external=args.check_external)
    if broken:
        cfile_lines = []
        print("\nBROKEN LINKS:")
        print("-" * 70)
        for entry in broken:
            msg = f"[{entry['status']}] {entry['link']}"
            msg += f"\n       found on: {entry['page']}"
            print(msg)
            cfile_lines.append(
                f"{entry['page']}:0: [{entry['status']}] broken link: {entry['link']}"
            )
        print("-" * 70)
        print(f"\nTotal broken: {len(broken)}")
        hio.to_file(args.cfile, "\n".join(cfile_lines))
        _LOG.info("Wrote cfile to '%s'", args.cfile)
        sys.exit(1)
    else:
        print("All links OK.")


if __name__ == "__main__":
    _main(_parse())
