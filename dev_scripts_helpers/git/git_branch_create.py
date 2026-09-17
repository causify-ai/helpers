#!/usr/bin/env python3

"""
Create and push an upstream branch for a GitHub issue or an explicit name.

Optionally creates a draft PR for the new branch.

# Usage Example

- Create a branch from a GitHub issue ID, auto-picking the next free suffix:
> git_branch_create.py --issue_id 123

- Create a branch with an explicit name, skipping the draft PR:
> git_branch_create.py --branch_name HelpersTask123_Fix_bug --no_create_pr

Import as:

import dev_scripts_helpers.git.git_branch_create as dsggibrc
"""

import argparse
import logging
import re
import shlex

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hparser as hparser
import helpers.hsystem as hsystem
import helpers.lib_tasks.lib_tasks_gh as hltltagh

_LOG = logging.getLogger(__name__)


# #############################################################################
# Branch name resolution
# #############################################################################


def _get_branch_name_for_issue(
    issue_id: int, repo_short_name: str, suffix: str
) -> str:
    """
    Compute the branch name corresponding to `issue_id`.

    When `suffix` is empty, auto-pick the next free suffix via
    `hgit.get_branch_next_name()` instead of requiring the caller to guess
    one.

    :param issue_id: GitHub issue ID to derive the branch name from
    :param repo_short_name: repo the issue belongs to
    :param suffix: explicit suffix to append (e.g., "02"); if empty, the
        next free suffix is auto-picked
    :return: branch name (e.g., `HelpersTask123_Fix_bug` or
        `HelpersTask123_Fix_bug_3`)
    """
    title, _ = hltltagh._get_gh_issue_title(issue_id, repo_short_name)
    branch_name = title
    _LOG.info(
        "Issue %d in %s repo_short_name corresponds to '%s'",
        issue_id,
        repo_short_name,
        branch_name,
    )
    if suffix != "":
        branch_name += "_" + suffix
    else:
        branch_name = hgit.get_branch_next_name(curr_branch_name=branch_name)
    return branch_name


def _dassert_branch_available(branch_name: str) -> None:
    """
    Assert that `branch_name` does not already exist locally or remotely.

    :param branch_name: branch name to check
    """
    hdbg.dassert(
        not hgit.does_branch_exist(branch_name, mode="all"),
        "Branch '%s' already exists",
        branch_name,
    )


def _dassert_valid_branch_name(branch_name: str) -> None:
    """
    Assert that `branch_name` follows the naming convention.

    Allows personal/scratch branches like `gp`, `gp_2`, `gp_scratch_3`, used
    for throwaway work not tied to a GitHub issue.

    :param branch_name: branch name to check
    """
    # Reject numeric-only branch names to avoid confusion with commit SHAs.
    m = re.match(r"^\d+$", branch_name)
    hdbg.dassert(
        not m,
        "Branch names with only numbers are invalid",
    )
    # Enforce naming convention `{RepoPrefix}TaskXYZ_Description` for
    # consistency, e.g., `AmpTask1903_Implemented_system_...`.
    task_pattern = r"^\S+Task\d+_\S+$"
    personal_pattern = r"^gp(_(scratch\w*|\d+))?$"
    m = re.match(task_pattern, branch_name) or re.match(
        personal_pattern, branch_name
    )
    hdbg.dassert(
        m,
        "Branch name must follow convention: '{RepoPrefix,Amp,...}TaskXYZ_...'",
    )


# #############################################################################
# Branch creation
# #############################################################################


def _create_branch(
    branch_name: str,
    issue_id: int,
    repo_short_name: str,
    suffix: str,
    *,
    only_branch_from_master: bool = True,
    check_branch_name: bool = True,
    create_pr: bool = True,
    abort_if_not_clean: bool = True,
    abort_if_not_master: bool = True,
) -> None:
    """
    Create and push upstream branch `branch_name` or the one corresponding
    to `issue_id` in repo `repo_short_name`.

    Same parameters as `invoke git_branch_create`.
    """
    hdbg.dassert(
        not any(suffix.startswith(char) for char in "_-."),
        "suffix='%s' should not start with _, -, or . since it's added as "
        "'_{suffix}'",
        suffix,
    )
    # Verify working directory is clean if requested.
    hgit.is_client_clean(dir_name=".", abort_if_not_clean=abort_if_not_clean)
    if issue_id > 0:
        # Convert GitHub issue ID to branch name.
        hdbg.dassert_eq(
            branch_name,
            "",
            "Cannot specify both --issue and --branch-name; choose one",
        )
        branch_name = _get_branch_name_for_issue(
            issue_id, repo_short_name, suffix
        )
    _LOG.info("branch_name='%s'", branch_name)
    hdbg.dassert_ne(branch_name, "", "Branch name cannot be empty")
    if check_branch_name:
        _dassert_valid_branch_name(branch_name)
    # Prevent accidental duplicate branches.
    _dassert_branch_available(branch_name)
    # Ensure we are branching from master if required.
    if only_branch_from_master:
        curr_branch = hgit.get_branch_name()
        if curr_branch != "master":
            hdbg.dassert(
                not abort_if_not_master,
                "Must be on 'master' branch to create new branch; "
                "currently on '%s'",
                curr_branch,
            )
            _LOG.info(
                "Switching from '%s' to 'master' to create branch",
                curr_branch,
            )
            hsystem.system("git checkout master", suppress_output=False)
    # Fetch latest master to ensure we have the most recent changes.
    hsystem.system("git pull --autostash --rebase", suppress_output=False)
    # git checkout -b LmTask169_Get_GH_actions_working_on_lm
    cmd = f"git checkout -b {shlex.quote(branch_name)}"
    hsystem.system(cmd, suppress_output=False)
    cmd = f"git push --set-upstream origin {shlex.quote(branch_name)}"
    hsystem.system(cmd, suppress_output=False)
    # Create a draft PR if requested.
    if create_pr:
        _LOG.info("Creating draft PR for branch '%s'", branch_name)
        # Create empty commit to ensure there's at least one commit for the
        # PR.
        cmd = 'git commit --allow-empty -m "Draft PR"'
        hsystem.system(cmd, suppress_output=False)
        hsystem.system("git push", suppress_output=False)
        rc = hsystem.system("invoke gh_create_pr --draft", abort_on_error=False)
        if rc != 0:
            _LOG.warning("Failed to create PR (rc=%s)", rc)


# #############################################################################
# CLI
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    parser.add_argument(
        "--branch_name",
        type=str,
        default="",
        help="Name of the branch to create (e.g., LemTask169_Get_GH_actions)",
    )
    parser.add_argument(
        "--issue_id",
        type=int,
        default=0,
        help="Use the canonical name for the branch corresponding to that "
        "issue",
    )
    parser.add_argument(
        "--repo_short_name",
        type=str,
        default="current",
        help="Name of the GitHub repo that `issue_id` belongs to",
    )
    parser.add_argument(
        "--suffix",
        type=str,
        default="",
        help="Suffix (e.g., '02') to add to the branch name when using "
        "--issue_id",
    )
    parser.add_argument(
        "--no_only_branch_from_master",
        action="store_true",
        help="Allow branching from a branch other than 'master'",
    )
    parser.add_argument(
        "--no_check_branch_name",
        action="store_true",
        help="Skip checking that the branch name follows the naming "
        "convention",
    )
    parser.add_argument(
        "--no_create_pr",
        action="store_true",
        help="Do not create a draft PR for the new branch",
    )
    parser.add_argument(
        "--no_abort_if_not_clean",
        action="store_true",
        help="Do not abort if the client has uncommitted changes",
    )
    parser.add_argument(
        "--no_abort_if_not_master",
        action="store_true",
        help="Do not abort if not on master branch; switch to master "
        "instead",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    _create_branch(
        args.branch_name,
        args.issue_id,
        args.repo_short_name,
        args.suffix,
        only_branch_from_master=not args.no_only_branch_from_master,
        check_branch_name=not args.no_check_branch_name,
        create_pr=not args.no_create_pr,
        abort_if_not_clean=not args.no_abort_if_not_clean,
        abort_if_not_master=not args.no_abort_if_not_master,
    )


if __name__ == "__main__":
    _main(_parse())
