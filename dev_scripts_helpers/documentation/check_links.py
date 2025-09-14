#!/usr/bin/env python3

"""
Check if all URL links in a file are reachable.

The script:
- processes the input file (e.g., Markdown, text files).
- extracts URLs in various formats like:
  - [text](https://example.com).
  - [display text](https://example.com).
  - https://example.com.
- checks if each URL is reachable via HTTP/HTTPS request.
- outputs a list of all URLs found and their reachability status.
- prints the count of broken URLs.

# Check links in a Markdown file:
> check_links.py --in_file README.md

# Check links in a text file with verbose output:
> check_links.py --in_file docs.txt -v DEBUG

Import as:

import dev_scripts_helpers.documentation.check_links as dsdocheli
"""

import argparse
import logging
import re
import urllib.error
import urllib.request
from typing import List, Tuple

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hmarkdown as hmarkdo
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


def _get_git_repo_info() -> Tuple[str, str]:
    """
    Get git repository URL and current branch name.

    :return: tuple of (repo_url, branch_name)
    """
    try:
        # Get current branch name using hgit function.
        branch_name = hgit.get_branch_name(".")
        # Get repository full name and convert to GitHub URL.
        repo_full_name = hgit.get_repo_full_name_from_dirname(
            ".", include_host_name=True
        )
        if repo_full_name.startswith("github.com/"):
            repo_url = f"https://{repo_full_name}"
        else:
            repo_url = f"https://github.com/{repo_full_name}"
        return repo_url, branch_name
    except Exception as e:
        _LOG.warning("Failed to get git repo info: %s", str(e))
        return "", ""


def _convert_local_path_to_url(
    file_path: str, repo_url: str, branch_name: str
) -> str:
    """
    Convert a local file path to a GitHub URL.

    :param file_path: local file path (e.g.,
    "/tutorial_template/README.md") :param repo_url: repository URL
    (e.g., "
    https://github.com/user/repo")
    :param file_path: local file path (e.g.,
        "/tutorial_template/README.md")
    :param repo_url: repository URL (e.g.,
        "https://github.com/user/repo")
    :param branch_name: branch name (e.g., "master")
    :return: GitHub URL for the file
    """
    # Remove leading slash if present.
    if file_path.startswith("/"):
        file_path = file_path[1:]
    return f"{repo_url}/blob/{branch_name}/{file_path}"


def _extract_urls_from_text_with_original_line_numbers(
    original_text: str, filtered_text: str
) -> List[Tuple[str, int]]:
    """
    Extract URLs from filtered text but return line numbers from original text.

    Convert local repository file paths to GitHub URLs.
    :param original_text: original text before any filtering
    :param filtered_text: text after TOC removal
    :return: list of tuples (url, original_line_number) found
    """
    urls = []
    original_lines = original_text.split("\n")
    filtered_lines = filtered_text.split("\n")
    url_set = set()
    # Get git repository information for local path conversion.
    repo_url, branch_name = _get_git_repo_info()
    # Create mapping from filtered line content to original line numbers.
    line_mapping = {}
    original_idx = 0
    for filtered_idx, filtered_line in enumerate(filtered_lines):
        # Find this line in the original text.
        while original_idx < len(original_lines):
            if original_lines[original_idx] == filtered_line:
                line_mapping[filtered_idx] = original_idx + 1  # 1-indexed
                original_idx += 1
                break
            original_idx += 1
    for filtered_line_num, line in enumerate(filtered_lines):
        original_line_num = line_mapping.get(
            filtered_line_num, filtered_line_num + 1
        )
        # Pattern for Markdown links: [text](url).
        markdown_pattern = r"\[([^\]]*)\]\(([^)]+)\)"
        matches = re.findall(markdown_pattern, line)
        for _, url in matches:
            url = url.strip()
            # Convert local file paths to GitHub URLs if in a git repo.
            if url.startswith("/") and repo_url and branch_name:
                # Check if it looks like a file path (has file extension or common dirs).
                if "." in url.split("/")[-1] or any(
                    part in url
                    for part in ["tutorial_template", "docs", "src", "helpers"]
                ):
                    url = _convert_local_path_to_url(url, repo_url, branch_name)
            if url not in url_set:
                urls.append((url, original_line_num))
                url_set.add(url)
        # Pattern for standalone URLs.
        url_pattern = r'https?://[^\s<>"\[\]{}|\\^`()]+(?=[\s\)]|$)'
        matches = re.findall(url_pattern, line)
        for url in matches:
            url = url.strip()
            if url not in url_set:
                urls.append((url, original_line_num))
                url_set.add(url)
        # Pattern for standalone local file paths.
        if repo_url and branch_name:
            local_path_pattern = r"(/[a-zA-Z0-9_/.-]+\.[a-zA-Z0-9]+(?:\s|$))"
            matches = re.findall(local_path_pattern, line)
            for match in matches:
                file_path = match.strip()
                if file_path not in url_set:
                    url = _convert_local_path_to_url(
                        file_path, repo_url, branch_name
                    )
                    urls.append((url, original_line_num))
                    url_set.add(file_path)
    return urls


def _check_url_reachable(url: str) -> bool:
    """
    Check if a URL is reachable via HTTP/HTTPS request.

    :param url: URL to check
    :return: True if URL is reachable, False otherwise
    """
    try:
        # Create request with a user agent to avoid blocking.
        request = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0 (Link Checker)"}
        )
        # Set timeout to 10 seconds.
        with urllib.request.urlopen(request, timeout=10) as response:
            # Check if status code indicates success.
            return response.getcode() < 400
    except (urllib.error.URLError, urllib.error.HTTPError, Exception) as e:
        _LOG.debug("URL %s failed: %s", url, str(e))
        return False


def _check_links_in_file(
    input_file: str,
) -> Tuple[List[str], List[Tuple[str, int]]]:
    """
    Check all links in a file and categorize them as reachable or broken.

    :param input_file: path to input file
    :return: tuple of (reachable_urls, broken_urls_with_line_numbers)
    """
    hdbg.dassert_file_exists(input_file)
    # Read file content.
    original_content = hio.from_file(input_file)
    # Remove table of contents between <!-- toc --> and <!-- tocstop --> tags.
    filtered_content = hmarkdo.remove_table_of_contents(original_content)
    # Extract URLs from content with original line numbers.
    urls = _extract_urls_from_text_with_original_line_numbers(
        original_content, filtered_content
    )
    _LOG.info("Found %d URLs in file %s", len(urls), input_file)
    # Check each URL.
    reachable_urls = []
    broken_urls = []
    for i, (url, line_num) in enumerate(urls, 1):
        _LOG.debug(
            "Checking URL %d/%d: %s (line %d)", i, len(urls), url, line_num
        )
        if _check_url_reachable(url):
            reachable_urls.append(url)
            _LOG.info("✓ %s", url)
        else:
            broken_urls.append((url, line_num))
            _LOG.info("✗ %s (line %d)", url, line_num)
    return reachable_urls, broken_urls


def _generate_cfile_for_broken_urls(
    input_file: str, broken_urls: List[Tuple[str, int]]
) -> List[str]:
    """
    Generate a vim cfile format for broken URLs.

    :param input_file: path to input file
    :param broken_urls: list of tuples (url, line_number) for broken
        URLs
    :return: cfile content as list of strings
    """
    cfile_lines = []
    for url, line_num in broken_urls:
        cfile_lines.append(f"{input_file}:{line_num}:Broken URL: {url}")
    return cfile_lines


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--in_file",
        action="store",
        required=True,
        help="Input file to check for URLs.",
    )
    parser.add_argument(
        "--cfile",
        action="store",
        default="cfile",
        help="Output file to write broken URLs in vim cfile format (default: 'cfile').",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Check links in the input file.
    reachable_urls, broken_urls = _check_links_in_file(args.in_file)
    # Generate cfile by default if there are broken URLs.
    if broken_urls:
        cfile_content = _generate_cfile_for_broken_urls(args.in_file, broken_urls)
        hio.to_file(args.cfile, "\n".join(cfile_content))
        _LOG.info("Generated cfile with broken URLs: %s", args.cfile)
    elif args.cfile != "cfile":
        # If user specified a custom cfile name but no broken URLs, create empty file.
        hio.to_file(args.cfile, "")
        _LOG.info("Generated empty cfile (no broken URLs): %s", args.cfile)
    # Print summary.
    total_urls = len(reachable_urls) + len(broken_urls)
    _LOG.info("=" * 60)
    _LOG.info("SUMMARY:")
    _LOG.info("Total URLs found: %d", total_urls)
    _LOG.info("Reachable URLs: %d", len(reachable_urls))
    _LOG.info("Broken URLs: %d", len(broken_urls))
    if broken_urls:
        _LOG.info("=" * 60)
        _LOG.info("BROKEN URLS:")
        for url, line_num in broken_urls:
            _LOG.info("  %s (line %d)", url, line_num)


if __name__ == "__main__":
    _main(_parse())
