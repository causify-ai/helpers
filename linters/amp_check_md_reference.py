#!/usr/bin/env python
"""
Check and ensure every Markdown file in the repository is referenced.

Steps:
1. Traverse the repository to list all Markdown files.
2. Parse all Markdown files to extract references.
3. Compare the list of all Markdown files with the list of references.
4. Report unreferenced Markdown files.
"""

import argparse
import logging
import os
import re
from typing import List, Set, Tuple

import helpers.hdbg as hdbg
import helpers.hparser as hparser

import linters.action as liaction

_LOG = logging.getLogger(__name__)

MARKDOWN_EXT = ".md"
MARKDOWN_LINK_REGEX = r"\[.*?\]\((.*?)\)"

def list_markdown_files(repo_path: str) -> Set[str]:
    """
    Traverse the repository to list all Markdown files.

    :param repo_path: the path to the repository
    :return: a set of relative paths to all Markdown files
    """
    markdown_files = set()
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(MARKDOWN_EXT):
                full_path = os.path.relpath(os.path.join(root, file), repo_path)
                markdown_files.add(full_path)
    _LOG.info("Found %d Markdown files.", len(markdown_files))
    return markdown_files


def _extract_references_from_file(
        file_path: str
) -> Tuple[Set[str], List[str]]:
    """
    Parse a Markdown file to extract all referenced paths.

    :param file_path: the path to the Markdown file
    :return:
        - a set of paths referenced in the file
        - a list of warnings about issues encountered while processing the file
    """
    references: Set[str] = set()
    warnings: List[str] = []
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            for line_num, line in enumerate(file, start=1):
                try:
                    # Extract Markdown-style links.
                    markdown_links = re.findall(MARKDOWN_LINK_REGEX, line)
                    references.update(markdown_links)
                except Exception as e:
                    warnings.append(f"Error processing line {line_num} in '{file_path}': {e}")
    except FileNotFoundError:
        warnings.append(f"File not found: {file_path}")
    except Exception as e:
        warnings.append(f"Error opening file '{file_path}': {e}")
    return references, warnings


def extract_all_references(
        repo_path: str, markdown_files: Set[str]
) -> Tuple[Set[str], List[str]]:
    """
    Parse all Markdown files to extract all references.

    :param repo_path: the path to the repository
    :param markdown_files: a set of Markdown files to parse
    :return:
        - a set of referenced paths
        - a list of warnings about issues encountered while processing the files
    """
    all_references: Set[str] = set()
    all_warnings: List[str] = []
    for md_file in markdown_files:
        file_path = os.path.join(repo_path, md_file)
        try:
            references, warnings = _extract_references_from_file(file_path)
            all_references.update(references)
            all_warnings.extend(warnings)
        except Exception as e:
            all_warnings.append(f"Error processing file '{file_path}': {e}")
    _LOG.info("Extracted %d unique references.", len(all_references))
    return all_references, all_warnings


def find_unreferenced_files(
    markdown_files: Set[str], references: Set[str]
) -> Tuple[List[str], List[str]]:
    """
    Identify Markdown files that are not referenced anywhere.

    :param markdown_files: a set of all Markdown file paths (relative to repo root)
    :param references: a set of all referenced paths (relative to repo root)
    :return:
        - a sorted list of unreferenced Markdown files
        - a list of warnings about unreferenced files
    """
    warnings: List[str] = []
    unreferenced_files: List[str] = []
    # Normalize paths for consistent comparison.
    normalized_markdown_files = {os.path.normcase(os.path.normpath(file)) for file in markdown_files}
    normalized_references = {
        os.path.normcase(os.path.normpath(ref.split("#")[0]))  
        for ref in references
        if ref.endswith(MARKDOWN_EXT)
    }
    # Identify unreferenced files.
    for file in normalized_markdown_files:
        if file not in normalized_references:
            unreferenced_files.append(file)
            warnings.append(f"Unreferenced Markdown file: {file}")
    # Sort unreferenced files for consistency.
    unreferenced_files.sort()
    return unreferenced_files, warnings


def check_markdown_references(repo_path: str) -> Tuple[List[str], List[str]]:
    """
    Check and ensure Markdown references by combining all logic from helper functions.

    :param repo_path: the path to the repository
    :return:
        - a list of unreferenced Markdown files
        - a list of warnings or issues found
    """
    all_warnings: List[str] = []
    # List all Markdown files in the repository.
    markdown_files = list_markdown_files(repo_path)
    if not markdown_files:
        _LOG.info("No Markdown files found in the repository.")
        return ["No Markdown files found in the repository."], []
    # Extract all references from the Markdown files.
    references, extract_warnings = extract_all_references(repo_path, markdown_files)
    all_warnings.extend(extract_warnings)
    references = set(references)
    # Find unreferenced Markdown files.
    unreferenced_files, unreferenced_warnings = find_unreferenced_files(markdown_files, references)
    all_warnings.extend(unreferenced_warnings)
    # Log results
    if not unreferenced_files:
        _LOG.info("No unreferenced Markdown files found.")
    else:
        _LOG.info("%d unreferenced Markdown files found.", len(unreferenced_files))
    return unreferenced_files, all_warnings

class _CheckMarkdownReferences(liaction.Action):
    """
    Action class for checking and ensuring Markdown references.
    """
    def check_if_possible(self) -> bool:
        return True

    def _execute(self, repo_path: str, pedantic: int) -> List[str]:
        """
        Execute the action to check and ensure Markdown references.
        """
        _ = pedantic
        unreferenced_files, warnings = check_markdown_references(repo_path)
        if unreferenced_files is None:
            # Add the unreferenced files to the index file.
            _LOG.info("No unreferenced Markdown files found.")
        return warnings


def _parse_args() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "repo_path",
        type=str,
        help="Path to the repository to analyze.",
    )
    hparser.add_verbosity_arg(parser)
    return parser

def _main() -> None:
    args = _parse_args().parse_args()
    hdbg.init_logger(verbosity=args.log_level)
    action = _CheckMarkdownReferences()
    action.run(args.repo_path)

if __name__ == "__main__":
    _main()

