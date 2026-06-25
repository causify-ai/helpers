#!/usr/bin/env python3

"""
Compute git productivity metrics for one or more repositories.

Generates a CSV with commits, lines added/removed, and files changed per repo
and aggregated across all repos for a specific author and date range.

If --author is not specified, uses the current git user (git config user.email).

Usage:
> git_productivity_metrics.py --since "2026-01-01" --until "2026-12-31"
> git_productivity_metrics.py --since "today" --repo-dir /path/to/repos
> git_productivity_metrics.py --author email@example.com --since "7 days ago" --repo-dir .
"""

import argparse
import csv
import logging
import os
import subprocess
from typing import Dict, List

import helpers.hdbg as hdbg
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

# #############################################################################
# Constants
# #############################################################################

_DEFAULT_OUTPUT_FILE = "tmp.git_productivity_metrics.csv"


# #############################################################################
# Helper functions
# #############################################################################


def _run_git_cmd(cmd: str, *, cwd: str = ".") -> str:
    """
    Run a git command and return output.

    :param cmd: Git command to run (without 'git' prefix)
    :param cwd: Working directory for the command
    :return: Command output as string
    """
    full_cmd = f"git {cmd}"
    result = subprocess.run(
        full_cmd,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Git command failed in '{cwd}': {full_cmd}\nError: {result.stderr}"
        )
    return result.stdout.strip()


def _get_repo_stats(
    repo_path: str,
    author: str,
    since: str,
    until: str,
) -> Dict[str, int]:
    """
    Get git statistics for a single repository.

    :param repo_path: Path to the git repository
    :param author: Author email to filter commits
    :param since: Start date for filtering (git format)
    :param until: End date for filtering (git format)
    :return: Dict with commits, lines_added, lines_removed, files_changed
    """
    try:
        # Get number of commits.
        cmd_commits = (
            f"log --since='{since}' --until='{until}' --author='{author}' "
            "--oneline | wc -l"
        )
        commits_output = _run_git_cmd(cmd_commits, cwd=repo_path)
        commits = int(commits_output)
        # Get lines added/removed.
        cmd_numstat = (
            f"log --since='{since}' --until='{until}' --author='{author}' "
            "--numstat --pretty=format:"
        )
        numstat_output = _run_git_cmd(cmd_numstat, cwd=repo_path)
        lines_added = 0
        lines_removed = 0
        files_changed_set = set()
        for line in numstat_output.split("\n"):
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) >= 3:
                try:
                    added = int(parts[0]) if parts[0].isdigit() else 0
                    removed = int(parts[1]) if parts[1].isdigit() else 0
                    lines_added += added
                    lines_removed += removed
                    files_changed_set.add(parts[2])
                except (ValueError, IndexError):
                    continue
        files_changed = len(files_changed_set)
        stats = {
            "commits": commits,
            "lines_added": lines_added,
            "lines_removed": lines_removed,
            "files_changed": files_changed,
        }
        return stats
    except RuntimeError as e:
        _LOG.warning("Failed to get stats for repo '%s': %s", repo_path, str(e))
        return {
            "commits": 0,
            "lines_added": 0,
            "lines_removed": 0,
            "files_changed": 0,
        }


def _find_git_repos(repo_dir: str) -> List[str]:
    """
    Find all git repositories in a directory.

    :param repo_dir: Root directory to search for git repos
    :return: List of paths to found git repositories
    """
    repos = []
    for root, dirs, _ in os.walk(repo_dir):
        if ".git" in dirs:
            repos.append(root)
            # Don't descend into git directories.
            dirs[:] = []
        else:
            # Skip hidden directories.
            dirs[:] = [d for d in dirs if not d.startswith(".")]
    return sorted(repos)


def _write_csv(
    output_file: str,
    repo_stats: Dict[str, Dict[str, int]],
    aggregated_stats: Dict[str, int],
) -> None:
    """
    Write metrics to a CSV file.

    :param output_file: Path to output CSV file
    :param repo_stats: Dictionary of stats per repository
    :param aggregated_stats: Aggregated statistics across all repos
    """
    rows = []
    # Add per-repo rows.
    for repo_name in sorted(repo_stats.keys()):
        stats = repo_stats[repo_name]
        rows.append(
            {
                "repository": repo_name,
                "commits": stats["commits"],
                "lines_added": stats["lines_added"],
                "lines_removed": stats["lines_removed"],
                "files_changed": stats["files_changed"],
            }
        )
    # Add aggregated row.
    rows.append(
        {
            "repository": "TOTAL",
            "commits": aggregated_stats["commits"],
            "lines_added": aggregated_stats["lines_added"],
            "lines_removed": aggregated_stats["lines_removed"],
            "files_changed": aggregated_stats["files_changed"],
        }
    )
    # Write CSV.
    fieldnames = [
        "repository",
        "commits",
        "lines_added",
        "lines_removed",
        "files_changed",
    ]
    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    _LOG.info("Wrote metrics to '%s'", output_file)


# #############################################################################
# Parser
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
    )
    parser.add_argument(
        "--author",
        type=str,
        default="",
        help="Author email to filter commits (uses current git user if not specified)",
    )
    # Date range options: mutually exclusive.
    date_group = parser.add_mutually_exclusive_group(required=True)
    date_group.add_argument(
        "--since",
        type=str,
        default="",
        help="Start date for filtering (git format, e.g., '2026-01-01' or 'today')",
    )
    date_group.add_argument(
        "--today",
        action="store_true",
        help="Compute stats for today",
    )
    date_group.add_argument(
        "--yesterday",
        action="store_true",
        help="Compute stats for yesterday",
    )
    date_group.add_argument(
        "--this_week",
        action="store_true",
        help="Compute stats for this week (Monday to today)",
    )
    parser.add_argument(
        "--until",
        type=str,
        default="",
        help="End date for filtering (required if using --since)",
    )
    parser.add_argument(
        "--repo_dir",
        type=str,
        default=".",
        help="Directory containing git repositories (searches recursively)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=_DEFAULT_OUTPUT_FILE,
        help="Output CSV file path",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main function to compute git productivity metrics.
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Use current git user if author not specified.
    if not args.author:
        try:
            args.author = _run_git_cmd("config user.email")
            _LOG.info("Using current git user: '%s'", args.author)
        except RuntimeError:
            raise ValueError(
                "Author email not specified and no git user configured. "
                "Use --author or run 'git config user.email'"
            )
    # Convert preset time period options to since/until.
    if args.today:
        args.since = "today"
        args.until = "today"
    elif args.yesterday:
        args.since = "yesterday"
        args.until = "yesterday"
    elif args.this_week:
        args.since = "Monday"
        args.until = "today"
    # Validate required arguments.
    hdbg.dassert_ne(
        args.author,
        "",
        "Author email is required (use --author)",
    )
    hdbg.dassert_ne(
        args.since,
        "",
        "Start date is required (use --since or a preset like --today)",
    )
    hdbg.dassert_ne(
        args.until,
        "",
        "End date is required (use --until or a preset like --today)",
    )
    hdbg.dassert_dir_exists(args.repo_dir, "Repository directory does not exist")
    # Find all git repositories.
    _LOG.info("Searching for git repositories in '%s'...", args.repo_dir)
    repos = _find_git_repos(args.repo_dir)
    hdbg.dassert(
        len(repos) > 0,
        "No git repositories found in directory '%s'",
        args.repo_dir,
    )
    _LOG.info("Found %d git repository(ies)", len(repos))
    # Get stats for each repository.
    repo_stats: Dict[str, Dict[str, int]] = {}
    aggregated_stats: Dict[str, int] = {
        "commits": 0,
        "lines_added": 0,
        "lines_removed": 0,
        "files_changed": 0,
    }
    for repo_path in repos:
        repo_name = os.path.basename(repo_path)
        _LOG.info("Processing repository '%s'...", repo_name)
        stats = _get_repo_stats(repo_path, args.author, args.since, args.until)
        repo_stats[repo_name] = stats
        # Aggregate stats.
        aggregated_stats["commits"] += stats["commits"]
        aggregated_stats["lines_added"] += stats["lines_added"]
        aggregated_stats["lines_removed"] += stats["lines_removed"]
        aggregated_stats["files_changed"] += stats["files_changed"]
    # Write CSV.
    _write_csv(args.output, repo_stats, aggregated_stats)
    # Display results.
    _LOG.info("Summary:")
    _LOG.info(
        "  Commits: %d, Lines Added: %d, Lines Removed: %d, Files Changed: %d",
        aggregated_stats["commits"],
        aggregated_stats["lines_added"],
        aggregated_stats["lines_removed"],
        aggregated_stats["files_changed"],
    )
    # Display CSV with csvlook.
    result = subprocess.run(
        f"csvlook {args.output}",
        shell=True,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(result.stdout)
    else:
        _LOG.warning("Failed to run csvlook: %s", result.stderr)


if __name__ == "__main__":
    parser = _parse()
    _main(parser)
