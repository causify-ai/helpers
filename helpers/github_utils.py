"""
Import as:

import helpers.github_utils as hgitutil
"""

import datetime
import functools
import itertools
import json
import logging
import os
import time
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple

import github
import IPython
import matplotlib.pyplot as plt
import pandas as pd
import tqdm as td
from tqdm import tqdm

import helpers.hcache_simple as hcacsimp
import helpers.hdbg as hdbg

_LOG = logging.getLogger(__name__)


def github_cached(cache_type: str = "json", write_through: bool = True):
    """
    Cache decorator specifically for GitHub API functions.

    Automatically excludes the 'client' parameter (first positional arg)
    from cache keys since client instances change across sessions.

    :param cache_type: Type of cache ('json' or 'pickle')
    :param write_through: If True, write to disk after each cache update
    :return: Decorated function with caching
    """

    def decorator(func: Callable) -> Callable:
        # Get function name for cache
        func_name = func.__name__
        if func_name.endswith("_intrinsic"):
            func_name = func_name[: -len("_intrinsic")]
        # SET CACHE TYPE PROPERTY (this was missing!)
        existing_type = hcacsimp.get_cache_property("system", func_name, "type")
        if not existing_type:
            hcacsimp.set_cache_property("system", func_name, "type", cache_type)

        # Create a cached version that only uses args after client.
        @functools.wraps(func)
        def wrapper(client, *args, **kwargs):
            # Create cache key from everything EXCEPT client.
            cache_key = json.dumps(
                {"args": args, "kwargs": kwargs},
                sort_keys=True,
                default=str,
            )
            # Get cache.
            cache = hcacsimp.get_cache(func_name)
            # Check if we have cached value.
            if cache_key in cache:
                _LOG.debug("Cache hit for %s", func_name)
                return cache[cache_key]
            # Cache miss - call the actual function.
            _LOG.debug("Cache miss for %s, fetching from API", func_name)
            result = func(client, *args, **kwargs)
            # Store in cache
            cache[cache_key] = result
            # Write to disk if enabled.
            if write_through:
                hcacsimp.flush_cache_to_disk(func_name)
            return result

        return wrapper

    return decorator


# #############################################################################
# GitHubAPI
# #############################################################################


class GitHubAPI:
    """
    Initialize and manage authentication with the GitHub API using PyGithub.
    """

    def __init__(
        self,
        *,
        access_token: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Initialize the GitHub API client.

        :param access_token: GitHub personal access token; if not provided, it
            is fetched from the environment variable `GITHUB_ACCESS_TOKEN`
        :param base_url: optional custom GitHub Enterprise base URL
        """
        self.access_token = access_token or os.getenv("GITHUB_ACCESS_TOKEN")
        if not self.access_token:
            raise ValueError(
                "GitHub Access Token is required. Set it as an environment variable or pass it explicitly."
            )
        auth = github.Auth.Token(self.access_token)
        self.github = (
            github.Github(base_url=base_url, auth=auth)
            if base_url
            else github.Github(auth=auth)
        )

    def get_client(self) -> github.Github:
        """
        Return the authenticated GitHub client.

        :return: an instance of the authenticated PyGithub client
        """
        return self.github

    def close_connection(self) -> None:
        """
        Close the GitHub API connection.
        """
        self.github.close()


# #############################################################################
# Utility APIs
# #############################################################################


def get_repo_names(client: github.Github, org_name: str) -> Dict[str, List[str]]:
    """
    Retrieve a list of repositories under a specific organization.

    :param client: authenticated instance of the PyGithub client
    :param org_name: name of the GitHub organization
    :return: a dictionary containing:
        - owner: name of the organization
        - repositories: repository names
    """
    owner = client.get_organization(org_name)
    hdbg.dassert_is_not(
        owner, None, f"'{org_name}' is not a valid GitHub organization"
    )
    repos = [repo.name for repo in owner.get_repos()]
    result = {"owner": org_name, "repositories": repos}
    return result


def get_github_contributors(
    client: github.Github, repo_names: List[str]
) -> Dict[str, List[str]]:
    """
    Retrieve GitHub usernames contributing to specified repositories.

    :param client: authenticated instance of the PyGithub client
    :param repo_names: repository names in the format 'owner/repo' to fetch
        contributor usernames
    :return: a dictionary containing:
        - repository: repository name
        - contributors: contributor GitHub usernames
    """
    result = {}
    for repo_name in repo_names:
        repo = client.get_repo(repo_name)
        hdbg.dassert_is_not(repo, None, f"Could not fetch repo: {repo_name}")
        contributors = [
            contributor.login for contributor in repo.get_contributors()
        ]
        result[repo_name] = contributors
    return result


def normalize_period_to_utc(
    period: Optional[Tuple[datetime.datetime, datetime.datetime]],
) -> Tuple[Optional[datetime.datetime], Optional[datetime.datetime]]:
    """
    Convert a datetime period to UTC and ensure both dates are timezone-aware.

    :param period: start and end datetime
    :return: UTC-aware start and end datetime, or (None, None) if period
        is None
    """

    def to_utc(dt: Optional[datetime.datetime]) -> Optional[datetime.datetime]:
        res = None
        if dt is None:
            return res
        else:
            res = (
                dt.replace(tzinfo=datetime.timezone.utc)
                if dt.tzinfo is None
                else dt.astimezone(datetime.timezone.utc)
            )
        return res

    norm = (
        tuple(to_utc(dt) for dt in period) if period is not None else (None, None)
    )
    return norm


# #############################################################################
# Global Metrics APIs
# #############################################################################


def get_total_commits(
    client: github.Github,
    org_name: str,
    *,
    usernames: Optional[List[str]] = None,
    period: Optional[Tuple[datetime.datetime, datetime.datetime]] = None,
) -> Dict[str, Any]:
    """
    Fetch the number of commits made in the repositories of the specified
    organization, optionally filtered by GitHub usernames and a specified time
    period.

    :param client: authenticated instance of the PyGithub client
    :param org_name: name of the GitHub organization
    :param usernames: GitHub usernames to filter commits; if None, fetches for
        all users
    :param period: start and end datetime for filtering commits
    :return: a dictionary containing:
        - total_commits (int): total number of commits across all repositories
        - period (str): the time range considered
        - commits_per_repository (Dict[str, int]): repository names as keys and
          commit counts as values
    """
    # Retrieve organization repositories
    repos_info = get_repo_names(client, org_name)
    hdbg.dassert_in(
        "repositories",
        repos_info,
        "Missing 'repositories' key in get_repo_names() output",
    )
    repositories = repos_info["repositories"]
    total_commits = 0
    commits_per_repository = {}
    since, until = period if period else (None, None)
    for repo_name in tqdm(
        repositories, desc="Processing repositories", unit="repo"
    ):
        repo = client.get_repo(f"{org_name}/{repo_name}")
        hdbg.dassert_is_not(repo, None, f"Could not retrieve repo: {repo_name}")
        repo_commit_count = 0
        if usernames:
            for username in usernames:
                commits = repo.get_commits(
                    author=username, since=since, until=until
                )
                hdbg.dassert_is_not(
                    commits,
                    None,
                    f"Failed to get commits by '{username}' in {repo_name}",
                )
                repo_commit_count += commits.totalCount
        else:
            commits = repo.get_commits(since=since, until=until)
            hdbg.dassert_is_not(
                commits, None, f"Failed to get commits in {repo_name}"
            )
            repo_commit_count = commits.totalCount
        commits_per_repository[repo_name] = repo_commit_count
        total_commits += repo_commit_count
    result = {
        "total_commits": total_commits,
        "period": f"{since} to {until}" if since and until else "All time",
        "commits_per_repository": commits_per_repository,
    }
    return result


def get_total_prs(
    client: github.Github,
    org_name: str,
    *,
    usernames: Optional[List[str]] = None,
    period: Optional[Tuple[datetime.datetime, datetime.datetime]] = None,
    state: str = "all",
) -> Dict[str, Any]:
    """
    Fetch the number of pull requests made in the repositories of the specified
    organization, optionally filtered by GitHub usernames, a specified time
    period, and the state of the pull requests.

    :param client: authenticated instance of the PyGithub client
    :param org_name: name of the GitHub organization
    :param usernames: GitHub usernames to filter pull requests; if None, fetches
        for all users
    :param period: start and end datetime for filtering pull requests
    :param state: the state of the pull requests to fetch; can be 'open', 'closed', or 'all'
    :return: a dictionary containing:
        - total_prs (int): total number of pull requests
        - period (str): the time range considered
        - prs_per_repository (Dict[str, int]): repository names as keys and pull
            request counts as values
    """
    # Retrieve repositories for the organization
    repos_info = get_repo_names(client, org_name)
    hdbg.dassert_in(
        "repositories", repos_info, "Missing 'repositories' key in repo info"
    )
    repositories = repos_info["repositories"]
    total_prs = 0
    prs_per_repository = {}
    since, until = normalize_period_to_utc(period)
    for repo_name in tqdm(
        repositories, desc="Processing repositories", unit="repo"
    ):
        repo = client.get_repo(f"{org_name}/{repo_name}")
        hdbg.dassert_is_not(
            repo, None, f"Could not retrieve repository: {repo_name}"
        )
        repo_pr_count = 0
        pulls = repo.get_pulls(state=state)
        for pr in pulls:
            hdbg.dassert_is_not(
                pr, None, f"PR could not be fetched in {repo_name}"
            )
            if usernames and pr.user.login not in usernames:
                continue
            pr_created_at = (
                pr.created_at.replace(tzinfo=datetime.timezone.utc)
                if pr.created_at.tzinfo is None
                else pr.created_at.astimezone(datetime.timezone.utc)
            )
            if since and until and not (since <= pr_created_at <= until):
                continue
            repo_pr_count += 1
        prs_per_repository[repo_name] = repo_pr_count
        total_prs += repo_pr_count
    result = {
        "total_prs": total_prs,
        "period": f"{since} to {until}" if since and until else "All time",
        "prs_per_repository": prs_per_repository,
    }
    return result


def get_prs_not_merged(
    client: github.Github,
    org_name: str,
    *,
    usernames: Optional[List[str]] = None,
    period: Optional[Tuple[datetime.datetime, datetime.datetime]] = None,
) -> Dict[str, Any]:
    """
    Fetch the count of closed but unmerged pull requests in the specified
    repositories and by the specified GitHub users within a given period.

    :param client: authenticated instance of the PyGithub client
    :param org_name: name of the GitHub organization
    :param usernames: GitHub usernames to filter pull requests; if None, fetches for all users
    :param period: start and end datetime for filtering pull requests
    :return: a dictionary containing:
        - prs_not_merged (int): total number of closed but unmerged pull requests
        - period (str): the time range considered
        - prs_per_repository (Dict[str, int]): repository names as keys and
            unmerged pull request counts as values
    """
    # Fetch all repositories in the org.
    repos_info = get_repo_names(client, org_name)
    hdbg.dassert_in(
        "repositories",
        repos_info,
        "Missing 'repositories' in get_repo_names() output",
    )
    repositories = repos_info["repositories"]
    total_unmerged_prs = 0
    prs_per_repository = {}
    since, until = normalize_period_to_utc(period)
    for repo_name in tqdm(
        repositories, desc="Processing repositories", unit="repo"
    ):
        # Fetch repo object.
        repo = client.get_repo(f"{org_name}/{repo_name}")
        hdbg.dassert_is_not(
            repo, None, f"Could not fetch repo: {org_name}/{repo_name}"
        )
        repo_unmerged_pr_count = 0
        issues = repo.get_issues(state="closed", since=since)
        pulls = []
        for issue in issues:
            if issue.pull_request:
                pull = repo.get_pull(issue.number)
                hdbg.dassert_is_not(
                    pull,
                    None,
                    f"Could not fetch pull request #{issue.number} in {repo_name}",
                )
                pulls.append(pull)
        for pr in pulls:
            _LOG.debug("Processing PR #%d from %s", pr.number, repo_name)
            pr_created_at = pr.created_at or datetime.datetime.min
            pr_created_at = (
                pr_created_at.replace(tzinfo=datetime.timezone.utc)
                if pr_created_at.tzinfo is None
                else pr_created_at.astimezone(datetime.timezone.utc)
            )
            if pr.merged:
                continue
            if usernames and pr.user.login not in usernames:
                continue
            if since and until and not (since <= pr_created_at <= until):
                continue
            repo_unmerged_pr_count += 1
        prs_per_repository[repo_name] = repo_unmerged_pr_count
        total_unmerged_prs += repo_unmerged_pr_count
    result = {
        "prs_not_merged": total_unmerged_prs,
        "period": f"{since} to {until}" if since and until else "All time",
        "prs_per_repository": prs_per_repository,
    }
    return result


# #############################################################################
# Individual User Metrics APIs
# #############################################################################


def get_commits_by_user(
    client: github.Github,
    username: str,
    org_name: str,
    *,
    period: Optional[Tuple[datetime.datetime, datetime.datetime]] = None,
) -> Dict[str, Any]:
    """
    Retrieve the number of commits made by a specific GitHub user.

    :param client: authenticated instance of the PyGithub client
    :param username: GitHub username to fetch commit data for
    :param org_name: name of the GitHub organization
    :param period: start and end datetime for filtering commits
    :return: a dictionary containing:
        - user (str): GitHub username
        - total_commits (int): total number of commits made by the user
        - period (str): the time range considered
        - commits_per_repository (Dict[str, int]): repository names as keys and
          commit counts as values
    """
    result = get_total_commits(
        client=client, org_name=org_name, usernames=[username], period=period
    )
    res_dict = {
        "user": username,
        "total_commits": result["total_commits"],
        "period": result["period"],
        "commits_per_repository": result["commits_per_repository"],
    }
    return res_dict


def get_prs_by_user(
    client: github.Github,
    username: str,
    org_name: str,
    *,
    period: Optional[Tuple[datetime.datetime, datetime.datetime]] = None,
    state: str = "all",
) -> Dict[str, Any]:
    """
    Fetch the number of pull requests created by a specific GitHub user in the
    given repositories and time period.

    :param client: authenticated instance of the PyGithub client
    :param username: GitHub username to fetch pull request data for
    :param org_name: name of the GitHub organization
    :param period: start and end datetime for filtering pull requests
    :param state: state of the pull requests to fetch; can be 'open', 'closed',
        or 'all'
    :return: a dictionary containing:
        - user (str): GitHub username
        - total_prs (int): total number of pull requests created
        - period (str): the time range considered
        - prs_per_repository (Dict[str, int]): repository names as keys and pull
          request counts as values
    """
    result = get_total_prs(
        client=client,
        org_name=org_name,
        usernames=[username],
        period=period,
        state=state,
    )
    res_dict = {
        "user": username,
        "total_prs": result["total_prs"],
        "period": result["period"],
        "prs_per_repository": result["prs_per_repository"],
    }
    return res_dict


def get_prs_not_merged_by_user(
    client: github.Github,
    username: str,
    org_name: str,
    *,
    period: Optional[Tuple[datetime.datetime, datetime.datetime]] = None,
) -> Dict[str, Any]:
    """
    Fetch the number of closed but unmerged pull requests created by a specific
    GitHub user in the given repositories and time period.

    :param client: authenticated instance of the PyGithub client
    :param username: GitHub username to fetch unmerged pull request data for
    :param org_name: name of the GitHub organization
    :param period: start and end datetime for filtering pull requests
    :return: a dictionary containing:
        - user (str): GitHub username
        - prs_not_merged (int): total number of closed but unmerged pull requests
        - period (str): the time range considered
        - prs_per_repository (Dict[str, int]): repository names as keys and
          unmerged PR counts as values
    """
    result = get_prs_not_merged(
        client=client, org_name=org_name, usernames=[username], period=period
    )
    res_dict = {
        "user": username,
        "prs_not_merged": result["prs_not_merged"],
        "period": result["period"],
        "prs_per_repository": result["prs_per_repository"],
    }
    return res_dict


def days_between(
    period: Tuple[datetime.datetime, datetime.datetime],
) -> List[datetime.date]:
    """
    Generate each date in time span.

    :param period: start and end datetime
    :return: date span
    """
    start_date = period[0].date()
    end_date = period[1].date()
    days: List[datetime.date] = []
    current = start_date
    while current <= end_date:
        days.append(current)
        current += datetime.timedelta(days=1)
    _LOG.debug("Generated %d days in period.", len(days))
    return days


@github_cached(cache_type="json", write_through=True)
def get_commit_datetimes_by_repo_period_intrinsic(
    client,
    org: str,
    repo: str,
    username: Optional[str],
    since: datetime.datetime,
    until: datetime.datetime,
) -> List[str]:
    """
    Fetch commit timestamps for user in repo over period.

    :param client: authenticated PyGithub client
    :param org: GitHub org name
    :param repo: repository name
    :param username: GitHub username
    :param since: start datetime
    :param until: end datetime
    :return: commit timestamps in ISO format
    """
    timestamps: List[str] = []
    # Fetch the repository object.
    repo_obj = client.get_repo(f"{org}/{repo}")
    # Retrieve all commits in the specified time period.
    commits = repo_obj.get_commits(since=since, until=until)
    # Iterate through each commit to find ones by the specified user.
    for c in commits:
        # Skip commits with incomplete metadata.
        if not c.commit or not c.commit.author or not c.commit.author.date:
            continue
        # Extract author and committer logins.
        author_login = c.author.login if c.author else None
        committer_login = c.committer.login if c.committer else None
        # Check if this commit belongs to the target user.
        if username in (author_login, committer_login):
            # Convert commit date to UTC timezone.
            dt = c.commit.author.date
            dt_utc = dt if dt.tzinfo else dt.replace(tzinfo=datetime.timezone.utc)
            # Add timestamp to results list.
            timestamps.append(dt_utc.isoformat())
    # Log the results summary.
    if not timestamps:
        _LOG.info(
            "No commits found for %s/%s user=%s in %s to %s — possibly outdated or inactive.",
            org,
            repo,
            username,
            since.date(),
            until.date(),
        )
    else:
        _LOG.info(
            "Fetched %d commits for %s/%s user=%s.",
            len(timestamps),
            org,
            repo,
            username,
        )

    return timestamps


@github_cached(cache_type="json", write_through=True)
def get_pr_datetimes_by_repo_period_intrinsic(
    client,
    org: str,
    repo: str,
    username: str,
    since: datetime.datetime,
    until: datetime.datetime,
) -> List[str]:
    """
    Fetch pull request timestamps for user in repo over period.

    :param client: authenticated PyGithub client
    :param org: GitHub org name
    :param repo: repository name
    :param username: GitHub username
    :param since: start datetime
    :param until: end datetime
    :return: PR created timestamps in ISO format
    """
    timestamps: List[str] = []
    # Format dates for GitHub search query.
    since_date = since.date().isoformat()
    until_date = until.date().isoformat()
    # Build search query for PRs authored by the user.
    query = f"repo:{org}/{repo} is:pr author:{username} created:{since_date}..{until_date}"
    # Execute the search query.
    results = client.search_issues(query)
    # Process each PR from search results.
    for issue in results:
        # Convert PR creation date to UTC timezone.
        dt = issue.created_at
        dt_utc = dt if dt.tzinfo else dt.replace(tzinfo=datetime.timezone.utc)
        # Add timestamp to results list.
        timestamps.append(dt_utc.isoformat())
    # Log the results summary.
    if not timestamps:
        _LOG.debug(
            "No PRs found for %s/%s user=%s in %s to %s — possibly inactive or outdated.",
            org,
            repo,
            username,
            since_date,
            until_date,
        )
    else:
        _LOG.info(
            "Found %d PRs for %s/%s user=%s.",
            len(timestamps),
            org,
            repo,
            username,
        )

    return timestamps


@github_cached(cache_type="json", write_through=True)
def get_issue_datetimes_by_repo_intrinsic(
    client,
    org: str,
    repo: str,
    username: str,
    period: Tuple[datetime.datetime, datetime.datetime],
) -> Dict[str, List[str]]:
    """
    Fetch opened and closed issue timestamps for a user in a repo over a given
    period.

    :param client: authenticated PyGithub client
    :param org: GitHub organization name
    :param repo: repository name
    :param username: GitHub username
    :param period: time window to filter issues
    :return: 'assigned' and 'closed' issues containing ISO timestamps
    """
    # Extract and format the time period.
    since_date = period[0].date().isoformat()
    until_date = period[1].date().isoformat()
    # Build search query for issues assigned to the user.
    query = (
        f"repo:{org}/{repo} type:issue assignee:{username} "
        f"created:{since_date}..{until_date}"
    )
    # Execute the search query.
    issues = client.search_issues(query)
    # Initialize lists for assigned and closed issues.
    assigned: List[str] = []
    closed: List[str] = []
    # Process each issue from search results.
    for issue in issues:
        # Skip pull requests that appear in issue search.
        if issue.pull_request is not None:
            continue
        # Add issue creation timestamp to assigned list.
        assigned.append(issue.created_at.isoformat())
        # Check if issue was closed within the period.
        if issue.closed_at:
            # Convert closed date to UTC timezone.
            closed_dt = issue.closed_at
            dt_utc = (
                closed_dt
                if closed_dt.tzinfo
                else closed_dt.replace(tzinfo=datetime.timezone.utc)
            )
            # Add to closed list if within the specified period.
            if period[0] <= dt_utc <= period[1]:
                closed.append(dt_utc.isoformat())
    # Log the results summary.
    _LOG.info(
        "Found %d opened and %d closed issues for %s/%s user=%s",
        len(assigned),
        len(closed),
        org,
        repo,
        username,
    )
    # Return the results dictionary.
    result_dict = {"assigned": assigned, "closed": closed}
    return result_dict


@github_cached(cache_type="json", write_through=True)
def get_loc_stats_by_repo_period_intrinsic(
    client,
    org: str,
    repo: str,
    username: str,
    since: datetime.datetime,
    until: datetime.datetime,
) -> List[Dict[str, int]]:
    """
    Fetch commit LOC stats for user in repo over period.

    :param client: authenticated PyGithub client
    :param org: GitHub org name
    :param repo: repository name
    :param username: GitHub username
    :param since: start datetime
    :param until: end datetime
    :return: additions, deletions in code
    """
    stats_list: List[Dict[str, int]] = []
    # Fetch the repository object.
    repo_obj = client.get_repo(f"{org}/{repo}")
    # Retrieve all commits in the specified time period.
    commits = repo_obj.get_commits(since=since, until=until)
    # Track number of commits processed for safety limit.
    commit_count = 0
    # Process each commit to extract LOC statistics.
    for c in commits:
        # Extract author and committer logins.
        author_login = c.author.login if c.author else None
        committer_login = c.committer.login if c.committer else None
        # Skip commits not by the target user.
        if username not in (author_login, committer_login):
            continue
        # Fetch commit statistics.
        s = c.stats
        # Skip if statistics are not available.
        if s is None:
            _LOG.debug("No stats available for commit %s", c.sha)
            continue
        # Convert commit date to UTC timezone.
        dt = c.commit.author.date
        dt_utc = dt if dt.tzinfo else dt.replace(tzinfo=datetime.timezone.utc)
        iso = dt_utc.date().isoformat()
        # Add statistics to results list.
        stats_list.append(
            {"date": iso, "additions": s.additions, "deletions": s.deletions}
        )
        # Increment commit counter and check safety limit.
        commit_count += 1
        if commit_count > 1000:
            _LOG.warning("Processed 1000 commits, stopping to avoid timeout")
            break
    # Log the results summary.
    if not stats_list:
        _LOG.info(
            "No LOC stats found for %s/%s user=%s in %s to %s — possibly inactive or outdated.",
            org,
            repo,
            username,
            since.date(),
            until.date(),
        )
    else:
        _LOG.info(
            "Fetched LOC stats for %s/%s user=%s entries=%d.",
            org,
            repo,
            username,
            len(stats_list),
        )

    return stats_list


@github_cached(cache_type="json", write_through=True)
def get_issue_comment_datetimes_by_repo_period_intrinsic(
    client,
    org: str,
    repo: str,
    username: str,
    since: datetime.datetime,
    until: datetime.datetime,
) -> List[str]:
    """
    Fetch issue comment timestamps for user in repo over period using search
    API.

    :param client: authenticated PyGithub client
    :param org: GitHub org name
    :param repo: repository name
    :param username: GitHub username
    :param since: start datetime
    :param until: end datetime
    :return: comment timestamps in ISO format
    """
    timestamps: List[str] = []
    # Format dates for GitHub search query.
    since_date = since.date().isoformat()
    until_date = until.date().isoformat()
    # Build search query for issues where user has commented.
    query = f"repo:{org}/{repo} is:issue commenter:{username} updated:{since_date}..{until_date}"
    # Execute the search query.
    results = client.search_issues(query)
    # Process each issue to find user's comments.
    for issue in results:
        # Skip pull requests that appear in issue search.
        if issue.pull_request:
            continue
        # Fetch all comments for this issue.
        comments = issue.get_comments()
        # Filter comments by the target user.
        for comment in comments:
            # Skip comments by other users.
            if comment.user.login != username:
                continue
            # Convert comment date to UTC timezone.
            comment_dt = comment.created_at
            comment_dt_utc = (
                comment_dt
                if comment_dt.tzinfo
                else comment_dt.replace(tzinfo=datetime.timezone.utc)
            )
            # Add timestamp if within the specified period.
            if since <= comment_dt_utc <= until:
                timestamps.append(comment_dt_utc.isoformat())
    # Log the results summary.
    if not timestamps:
        _LOG.info(
            "No issue comments found for %s/%s user=%s in %s to %s — possibly inactive or outdated.",
            org,
            repo,
            username,
            since.date(),
            until.date(),
        )
    else:
        _LOG.info(
            "Fetched %d issue comments for %s/%s user=%s.",
            len(timestamps),
            org,
            repo,
            username,
        )
    return timestamps


@github_cached(cache_type="json", write_through=True)
def get_pr_review_datetimes_by_repo_period_intrinsic(
    client,
    org: str,
    repo: str,
    username: str,
    since: datetime.datetime,
    until: datetime.datetime,
) -> List[str]:
    """
    Fetch PR review timestamps for user in repo over period.

    :param client: authenticated PyGithub client
    :param org: GitHub org name
    :param repo: repository name
    :param username: GitHub username
    :param since: start datetime
    :param until: end datetime
    :return: review timestamps in ISO format
    """
    timestamps: List[str] = []
    # Fetch the repository object.
    repo_obj = client.get_repo(f"{org}/{repo}")
    # Format dates for GitHub search query.
    since_date = since.date().isoformat()
    until_date = until.date().isoformat()
    # Build search query for PRs reviewed by the user.
    query = f"repo:{org}/{repo} is:pr reviewed-by:{username} updated:{since_date}..{until_date}"
    # Execute the search query.
    results = client.search_issues(query)
    # Process each PR to find user's reviews.
    for issue in results:
        # Fetch the full PR object.
        pr = repo_obj.get_pull(issue.number)
        # Fetch all reviews for this PR.
        reviews = pr.get_reviews()
        # Filter reviews by the target user.
        for review in reviews:
            # Skip reviews by other users.
            if review.user.login != username:
                continue
            # Convert review date to UTC timezone.
            review_dt = review.submitted_at
            review_dt_utc = (
                review_dt
                if review_dt.tzinfo
                else review_dt.replace(tzinfo=datetime.timezone.utc)
            )
            # Add timestamp if within the specified period.
            if since <= review_dt_utc <= until:
                timestamps.append(review_dt_utc.isoformat())
    # Log the results summary.
    if not timestamps:
        _LOG.info(
            "No PR reviews found for %s/%s user=%s in %s to %s — possibly inactive or outdated.",
            org,
            repo,
            username,
            since.date(),
            until.date(),
        )
    else:
        _LOG.info(
            "Fetched %d PR reviews for %s/%s user=%s.",
            len(timestamps),
            org,
            repo,
            username,
        )

    return timestamps


def build_daily_commit_df(
    client,
    org: str,
    repo: str,
    username: str,
    period: Tuple[datetime.datetime, datetime.datetime],
) -> pd.DataFrame:
    """
    Build daily commit counts for user and repo over period.

    :param client: authenticated PyGithub client
    :param org: GitHub org name
    :param repo: repository name
    :param username: GitHub username
    :param period: start and end datetime objects
    :return: data with date, commits, repo, user
    """
    since, until = period
    timestamps = get_commit_datetimes_by_repo_period_intrinsic(
        client, org, repo, username, since, until
    )
    df = pd.DataFrame({"ts": pd.to_datetime(timestamps)})
    df["date"] = df.ts.dt.date
    daily = df.groupby("date").size().reset_index(name="commits")
    all_days = pd.DataFrame({"date": days_between(period)})
    daily = all_days.merge(daily, on="date", how="left")
    daily["commits"] = daily["commits"].fillna(0).astype(int)
    daily["repo"] = repo
    daily["user"] = username
    _LOG.debug("Built daily commit DataFrame rows=%d.", len(daily))
    return daily


def slice_by_date(df, start, end, date_col="date"):
    """
    Slice DataFrame by date range.

    :param df: input DataFrame
    :param start: start date (inclusive)
    :param end: end date (inclusive)
    :param date_col: name of the date column in df
    :return: filtered DataFrame
    """
    out = df.copy()
    out[date_col] = pd.to_datetime(out[date_col], errors="coerce")
    res = out.loc[(out[date_col] >= start) & (out[date_col] <= end)].copy()
    return res


def build_daily_issue_df(
    client,
    org: str,
    repo: str,
    username: str,
    period: Tuple[datetime.datetime, datetime.datetime],
) -> pd.DataFrame:
    """
    Build daily assigned / closed issue counts for a user-repo pair.

    :param client: authenticated PyGithub client
    :param org: GitHub org name
    :param repo: repository name
    :param username: GitHub username
    :param period: start and end datetime objects
    :return: data with columns date, issues_assigned, issues_closed,
        repo, user
    """
    issue_data = get_issue_datetimes_by_repo_intrinsic(
        client, org, repo, username, period
    )
    df_assigned = pd.DataFrame(
        {"ts": pd.to_datetime(issue_data["assigned"]), "issues_assigned": 1}
    )
    df_assigned["date"] = df_assigned.ts.dt.date
    df_closed = pd.DataFrame(
        {"ts": pd.to_datetime(issue_data["closed"]), "issues_closed": 1}
    )
    df_closed["date"] = df_closed.ts.dt.date
    # Daily counts.
    daily_assigned = (
        df_assigned.groupby("date")["issues_assigned"].sum().reset_index()
    )
    daily_closed = df_closed.groupby("date")["issues_closed"].sum().reset_index()
    all_days = pd.DataFrame({"date": days_between(period)})
    daily = all_days.merge(daily_assigned, on="date", how="left").merge(
        daily_closed, on="date", how="left"
    )
    daily[["issues_assigned", "issues_closed"]] = (
        daily[["issues_assigned", "issues_closed"]].fillna(0).astype(int)
    )
    daily["repo"] = repo
    daily["user"] = username
    _LOG.debug("Built daily issue DataFrame rows=%d.", len(daily))
    return daily


def build_daily_pr_df(
    client,
    org: str,
    repo: str,
    username: str,
    period: Tuple[datetime.datetime, datetime.datetime],
) -> pd.DataFrame:
    """
    Build daily PR counts for user and repo over period.

    :param client: authenticated PyGithub client
    :param org: GitHub org name
    :param repo: repository name
    :param username: GitHub username
    :param period: start and end datetime objects
    :return: data with date, prs, repo, user
    """
    since, until = period
    timestamps = get_pr_datetimes_by_repo_period_intrinsic(
        client, org, repo, username, since, until
    )
    df = pd.DataFrame({"ts": pd.to_datetime(timestamps)})
    df["date"] = df.ts.dt.date
    daily = df.groupby("date").size().reset_index(name="prs")
    all_days = pd.DataFrame({"date": days_between(period)})
    daily = all_days.merge(daily, on="date", how="left")
    daily["prs"] = daily["prs"].fillna(0).astype(int)
    daily["repo"] = repo
    daily["user"] = username
    _LOG.debug("Built daily PR DataFrame rows=%d.", len(daily))
    return daily


def build_daily_loc_df(
    client,
    org: str,
    repo: str,
    username: str,
    period: Tuple[datetime.datetime, datetime.datetime],
) -> pd.DataFrame:
    """
    Build daily LOC additions and deletions for user and repo over period.

    :param client: authenticated PyGithub client
    :param org: GitHub org name
    :param repo: repository name
    :param username: GitHub username
    :param period: start and end datetime objects
    :return: data with date, additions, deletions, repo, user
    """
    since, until = period
    # Fetch raw LOC stats list.
    stats_list = get_loc_stats_by_repo_period_intrinsic(
        client, org, repo, username, since, until
    )
    # If no stats, return zeros for full range.
    if not stats_list:
        all_days = pd.DataFrame({"date": days_between(period)})
        # Initialize zeroes.
        all_days["additions"] = all_days["date"].apply(lambda _: 0)
        all_days["deletions"] = all_days["date"].apply(lambda _: 0)
        # Format signs.
        all_days["additions"] = (
            all_days["additions"].astype(str).apply(lambda x: "+" + x)
        )
        all_days["deletions"] = (
            all_days["deletions"].astype(str).apply(lambda x: "-" + x)
        )
        # Add context.
        all_days["repo"] = repo
        all_days["user"] = username
        # TODO(*): Logging-248: Use `_LOG.debug()` instead of `_LOG.info()` for tracing execution.
        _LOG.debug("Built daily LOC DataFrame rows=%d (no data).", len(all_days))
        return all_days
    # Otherwise build from stats_list.
    df = pd.DataFrame(stats_list)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    # Sum per date.
    daily = df.groupby("date")[["additions", "deletions"]].sum().reset_index()
    # Ensure full date coverage.
    all_days = pd.DataFrame({"date": days_between(period)})
    daily = all_days.merge(daily, on="date", how="left")
    # Fill missing and integerize.
    daily[["additions", "deletions"]] = (
        daily[["additions", "deletions"]].fillna(0).astype(int)
    )
    # Apply sign formatting.
    daily["additions"] = daily["additions"].astype(str).apply(lambda x: "+" + x)
    daily["deletions"] = daily["deletions"].astype(str).apply(lambda x: "-" + x)
    # Add context.
    daily["repo"] = repo
    daily["user"] = username
    _LOG.debug("Built daily LOC DataFrame rows=%d.", len(daily))
    return daily


def get_total_loc_for_period(
    client,
    org: str,
    repo: str,
    username: str,
    period: Tuple[datetime.datetime, datetime.datetime],
) -> Dict[str, int]:
    """
    Get total LOC additions and deletions for user and repo over period.

    :param client: authenticated PyGithub client
    :param org: GitHub org name
    :param repo: repository name
    :param username: GitHub username
    :param period: start and end datetime objects
    :return: additions and deletions totals
    """
    since, until = period
    stats = get_loc_stats_by_repo_period_intrinsic(
        client, org, repo, username, since, until
    )
    total_add = sum(item["additions"] for item in stats)
    total_del = sum(item["deletions"] for item in stats)
    _LOG.info(
        "Total LOC for %s/%s user=%s => +%d -%d.",
        org,
        repo,
        username,
        total_add,
        total_del,
    )
    return {"additions": total_add, "deletions": total_del}


def prefetch_periodic_user_repo_data(
    client,
    org: str,
    repos: List[str],
    users: List[str],
    period: Tuple[datetime.datetime, datetime.datetime],
) -> None:
    """
    Prefetch and cache commits, PRs, LOC, issues, comments, and reviews for
    each user and repo over period.

    :param client: authenticated PyGithub client
    :param org: GitHub org name
    :param repos: repository names
    :param users: GitHub usernames
    :param period: start and end datetime objects
    """
    # Validate input types.
    if not isinstance(org, str):
        raise ValueError(f"org must be a string, got {type(org).__name__}")
    if not isinstance(repos, list) or not all(isinstance(r, str) for r in repos):
        raise ValueError("repos must be a list of strings")
    if not isinstance(users, list) or not all(isinstance(u, str) for u in users):
        raise ValueError("users must be a list of strings")
    # Initialize timer and pair up (repo, user) combinations.
    start = time.time()
    count = 0
    since, until = period
    user_repo_pairs = list(itertools.product(repos, users))
    # Prefetch and cache GitHub data for each user-repo pair
    for repo, user in td.tqdm(user_repo_pairs, desc="Prefetching user-repo data"):
        commits = get_commit_datetimes_by_repo_period_intrinsic(
            client, org, repo, user, since, until
        )
        prs = get_pr_datetimes_by_repo_period_intrinsic(
            client, org, repo, user, since, until
        )
        locs = get_loc_stats_by_repo_period_intrinsic(
            client, org, repo, user, since, until
        )
        issues = get_issue_datetimes_by_repo_intrinsic(
            client, org, repo, user, period
        )
        # issue_comments = get_issue_comment_datetimes_by_repo_period_intrinsic(
        #     client, org, repo, user, since, until
        # )
        # pr_reviews = get_pr_review_datetimes_by_repo_period_intrinsic(
        #     client, org, repo, user, since, until
        # )
        issue_comments = []
        pr_reviews = []
        td.tqdm.write(
            f"{repo}/{user}: {len(commits)} commits, {len(prs)} PRs, "
            f"{len(locs)} LOC entries, {len(issues['assigned'])} issues assigned, "
            f"{len(issues['closed'])} closed, {len(issue_comments)} issue comments, "
            f"{len(pr_reviews)} PR reviews"
        )
        count += 1
    # Report overall prefetch duration.
    elapsed = time.time() - start
    _LOG.info(
        "Prefetched %d user-repo combos in %.2f seconds for period %s to %s.",
        count,
        elapsed,
        period[0],
        period[1],
    )


def build_daily_issue_comment_df(
    client,
    org: str,
    repo: str,
    username: str,
    period: Tuple[datetime.datetime, datetime.datetime],
) -> pd.DataFrame:
    """
    Build daily issue comment counts for user and repo over period.

    :param client: authenticated PyGithub client
    :param org: GitHub org name
    :param repo: repository name
    :param username: GitHub username
    :param period: start and end datetime objects
    :return: data with date, issue_comments, repo, user
    """
    since, until = period
    timestamps = get_issue_comment_datetimes_by_repo_period_intrinsic(
        client, org, repo, username, since, until
    )
    df = pd.DataFrame({"ts": pd.to_datetime(timestamps)})
    df["date"] = df.ts.dt.date
    daily = df.groupby("date").size().reset_index(name="issue_comments")
    all_days = pd.DataFrame({"date": days_between(period)})
    daily = all_days.merge(daily, on="date", how="left")
    daily["issue_comments"] = daily["issue_comments"].fillna(0).astype(int)
    daily["repo"] = repo
    daily["user"] = username
    _LOG.debug("Built daily issue comment DataFrame rows=%d.", len(daily))
    return daily


def build_daily_pr_review_df(
    client,
    org: str,
    repo: str,
    username: str,
    period: Tuple[datetime.datetime, datetime.datetime],
) -> pd.DataFrame:
    """
    Build daily PR review counts for user and repo over period.

    :param client: authenticated PyGithub client
    :param org: GitHub org name
    :param repo: repository name
    :param username: GitHub username
    :param period: start and end datetime objects
    :return: data with date, pr_reviews, repo, user
    """
    since, until = period
    timestamps = get_pr_review_datetimes_by_repo_period_intrinsic(
        client, org, repo, username, since, until
    )
    df = pd.DataFrame({"ts": pd.to_datetime(timestamps)})
    df["date"] = df.ts.dt.date
    daily = df.groupby("date").size().reset_index(name="pr_reviews")
    all_days = pd.DataFrame({"date": days_between(period)})
    daily = all_days.merge(daily, on="date", how="left")
    daily["pr_reviews"] = daily["pr_reviews"].fillna(0).astype(int)
    daily["repo"] = repo
    daily["user"] = username
    _LOG.debug("Built daily PR review DataFrame rows=%d.", len(daily))
    return daily


def collect_all_metrics(
    client,
    org: str,
    repos: List[str],
    users: List[str],
    period: Tuple[datetime.datetime, datetime.datetime],
    skip_issue_comments: bool = True,
    skip_pr_reviews: bool = True,
) -> pd.DataFrame:
    """
    Collect daily metrics for all user-repo combinations.

    :param client: authenticated PyGithub client
    :param org: Github org name
    :param repos: repository names
    :param users: github usernames
    :param period: start and end datetime
    :param skip_issue_comments: skip fetching issue comments (for speed)
    :param skip_pr_reviews: skip fetching PR reviews (for speed)
    :return: concatenated data with date, commits, prs, additions,
        deletions, issues_assigned, issues_closed, issue_comments
        (optional), pr_reviews (optional), repo, user
    """
    combined_frames: List[pd.DataFrame] = []
    # Track progress.
    total_combinations = len(repos) * len(users)
    current = 0
    for repo in repos:
        # Ensure repo is a string.
        if not isinstance(repo, str):
            raise ValueError(f"Expected repo to be a string but got {repo!r}")
        for user in users:
            # Ensure user is a string.
            if not isinstance(user, str):
                raise ValueError(f"Expected user to be a string but got {user!r}")
            current += 1
            _LOG.info(f"Processing {current}/{total_combinations}: {repo}/{user}")
            # Build each metric DataFrame.
            df_c = build_daily_commit_df(client, org, repo, user, period)
            df_p = build_daily_pr_df(client, org, repo, user, period)
            df_l = build_daily_loc_df(client, org, repo, user, period)
            df_i = build_daily_issue_df(client, org, repo, user, period)
            # Start merging with required metrics.
            df = (
                df_c.merge(df_p, on=["date", "repo", "user"], how="inner")
                .merge(df_l, on=["date", "repo", "user"], how="inner")
                .merge(df_i, on=["date", "repo", "user"], how="inner")
            )
            # Optionally add issue comments.
            if not skip_issue_comments:
                df_ic = build_daily_issue_comment_df(
                    client, org, repo, user, period
                )
                df = df.merge(df_ic, on=["date", "repo", "user"], how="inner")
            else:
                # Add dummy column for consistency.
                df["issue_comments"] = 0
            # Optionally add PR reviews.
            if not skip_pr_reviews:
                df_pr = build_daily_pr_review_df(client, org, repo, user, period)
                df = df.merge(df_pr, on=["date", "repo", "user"], how="inner")
            else:
                # Add dummy column for consistency.
                df["pr_reviews"] = 0
            combined_frames.append(df)
    # Concatenate all DataFrames or return empty.
    combined = (
        pd.concat(combined_frames, ignore_index=True)
        if combined_frames
        else pd.DataFrame()
    )
    _LOG.info(f"Collected metrics for {len(combined)} daily records")
    return combined


def summarize_user_metrics_for_repo(
    combined: pd.DataFrame, repo: str
) -> pd.DataFrame:
    """
    Summarize total commits, PRs, LOC, issues, comments, and reviews per user
    in a specific repository.

    :param combined: data with all metrics
    :param repo: repository name
    :return: data with columns user, commits, prs, additions, deletions,
        issues_assigned, issues_closed, issue_comments, pr_reviews
    """
    df = combined[combined["repo"] == repo].copy()
    df["additions"] = df["additions"].str.replace("+", "").astype(int)
    df["deletions"] = df["deletions"].str.replace("-", "").astype(int)
    df["issues_assigned"] = df["issues_assigned"].astype(int)
    df["issues_closed"] = df["issues_closed"].astype(int)
    # df["issue_comments"] = df["issue_comments"].astype(int)
    # df["pr_reviews"] = df["pr_reviews"].astype(int)
    summary = (
        df.groupby("user")
        .agg(
            commits=pd.NamedAgg(column="commits", aggfunc="sum"),
            prs=pd.NamedAgg(column="prs", aggfunc="sum"),
            additions=pd.NamedAgg(column="additions", aggfunc="sum"),
            deletions=pd.NamedAgg(column="deletions", aggfunc="sum"),
            issues_assigned=pd.NamedAgg(column="issues_assigned", aggfunc="sum"),
            issues_closed=pd.NamedAgg(column="issues_closed", aggfunc="sum"),
            # issue_comments=pd.NamedAgg(column="issue_comments", aggfunc="sum"),
            # pr_reviews=pd.NamedAgg(column="pr_reviews", aggfunc="sum"),
        )
        .reset_index()
    )
    return summary


def summarize_repo_metrics_for_user(
    combined: pd.DataFrame, user: str
) -> pd.DataFrame:
    """
    Summarize total commits, PRs, LOC, issues, comments, and reviews per repo
    for a user.

    :param combined: data with all metrics
    :param user: GitHub username
    :return: columns repo, commits, prs, additions, deletions,
        issues_assigned, issues_closed, issue_comments, pr_reviews
    """
    df = combined[combined["user"] == user].copy()
    df["additions"] = df["additions"].str.replace("+", "").astype(int)
    df["deletions"] = df["deletions"].str.replace("-", "").astype(int)
    df["issue_comments"] = df["issue_comments"].astype(int)
    df["pr_reviews"] = df["pr_reviews"].astype(int)
    summary = (
        df.groupby("repo")
        .agg(
            commits=pd.NamedAgg(column="commits", aggfunc="sum"),
            prs=pd.NamedAgg(column="prs", aggfunc="sum"),
            additions=pd.NamedAgg(column="additions", aggfunc="sum"),
            deletions=pd.NamedAgg(column="deletions", aggfunc="sum"),
            issues_assigned=pd.NamedAgg(column="issues_assigned", aggfunc="sum"),
            issues_closed=pd.NamedAgg(column="issues_closed", aggfunc="sum"),
            issue_comments=pd.NamedAgg(column="issue_comments", aggfunc="sum"),
            pr_reviews=pd.NamedAgg(column="pr_reviews", aggfunc="sum"),
        )
        .reset_index()
    )
    return summary


def summarize_users_across_repos(
    combined: pd.DataFrame,
    users: List[str],
    repos: List[str],
) -> pd.DataFrame:
    """
    Aggregate commit / PR / LOC / issue / comment / review totals per-user
    across a repo subset.

    :param combined: output of `collect_all_metrics`
    :param users: GitHub usernames
    :param repos: repository names
    :return: data with columns user, commits, prs, additions, deletions,
        issues_assigned, issues_closed, issue_comments, pr_reviews
    """
    # Filter to requested slice.
    df = combined[
        combined["user"].isin(users) & combined["repo"].isin(repos)
    ].copy()
    # Normalise numeric columns.
    df["additions"] = df["additions"].str.replace("+", "").astype(int)
    df["deletions"] = df["deletions"].str.replace("-", "").astype(int)
    df["issue_comments"] = df["issue_comments"].astype(int)
    df["pr_reviews"] = df["pr_reviews"].astype(int)
    df.rename(
        columns={
            "issues_assigned": "issues_assigned",
            "issues_closed": "issues_closed",
        },
        inplace=True,
        errors="ignore",
    )
    # Aggregate across repos.
    summary = (
        df.groupby("user")
        .agg(
            commits=("commits", "sum"),
            prs=("prs", "sum"),
            additions=("additions", "sum"),
            deletions=("deletions", "sum"),
            issues_assigned=("issues_assigned", "sum"),
            issues_closed=("issues_closed", "sum"),
            issue_comments=("issue_comments", "sum"),
            pr_reviews=("pr_reviews", "sum"),
        )
        .reset_index()
    )
    return summary


def _filter_period(
    df: pd.DataFrame,
    *,
    start: Optional[datetime.datetime] = None,
    end: Optional[datetime.datetime] = None,
) -> pd.DataFrame:
    """
    Slice a DataFrame by date using optional start and end boundaries.

    :param df: data with a 'date' column
    :param start: start datetime (inclusive)
    :param end: end datetime (inclusive)
    :return: filtered data such that start ≤ date ≤ end
    """
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
    if start is not None:
        df = df[df["date"] >= start]
    if end is not None:
        df = df[df["date"] <= end]
    return df


def _plot_grouped_bars(
    summary: pd.DataFrame,
    index_col: str,
    title: str,
    *,
    metrics: Optional[List[str]] = None,
) -> None:
    """
    Internal helper to render grouped bar plots.

    :param summary: data with one row per category (user or repo), and
        one column per metric
    :param index_col: column name(e.g., "user" or "repo")
    :param metrics: subset of metrics to plot (e.g., ["commits", "prs"])
    :param title: chart title
    """
    # Validate and prepare the list of metrics to plot.
    default_metrics = [
        "commits",
        "prs",
        "additions",
        "deletions",
        "issues_assigned",
        "issues_closed",
        "issue_comments",
        "pr_reviews",
    ]
    to_plot = metrics if metrics else default_metrics
    for m in to_plot:
        if m not in default_metrics:
            raise ValueError(f"Unsupported metric '{m}'")
    # Filter to only metrics that exist in the summary.
    to_plot = [m for m in to_plot if m in summary.columns]
    # Compute layout parameters.
    categories = summary[index_col].tolist()
    x = range(len(to_plot))
    n_cat = len(categories)
    width = 0.8 / n_cat if n_cat else 0.8
    # Plot bars for each category (user or repo).
    fig_width = max(12, len(to_plot) * 1.5)
    fig, ax = plt.subplots(figsize=(fig_width, 5))
    for idx, cat in enumerate(categories):
        values = (
            summary.loc[summary[index_col] == cat, to_plot].astype(int).iloc[0]
        )
        pos = [i + idx * width for i in x]
        bars = ax.bar(pos, values, width=width, label=str(cat))
        for b in bars:
            ax.text(
                b.get_x() + b.get_width() / 2,
                b.get_height(),
                str(int(b.get_height())),
                ha="center",
                va="bottom",
                fontsize=8,
            )
    # Finalize plot aesthetics.
    ax.set_xticks([i + width * (n_cat - 1) / 2 for i in x])
    ax.set_xticklabels(
        [m.replace("_", " ").title() for m in to_plot], rotation=45, ha="right"
    )
    ax.set_ylabel("Count")
    ax.set_title(title)
    ax.legend(title=index_col.replace("_", " ").title())
    plt.tight_layout()
    plt.show()


def plot_metrics_by_user(
    combined: pd.DataFrame,
    repo: str,
    *,
    start: Optional[datetime.datetime] = None,
    end: Optional[datetime.datetime] = None,
    users: Optional[List[str]] = None,
    metrics: Optional[List[str]] = None,
) -> None:
    """
    Plot selected metrics for users in one repo.

    :param combined: output from `collect_all_metrics`
    :param repo: repository name
    :param start: start datetime (inclusive)
    :param end: end datetime (inclusive)
    :param users: optional subset of GitHub usernames to show
    :param metrics: list of metrics to plot; defaults to all numeric columns
    :return: grouped bar chart where each group = metric, each bar = user
    """
    df_period = _filter_period(df=combined, start=start, end=end)
    summary = summarize_user_metrics_for_repo(df_period, repo)
    if users is not None:
        summary = summary[summary["user"].isin(users)]
    _plot_grouped_bars(
        summary,
        index_col="user",
        metrics=metrics,
        title=f"Metric comparison for {repo} "
        f"({start.date() if start else 'ALL'} → {end.date() if end else 'ALL'})",
    )


def plot_metrics_by_repo(
    combined: pd.DataFrame,
    user: str,
    *,
    start: Optional[datetime.datetime] = None,
    end: Optional[datetime.datetime] = None,
    repos: Optional[List[str]] = None,
    metrics: Optional[List[str]] = None,
) -> None:
    """
    Plot specified metrics for repos for a single user as grouped bar chart.

    :param combined: data from `collect_all_metrics`
    :param user: GitHub username
    :param start: start datetime (inclusive)
    :param end: end datetime (inclusive)
    :param repos: repos to include
    :param metrics: metrics to plot; defaults to all numeric columns
    :return: grouped bar chart where each group = metric, each bar = repo
    """
    df_period = _filter_period(df=combined, start=start, end=end)
    summary = summarize_repo_metrics_for_user(df_period, user)
    if repos is not None:
        summary = summary[summary["repo"].isin(repos)]
    _plot_grouped_bars(
        summary,
        index_col="repo",
        metrics=metrics,
        title=f"Metric comparison for {user} "
        f"({start.date() if start else 'ALL'} → {end.date() if end else 'ALL'})",
    )


def plot_multi_metrics_totals_by_user(
    combined: pd.DataFrame,
    metrics: List[str],
    *,
    start: Optional[datetime.datetime] = None,
    end: Optional[datetime.datetime] = None,
    users: Optional[List[str]] = None,
    repos: Optional[List[str]] = None,
) -> None:
    """
    Plot multiple metrics (summed across repos) per user as grouped bars.

    :param combined: data from `collect_all_metrics`
    :param metrics: metrics to plot, e.g. ["commits", "prs", "additions"]
    :param start: start datetime (inclusive)
    :param end: end datetime (inclusive)
    :param users: users to include
    :param repos: repos to include
    :return: grouped bar chart where each group = user, each bar = one metric
    """
    df_period = _filter_period(df=combined, start=start, end=end)
    # Aggregate totals for each user across the selected repos.
    summary = summarize_users_across_repos(
        df_period,
        users or df_period["user"].unique().tolist(),
        repos or df_period["repo"].unique().tolist(),
    )
    if users is not None:
        summary = summary[summary["user"].isin(users)]
    # Validate metrics exist.
    for metric in metrics:
        if metric not in summary.columns:
            raise ValueError(f"Metric '{metric}' not found in summary columns")
    # Set up bar positions and sizing.
    users_sorted = summary["user"].tolist()
    x = range(len(users_sorted))
    width = 0.8 / len(metrics) if metrics else 0.8
    fig_width = max(10, len(users_sorted) * 0.7)
    fig, ax = plt.subplots(figsize=(fig_width, 5))
    # Draw bars for each metric across users
    for i, metric in enumerate(metrics):
        offsets = [pos + i * width for pos in x]
        values = (
            summary.set_index("user")
            .loc[users_sorted, metric]
            .astype(int)
            .tolist()
        )
        bars = ax.bar(
            offsets, values, width=width, label=metric.replace("_", " ").title()
        )
        for bar in bars:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                str(int(bar.get_height())),
                ha="center",
                va="bottom",
                fontsize=8,
            )
    # Final plot styling.
    ax.set_xticks([pos + width * (len(metrics) - 1) / 2 for pos in x])
    ax.set_xticklabels(users_sorted, rotation=15, ha="right")
    ax.set_ylabel("Total count across repos")
    ax.set_title(
        f"Metric totals across repos by user "
        f"({start.date() if start else 'ALL'} → {end.date() if end else 'ALL'})"
    )
    ax.legend()
    plt.tight_layout()
    plt.show()


def get_contributors_for_repo(
    client,
    org: str,
    repo: str,
    *,
    top_n: Optional[int] = None,
) -> List[str]:
    """
    Fetch GitHub usernames of contributors to a repository.

    :param client: authenticated PyGithub client
    :param org: GitHub organization name
    :param repo: repository name
    :param top_n: if specified, return only the top N contributors by
        commit count
    :return: GitHub usernames
    """
    repo_obj = client.get_repo(f"{org}/{repo}")
    contributors = repo_obj.get_contributors()
    usernames = list()
    for idx, user in enumerate(contributors):
        if top_n and idx >= top_n:
            break
        usernames.append(user.login)
    _LOG.info("Fetched %d contributors for %s/%s", len(usernames), org, repo)
    return usernames


def utc_period(
    start: str, end: str
) -> Tuple[datetime.datetime, datetime.datetime]:
    """
    Construct a UTC datetime period from string inputs.

    :param start: start date e.g. '2025-01-01'
    :param end: end date e.g. '2025-05-24'
    """
    date = (
        datetime.datetime.fromisoformat(start).replace(
            tzinfo=datetime.timezone.utc
        ),
        datetime.datetime.fromisoformat(end).replace(
            tzinfo=datetime.timezone.utc
        ),
    )
    return date


def slice_period(
    df: pd.DataFrame,
    start: datetime.date,
    end: datetime.date,
) -> pd.DataFrame:
    """
    Filter a DataFrame by date range.

    :param df: data with a `date` column of type `datetime.date`
    :param start: start date for the filtering window
    :param end: end date for the filtering window
    :return: filtered data within the specified date range
    """
    req_period = df[(df["date"] >= start) & (df["date"] <= end)]
    return req_period


def compute_z_scores(summary: pd.DataFrame, metrics: List[str]) -> pd.DataFrame:
    """
    Compute z-score (standardized score) for specified metrics across users.

    This helps assess how far a user's metric is from the group mean in units
    of standard deviation.

    :param summary: data with users and raw metric values
    :param metrics: metric column names to compute z-scores for
    :return: data with added z-score columns suffixed with `_z`
    """
    z_df = summary.copy()
    for metric in metrics:
        mean = z_df[metric].mean()
        std = z_df[metric].std()
        z_df[metric + "_z"] = (z_df[metric] - mean) / std
    return z_df


def compute_percentile_ranks(
    summary: pd.DataFrame, metrics: List[str]
) -> pd.DataFrame:
    """
    Compute percentile rank for each user for the specified metrics.

    Percentile rank reflects the relative standing of a user compared to the
    group. For example, a percentile of 0.8 means the user is ahead of 80%
    of the group for that metric.

    :param summary: data with users and raw metric values
    :param metrics: metric column names
    :return: data with added percentile columns suffixed with `_pctile`
    """
    perc_df = summary.copy()
    for metric in metrics:
        perc_df[metric + "_pctile"] = perc_df[metric].rank(pct=True)
    return perc_df


def visualize_user_metric_comparison(
    stats: pd.DataFrame,
    *,
    score_type: Literal["z", "percentile"] = "z",
    top_n: Optional[int] = None,
) -> None:
    """
    Visualize user performance across all available metrics using z-scores or
    percentiles.

    :param stats: data with user metrics and their standardized scores
    :param score_type: "z" for z-scores or "percentile" for relative
        percentiles
    :param top_n: number of top users to show in leaderboard bar chart
    """
    suffix = "_z" if score_type == "z" else "_pctile"
    score_cols = [col for col in stats.columns if col.endswith(suffix)]
    if not score_cols:
        raise ValueError(
            f"No columns ending with '{suffix}' found in input DataFrame."
        )
    # Stylized table.
    IPython.display.display(
        stats[["user"] + score_cols]
        .set_index("user")
        .style.format("{:.2f}")
        .background_gradient(
            axis=0, cmap="Greens" if score_type == "percentile" else "RdYlGn"
        )
    )
    # Leaderboard chart (by average score).
    stats["__score_avg__"] = stats[score_cols].mean(axis=1)
    if top_n is None:
        top_users = stats.sort_values("__score_avg__", ascending=False)
        top_n_display = len(top_users)
    else:
        top_users = stats.sort_values("__score_avg__", ascending=False).head(
            top_n
        )
        top_n_display = top_n
    fig, ax = plt.subplots(figsize=(max(8, 0.5 * len(top_users)), 4))
    ax.bar(top_users["user"], top_users["__score_avg__"], color="skyblue")
    ax.set_ylabel(
        "Average Score" + (" (Z-score)" if score_type == "z" else " (Percentile)")
    )
    ax.set_title(f"Top {top_n_display} Users by Average {score_type.title()}")
    ax.axhline(0 if score_type == "z" else 0.5, color="gray", linestyle="--")
    plt.xticks(rotation=15, ha="right")
    plt.tight_layout()
    plt.show()
    stats.drop(columns="__score_avg__", inplace=True)


def compute_engagement_score(
    summary: pd.DataFrame,
    weights: Optional[Dict[str, float]] = None,
) -> pd.DataFrame:
    """
    Compute a weighted engagement score for each user based on all metrics.

    :param summary: data with user metrics
    :param weights: optional dictionary of metric weights; if None, uses
        defaults
    :return: summary with an added 'engagement_score' column
    """
    # Default weights emphasizing collaboration and code quality.
    default_weights = {
        "commits": 1.0,
        "prs": 2.0,
        "additions": 0.001,
        "deletions": 0.0005,
        "issues_assigned": 0.5,
        "issues_closed": 1.5,
        "issue_comments": 0.3,
        "pr_reviews": 2.5,
    }
    weights = weights or default_weights
    summary = summary.copy()
    summary["engagement_score"] = 0
    for metric, weight in weights.items():
        if metric in summary.columns:
            summary["engagement_score"] += summary[metric] * weight
    # Normalize to 0-100 scale.
    max_score = summary["engagement_score"].max()
    if max_score > 0:
        summary["engagement_score"] = (
            summary["engagement_score"] / max_score * 100
        ).round(2)
    sum = summary.sort_values("engagement_score", ascending=False)
    return sum
