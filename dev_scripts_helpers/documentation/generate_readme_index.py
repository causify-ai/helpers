#!/usr/bin/env python

"""
Generate a Markdown index in the README file.

Usage:
    generate_readme_index.py --index_mode {generate,refresh} [--target_path TARGET_PATH] [--model MODEL]

This script creates or updates a README file with an index of Markdown files in a given directory, 
including their relative paths and summaries.

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
    --target_path TARGET_PATH
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
    target_path: str, markdown_files: List[str]
) -> Dict[str, str]:
    """
    Extract and filter summaries from the existing README file.

    Only summaries for Markdown files that still exist in the codebase are retained.

    :param target_path: target path where README.md file is located
    :param markdown_files: all Markdown file paths
    :return: summaries of existing files
    """
    readme_path = os.path.join(target_path, "README.md")
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
    summaries = {}
    for match in pattern.finditer(content):
        # Parse content.
        rel_path = match.group("rel_path").strip()
        summary = match.group("summary").strip().replace("\n", " ")
        if rel_path in markdown_files:
            # Store summaries of the files that still exist.
            summaries[rel_path] = summary
        else:
            _LOG.debug("Deleting summary for %s", rel_path)
    return summaries


def _generate_summary_for_file(
    file_path: str, model: str
) -> str:
    """
    Generate a two-line summary for a given Markdown file.

    :param file_path: full path to the Markdown file
    :param model: name of the model for summary generation, e.g. "placeholder", "gpt-4o-mini"
        - "placeholder" model inserts a dummy summary instead of generating one
    :return: a short summary of a file
    """
    if model == "placeholder":
        # Skip OpenAI API usage.
        _LOG.debug("Using placeholder summary for %s", file_path)
        summary = f"Placeholder summary for {file_path}"
        return summary
    _LOG.debug("Generating summary for: %s", file_path)
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
    target_path: str,
    markdown_files: List[str],
    summaries: Dict[str, str],
    model: str
) -> str:
    """
    Construct the Markdown index content to write into README.

    :param target_path: target path to label README
    :param markdown_files: all Markdown file paths
    :param summaries: Markdown file paths and their summaries
    :param model: name of the model for summary generation, e.g. "placeholder", "gpt-4o-mini"
        - "placeholder" model inserts a dummy summary instead of generating one
    :return: formatted Markdown files index
    """
    # File starter.
    if target_path == hgit.find_git_root():
        lines = [
            "# README for the repository",
            "",
            "Below is a list of all Markdown files found in the repository.",
        ]
    else:
        rel_path = os.path.relpath(target_path)
        lines = [
            f"# README for `{rel_path}`",
            "",
            f"Below is a list of all Markdown files found under `{rel_path}`.",
        ]
    lines.extend([
        "",
        "## Markdown Index",
        "",
    ])
    for file_path in markdown_files:
        if file_path not in summaries:
            # Construct the info paragraph in the README format.
            summary = _generate_summary_for_file(file_path, model=model)
        else:
            summary = summaries[file_path]
        # README format.
        lines.append(
            f"- **File Name**: {file_path}  \n"
            f"  **Relative Path**: [{file_path}]({file_path})  \n"
            f"  **Summary**: {summary}  \n"
        )
    content = "\n".join(lines)
    return content


def list_markdown_files(target_path: str) -> List[str]:
    """
    List all Markdown files in the given directory.

    :param target_path: target path to search
    :return: the full paths of all Markdown files found
    """
    markdown_files = []
    for root, _, files in os.walk(target_path):
        for file in files:
            if file.endswith(".md") and file.lower() != "readme.md":
                # Get markdown files and ignore README.md.
                rel_path = os.path.relpath(os.path.join(root, file), target_path)
                markdown_files.append(rel_path)
    markdown_files = sorted(markdown_files)
    return markdown_files


def generate_markdown_index(
    target_path: str,
    markdown_files: List[str],
    index_mode: str,
    *,
    model: str = "placeholder",
) -> str:
    """
    Generate the full Markdown index content to be written into README.

    Depending on the index mode, this function either creates new summaries
    for all Markdown files (`generate`) or only for newly added ones (`refresh`).
    Summaries are created using a provided model or a placeholder string.

    :param target_path: target path to index Markdown files
    :param markdown_files: all Markdown file paths
    :param index_mode: method of dealing with the existing README file
        - "generate": overwrite with the index generated from scratch
        - "refresh": remove obsolete entries and add missing ones
    :param model: LLM model to use for summarization
    :return: complete Markdown index content
    """
    if index_mode == "generate":
        # Start with empty summary.
        summaries = {}
    elif index_mode == "refresh":
        # Retrieves summaries from existing README.
        summaries = _get_existing_summaries(target_path, markdown_files)
    else:
        raise ValueError(f"Invalid index_mode='{index_mode}'. Expected 'generate' or 'refresh'.")
    content = _build_index_lines(target_path, markdown_files, model=model, summaries=summaries)
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
        "--target_path",
        type=str,
        default=hgit.find_git_root(),
        help="Path to target folder. Defaults to Git root.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default='placeholder',
        help="LLM model to use for summarization. Defaults to 'placeholder', which creates a dummy summary.",
    )
    args = parser.parse_args()
    # Fetch all Markdown files in the target path.
    markdown_files = list_markdown_files(args.target_path)
    if markdown_files:
        content = generate_markdown_index(
            target_path=args.target_path,
            markdown_files=markdown_files,
            index_mode=args.index_mode,
            model=args.model,
        )
        # Write content to README.
        readme_path = os.path.join(args.target_path, "README.md")
        hio.to_file(readme_path, content)
    else:
        # Skip if no Markdown files in directory.
        _LOG.debug("No Markdown files found; skipping index generation.")


if __name__ == "__main__":
    _main()
