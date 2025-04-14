#!/usr/bin/env python

"""
Generate a Markdown index in the README file.

Usage:
    generate_readme_index.py --index_mode {generate,refresh} [--repo_path REPO_PATH] [--model MODEL]

This script locates the given directory or the root of a Git repository, finds all Markdown files,
and creates or updates a README file with an index of Markdown files including their relative paths
and summaries.

Example output:

# Repository README

This section lists all Markdown files in the repository.

## Markdown Index

- **File Name**: welcome.md
  **Relative Path**: [welcome.md](welcome.md)
  **Summary**: Introduces the repository, its purpose, and how to navigate the documentation.
  Serves as the landing page for new contributors and users.

- **File Name**: docs/intro.md
  **Relative Path**: [docs/intro.md](docs/intro.md)
  **Summary**: Provides an overview of the project's architecture and core concepts.
  Useful for understanding the big picture before diving into the codebase.

- **File Name**: docs/guide/setup.md
  **Relative Path**: [docs/guide/setup.md](docs/guide/setup.md)
  **Summary**: Placeholder summary for docs/guide/setup.md

Options:
    --index_mode {generate,refresh}
        Choose to either generate summaries from scratch or refresh only new files.
    --dir_path DIR_PATH
        Path to the target directory. Defaults to the Git repository root.
    --model MODEL
        Specify the summarization model. Use 'placeholder' to skip OpenAI API usage.
"""

import argparse
import logging
import os
import re
from typing import Dict, List, Optional

import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hopenai as hopenai

_LOG = logging.getLogger(__name__)


def _get_existing_summaries(
    readme_path: str, markdown_files: List[str]
) -> Dict[str, str]:
    """
    Extract and filter summaries from the existing README file.

    :param readme_path: path to the README.md file
    :param markdown_files: list of current Markdown file paths
    :return: existing summaries
    """
    summaries = {}
    content = hio.from_file(readme_path)
    content = content.strip()
    pattern = re.compile(
        # Matches **File Name**: file_name.md.
        r"- \*\*File Name\*\*: (?P<file_name>.+?)"
        # Matches **Relative Path**: [path](link).
        r"\*\*Relative Path\*\*: \[(?P<rel_path>[^\]]+)\]\([^)]+\)\s*"
        # Matches **Summary**: content.
        r"\*\*Summary\*\*: (?P<summary>.*?)(?=\n- \*\*File Name|\Z)",
        re.DOTALL,
    )
    for match in pattern.finditer(content):
        # Parse content.
        rel_path = match.group("rel_path").strip()
        summary = match.group("summary").strip().replace("\n", " ")
        if rel_path in markdown_files:
            # Filter out deleted files
            summaries[rel_path] = summary
        else:
            _LOG.debug("Deleting summary for %s", rel_path)
    return summaries


def _generate_summary_for_file(
    file_path: str, *, model: Optional[str] = None
) -> str:
    """
    Generate a two-line summary for a given Markdown file.

    :param file_path: full path to the Markdown file
    :param model: model identifier (e.g., "placeholder", "gpt-4o-mini")
    :return: a short summary of a file
    """
    if model is None:
        raise ValueError(
            "`model` must be specified (e.g., 'placeholder' or a valid ChatGPT model)."
        )
    if model == "placeholder":
        # Skip OpenAI API usage.
        _LOG.debug("Using placeholder summary for %s", file_path)
        summary = f"Placeholder summary for {file_path}"
        return summary
    _LOG.debug("Generating real summary for: %s", file_path)
    content = hio.from_file(file_path)
    prompt = (
        "Summarize the following content in exactly two lines. "
        "Do not include any introduction or list markers. "
        "Just return the summary itself, nothing else.\n\n"
        f"{content}"
    )
    summary = hopenai.get_completion(user_prompt=prompt, model=model)
    summary = str(summary.strip())
    return summary


def _build_index_lines(
    markdown_files: List[str],
    summaries: Dict[str, str],
    *,
    model: Optional[str] = None,
) -> str:
    """
    Construct the Markdown index content to write into README.

    :param markdown_files: list of Markdown file paths
    :param model: model identifier (e.g., "placeholder", "gpt-4o-mini")
    :param summaries: dictionary of file summaries
    :return: formatted markdown files index
    """
    # File starter.
    lines = [
        "# Repository README",
        "",
        "This section lists all Markdown files in the repository.",
        "",
        "## Markdown Index",
        "",
    ]
    for file_path in markdown_files:
        if file_path not in summaries:
            # Check for new files.
            summaries[file_path] = _generate_summary_for_file(
                file_path, model=model
            )
        summary = summaries[file_path]
        # README format.
        lines.append(
            f"- **File Name**: {file_path}  \n"
            f"  **Relative Path**: [{file_path}]({file_path})  \n"
            f"  **Summary**: {summary}  \n"
        )
    content = "\n".join(lines)
    return content


def list_markdown_files(dir_path: str) -> List[str]:
    """
    List all Markdown files in the given directory.

    :param dir_path: directory to search
    :return: the full paths of all markdown files found
    """
    markdown_files = []
    for root, _, files in os.walk(dir_path):
        for file in files:
            if file.endswith(".md") and file.lower() != "readme.md":
                # Get markdown files and ignore README.md.
                rel_path = os.path.relpath(os.path.join(root, file), dir_path)
                markdown_files.append(rel_path)
    markdown_files = sorted(markdown_files)
    return markdown_files


def generate_markdown_index(
    readme_path: str,
    markdown_files: List[str],
    index_mode: str,
    *,
    model: Optional[str] = None,
) -> str:
    """
    Generate a README index of Markdown files.

    The function lists all Markdown files in the repository, organized
    hierarchically by directory, and appends this index to the README
    along with basic metadata.

    :param readme_path: path to README.md file to read/write
    :param markdown_files: list of relative Markdown paths
    :param index_mode: whether to "generate" or "refresh" summaries
    :param model: summarization model to use
    :return: complete Markdown index content
    """
    summaries = {}
    if index_mode == "refresh":
        # Add and delete files from existing README.
        summaries = _get_existing_summaries(readme_path, markdown_files)
    content = _build_index_lines(markdown_files, model=model, summaries=summaries)
    return content


def _main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate or refresh a Markdown index in the README file."
    )
    parser.add_argument(
        "--index_mode",
        choices=["generate", "refresh"],
        required=True,
        help="Choose execute index mode: generate or refresh",
    )
    parser.add_argument(
        "--dir_path",
        type=str,
        default=hgit.find_git_root(),
        help="Path to target folder. Defaults to Git root.",
    )
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Choice of ChatGPT model. Use `placeholder` to create dummy summary.",
    )
    args = parser.parse_args()
    # Fetch all Markdown files in the repository.
    markdown_files = list_markdown_files(args.dir_path)
    if markdown_files:
        # Skip if no markdown files in directory
        readme_path = os.path.join(args.dir_path, "README.md")
        content = generate_markdown_index(
            readme_path=readme_path,
            markdown_files=markdown_files,
            index_mode=args.index_mode,
            model=args.model,
        )
        # Write content to README.
        hio.to_file(readme_path, content)
    else:
        _LOG.debug("No Markdown files found; skipping index generation.")


if __name__ == "__main__":
    _main()
