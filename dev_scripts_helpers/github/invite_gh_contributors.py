#!/usr/bin/env python
"""
Invite GitHub collaborators listed in a Google Sheet while obeying the
50-invite / 24-hour cap.

> automate_collaborator_invitations.py \
    --drive_url "https://docs.google.com/spreadsheets/d/1Ez5uRvOgvDMkFc9c6mI21kscTKnpiCSh4UkUh_ifLIw
    /edit?gid=0#gid=0" \
    --gh_token "$GH_PAT" \
    --org_name causify-ai \
    --repo_name tutorials
"""
import argparse
import datetime
import logging
import subprocess
import sys
from typing import List

import helpers.hdbg as hdbg
import helpers.hparser as hparser

# Install required packages and configure.
packages = [
    "pygithub",
    "google-api-python-client",
    "oauth2client",
    "gspread",
    "ratelimit",
]
for pkg in packages:
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--quiet", "--upgrade", pkg],
        check=True,
    )

_LOG = logging.getLogger(__name__)

import github
import ratelimit

import helpers.hgoogle_drive_api as hgodrapi

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
    gh_access_token: str,
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
    parser.add_argument(
        "--drive_url",
        required=True,
        help="Google‑Sheet URL with a 'GitHub user' column",
    )
    parser.add_argument(
        "--gh_token",
        required=True,
        help="GitHub personal‑access token (repo scope)",
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
    usernames = extract_usernames_from_gsheet(args.drive_url)
    send_invitations(usernames, args.gh_token, args.repo_name, args.org_name)


if __name__ == "__main__":
    _main(_parse())
