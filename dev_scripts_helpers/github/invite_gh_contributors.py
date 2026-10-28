#!/usr/bin/env -S uv run

# /// script
# dependencies = [
#   "google-api-python-client",
#   "google-auth",
#   "gspread",
#   "pandas",
#   "pygithub",
#   "pyyaml",
#   "ratelimit",
#   "tqdm",
# ]
# ///

"""
Invite GitHub collaborators listed in a Google Sheet/CSV, or passed on the
command line, while obeying the 50-invite / 24-hour cap.

By default only the difference between the passed users and the users already
invited (i.e., collaborators or users with a pending invitation) is invited.
Use `--no_skip_invited` to invite all the passed users.

The GitHub token is read from the env var `GITHUB_TOKEN`. If it is not set, the
token of the logged-in `gh` CLI (`gh auth token`) is used.

The Google Sheet is read with the service account key in
`~/.config/gspread_pandas/google_secret.json`.

# Usage Example

- Invite to the repo `causify-ai/tutorials` the users in the passed Google Sheet:
> invite_gh_contributors.py \
    --drive_url "https://docs.google.com/spreadsheets/d/1Ez5uRvOgvDMkFc9c6mI21kscTKnpiCSh4UkUh_ifLIw
    /edit?gid=0#gid=0" \
    --org_name causify-ai \
    --repo_name tutorials

- Invite to the repo `causify-ai/tutorials` the users in the passed CSV file:
> invite_gh_contributors.py \
    --csv_file "/tmp/github_users.csv" \
    --org_name causify-ai \
    --repo_name tutorials

- Invite to the repo `causify-ai/tutorials` one or more users passed on the
  command line, with read-only access:
> invite_gh_contributors.py \
    --add_gh_user alice \
    --add_gh_user bob \
    --org_name causify-ai \
    --repo_name tutorials \
    --permission pull

- Show who is already invited and who would be invited, without inviting anyone:
> invite_gh_contributors.py \
    --csv_file "/tmp/github_users.csv" \
    --org_name causify-ai \
    --repo_name tutorials \
    --dry_run

Import as:

import dev_scripts_helpers.github.invite_gh_contributors as dshgigco
"""

import argparse
import csv
import datetime
import logging
import os
from typing import List, Optional, Set, Tuple

import github
import ratelimit

import helpers.hdbg as hdbg
import helpers.hgoogle_drive_api as hgodrapi
import helpers.hparser as hparser
import helpers.hsystem as hsystem

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
    credentials = hgodrapi.get_credentials()
    df = hgodrapi.from_gsheet(gsheet_url, credentials=credentials)
    # Empty cells can be `None` or `NaN`, so keep only non-empty strings.
    usernames = [
        user
        for user in df["GitHub user"].tolist()
        if isinstance(user, str) and user.strip()
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


def _get_invited_usernames(repo) -> Tuple[Set[str], Set[str]]:
    """
    Get the users already invited to a repo.

    :param repo: GitHub repo
    :return: lowercase usernames of the collaborators and of the users with a
        pending invitation
    """
    collaborators = {user.login.lower() for user in repo.get_collaborators()}
    pending = {
        invitation.invitee.login.lower()
        for invitation in repo.get_pending_invitations()
        if invitation.invitee is not None
    }
    return collaborators, pending


def _split_usernames(
    usernames: List[str], collaborators: Set[str], pending: Set[str]
) -> Tuple[List[str], List[str], List[str]]:
    """
    Split the passed users into already invited and still to invite.

    The comparison is case-insensitive, as GitHub usernames are. Duplicates are
    dropped and the order of the passed users is kept.

    :param usernames: GitHub usernames to invite
    :param collaborators: lowercase usernames of the collaborators
    :param pending: lowercase usernames of the users with a pending invitation
    :return: users that are collaborators, users with a pending invitation,
        users to invite
    """
    already_collaborators: List[str] = []
    already_pending: List[str] = []
    to_invite: List[str] = []
    for username in dict.fromkeys(usernames):
        if username.lower() in collaborators:
            already_collaborators.append(username)
        elif username.lower() in pending:
            already_pending.append(username)
        else:
            to_invite.append(username)
    return already_collaborators, already_pending, to_invite


def send_invitations(
    usernames: List[str],
    gh_access_token: Optional[str],
    repo_name: str,
    org_name: str,
    *,
    skip_invited: bool,
    dry_run: bool,
    permission: str = "write",
) -> None:
    """
    Send GitHub collaborator invitations to given usernames.

    :param usernames: List of GitHub usernames
    :param gh_access_token: GitHub API access token
    :param repo_name: target repository name (without org)
    :param org_name: GitHub organisation name
    :param skip_invited: invite only the users that are neither collaborators
        nor have a pending invitation
    :param dry_run: report who would be invited without inviting anyone
    :param permission: permission granted to the invited users (e.g., `pull`
        for read-only access, `write`, `admin`)
    """
    # Initialize GitHub API.
    gh = github.Github(gh_access_token)
    # Get the repository.
    repo = gh.get_repo(f"{org_name}/{repo_name}")
    # Compute the difference between the passed users and the invited ones.
    if skip_invited:
        collaborators, pending = _get_invited_usernames(repo)
    else:
        collaborators, pending = set(), set()
    already_collaborators, already_pending, to_invite = _split_usernames(
        usernames, collaborators, pending
    )
    _LOG.info("Already collaborators: %s", already_collaborators)
    _LOG.info("Already pending invitation: %s", already_pending)
    _LOG.info("To invite: %s", to_invite)
    # Send invitations.
    for username in to_invite:
        if dry_run:
            _LOG.warning("[DRY_RUN] Would invite '%s'", username)
        else:
            try:
                _invite(repo, username, permission=permission)
            except github.GithubException as exc:
                _LOG.error(
                    "Failed to invite '%s': %s",
                    username,
                    exc.data.get("message"),
                )


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    # Set `--drive_url`, `--csv_file`, and `--add_gh_user` to be mutually
    # exclusive.
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--drive_url",
        help="Google Sheet URL containing a 'GitHub user' column",
    )
    input_group.add_argument(
        "--csv_file",
        help="Path to CSV file containing a 'GitHub user' column",
    )
    input_group.add_argument(
        "--add_gh_user",
        action="append",
        help="GitHub username to invite (can be repeated to invite many users)",
    )
    parser.add_argument(
        "--repo_name", required=True, help="Target repository name (without org)"
    )
    parser.add_argument(
        "--org_name", required=True, help="GitHub organisation name"
    )
    parser.add_argument(
        "--permission",
        default="write",
        help=(
            "Permission granted to the invited users (e.g., 'pull' for "
            "read-only access, 'write', 'admin')"
        ),
    )
    hparser.add_bool_arg(
        parser,
        "skip_invited",
        default_value=True,
        help_="Invite only the difference between the passed users and the users already invited (collaborators or pending invitation)",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Show what would be done without actually doing it",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _get_github_token() -> str:
    """
    Get the GitHub token from `GITHUB_TOKEN` or from the `gh` CLI.

    :return: GitHub access token
    """
    gh_token = os.getenv("GITHUB_TOKEN")
    if not gh_token:
        # Fall back to the token of the logged-in `gh` CLI.
        _LOG.info("Env var 'GITHUB_TOKEN' not set: using 'gh auth token'")
        # Do not log the command output, since it is the token.
        _, gh_token = hsystem.system_to_string(
            "gh auth token",
            print_command=False,
            abort_on_error=False,
            suppress_output=True,
        )
        gh_token = gh_token.strip()
    hdbg.dassert(
        gh_token,
        "Set env var 'GITHUB_TOKEN' or log in with 'gh auth login'",
    )
    return gh_token


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    gh_token = _get_github_token()
    if args.csv_file:
        usernames = extract_usernames_from_csv(args.csv_file)
    elif args.drive_url:
        usernames = extract_usernames_from_gsheet(args.drive_url)
    else:
        usernames = [user.strip() for user in args.add_gh_user if user.strip()]
        hdbg.dassert_lte(1, len(usernames), "No GitHub user passed")
    send_invitations(
        usernames,
        gh_token,
        args.repo_name,
        args.org_name,
        skip_invited=args.skip_invited,
        dry_run=args.dry_run,
        permission=args.permission,
    )


if __name__ == "__main__":
    _main(_parse())
