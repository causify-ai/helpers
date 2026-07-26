#!/usr/bin/env python3

"""
Create a new branch with the same content as the current branch.

Workflow:
1. Cleans the working tree
2. Detects the parent branch of the current branch (explicit override, remote
   tracking branch, or fallback to `master`)
3. Merges the parent branch into the current branch (unless skipped)
4. Creates the new branch from the detected parent (or checks it out if it
   already exists)
5. Squash-merges the current branch into the new branch

Import as:

import dev_scripts_helpers.git.git_branch_copy as dshggbc
"""

import argparse
import logging
from typing import Optional

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# #############################################################################
# Parent branch detection
# #############################################################################


def _get_remote_tracking_branch() -> Optional[str]:
    """
    Get the local name of the branch tracked by the current branch.

    :return: name of the tracked branch (e.g., `master` for a remote
        branch `origin/master`), or `None` if the current branch does not
        track any remote branch
    """
    cmd = "git rev-parse --abbrev-ref @{u}"
    rc, output = hsystem.system_to_string(cmd, abort_on_error=False)
    if rc != 0:
        return None
    # Strip the remote name (e.g., `origin/master` -> `master`).
    _, _, branch_name = output.strip().partition("/")
    return branch_name or None


def get_parent_branch(parent_branch: str) -> str:
    """
    Detect the parent branch to create the new branch from.

    :param parent_branch: explicit parent branch override; if empty,
        auto-detection is attempted
    :return: name of the parent branch to use
    """
    if parent_branch:
        _LOG.info(
            "Using explicit parent branch override: '%s'", parent_branch
        )
        return parent_branch
    detected_branch = _get_remote_tracking_branch()
    if detected_branch:
        _LOG.info("Auto-detected parent branch: '%s'", detected_branch)
        return detected_branch
    _LOG.warning(
        "Unable to auto-detect the parent branch (no remote tracking branch "
        "found); falling back to 'master'"
    )
    return "master"


# #############################################################################
# Core workflow
# #############################################################################


def _clean_working_tree() -> None:
    """
    Remove untracked files to ensure a clean state when copying a branch.
    """
    cmd = "git clean -fd"
    hsystem.system(cmd, log_level=logging.INFO)


def _merge_parent_branch(parent_branch: str) -> None:
    """
    Merge the latest changes of the parent branch into the current branch.

    :param parent_branch: name of the parent branch to sync with
    """
    if parent_branch == "master":
        # Preserve the existing, more thorough workflow for `master` (fetch,
        # fast-forward check, auto-commit).
        cmd = "invoke git_merge_master --abort-if-not-ff --no-auto-merge"
    else:
        cmd = f"git merge {parent_branch} --ff-only"
    hsystem.system(cmd, log_level=logging.INFO)


def _generate_branch_name(new_branch_name: str, method: str) -> str:
    """
    Generate a unique branch name if one was not provided.

    :param new_branch_name: requested branch name, or empty to auto-generate
        one
    :param method: method to use for generating the branch name (see
        `hgit.get_branch_next_name`)
    :return: branch name to use
    """
    if not new_branch_name:
        new_branch_name = hgit.get_branch_next_name(method=method)
    _LOG.info("new_branch_name='%s'", new_branch_name)
    hdbg.dassert_ne(
        new_branch_name, None, "Branch name must not be None after generation"
    )
    return new_branch_name


def _create_or_checkout_branch(
    new_branch_name: str, parent_branch: str, check_branch_name: bool
) -> None:
    """
    Create the new branch from the parent branch, or check it out if it
    already exists.

    :param new_branch_name: name of the new branch
    :param parent_branch: name of the parent branch to create the new
        branch from
    :param check_branch_name: whether to enforce the branch naming
        convention
    """
    mode = "all"
    new_branch_exists = hgit.does_branch_exist(new_branch_name, mode)
    if new_branch_exists:
        # Switch to the existing branch to copy changes into it.
        cmd = f"git checkout {new_branch_name}"
    else:
        cmd = (
            f"git checkout {parent_branch} && "
            f"invoke git_branch_create --branch-name '{new_branch_name}'"
        )
        if not check_branch_name:
            cmd += " --no-check-branch-name"
    hsystem.system(cmd, log_level=logging.INFO)


def _squash_merge_branch(source_branch: str) -> None:
    """
    Squash-merge the source branch into the current branch.

    Copies all commits from `source_branch` as a single staged change,
    without creating a merge commit.

    :param source_branch: name of the branch to copy commits from
    """
    cmd = f"git merge --squash --ff {source_branch} && git reset HEAD"
    hsystem.system(cmd, log_level=logging.INFO)


def copy_branch(
    *,
    new_branch_name: str = "",
    skip_git_merge_master: bool = False,
    use_patch: bool = False,
    check_branch_name: bool = True,
    method: str = "auto",
    parent_branch: str = "",
) -> None:
    """
    Create a new branch with the same content as the current branch.

    :param new_branch_name: name for the new branch; if empty, a name is
        auto-generated
    :param skip_git_merge_master: skip merging the parent branch into the
        current branch
    :param use_patch: apply patching instead of merging (not implemented
        yet)
    :param check_branch_name: enforce branch naming convention like
        `{Amp,...}TaskXYZ_...`
    :param method: method to use for generating the branch name (see
        `hgit.get_branch_next_name`)
    :param parent_branch: explicit override for the parent branch; if
        empty, the parent is auto-detected from the remote tracking branch,
        falling back to `master`
    """
    # Patch-based copying is not yet implemented.
    hdbg.dassert(
        not use_patch, "Patch-based branch copying is not yet implemented"
    )
    _clean_working_tree()
    curr_branch_name = hgit.get_branch_name()
    # Cannot copy master branch since it would be copying the source to
    # itself.
    hdbg.dassert_ne(curr_branch_name, "master", "Cannot copy master branch")
    # Detect the parent branch while still on the source branch, since
    # detection relies on the source branch's remote tracking information.
    detected_parent_branch = get_parent_branch(parent_branch)
    if not skip_git_merge_master:
        _merge_parent_branch(detected_parent_branch)
    else:
        _LOG.warning("Skipping merge of parent branch as requested")
    new_branch_name = _generate_branch_name(new_branch_name, method)
    # Allow scratch branches to bypass the naming convention.
    if new_branch_name.startswith("gp_scratch"):
        check_branch_name = False
    _create_or_checkout_branch(
        new_branch_name, detected_parent_branch, check_branch_name
    )
    _squash_merge_branch(curr_branch_name)


# #############################################################################
# Entry point
# #############################################################################


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main entry point for the script.
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level)
    copy_branch(
        new_branch_name=args.new_branch_name,
        skip_git_merge_master=args.skip_git_merge_master,
        use_patch=args.use_patch,
        check_branch_name=args.check_branch_name,
        method=args.method,
        parent_branch=args.parent_branch,
    )


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments.

    :return: ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--new_branch_name",
        type=str,
        default="",
        help="Name for the new branch (default: auto-generated)",
    )
    parser.add_argument(
        "--skip_git_merge_master",
        action="store_true",
        default=False,
        help="Skip merging the parent branch into the current branch",
    )
    parser.add_argument(
        "--use_patch",
        action="store_true",
        default=False,
        help="Apply patching instead of merging (not implemented yet)",
    )
    parser.add_argument(
        "--check_branch_name",
        action="store_true",
        default=True,
        help="Enforce branch naming convention (default: True)",
    )
    parser.add_argument(
        "--no_check_branch_name",
        action="store_false",
        dest="check_branch_name",
        help="Do not enforce branch naming convention",
    )
    parser.add_argument(
        "--method",
        type=str,
        default="auto",
        choices=["auto", "github_api", "linear_scan"],
        help="Method to use for generating the branch name (default: auto)",
    )
    parser.add_argument(
        "--parent_branch",
        type=str,
        default="",
        help=(
            "Explicit override for the parent branch to branch from "
            "(default: auto-detected from the remote tracking branch, "
            "falling back to 'master')"
        ),
    )
    hparser.add_verbosity_arg(parser)
    return parser


if __name__ == "__main__":
    _main(_parse())
