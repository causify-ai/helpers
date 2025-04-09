#!/usr/bin/env python

"""
Generate or update a Markdown index in the README file.

Usage:
    generate_readme_index.py [--generate_summary] [--update_summary]

This script locates the root of a Git repository, finds all Markdown files,
and either updates an existing README file or creates one if it doesn't exist,
appending a list of Markdown files organized hierarchically by directory.

Options:
    --generate_summary  Generate a two-line summary for Markdown files that lack a summary.
    --update_summary    Update the summary for all Markdown files.
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

def generate_markdown_index(
    repo_path: str, markdown_files: Set[str], readme_file_name: str = "README.md"
) -> None:
    """
    Generate or update a README index of Markdown files.

    The function lists all Markdown files in the repository, organized hierarchically by
    directory, and appends this index to the README along with basic metadata.

    :param repo_path: the root path of the repository
    :param markdown_files: a set of markdown file paths (relative to repo_path)
    :param readme_file_name: the name of the README file (default is "README.md")
    """
    # Build a dictionary of directory -> list of (filename, relative_path)
    directory_map = defaultdict(list)
    for md_file in markdown_files:
        directory = os.path.dirname(md_file)
        filename = os.path.basename(md_file)
        directory_map[directory].append((filename, md_file))
    # Prepare the lines for the Markdown index.
    lines = []
    lines.append("## Markdown Index")
    lines.append("")
    lines.append("This section lists all Markdown files in the repository.")
    lines.append("")
    # Sort directories to get a deterministic ordering.
    for directory in sorted(directory_map.keys()):
        # Use '.' for the top-level directory if empty.
        dir_display = directory if directory else "."
        lines.append(f"### {dir_display}")
        lines.append("")
        # Sort within each directory for consistency.
        for filename, rel_path in sorted(directory_map[directory]):
            lines.append(
                f"- **File Name**: {filename}  \n"
                f"  **Relative Path**: [{rel_path}]({rel_path})"
            )
        lines.append("")
    # Read existing README or create a new one.
    readme_file_path = os.path.join(repo_path, readme_file_name)
    if os.path.exists(readme_file_path):
        existing_content = hio.from_file(readme_file_path)
    else:
        existing_content = "# Repository README\n\n"
    # Append the Markdown index to the README content.
    updated_content = existing_content.strip() + "\n\n" + "\n".join(lines)
    # Write the updated README.
    hio.to_file(readme_file_path, updated_content)
    _LOG.info("README updated with Markdown index at '%s'.", readme_file_path)


def generate_summary_for_file(file_path: str) -> str:
    """
    Generate a two-line summary for the given Markdown file.

    :param file_path: path to the Markdown file
    :return: a generated summary string
    """
    content = hio.from_file(file_path)
    prompt = f"Summarize the following content into two lines:\n\n{content}"
    summary = hopenai.get_completion(user=prompt, model="gpt-4o-mini")
    return summary.strip()


def check_and_generate_summaries(repo_path: str, markdown_files: Set[str], update: bool = False) -> None:
    """
    Check each Markdown file for a summary, and generate or update one if required.

    :param repo_path: root path of the repository
    :param markdown_files: set of Markdown file paths relative to repo_path
    :param update: whether to update summaries for all files
    """
    for rel_path in markdown_files:
        file_path = os.path.join(repo_path, rel_path)
        content = hio.from_file(file_path)
        if "## Summary" not in content or update:
            action = "Updating" if update else "Generating"
            _LOG.info("%s summary for %s...", action, rel_path)
            summary = generate_summary_for_file(file_path)
            if "## Summary" in content:
                # Update existing summary.
                content = content.split("## Summary")[0].strip()
            hio.to_file(file_path, content + "\n\n## Summary\n" + summary)
            _LOG.info("Summary %s to %s.", "updated" if update else "added", rel_path)


def list_markdown_files(repo_path: str) -> Set[str]:
    """
    List all Markdown files in the given repository path.

    :param repo_path: root path of the repository
    :return: a set containing the relative paths of all `.md` files found
    """
    markdown_files = set()
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(".md"):
                markdown_files.add(os.path.relpath(os.path.join(root, file), repo_path))
    return markdown_files


def _main() -> None:
    parser = argparse.ArgumentParser(description="Generate or update a Markdown index in the README file.")
    parser.add_argument(
        "--generate_summary",
        action="store_true",
        help="Generate a two-line summary for Markdown files that lack a summary.",
    )
    parser.add_argument(
        "--update_summary",
        action="store_true",
        help="Update the summary for all Markdown files.",
    )
    args = parser.parse_args()
    # Find the repository root.
    repo_path = hgit.find_git_root()
    # Fetch all Markdown files in the repository.
    markdown_files = list_markdown_files(repo_path)
    if markdown_files:
        generate_markdown_index(repo_path, markdown_files)
        if args.generate_summary or args.update_summary:
            check_and_generate_summaries(repo_path, markdown_files, update=args.update_summary)
    else:
        _LOG.debug("No Markdown files found; skipping index generation.")


if __name__ == "__main__":
    _main()
