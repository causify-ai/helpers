#!/usr/bin/env python

"""
Convert a local file path to the corresponding GitHub URL.

This script takes a file or directory path and generates a GitHub URL
by combining the repository's remote URL with the current (or master)
branch and the relative file path.

Simple usage:

> ./dev_scripts_helpers/github/to_github.py --input helpers/hdbg.py

> ./dev_scripts_helpers/github/to_github.py --input helpers/hdbg.py --use_master

> ./dev_scripts_helpers/github/to_github.py --input helpers/hdbg.py --open

> ./dev_scripts_helpers/github/to_github.py --input helpers/hdbg.py --copy

Import as:

import dev_scripts_helpers.github.to_github as dscghtogh
"""

import argparse
import logging
import os
import webbrowser

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


def _get_github_url(
    *,
    file_path: str,
    use_master: bool,
) -> str:
    """
    Generate GitHub URL for a given file path.

    :param file_path: path to file or directory
    :param use_master: use master branch instead of current branch
    :return: GitHub URL for the file
    """
    # Check if file or directory exists.
    if not os.path.exists(file_path):
        _LOG.warning("Path does not exist: %s", file_path)
    # Get the git root directory.
    git_root_cmd = "git rev-parse --show-toplevel"
    _, git_root = hsystem.system_to_string(git_root_cmd)
    git_root = git_root.strip()
    _LOG.debug("Git root: %s", git_root)
    # Get absolute path and compute relative path from git root.
    abs_file_path = os.path.abspath(file_path)
    _LOG.debug("Absolute file path: %s", abs_file_path)
    # Compute relative path from git root.
    if abs_file_path.startswith(git_root):
        relative_path = os.path.relpath(abs_file_path, git_root)
    else:
        hdbg.dfatal(
            "File path is not within git repository:",
            file_path,
        )
    _LOG.debug("Relative path: %s", relative_path)
    # Get repository URL.
    repo_url_cmd = "git remote get-url origin"
    _, repo_url = hsystem.system_to_string(repo_url_cmd)
    repo_url = repo_url.strip()
    _LOG.debug("Raw repository URL: %s", repo_url)
    # Convert SSH URL to HTTPS URL and remove .git suffix.
    if repo_url.startswith("git@github.com:"):
        repo_url = repo_url.replace("git@github.com:", "https://github.com/")
    if repo_url.endswith(".git"):
        repo_url = repo_url[:-4]
    _LOG.debug("Formatted repository URL: %s", repo_url)
    # Get branch name.
    if use_master:
        branch_name = "master"
    else:
        branch_name_cmd = "git branch --show-current"
        _, branch_name = hsystem.system_to_string(branch_name_cmd)
        branch_name = branch_name.strip()
    _LOG.debug("Branch name: %s", branch_name)
    # Construct GitHub URL.
    github_url = f"{repo_url}/blob/{branch_name}/{relative_path}"
    return github_url


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input",
        action="store",
        required=True,
        type=str,
        help="Path to file or directory to convert to GitHub URL",
    )
    parser.add_argument(
        "--use_master",
        action="store_true",
        help="Use master branch instead of current branch",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the URL in default web browser",
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy the URL to system clipboard",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Generate GitHub URL.
    github_url = _get_github_url(
        file_path=args.input,
        use_master=args.use_master,
    )
    # Print the URL.
    _LOG.info("GitHub URL: %s", github_url)
    # Copy to clipboard if requested.
    if args.copy:
        hsystem.to_pbcopy(github_url, pbcopy=True)
    # Open in browser if requested.
    if args.open:
        _LOG.info("Opening URL in browser")
        webbrowser.open(github_url)


if __name__ == "__main__":
    _main(_parse())
