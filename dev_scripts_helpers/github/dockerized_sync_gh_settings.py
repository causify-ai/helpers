#!/usr/bin/env python3
"""
The script is designed to synchronize GitHub repository settings from a
settings manifest file. It requires certain dependencies to be present (e.g.,
`pygithub`) and thus it is executed as a dockerized executable.

To use this script, you need to provide the input file, GitHub repository name,
owner, token environment variable, and optional flags for controlling the
synchronization behavior.

The command lines are the same as the `dev_scripts_helpers/github/sync_gh_repo_settings.py` script.
"""

import argparse
import logging
import os
from typing import Any, Dict

import github as gh
import github.GithubObject as gh_obj
import github.Repository as gh_repo
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
            repository settings.
        """
        self._settings = settings
        self._branch_protection = settings.get("branch_protection", {})
        self._repo_settings = settings.get("repository_settings", {})

    def __repr__(self):
        return f"settings(branch_protection={self.branch_protection}, repo_settings={self.repo_settings})"

    @staticmethod
    def load_settings(path: str) -> "Settings":
        """
        Load settings from a YAML file.

        :param path: path to settings manifest file
        :return: settings object
        """
        with open(path, "r", encoding="utf-8") as file:
            yaml_data = yaml.safe_load(file)
            return Settings(yaml_data)

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

    def prune_branch_protection(
        self, repo: gh_repo.Repository, execute: bool = True
    ) -> None:
        """
        Remove branch protection rules that exist in the repo but not in
        settings.

        :param repo: github repository object
        :param execute: whether to actually apply changes
        """
        try:
            branches = repo.get_branches()
            for branch in branches:
                try:
                    # Check if branch has protection.
                    protection = branch.get_protection()
                    # If branch is not in our settings but has protection, remove it.
                    if branch.name not in self.branch_protection:
                        if execute:
                            protection.remove()
                            _LOG.info(
                                "Branch protection removed from %s", branch.name
                            )
                        else:
                            _LOG.info(
                                "Would remove branch protection from %s",
                                branch.name,
                            )
                except gh.GithubException as e:
                    if e.status == 404:
                        # Branch has no protection, skip.
                        continue
                    else:
                        raise
        except gh.GithubException as e:
            _LOG.error("Failed to prune branch protection: %s", str(e))

    def prune_repo_settings(
        self, repo: gh_repo.Repository, execute: bool = True
    ) -> None:
        """
        Reset repository settings that exist in the repo but not in settings.

        :param repo: github repository object
        :param execute: whether to actually apply changes
        """
        current_settings = {
            "allow_merge_commit": repo.allow_merge_commit,
            "allow_squash_merge": repo.allow_squash_merge,
            "allow_rebase_merge": repo.allow_rebase_merge,
            "has_issues": repo.has_issues,
            "has_wiki": repo.has_wiki,
            "has_projects": repo.has_projects,
        }

        # Check each setting
        for setting, value in current_settings.items():
            if setting not in self.repo_settings and value:
                if execute:
                    # Reset the setting to its default value.
                    if setting in [
                        "allow_merge_commit",
                        "allow_squash_merge",
                        "allow_rebase_merge",
                    ]:
                        repo.edit(**{setting: False})
                        _LOG.info(
                            "Reset repository setting %s to default", setting
                        )
                    elif setting in ["has_issues", "has_wiki", "has_projects"]:
                        repo.edit(**{setting: False})
                        _LOG.info(
                            "Reset repository setting %s to default", setting
                        )
                else:
                    _LOG.info(
                        "Would reset repository setting %s to default", setting
                    )

    def apply_branch_protection(
        self, repo: gh_repo.Repository, execute: bool = True
    ) -> None:
        """
        Apply branch protection rules.

        :param repo: github repository object
        :param execute: whether to actually apply changes
        """
        for branch_name, protection in self.branch_protection.items():
            try:
                branch = repo.get_branch(branch_name)
                if execute:
                    # Get the protection settings.
                    required_status_checks = protection.get(
                        "required_status_checks", {}
                    )
                    required_pr_reviews = protection.get(
                        "required_pull_request_reviews", {}
                    )
                    restrictions = protection.get("restrictions", {})
                    # Only include status checks if explicitly set and non-empty.
                    contexts = required_status_checks.get("contexts", [])
                    strict = required_status_checks.get("strict")
                    # Apply branch protection with supported parameters.
                    branch.edit_protection(
                        strict=strict if strict is not None else gh_obj.NotSet,
                        contexts=contexts if contexts else gh_obj.NotSet,
                        enforce_admins=protection.get(
                            "enforce_admins", gh_obj.NotSet
                        ),
                        dismiss_stale_reviews=required_pr_reviews.get(
                            "dismiss_stale_reviews", gh_obj.NotSet
                        ),
                        require_code_owner_reviews=required_pr_reviews.get(
                            "require_code_owner_reviews", gh_obj.NotSet
                        ),
                        required_approving_review_count=required_pr_reviews.get(
                            "required_approving_review_count", gh_obj.NotSet
                        ),
                        dismissal_users=required_pr_reviews.get(
                            "dismissal_restrictions", {}
                        ).get("users", gh_obj.NotSet),
                        dismissal_teams=required_pr_reviews.get(
                            "dismissal_restrictions", {}
                        ).get("teams", gh_obj.NotSet),
                        user_push_restrictions=restrictions.get(
                            "users", gh_obj.NotSet
                        ),
                        team_push_restrictions=restrictions.get(
                            "teams", gh_obj.NotSet
                        ),
                    )
                    _LOG.info(
                        "Branch protection rules applied to %s", branch_name
                    )
                else:
                    _LOG.info(
                        "Would apply branch protection rules to %s", branch_name
                    )
            except gh.GithubException as e:
                _LOG.error(
                    "Failed to apply branch protection to %s: %s",
                    branch_name,
                    str(e),
                )

    def apply_repo_settings(
        self, repo: gh_repo.Repository, execute: bool = True
    ) -> None:
        """
        Apply repository settings.

        :param repo: github repository object
        :param execute: whether to actually apply changes
        """
        if execute:
            # Handle visibility/private conflict.
            private = self.repo_settings.get("private")
            # Apply basic repository settings.
            repo.edit(
                name=self.repo_settings.get("name"),
                description=self.repo_settings.get("description", gh_obj.NotSet),
                homepage=self.repo_settings.get("homepage", gh_obj.NotSet),
                private=private if private is not None else gh_obj.NotSet,
                has_issues=self.repo_settings.get("has_issues", gh_obj.NotSet),
                has_projects=self.repo_settings.get(
                    "has_projects", gh_obj.NotSet
                ),
                has_wiki=self.repo_settings.get("has_wiki", gh_obj.NotSet),
                default_branch=self.repo_settings.get(
                    "default_branch", gh_obj.NotSet
                ),
                allow_squash_merge=self.repo_settings.get(
                    "allow_squash_merge", gh_obj.NotSet
                ),
                allow_merge_commit=self.repo_settings.get(
                    "allow_merge_commit", gh_obj.NotSet
                ),
                allow_rebase_merge=self.repo_settings.get(
                    "allow_rebase_merge", gh_obj.NotSet
                ),
                archived=self.repo_settings.get("archived", gh_obj.NotSet),
            )
            # Apply security settings
            try:
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
            except gh.GithubException as e:
                _LOG.error(
                    "Failed to configure automated security fixes: %s", str(e)
                )
            try:
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
            except gh.GithubException as e:
                _LOG.error("Failed to configure vulnerability alerts: %s", str(e))
            # Update topics separately.
            try:
                if "topics" in self.repo_settings:
                    topics = [
                        topic.strip()
                        for topic in self.repo_settings["topics"].split(",")
                    ]
                    repo.replace_topics(topics)
                    _LOG.info("Updated repository topics")
            except gh.GithubException as e:
                _LOG.error("Failed to update repository topics: %s", str(e))
            _LOG.info("Repository settings applied")
        else:
            _LOG.info("Would apply repository settings")


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
        "--prune",
        action="store_true",
        help="Delete settings that exist in the repo but not in the settings manifest file",
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
    # Initialize GH client.
    client = gh.Github(token)
    repo = client.get_repo(f"{args.owner}/{args.repo}")
    # Get current settings from the repo.
    current_settings = {
        "branch_protection": {},
        "repository_settings": {
            "allow_merge_commit": repo.allow_merge_commit,
            "allow_squash_merge": repo.allow_squash_merge,
            "allow_rebase_merge": repo.allow_rebase_merge,
            "has_issues": repo.has_issues,
            "has_wiki": repo.has_wiki,
            "has_projects": repo.has_projects,
            "default_branch": repo.default_branch,
        },
    }
    # Execute code if not in dry run mode.
    execute = not args.dry_run
    # Backup current settings if requested.
    if args.backup:
        git_root_dir = hgit.get_client_root(False)
        backup_file = f"tmp.settings.{args.owner}.{args.repo}.yaml"
        backup_path = f"{git_root_dir}/{backup_file}"
        Settings.save_settings(current_settings, backup_path)
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
    # Change to default settings if pruning is enabled.
    if args.prune:
        settings.prune_branch_protection(repo, execute)
        settings.prune_repo_settings(repo, execute)
    # Apply new settings
    settings.apply_branch_protection(repo, execute)
    settings.apply_repo_settings(repo, execute)
    _LOG.info("Settings synchronization completed!")


if __name__ == "__main__":
    _main(_parse())
