#!/usr/bin/env python3
"""
The script is designed to synchronize GitHub repository settings and branch
protection rules from a settings manifest file. It requires certain
dependencies to be present (e.g., `pygithub`) and thus it is executed as a
dockerized executable.

To use this script, you need to provide the input file, GitHub repository name,
owner, token environment variable, and optional flags for controlling the
synchronization behavior.

The command lines are the same as the `dev_scripts_helpers/github/sync_gh_repo_settings.py` script.
"""

import argparse
import logging
import os
from typing import Any, Dict

import github
import yaml

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# #############################################################################
# Settings
# #############################################################################


class Settings:

    def __init__(self, settings: Dict[str, Any]):
        """
        Initialize the settings with a dictionary of branch protection and
        repository settings.

        :param settings: dictionary containing branch protection and
            repository settings
        """
        self._settings = settings
        self._branch_protection = settings.get("branch_protection", {})
        self._repo_settings = settings.get("repository_settings", {})

    def __repr__(self):
        return f"settings(branch_protection={self.branch_protection}, repo_settings={self.repo_settings})"

    @staticmethod
    def get_repository_settings(
        repo: github.Repository.Repository,
    ) -> Dict[str, Any]:
        """
        Get the current settings of the repository.

        :param repo: GitHub repository object
        :return: dictionary containing repository settings
        """
        current_settings = {
            "name": repo.name,
            "default_branch": repo.default_branch,
            "homepage": repo.homepage,
            "description": repo.description,
            "private": repo.private,
            "archived": repo.archived,
            "has_issues": repo.has_issues,
            "has_projects": repo.has_projects,
            "has_wiki": repo.has_wiki,
            "allow_squash_merge": repo.allow_squash_merge,
            "allow_merge_commit": repo.allow_merge_commit,
            "allow_rebase_merge": repo.allow_rebase_merge,
            "delete_branch_on_merge": repo.delete_branch_on_merge,
        }
        return current_settings

    @staticmethod
    def get_branch_protection_settings(
        repo: github.Repository.Repository,
    ) -> Dict[str, Any]:
        """
        Get the current branch protection settings of the repository.

        :param repo: GitHub repository object
        :return: dictionary containing branch protection settings
        """
        branch_protection = {}
        branches = repo.get_branches()
        for branch in branches:
            try:
                protection = branch.get_protection()
                branch_protection[branch.name] = {
                    "enforce_admins": protection.enforce_admins,
                    "allow_force_pushes": protection.allow_force_pushes,
                    "allow_deletions": protection.allow_deletions,
                    "required_status_checks": (
                        {
                            "strict": protection.required_status_checks.strict,
                            "contexts": protection.required_status_checks.contexts,
                        }
                        if protection.required_status_checks
                        else {}
                    ),
                    "required_pull_request_reviews": (
                        {
                            "dismiss_stale_reviews": protection.required_pull_request_reviews.dismiss_stale_reviews,
                            "require_code_owner_reviews": protection.required_pull_request_reviews.require_code_owner_reviews,
                            "required_approving_review_count": protection.required_pull_request_reviews.required_approving_review_count,
                            "dismissal_restrictions": (
                                {
                                    "users": [
                                        user.login
                                        for user in protection.required_pull_request_reviews.dismissal_restrictions.users
                                    ],
                                    "teams": [
                                        team.name
                                        for team in protection.required_pull_request_reviews.dismissal_restrictions.teams
                                    ],
                                }
                                if protection.required_pull_request_reviews.dismissal_restrictions
                                else {}
                            ),
                        }
                        if protection.required_pull_request_reviews
                        else {}
                    ),
                    "restrictions": (
                        {
                            "users": [
                                user.login
                                for user in protection.restrictions.users
                            ],
                            "teams": [
                                team.name
                                for team in protection.restrictions.teams
                            ],
                        }
                        if protection.restrictions
                        else {}
                    ),
                }
            except github.GithubException as e:
                if e.status == 404:
                    # Skip if branch has no protection.
                    continue
                _LOG.error(
                    "Failed to get branch protection for %s: %s",
                    branch.name,
                    str(e),
                )
        return branch_protection

    @staticmethod
    def load_settings(path: str) -> "Settings":
        """
        Load settings from settings manifest file.

        :param path: path to settings manifest file
        :return: settings object
        """
        with open(path, "r", encoding="utf-8") as file:
            yaml_data = yaml.safe_load(file)
            settings = Settings(yaml_data)
            return settings

    @staticmethod
    def save_settings(settings: "Settings", path: str) -> None:
        """
        Save settings to a settings manifest file.

        :param settings: settings object
        :param path: path to save the settings manifest file to
        """
        with open(path, "w", encoding="utf-8") as file:
            settings_data = {
                "branch_protection": settings.branch_protection,
                "repository_settings": settings.repo_settings,
            }
            # Set `default_flow_style=False` to use block style instead of
            # flow style for better readability.
            yaml.dump(
                settings_data, file, default_flow_style=False, sort_keys=False
            )

    @property
    def branch_protection(self) -> Dict[str, Any]:
        return self._branch_protection

    @property
    def repo_settings(self) -> Dict[str, Any]:
        return self._repo_settings

    def to_dict(self) -> Dict[str, Any]:
        """
        Return settings as a dictionary.

        :return: settings as a dictionary
        """
        return {
            "branch_protection": self._branch_protection,
            "repository_settings": self._repo_settings,
        }

    def switch_default_branch_protection(
        self, repo: github.Repository.Repository, dry_run: bool = True
    ) -> None:
        """
        Switch to default branch protection rules that exist in the repo but
        not in settings manifest file.

        By default, branch protection:
        - Disables force pushes
        - Prevents branch deletion
        - Does not apply restrictions to admins/bypassers
        - Rest of the settings have no default values

        Only these three settings are switched to default because they are the core
        protection settings that GitHub applies by default. Other settings like
        required status checks, pull request reviews, and restrictions are not
        automatically applied by GitHub and thus are not included in the default
        behavior.

        :param repo: GitHub repository object
        :param dry_run: whether to do dry run
        """
        branches = repo.get_branches()
        for branch in branches:
            try:
                # Set default protection if branch exists in repo but not in settings.
                if branch.name not in self.branch_protection:
                    default_settings = {
                        "enforce_admins": False,
                        "allow_force_pushes": False,
                        "allow_deletions": False,
                    }
                    if not dry_run:
                        # Apply default protection settings.
                        branch.edit_protection(
                            enforce_admins=default_settings["enforce_admins"],
                            allow_force_pushes=default_settings[
                                "allow_force_pushes"
                            ],
                            allow_deletions=default_settings["allow_deletions"],
                            strict=github.GithubObject.NotSet,
                            contexts=github.GithubObject.NotSet,
                            dismiss_stale_reviews=github.GithubObject.NotSet,
                            require_code_owner_reviews=github.GithubObject.NotSet,
                            required_approving_review_count=github.GithubObject.NotSet,
                            dismissal_users=github.GithubObject.NotSet,
                            dismissal_teams=github.GithubObject.NotSet,
                            user_push_restrictions=github.GithubObject.NotSet,
                            team_push_restrictions=github.GithubObject.NotSet,
                        )
                        _LOG.info(
                            "Applied default branch protection to %s:\n%s",
                            branch.name,
                            "\n".join(
                                f"  {k}: {v}" for k, v in default_settings.items()
                            ),
                        )
                    else:
                        _LOG.info(
                            "Would apply default branch protection to %s:\n%s",
                            branch.name,
                            "\n".join(
                                f"  {k}: {v}" for k, v in default_settings.items()
                            ),
                        )
            except github.GithubException as e:
                if e.status == 404:
                    # Skip if branch has no protection.
                    continue
                _LOG.error(
                    "Failed to apply default branch protection to %s: %s",
                    branch.name,
                    str(e),
                )

    def switch_default_repository_settings(
        self, repo: github.Repository.Repository, dry_run: bool = True
    ) -> None:
        """
        Switch to default repository settings that exist in the repo but not in
        settings manifest file.

        By default:
        - Merge options are enabled
        - Repository features are enabled
        - Delete branch on merge is disabled
        - Rest of the settings have no default values

        :param repo: GitHub repository object
        :param dry_run: whether to do dry run
        """
        current_settings = self.get_repository_settings(repo)
        default_settings = {
            "allow_merge_commit": True,
            "allow_squash_merge": True,
            "allow_rebase_merge": True,
            "has_issues": True,
            "has_wiki": True,
            "has_projects": True,
            "delete_branch_on_merge": False,
        }
        changes = {}
        for setting, value in current_settings.items():
            if setting not in self.repo_settings and setting in default_settings:
                changes[setting] = default_settings[setting]
        if changes:
            if not dry_run:
                for setting, value in changes.items():
                    repo.edit(**{setting: value})
                _LOG.info(
                    "Applied default repository settings:\n%s",
                    "\n".join(f"  {k}: {v}" for k, v in changes.items()),
                )
            else:
                _LOG.info(
                    "Would apply default repository settings:\n%s",
                    "\n".join(f"  {k}: {v}" for k, v in changes.items()),
                )

    def apply_branch_protection(
        self, repo: github.Repository.Repository, dry_run: bool = True
    ) -> None:
        """
        Apply branch protection rules.

        :param repo: GitHub repository object
        :param dry_run: whether to do dry run
        """
        for branch_name, protection in self.branch_protection.items():
            branch = repo.get_branch(branch_name)
            # Get the protection settings.
            required_status_checks = protection.get("required_status_checks", {})
            required_pr_reviews = protection.get(
                "required_pull_request_reviews", {}
            )
            restrictions = protection.get("restrictions", {})
            # Include status checks only if explicitly set and non-empty.
            contexts = required_status_checks.get("contexts", [])
            strict = required_status_checks.get("strict")
            # Apply branch protection using supported parameters.
            settings = {
                "strict": (
                    strict if strict is not None else github.GithubObject.NotSet
                ),
                "contexts": contexts if contexts else github.GithubObject.NotSet,
                "enforce_admins": protection.get(
                    "enforce_admins", github.GithubObject.NotSet
                ),
                "dismiss_stale_reviews": required_pr_reviews.get(
                    "dismiss_stale_reviews", github.GithubObject.NotSet
                ),
                "require_code_owner_reviews": required_pr_reviews.get(
                    "require_code_owner_reviews", github.GithubObject.NotSet
                ),
                "required_approving_review_count": required_pr_reviews.get(
                    "required_approving_review_count", github.GithubObject.NotSet
                ),
                "dismissal_users": required_pr_reviews.get(
                    "dismissal_restrictions", {}
                ).get("users", github.GithubObject.NotSet),
                "dismissal_teams": required_pr_reviews.get(
                    "dismissal_restrictions", {}
                ).get("teams", github.GithubObject.NotSet),
                "user_push_restrictions": restrictions.get(
                    "users", github.GithubObject.NotSet
                ),
                "team_push_restrictions": restrictions.get(
                    "teams", github.GithubObject.NotSet
                ),
            }
            if not dry_run:
                branch.edit_protection(**settings)
            # Filter out `NotSet` values for logging.
            log_settings = {
                k: v
                for k, v in settings.items()
                if v is not github.GithubObject.NotSet
            }
            if not dry_run:
                _LOG.info(
                    "Applied branch protection rules to %s:\n%s",
                    branch_name,
                    "\n".join(f"  {k}: {v}" for k, v in log_settings.items()),
                )
            else:
                _LOG.info(
                    "Would apply branch protection rules to %s:\n%s",
                    branch_name,
                    "\n".join(f"  {k}: {v}" for k, v in log_settings.items()),
                )

    def apply_repo_settings(
        self, repo: github.Repository.Repository, dry_run: bool = True
    ) -> None:
        """
        Apply repository settings.

        :param repo: GitHub repository object
        :param dry_run: whether to do dry run
        """
        private = self.repo_settings.get("private")
        # Apply basic repository settings.
        settings = {
            "name": self.repo_settings.get("name"),
            "description": self.repo_settings.get(
                "description", github.GithubObject.NotSet
            ),
            "homepage": self.repo_settings.get(
                "homepage", github.GithubObject.NotSet
            ),
            "private": (
                private if private is not None else github.GithubObject.NotSet
            ),
            "has_issues": self.repo_settings.get(
                "has_issues", github.GithubObject.NotSet
            ),
            "has_projects": self.repo_settings.get(
                "has_projects", github.GithubObject.NotSet
            ),
            "has_wiki": self.repo_settings.get(
                "has_wiki", github.GithubObject.NotSet
            ),
            "default_branch": self.repo_settings.get(
                "default_branch", github.GithubObject.NotSet
            ),
            "allow_squash_merge": self.repo_settings.get(
                "allow_squash_merge", github.GithubObject.NotSet
            ),
            "allow_merge_commit": self.repo_settings.get(
                "allow_merge_commit", github.GithubObject.NotSet
            ),
            "allow_rebase_merge": self.repo_settings.get(
                "allow_rebase_merge", github.GithubObject.NotSet
            ),
            "archived": self.repo_settings.get(
                "archived", github.GithubObject.NotSet
            ),
        }
        if not dry_run:
            repo.edit(**settings)
            # Apply security-related settings.
            enable_security_fixes = self.repo_settings.get(
                "enable_automated_security_fixes"
            )
            if enable_security_fixes is not None:
                if enable_security_fixes:
                    repo.enable_automated_security_fixes()
                    _LOG.info("Enabled automated security fixes")
                else:
                    repo.disable_automated_security_fixes()
                    _LOG.info("Disabled automated security fixes")

            enable_vuln_alerts = self.repo_settings.get(
                "enable_vulnerability_alerts"
            )
            if enable_vuln_alerts is not None:
                if enable_vuln_alerts:
                    repo.enable_vulnerability_alert()
                    _LOG.info("Enabled vulnerability alerts")
                else:
                    repo.disable_vulnerability_alert()
                    _LOG.info("Disabled vulnerability alerts")
            # Update repository topics.
            if "topics" in self.repo_settings:
                topics = self.repo_settings["topics"]
                repo.replace_topics(topics)
                _LOG.info("Updated repository topics: %s", ", ".join(topics))
        # Filter out `NotSet` values for logging.
        log_settings = {
            k: v
            for k, v in settings.items()
            if v is not github.GithubObject.NotSet
        }
        if not dry_run:
            _LOG.info(
                "Applied repository settings:\n%s",
                "\n".join(f"  {k}: {v}" for k, v in log_settings.items()),
            )
        else:
            _LOG.info(
                "Would apply repository settings:\n%s",
                "\n".join(f"  {k}: {v}" for k, v in log_settings.items()),
            )
            if enable_security_fixes is not None:
                _LOG.info(
                    "Would %s automated security fixes",
                    "enable" if enable_security_fixes else "disable",
                )
            if enable_vuln_alerts is not None:
                _LOG.info(
                    "Would %s vulnerability alerts",
                    "enable" if enable_vuln_alerts else "disable",
                )
            if "topics" in self.repo_settings:
                _LOG.info(
                    "Would update repository topics: %s",
                    ", ".join(self.repo_settings["topics"]),
                )


def _parse() -> argparse.ArgumentParser:
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    hparser.add_verbosity_arg(parser)
    parser.add_argument(
        "--input_file",
        required=True,
        help="Path to settings manifest file",
    )
    parser.add_argument(
        "--owner",
        required=True,
        help="GitHub repository owner/organization",
    )
    parser.add_argument("--repo", required=True, help="GitHub repository name")
    parser.add_argument(
        "--token_env_var",
        required=True,
        help="Name of the environment variable containing the GitHub token",
    )
    parser.add_argument(
        "--switch_default",
        action="store_true",
        help="Switch to default settings for settings that exist in the repo but not in the settings manifest file",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Print actions without executing them",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Backup current settings before making changes",
    )
    parser.add_argument(
        "--no_interactive",
        action="store_true",
        help="Skip confirmation prompts",
    )
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Load settings from the manifest file.
    settings = Settings.load_settings(args.input_file)
    token = os.environ[args.token_env_var]
    hdbg.dassert(token)
    # Initialize GitHub client.
    client = github.Github(token)
    repo = client.get_repo(f"{args.owner}/{args.repo}")
    # Get current repository settings.
    current_settings = {
        "branch_protection": Settings.get_branch_protection_settings(repo),
        "repository_settings": Settings.get_repository_settings(repo),
    }
    # Create backup of current settings if requested.
    if args.backup:
        git_root_dir = hgit.get_client_root(False)
        backup_file = f"tmp.settings.{args.owner}.{args.repo}.yaml"
        backup_path = f"{git_root_dir}/{backup_file}"
        Settings.save_settings(Settings(current_settings), backup_path)
        _LOG.info("Settings backed up to %s", backup_path)
    else:
        _LOG.warning("Skipping saving settings as per user request")
    # Confirm settings synchronization.
    if not args.no_interactive:
        hsystem.query_yes_no(
            "Are you sure you want to synchronize repository settings?",
            abort_on_no=True,
        )
    else:
        _LOG.warning("Running in non-interactive mode, skipping confirmation")
    # Switch to default settings if requested.
    if args.switch_default:
        settings.switch_default_branch_protection(repo, args.dry_run)
        settings.switch_default_repository_settings(repo, args.dry_run)
    # Apply branch protection and repository settings.
    settings.apply_branch_protection(repo, args.dry_run)
    settings.apply_repo_settings(repo, args.dry_run)
    _LOG.info("Settings synchronization completed!")


if __name__ == "__main__":
    _main(_parse())
