#!/usr/bin/env -S uv run

# /// script
# dependencies = ["pygithub", "pyyaml"]
# ///

"""
Compute PR statistics for a GitHub repository.

This script fetches and summarizes pull request (PR) data for a given repo,
including:
- Open PRs broken down by author and draft/ready status
- Closed PRs over a specified time period broken down by author

Examples:

> ./dev_scripts_helpers/github/compute_pr_stats.py \
    --repo causify-ai/helpers

> ./dev_scripts_helpers/github/compute_pr_stats.py \
    --repo causify-ai/helpers \
    --start_date 2024-01-01 \
    --end_date 2024-12-31

> ./dev_scripts_helpers/github/compute_pr_stats.py \
    --repo causify-ai/helpers \
    --start_date 2024-01-01 \
    --end_date 2024-12-31 \
    -v DEBUG

Import as:

import dev_scripts_helpers.github.compute_pr_stats as dsgicprs
"""

import argparse
import collections
import datetime
import logging
from typing import Dict, Optional, Tuple

import helpers.github_utils as hgitutil
import helpers.hdbg as hdbg
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


# #############################################################################
# PR counting helpers
# #############################################################################


def _count_open_prs_by_author(
    repo_obj,
) -> Dict[str, Dict[str, int]]:
    """
    Count open PRs grouped by author and draft/ready status.

    :param repo_obj: PyGithub repository object
    :return: dict mapping author -> {"ready": int, "draft": int}
    """
    stats: Dict[str, Dict[str, int]] = collections.defaultdict(
        lambda: {"ready": 0, "draft": 0}
    )
    pulls = repo_obj.get_pulls(state="open")
    for pr in pulls:
        author = pr.user.login
        status = "draft" if pr.draft else "ready"
        stats[author][status] += 1
        _LOG.debug(
            "Open PR #%d by %s status=%s", pr.number, author, status
        )
    return dict(stats)


def _count_closed_prs_by_author(
    repo_obj,
    *,
    period: Optional[Tuple[datetime.datetime, datetime.datetime]] = None,
) -> Dict[str, int]:
    """
    Count closed PRs grouped by author, optionally filtered by period.

    :param repo_obj: PyGithub repository object
    :param period: optional (start, end) UTC-aware datetimes for filtering
    :return: dict mapping author -> count of closed PRs
    """
    stats: Dict[str, int] = collections.defaultdict(int)
    since, until = hgitutil.normalize_period_to_utc(period)
    pulls = repo_obj.get_pulls(state="closed")
    for pr in pulls:
        # Normalize the PR closed_at timestamp to UTC.
        closed_at = pr.closed_at
        if closed_at is None:
            continue
        if closed_at.tzinfo is None:
            closed_at = closed_at.replace(tzinfo=datetime.timezone.utc)
        else:
            closed_at = closed_at.astimezone(datetime.timezone.utc)
        # Filter by period if specified.
        if since is not None and until is not None:
            if not (since <= closed_at <= until):
                continue
        author = pr.user.login
        stats[author] += 1
        _LOG.debug("Closed PR #%d by %s at %s", pr.number, author, closed_at)
    return dict(stats)


# #############################################################################
# Display helpers
# #############################################################################


def _print_open_pr_stats(
    open_stats: Dict[str, Dict[str, int]],
) -> None:
    """
    Print open PR statistics by author and draft/ready status.

    :param open_stats: dict mapping author -> {"ready": int, "draft": int}
    """
    if not open_stats:
        _LOG.info("No open PRs found.")
        return
    # Sort by total PR count descending.
    sorted_authors = sorted(
        open_stats.items(),
        key=lambda item: item[1]["ready"] + item[1]["draft"],
        reverse=True,
    )
    total_ready = 0
    total_draft = 0
    header = f"{'Author':<25} {'Ready':>7} {'Draft':>7} {'Total':>7}"
    separator = "-" * len(header)
    _LOG.info("Open PRs by author:")
    _LOG.info(separator)
    _LOG.info(header)
    _LOG.info(separator)
    for author, counts in sorted_authors:
        ready = counts["ready"]
        draft = counts["draft"]
        total = ready + draft
        total_ready += ready
        total_draft += draft
        _LOG.info("%-25s %7d %7d %7d", author, ready, draft, total)
    _LOG.info(separator)
    _LOG.info(
        "%-25s %7d %7d %7d",
        "TOTAL",
        total_ready,
        total_draft,
        total_ready + total_draft,
    )


def _print_closed_pr_stats(
    closed_stats: Dict[str, int],
    *,
    period: Optional[Tuple[datetime.datetime, datetime.datetime]] = None,
) -> None:
    """
    Print closed PR statistics by author.

    :param closed_stats: dict mapping author -> count of closed PRs
    :param period: optional period used for filtering (for display only)
    """
    if not closed_stats:
        _LOG.info("No closed PRs found.")
        return
    # Sort by count descending.
    sorted_authors = sorted(
        closed_stats.items(), key=lambda item: item[1], reverse=True
    )
    period_str = "all time"
    if period is not None:
        since, until = period
        period_str = f"{since.date()} to {until.date()}"
    header = f"{'Author':<25} {'Closed':>7}"
    separator = "-" * len(header)
    _LOG.info("Closed PRs by author (%s):", period_str)
    _LOG.info(separator)
    _LOG.info(header)
    _LOG.info(separator)
    total = 0
    for author, count in sorted_authors:
        total += count
        _LOG.info("%-25s %7d", author, count)
    _LOG.info(separator)
    _LOG.info("%-25s %7d", "TOTAL", total)


# #############################################################################
# Main logic
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--repo",
        action="store",
        required=True,
        type=str,
        help="GitHub repository in 'owner/repo' format, e.g. causify-ai/helpers",
    )
    parser.add_argument(
        "--start_date",
        action="store",
        type=str,
        default=None,
        help="Start date for closed PR filter in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--end_date",
        action="store",
        type=str,
        default=None,
        help="End date for closed PR filter in YYYY-MM-DD format",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Validate repo format.
    hdbg.dassert_eq(
        args.repo.count("/"),
        1,
        "Repo must be in 'owner/repo' format, got: %s",
        args.repo,
    )
    # Build period if dates provided.
    period = None
    if args.start_date is not None or args.end_date is not None:
        hdbg.dassert_is_not(
            args.start_date,
            None,
            "Both --start_date and --end_date must be specified together",
        )
        hdbg.dassert_is_not(
            args.end_date,
            None,
            "Both --start_date and --end_date must be specified together",
        )
        period = hgitutil.utc_period(args.start_date, args.end_date)
    # Authenticate and get repo.
    _LOG.info("Connecting to GitHub API...")
    gh_api = hgitutil.GitHubAPI()
    client = gh_api.get_client()
    _LOG.info("Fetching repository: %s", args.repo)
    repo_obj = client.get_repo(args.repo)
    hdbg.dassert_is_not(repo_obj, None, "Could not fetch repo: %s", args.repo)
    # Count open PRs.
    _LOG.info("Fetching open PRs...")
    open_stats = _count_open_prs_by_author(repo_obj)
    _print_open_pr_stats(open_stats)
    # Count closed PRs.
    _LOG.info("Fetching closed PRs...")
    closed_stats = _count_closed_prs_by_author(repo_obj, period=period)
    _print_closed_pr_stats(closed_stats, period=period)
    # Close connection.
    gh_api.close_connection()


if __name__ == "__main__":
    _main(_parse())
