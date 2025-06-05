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
from typing import Any, Dict, Optional, Set

import github
import yaml

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)

# Repo and branch protection settings keys for validation.
GH_SETTING_KEYS = {"repository_settings", "branch_protection"}
REPO_SETTING_KEYS = {
    "name",
    "description",
    "homepage",
    "private",
    "has_issues",
    "has_projects",
    "has_wiki",
    "default_branch",
    "allow_squash_merge",
    "allow_merge_commit",
    "allow_rebase_merge",
    "archived",
    "enable_automated_security_fixes",
    "enable_vulnerability_alerts",
    "topics",
    "delete_branch_on_merge",
}
BRANCH_PROTECTION_KEYS = {
    "enforce_admins",
    "allow_force_pushes",
    "allow_deletions",
    "required_status_checks",
    "required_pull_request_reviews",
    "restrictions",
}
STATUS_CHECK_KEYS = {
    "strict",
    "contexts",
}
PR_REVIEW_KEYS = {
    "dismiss_stale_reviews",
    "require_code_owner_reviews",
    "required_approving_review_count",
    "dismissal_restrictions",
}
RESTRICTION_KEYS = {
    "users",
    "teams",
}


# #############################################################################
# _RepoAndBranchSettings
# #############################################################################


class _RepoAndBranchSettings:
    def __init__(self, repo_and_branch_settings: Dict[str, Any]):
        """
        Initialize a nested dictionary of branch protection and repository
        settings.

        :param repo_and_branch_settings: dictionary containing
            repository and branch protection settings
        """
        self._repo_and_branch_settings = repo_and_branch_settings
        # Validate the settings.
        self._validate_settings()

    def __repr__(self) -> str:
        repo_settings = self._repo_and_branch_settings.get(
            "repository_settings", {}
        )
        branch_settings = self._repo_and_branch_settings.get(
            "branch_protection", {}
        )
        res = f"settings(branch_protection={branch_settings}, repo_settings={repo_settings})"
        return res

    @staticmethod
    def get_repository_settings(
        repo: github.Repository.Repository,
    ) -> Dict[str, Any]:
        """
        Get the current settings of the repository `repo`.

        :param repo: GitHub repository object
        :return: dictionary containing repository settings
        E.g.,
        {
            "name": str, "default_branch": str, "homepage": str,
            "description": str, "private": bool, "archived": bool,
            "has_issues": bool, "has_projects": bool, "has_wiki": bool,
            "allow_squash_merge": bool, "allow_merge_commit": bool,
            "allow_rebase_merge": bool, "delete_branch_on_merge": bool,
            "topics": List[str],
            "enable_automated_security_fixes": bool,
            "enable_vulnerability_alerts": bool,
            ...
        }
        """
        current_repo_settings = {
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
            "topics": repo.get_topics(),
        }
        return current_repo_settings

    @staticmethod
    def get_branch_protection_settings(
        repo: github.Repository.Repository,
    ) -> Dict[str, Any]:
        """
        Get the current branch protection settings of the repository `repo`.

        :param repo: GitHub repository object
        :return: dictionary containing branch protection settings
        E.g.,
        {
            "main" : {
                "enforce_admins": bool,
                "allow_force_pushes": bool,
                "allow_deletions": bool,
                "required_status_checks": {
                    "strict": bool,
                    "contexts": List[str]
                },
                "required_pull_request_reviews": {
                    "dismiss_stale_reviews": bool,
                    "require_code_owner_reviews": bool,
                    "required_approving_review_count": int,
                    "dismissal_restrictions": {
                        "users": List[str],
                        "teams": List[str]
                    }
                },
                "restrictions": {
                    "users": List[str],
                    "teams": List[str]
                }
            },
            ...
        }
        """
        branch_protection = {}
        _LOG.debug(
            "Getting branch protection settings for repo %s", repo.full_name
        )
        # Retrieve all Git branches of the repository (e.g., 'main', 'dev', etc.).
        branches = repo.get_branches()
        _LOG.debug("Found %d branches in repository", len(list(branches)))
        for branch in branches:
            _LOG.debug("Processing branch: %s", branch.name)
            try:
                # Get the protection information of the branch.
                protection = branch.get_protection()
                if protection is None:
                    _LOG.warning(
                        "No protection info for branch '%s': skipping.",
                        branch.name,
                    )
                    continue
                # 1) Extract the information about required status check for
                # the current branch.
                required_status_checks = {}
                status_checks = getattr(
                    protection, "required_status_checks", None
                )
                if status_checks:
                    required_status_checks["strict"] = getattr(
                        status_checks, "strict", None
                    )
                    required_status_checks["contexts"] = getattr(
                        status_checks, "contexts", []
                    )

                pr_reviews = getattr(
                    protection, "required_pull_request_reviews", None
                )
                # 2) Extract the information about required PR reviews for the
                # current branch.
                required_pr_reviews = {}
                if pr_reviews:
                    required_pr_reviews["dismiss_stale_reviews"] = getattr(
                        pr_reviews, "dismiss_stale_reviews", None
                    )
                    required_pr_reviews["require_code_owner_reviews"] = getattr(
                        pr_reviews, "require_code_owner_reviews", None
                    )
                    required_pr_reviews["required_approving_review_count"] = (
                        getattr(
                            pr_reviews, "required_approving_review_count", None
                        )
                    )
                    dismissal = getattr(
                        pr_reviews, "dismissal_restrictions", None
                    )
                    dismissal_restrictions = {}
                    if dismissal:
                        dismissal_restrictions["users"] = [
                            user.login
                            for user in getattr(dismissal, "users", [])
                        ]
                        dismissal_restrictions["teams"] = [
                            team.name for team in getattr(dismissal, "teams", [])
                        ]
                    required_pr_reviews["dismissal_restrictions"] = (
                        dismissal_restrictions
                    )
                # 3) Extract restrictions.
                restrictions = getattr(protection, "restrictions", None)
                restrictions_dict = {}
                if restrictions:
                    restrictions_dict["users"] = [
                        user.login for user in getattr(restrictions, "users", [])
                    ]
                    restrictions_dict["teams"] = [
                        team.name for team in getattr(restrictions, "teams", [])
                    ]
                # Package all the information in a dictionary for the current
                # branch.
                branch_protection[branch.name] = {
                    "enforce_admins": getattr(
                        protection, "enforce_admins", None
                    ),
                    "allow_force_pushes": getattr(
                        protection, "allow_force_pushes", None
                    ),
                    "allow_deletions": getattr(
                        protection, "allow_deletions", None
                    ),
                    "required_status_checks": required_status_checks,
                    "required_pull_request_reviews": required_pr_reviews,
                    "restrictions": restrictions_dict,
                }
            except github.GithubException as e:
                # It is possible that a branch has no protection set, so we
                # recover from this by leaving an empty dictionary and
                # continue.
                if hasattr(e, "status") and e.status == 404:
                    # Skip if branch has no protection.
                    _LOG.warning(
                        "Branch %s has no protection (404), skipping.",
                        branch.name,
                    )
                    continue
                # Assert for all other GitHub errors.
                hdbg.dassert(
                    False,
                    "Unexpected GitHub error for branch '%s': %s",
                    branch.name,
                    str(e),
                )
            except (AttributeError, TypeError, ValueError) as e:
                hdbg.dassert(
                    False,
                    "Error processing branch %s: %s",
                    branch.name,
                    str(e),
                )
        return branch_protection

    @staticmethod
    def load_settings(path: str) -> "_RepoAndBranchSettings":
        """
        Load settings from settings manifest file.

        :param path: path to settings manifest file
        :return: settings object
        """
        with open(path, "r", encoding="utf-8") as file:
            yaml_data = yaml.safe_load(file)
            settings = _RepoAndBranchSettings(yaml_data)
            return settings

    def save_settings(self, path: str) -> None:
        """
        Save settings to a settings manifest file.

        :param path: path to save the settings manifest file to
        """
        with open(path, "w", encoding="utf-8") as file:
            settings_data = {
                "branch_protection": self._repo_and_branch_settings.get(
                    "branch_protection", {}
                ),
                "repository_settings": self._repo_and_branch_settings.get(
                    "repository_settings", {}
                ),
            }
            # Set `default_flow_style=False` to use block style instead of
            # flow style for better readability.
            yaml.dump(
                settings_data, file, default_flow_style=False, sort_keys=False
            )

    def apply_branch_protection(
        self,
        repository: github.Repository.Repository,
        *,
        is_dry_run: Optional[bool] = False,
    ) -> None:
        """
        Apply branch protection rules to all the branches.

        This method applies branch protection settings to each branch specified in the
        configuration. It handles various branchprotection aspects including:
        - Required status checks
        - Pull request review requirements
        - Push restrictions
        - Force push and deletion settings

        :param repository: GitHub repository object
        :param is_dry_run: whether to perform a dry run without making changes
        """
        _LOG.info(
            "Starting branch protection configuration for %s.",
            repository.full_name,
        )
        # Get the target branch protection settings.
        target_branch_protection = self._repo_and_branch_settings.get(
            "branch_protection", {}
        )
        _LOG.debug(
            "Target branch protection settings: %s", target_branch_protection
        )
        for branch_name, protection in target_branch_protection.items():
            _LOG.debug(
                "Processing branch '%s' with protection settings: %s",
                branch_name,
                protection,
            )
            branch = repository.get_branch(branch_name)
            # Normalize the branch protection settings.
            # Extract top-level protection settings that don't require special handling.
            expected_branch_protection_keys = {
                "enforce_admins",
                "allow_force_pushes",
                "allow_deletions",
            }
            target_branch_settings = self.normalize_settings(
                protection,
                expected_branch_protection_keys,
            )
            _LOG.debug(
                "Normalized top-level branch settings for '%s': %s",
                branch_name,
                target_branch_settings,
            )
            # Extract nested protection settings that require special handling.
            # Process complex settings separately due to their nested structure.
            required_status_checks = protection.get("required_status_checks", {})
            required_pr_reviews = protection.get(
                "required_pull_request_reviews", {}
            )
            restrictions = protection.get("restrictions", {})
            _LOG.debug(
                "Extracted nested settings for '%s': status_checks=%s, pr_reviews=%s, restrictions=%s",
                branch_name,
                required_status_checks,
                required_pr_reviews,
                restrictions,
            )
            # Process required status checks.
            # Configure which CI checks must pass before merging.
            status_checks = self.normalize_settings(
                required_status_checks,
                STATUS_CHECK_KEYS,
            )
            if status_checks:
                target_branch_settings["strict"] = status_checks.get("strict")
                target_branch_settings["contexts"] = (
                    status_checks.get("contexts", [])
                    or github.GithubObject.NotSet
                )
                _LOG.debug(
                    "Configured status checks for '%s': strict=%s, contexts=%s",
                    branch_name,
                    status_checks.get("strict"),
                    status_checks.get("contexts", []),
                )

            # Process pull request review requirements.
            # Configure who can approve PRs and how many approvals are needed.
            pr_reviews = self.normalize_settings(
                required_pr_reviews,
                PR_REVIEW_KEYS,
            )
            if pr_reviews:
                target_branch_settings["dismiss_stale_reviews"] = pr_reviews.get(
                    "dismiss_stale_reviews"
                )
                target_branch_settings["require_code_owner_reviews"] = (
                    pr_reviews.get("require_code_owner_reviews")
                )
                target_branch_settings["required_approving_review_count"] = (
                    pr_reviews.get("required_approving_review_count")
                )
                _LOG.debug(
                    "Configured PR review requirements for '%s': %s",
                    branch_name,
                    pr_reviews,
                )
                # Handle dismissal restrictions.
                # These determine who can dismiss PR reviews.
                dismissal = pr_reviews.get("dismissal_restrictions", {})
                if dismissal:
                    target_branch_settings["dismissal_users"] = dismissal.get(
                        "users", []
                    )
                    target_branch_settings["dismissal_teams"] = dismissal.get(
                        "teams", []
                    )
                    _LOG.debug(
                        "Configured dismissal restrictions for '%s': users=%s, teams=%s",
                        branch_name,
                        dismissal.get("users", []),
                        dismissal.get("teams", []),
                    )

            # Process push restrictions.
            # Configure who can push to the branch.
            if restrictions:
                target_branch_settings["user_push_restrictions"] = (
                    restrictions.get("users", [])
                )
                target_branch_settings["team_push_restrictions"] = (
                    restrictions.get("teams", [])
                )
                _LOG.debug(
                    "Configured push restrictions for '%s': users=%s, teams=%s",
                    branch_name,
                    restrictions.get("users", []),
                    restrictions.get("teams", []),
                )

            # Apply branch protection settings.
            if not is_dry_run:
                _LOG.debug(
                    "Applying branch protection settings for '%s': %s",
                    branch_name,
                    target_branch_settings,
                )
                branch.edit_protection(**target_branch_settings)
            # Log the branch protection settings that are applied.
            self._log_settings(
                target_branch_settings,
                "branch protection rules",
                branch_name,
                dry_run=is_dry_run,
            )

    def apply_repo_settings(
        self,
        repository: github.Repository.Repository,
        *,
        is_dry_run: Optional[bool] = False,
    ) -> None:
        """
        Apply repository settings.

        This method applies various repository settings including:
        - Basic repository properties (name, description, etc.)
        - Security settings (automated fixes, vulnerability alerts)
        - Repository topics
        - Merge settings

        :param repository: GitHub repository object
        :param is_dry_run: whether to perform a dry run without making changes
        """
        _LOG.info(
            "Starting repository settings configuration for %s.",
            repository.full_name,
        )
        # Extract repository settings from the configuration.
        target_repo_settings = self._repo_and_branch_settings.get(
            "repository_settings", {}
        )
        _LOG.debug("Target repository settings: %s", target_repo_settings)
        # Normalize the repository settings.
        target_repo_settings = self.normalize_settings(
            target_repo_settings,
            REPO_SETTING_KEYS,
        )
        _LOG.debug("Normalized repository settings: %s", target_repo_settings)
        # Remove security-related settings for special handling.
        # Use dedicated API calls instead of the standard edit method.
        enable_security_fixes = target_repo_settings.pop(
            "enable_automated_security_fixes", None
        )
        enable_vuln_alerts = target_repo_settings.pop(
            "enable_vulnerability_alerts", None
        )
        topics = target_repo_settings.pop("topics", None)
        _LOG.debug(
            "Extracted special settings: security_fixes=%s, vuln_alerts=%s, topics=%s",
            enable_security_fixes,
            enable_vuln_alerts,
            topics,
        )
        # Apply settings if not in dry run mode.
        if not is_dry_run:
            _LOG.debug(
                "Applying basic repository settings: %s", target_repo_settings
            )
            # Update basic repository settings.
            repository.edit(**target_repo_settings)
            if enable_security_fixes is not None:
                # Configure automated security fixes.
                if enable_security_fixes:
                    repository.enable_automated_security_fixes()
                    _LOG.info("Enabled automated security fixes.")
                else:
                    repository.disable_automated_security_fixes()
                    _LOG.info("Disabled automated security fixes.")
            if enable_vuln_alerts is not None:
                # Configure vulnerability alerts.
                if enable_vuln_alerts:
                    repository.enable_vulnerability_alert()
                    _LOG.info("Enabled vulnerability alerts.")
                else:
                    repository.disable_vulnerability_alert()
                    _LOG.info("Disabled vulnerability alerts.")
            if topics is not None:
                # Update repository topics.
                repository.replace_topics(topics)
                _LOG.info("Updated repository topics: %s.", ", ".join(topics))
        # Log the repository settings that are applied.
        self._log_settings(
            target_repo_settings,
            "repository settings",
            repository.full_name,
            dry_run=is_dry_run,
        )
        if is_dry_run:
            # Log few repository settings for `dry_run` mode separately.
            if enable_security_fixes is not None:
                _LOG.info(
                    "If not --dry_run, automated security fixes will be %s.",
                    "enabled" if enable_security_fixes else "disabled",
                )
            if enable_vuln_alerts is not None:
                _LOG.info(
                    "If not --dry_run, vulnerability alerts will be %s.",
                    "enabled" if enable_vuln_alerts else "disabled",
                )
            if topics is not None:
                _LOG.info(
                    "If not --dry_run, repository topics will be updated to: %s.",
                    ", ".join(topics),
                )

    def normalize_settings(
        self,
        settings: Dict[str, Any],
        expected_keys: Set[str],
    ) -> Dict[str, Any]:
        """
        Normalize a settings dictionary by filtering for expected keys and
        converting missing values to NotSet.

        This method uses `github.GithubObject.NotSet` for missing keys to ensure
        safe updates of GitHub repository settings. When a field is not present
        in the input YAML file, using `NotSet` instead of `None` or omitting the
        field entirely prevents accidental overwrites of existing settings.

        Examples-
        - If a field is set to `None` in the YAML, it will explicitly clear that setting.
        - If a field is omitted from the YAML, using `NotSet` preserves the existing value.
        - If a field has a value in the YAML, that value will be used to update the setting.

        :param settings: source dictionary containing settings
        :param expected_keys: set of expected keys to extract
        :return: normalized settings dictionary with NotSet values for
            missing keys
        """
        normalized_settings = {}
        for key in expected_keys:
            value = settings.get(key)
            normalized_settings[key] = (
                value if value is not None else github.GithubObject.NotSet
            )
        return normalized_settings

    def _validate_settings(self) -> None:
        """
        Validate that all settings keys in the input file are known and
        expected.

        Raises an assertion error if unknown keys are found.
        """
        gh_setting_keys = set(self._repo_and_branch_settings.keys())
        unknown_gh_setting_keys = gh_setting_keys - GH_SETTING_KEYS
        hdbg.dassert(
            not unknown_gh_setting_keys,
            "Unexpected top-level keys in settings: %s",
            unknown_gh_setting_keys,
        )
        repo_setting_keys = self._repo_and_branch_settings.get(
            "repository_settings", {}
        ).keys()
        unknown_repo_setting_keys = repo_setting_keys - REPO_SETTING_KEYS
        hdbg.dassert(
            not unknown_repo_setting_keys,
            "Unexpected keys in 'repository_settings': %s",
            unknown_repo_setting_keys,
        )
        branch_protection_keys = self._repo_and_branch_settings.get(
            "branch_protection", {}
        )
        for branch, protection in branch_protection_keys.items():
            unknown_branch_protection_keys = (
                set(protection.keys()) - BRANCH_PROTECTION_KEYS
            )
            hdbg.dassert(
                not unknown_branch_protection_keys,
                "Unexpected keys in 'branch_protection' for branch '%s': %s",
                branch,
                unknown_branch_protection_keys,
            )
            status_checks_keys = protection.get(
                "required_status_checks", {}
            ).keys()
            unknown_status_checks_keys = status_checks_keys - STATUS_CHECK_KEYS
            hdbg.dassert(
                not unknown_status_checks_keys,
                "Unexpected keys in 'required_status_checks' for branch '%s': %s",
                branch,
                unknown_status_checks_keys,
            )
            pr_reviews_keys = protection.get(
                "required_pull_request_reviews", {}
            ).keys()
            unknown_pr_reviews_keys = pr_reviews_keys - PR_REVIEW_KEYS
            hdbg.dassert(
                not unknown_pr_reviews_keys,
                "Unexpected keys in 'required_pull_request_reviews' for branch '%s': %s",
                branch,
                unknown_pr_reviews_keys,
            )
            restrictions_keys = protection.get("restrictions", {}).keys()
            unknown_restrictions_keys = restrictions_keys - RESTRICTION_KEYS
            hdbg.dassert(
                not unknown_restrictions_keys,
                "Unexpected keys in 'restrictions' for branch '%s': %s",
                branch,
                unknown_restrictions_keys,
            )

    def _log_settings(
        self,
        settings: Dict[str, Any],
        action: str,
        target: str,
        *,
        dry_run: Optional[bool] = False,
    ) -> None:
        """
        Log repository or branch protection settings that have been synced.

        :param settings: settings dictionary to log
        :param action: action being performed (e.g., "apply branch protection rules")
        :param target: target of the action (e.g., `branch` name or `repo` name)
        :param dry_run: whether this is a dry run
        """
        # Filter out NotSet values from settings dictionary.
        log_settings = {
            k: v
            for k, v in settings.items()
            if v is not github.GithubObject.NotSet
        }
        if not dry_run:
            _LOG.info(
                "The below %s are applied to %s:\n%s",
                action,
                target,
                "\n".join(f"  {k}: {v}" for k, v in log_settings.items()),
            )
        else:
            _LOG.info(
                "The below %s will be applied to %s without --dry_run:\n%s",
                action,
                target,
                "\n".join(f"  {k}: {v}" for k, v in log_settings.items()),
            )


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # Create subparsers for different commands.
    subparsers = parser.add_subparsers(dest="command", help="Sub-command help")
    # Add export command to save repo settings to a file.
    export_parser = subparsers.add_parser(
        "export",
        help="Save repository and branch protection settings to a YAML file",
    )
    hparser.add_verbosity_arg(export_parser)
    export_parser.add_argument(
        "--output_file",
        required=True,
        help="Path to save the repository and branch protection settings",
    )
    export_parser.add_argument(
        "--owner",
        required=True,
        help="GitHub repository owner/organization",
    )
    export_parser.add_argument(
        "--repo", required=True, help="GitHub repository name"
    )
    export_parser.add_argument(
        "--token_env_var",
        required=True,
        help="Name of the environment variable containing the GitHub token",
    )
    export_parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Print actions without executing them",
    )
    # Add sync command to sync settings from file to repo.
    sync_parser = subparsers.add_parser(
        "sync",
        help="Sync repository and branch protection settings from a YAML file",
    )
    hparser.add_verbosity_arg(sync_parser)
    sync_parser.add_argument(
        "--input_file",
        required=True,
        help="Path to settings manifest file",
    )
    sync_parser.add_argument(
        "--owner",
        required=True,
        help="GitHub repository owner/organization",
    )
    sync_parser.add_argument(
        "--repo", required=True, help="GitHub repository name"
    )
    sync_parser.add_argument(
        "--token_env_var",
        required=True,
        help="Name of the environment variable containing the GitHub token",
    )
    sync_parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Print out the actions that would be taken without executing them",
    )
    return parser


def _get_repo(args: argparse.Namespace) -> github.Repository.Repository:
    """
    Initialize GitHub client and get repository object.

    :param args: Command line arguments containing owner, repo name, and
        token env var
    :return: GitHub repository object
    """
    # Get GitHub token from environment variable.
    token = os.environ[args.token_env_var]
    hdbg.dassert(token, "Missing token from %s", args.token_env_var)
    # Initialize GitHub client.
    client = github.Github(token)
    repo = client.get_repo(f"{args.owner}/{args.repo}")
    _LOG.debug(hprint.to_str("repo"))
    return repo


def _get_repo_and_branch_settings(
    repo: github.Repository.Repository,
) -> _RepoAndBranchSettings:
    """
    Get current settings from a GitHub repository.

    :param repo: GitHub repository object
    :return: Settings object containing current repository settings
    """
    current_repo_and_branch_settings = _RepoAndBranchSettings(
        {
            "branch_protection": _RepoAndBranchSettings.get_branch_protection_settings(
                repo
            ),
            "repository_settings": _RepoAndBranchSettings.get_repository_settings(
                repo
            ),
        }
    )
    return current_repo_and_branch_settings


def _export_repo_settings(args: argparse.Namespace) -> None:
    """
    Export repository settings to a YAML file.

    :param args: Command line arguments containing output file path,
        owner, repo name, and token env var
    """
    # Get GitHub repository object.
    repo = _get_repo(args)
    if not args.dry_run:
        # Get current settings and save to file.
        repo_and_branch_settings = _get_repo_and_branch_settings(repo)
        repo_and_branch_settings.save_settings(args.output_file)
        _LOG.info("Repository settings exported to %s", args.output_file)
    else:
        _LOG.info(
            "Repository settings will be exported to %s without --dry_run",
            args.output_file,
        )


def _sync_repo_settings(args: argparse.Namespace) -> None:
    """
    Import repository settings from a YAML file.

    :param args: Command line arguments containing input file path,
        owner, repo name, token env var, and dry run flag
    """
    # Get GitHub repository object.
    repo = _get_repo(args)
    # Create backup of current settings.
    backup_file = f"settings.{args.owner}.{args.repo}.backup.yaml"
    current_repo_and_branch_settings = _get_repo_and_branch_settings(repo)
    current_repo_and_branch_settings.save_settings(backup_file)
    _LOG.info("Repository settings backed up to %s", backup_file)
    # Load settings from input file.
    target_repo_and_branch_settings = _RepoAndBranchSettings.load_settings(
        args.input_file
    )
    # Apply branch protection and repository settings.
    target_repo_and_branch_settings.apply_branch_protection(
        repo, is_dry_run=args.dry_run
    )
    target_repo_and_branch_settings.apply_repo_settings(
        repo, is_dry_run=args.dry_run
    )
    _LOG.info("Repository settings import completed!")


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    if args.command == "export":
        _export_repo_settings(args)
    elif args.command == "sync":
        _sync_repo_settings(args)
    else:
        _LOG.error("Invalid command. Use 'export' or 'sync'.")


if __name__ == "__main__":
    _main(_parse())
