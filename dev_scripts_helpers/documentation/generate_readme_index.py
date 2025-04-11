#!/usr/bin/env python

"""
Generate a Markdown index in the README file.

Usage:
    generate_readme_index.py [--repo_path REPO_PATH] [--use_placeholder_summary]

This script locates the root of a Git repository, finds all Markdown files,
and creates a README file, appending a list of Markdown files organized hierarchically by directory.

Options:
    --repo_path REPO_PATH           Path to the target directory. Defaults to Git repo root.
    --use_placeholder_summary       Use a placeholder summary instead of calling OpenAI.
"""

import os
import logging
import argparse
from collections import defaultdict
from typing import Set

import helpers.hgit as hgit
import helpers.hopenai as hopenai
import helpers.hio as hio

_LOG = logging.getLogger(__name__)

def list_markdown_files(repo_path: str) -> Set[str]:
    """
    List all Markdown files in the given repository path.

    :param `repo_path`: root path of the repository
    :return: a set containing the relative paths of all `.md` files found
    """
    markdown_files = set()
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(".md") and file.lower() != "readme.md":
                markdown_files.add(os.path.relpath(os.path.join(root, file), repo_path))
    return markdown_files

def generate_summary_for_file(file_path: str, use_placeholder: bool = False) -> str:
    """
    Generate a two-line summary for a given Markdown file.

    :param `file_path`: full path to the Markdown file
    :param `use_placeholder`: use a dummy summary instead of calling OpenAI
    :return: a short summary string
    """
    if use_placeholder:
        _LOG.debug("Using placeholder summary for %s", file_path)
        return f"Placeholder summary for {os.path.basename(file_path)}"
    
    _LOG.debug("Generating real summary for: %s", file_path)
    content = hio.from_file(file_path)
    prompt = f"Summarize the following content into two lines:\n\n{content}"
    summary = hopenai.get_completion(user=prompt, model="gpt-4o-mini")
    return summary.strip()

def generate_markdown_index(repo_path: str, markdown_files: Set[str], use_placeholder: bool) -> None:
    """
    Generate a README index of Markdown files.

    The function lists all Markdown files in the repository, organized hierarchically by
    directory, and appends this index to the README along with basic metadata.

    :param `repo_path`: the root path of the repository
    :param `markdown_files`: a set of markdown file paths (relative to repo_path)
    :param `use_placeholder`: indicates if summary generation is mocked
    """
    readme_file_path = os.path.join(repo_path, "README.md")
    # Generate README
    summaries = {}
    for rel_path in markdown_files:
        file_path = os.path.join(repo_path, rel_path)
        summaries[rel_path] = generate_summary_for_file(file_path, use_placeholder)
    # Build directory map
    directory_map = defaultdict(list)
    for md_file in markdown_files:
        directory = os.path.dirname(md_file)
        filename = os.path.basename(md_file)
        directory_map[directory].append((filename, md_file))
    # Create file starter
    lines = [
        "# Repository README",
        "",
        "## Markdown Index",
        "",
        "This section lists all Markdown files in the repository.",
        "",
    ]
    # Create summary block
    for directory in sorted(directory_map.keys()):
        # Gets directory or root name
        if directory:
            dir_display = directory
        else:
            dir_display = os.path.basename(os.path.abspath(repo_path))
        # Directory Header
        lines.append(f"### {dir_display}")
        lines.append("")
        # Summary block generation
        for filename, rel_path in sorted(directory_map[directory]):
            summary = summaries.get(rel_path, f"No summary available for {rel_path}.")
            _LOG.debug("Adding entry for file: %s with summary: %s", rel_path, summary)
            lines.append(
                f"- **File Name**: {filename}  \n"
                f"  **Relative Path**: [{rel_path}]({rel_path})  \n"
                f"  **Summary**: {summary}  \n"
                )
    updated_content = "\n".join(lines)
    hio.to_file(readme_file_path, updated_content)
    _LOG.debug(f"README updated with Markdown index at '{readme_file_path}'.")


def _main() -> None:
    parser = argparse.ArgumentParser(description="Generate or update a Markdown index in the README file.")
    parser.add_argument(
        "--repo_path",
        type=str,
        default=hgit.find_git_root(),
        help="Path to target folder. Defaults to Git root.",
    )
    parser.add_argument(
        "--use_placeholder_summary",
        action="store_true",
        help="Use a placeholder summary instead of calling OpenAI.",
    )
    args = parser.parse_args()
    repo_path = args.repo_path
    use_placeholder = args.use_placeholder_summary

    # Fetch all Markdown files in the repository.
    markdown_files = list_markdown_files(repo_path)
    # Check for Markdown file
    if markdown_files:
        generate_markdown_index(repo_path, markdown_files, use_placeholder)
    else:
        _LOG.debug("No Markdown files found; skipping index generation.")

if __name__ == "__main__":
    _main()
