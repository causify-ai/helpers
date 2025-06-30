#!/usr/bin/env python
"""
Invite GitHub collaborators listed in a Google Sheet/CSV while obeying the
50-invite / 24-hour cap. This requires some dependencies, which is why it is
executed in a Docker container.

# Invite to the repo `causify-ai/tutorials` the users in the passed Google Sheet:
> invite_gh_contributors.py \
    --drive_url "https://docs.google.com/spreadsheets/d/1Ez5uRvOgvDMkFc9c6mI21kscTKnpiCSh4UkUh_ifLIw
    /edit?gid=0#gid=0" \
    --org_name causify-ai \
    --repo_name tutorials

# Invite to the repo `causify-ai/tutorials` the users in the passed CSV file:
> invite_gh_contributors.py \
    --csv_file "/tmp/github_users.csv" \
    --org_name causify-ai \
    --repo_name tutorials
"""
import argparse
import csv
import datetime
import logging
import os
from typing import List, Optional

import github
import ratelimit

import helpers.hdbg as hdbg
import helpers.hgoogle_drive_api as hgodrapi
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

# Set constraints.
_INVITES_PER_WINDOW = 50
_WINDOW_SECONDS = int(datetime.timedelta(hours=24).total_seconds())


def extract_usernames_from_gsheet(gsheet_url: str) -> List[str]:
    """
    Extract usernames from a Google Sheet URL.

    :param gsheet_url: URL of the Google Sheet
    :return: github usernames
    """
    credentials = hgodrapi.get_credentials(
        service_key_path="/app/DATA605/google_secret.json"
    )
    df = hgodrapi.read_google_file(gsheet_url, credentials=credentials)
    usernames = [
        user for user in df["GitHub user"].tolist() if user and user.strip()
    ]
    _LOG.info("Usernames = \n  %s", usernames)
    return usernames


def extract_usernames_from_csv(csv_path: str) -> List[str]:
    """
    Extract GitHub usernames from a CSV file containing a *GitHub user* column.

    :param csv_path: path to csv
    :return: github usernames
    """
    usernames: List[str] = []
    with open(csv_path, newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        hdbg.dassert_in(
            "GitHub user",
            reader.fieldnames,
            "CSV missing required column 'GitHub user'",
        )
        for row in reader:
            usernames.append(row["GitHub user"])
    usernames = [user.strip() for user in usernames if user and user.strip()]
    _LOG.info("Usernames (CSV)   = %s", usernames)
    return usernames


@ratelimit.sleep_and_retry
@ratelimit.limits(calls=_INVITES_PER_WINDOW, period=_WINDOW_SECONDS)
def _invite(repo, username: str, *, permission: str = "write") -> None:
    """
    Invite one user, limiting it to 50 invites/24h.

    :param repo: path to repo
    :param username: username to add
    :param permission: type of permission
    """
    repo.add_to_collaborators(username, permission=permission)
    _LOG.info("Invitation sent to %s", username)


def send_invitations(
    usernames: List[str],
    gh_access_token: Optional[str],
    repo_name: str,
    org_name: str,
) -> None:
    """
    Send GitHub collaborator invitations to given usernames.

    :param usernames: List of GitHub usernames
    :param gh_access_token: GitHub API access token
    :param repo_url: URL of the target repository
    """
    # Initialize GitHub API.
    gh = github.Github(gh_access_token)
    # Get the repository.
    repo = gh.get_repo(f"{org_name}/{repo_name}")
    # Send invitations.
    for username in usernames:
        if repo.has_in_collaborators(username):
            _LOG.info("User %s is already a collaborator", username)
            continue
        try:
            _invite(repo, username)
        except github.GithubException as exc:
            _LOG.error(
                "Failed to invite %s: %s", username, exc.data.get("message")
            )


def _parse() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Invite GitHub collaborators from a Google Sheet, respecting limit.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    # Set `--drive_url` and `--csv_file` to be mutually exclusive.
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--drive_url",
        help="Google Sheet URL containing a 'GitHub user' column",
    )
    input_group.add_argument(
        "--csv_file",
        help="Path to CSV file containing a 'GitHub user' column",
    )
    parser.add_argument(
        "--repo_name", required=True, help="Target repository name (without org)"
    )
    parser.add_argument(
        "--org_name", required=True, help="GitHub organisation name"
    )
    hparser.add_verbosity_arg(parser)
    return parser.parse_args()


def _main(args: argparse.Namespace) -> None:
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Retrieve GitHub token from env var.
    gh_token = os.getenv("GITHUB_TOKEN")
    hdbg.dassert(gh_token, "Environment variable GITHUB_TOKEN must be set")
    if args.csv_file:
        usernames = extract_usernames_from_csv(args.csv_file)
    else:
        usernames = extract_usernames_from_gsheet(args.drive_url)
    send_invitations(usernames, gh_token, args.repo_name, args.org_name)


if __name__ == "__main__":
    _main(_parse())
