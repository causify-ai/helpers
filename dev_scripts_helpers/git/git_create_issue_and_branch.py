#!/usr/bin/env python3

"""
Create a GitHub issue and corresponding git worktree for a repo.

Workflow:
1. Creates a GitHub issue with the provided title and body (or uses existing
   issue ID) in one repo
2. Creates a git branch (and worktree) based on the issue ID, symmetrically
   in the outer repo and, if present, every submodule (e.g., `helpers_root`)
   unless `--no_submodules` is passed
3. Commits workflow template files to the branch
4. Prints instructions for using the worktree

The GH issue is always created/read against the outer repo's tracker: a
submodule (e.g., `helpers_root`) is a shared library reused by many parent
projects and has its own, disjoint issue numbering. The branch name is computed
once from the outer repo's issue and reused verbatim in every submodule.

Uses invoke tasks for issue and branch creation:
- `invoke gh_issue_create` to create issues
- `invoke git_branch_create --issue-id` to create the outer repo's branch
- `invoke git_branch_create --branch-name` to create the same branch, by
  name, in every submodule

Import as:

import dev_scripts_helpers.git.git_create_issue_and_branch as dsggiab
"""

import argparse
import logging
import os
import re
import shlex
from typing import List, Optional

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.lib_tasks.lib_tasks_gh as hltltagh

_LOG = logging.getLogger(__name__)

# #############################################################################
# Repo targets
# #############################################################################


# TODO(gp): This is general enough that it could go in hgit.py
def _get_repo_targets(no_submodules: bool) -> List[str]:
    """
    Return the repo directories to operate on symmetrically.

    The outer repo (".") always comes first, so callers can rely on
    `repo_targets[0]` being the outer repo and `repo_targets[1:]` being the
    submodules.

    :param no_submodules: if True, disable symmetric submodule handling and
        always return the outer repo only, even if submodules are present
    :return: `["."]`, or `["."] + <submodule paths>` when submodules are
        present and `no_submodules` is False
    """
    repo_targets = ["."]
    if not no_submodules and hgit.has_submodules():
        repo_targets.extend(hgit.get_submodule_paths())
    _LOG.debug("repo_targets=%s", repo_targets)
    return repo_targets


def _dassert_all_targets_clean(repo_targets: List[str]) -> None:
    """
    Assert that every repo target is clean, before mutating any of them.

    :param repo_targets: repo directories to check
    """
    dirty_targets = [
        target
        for target in repo_targets
        if not hgit.is_client_clean(dir_name=target, abort_if_not_clean=False)
    ]
    hdbg.dassert(
        not dirty_targets,
        "The following repo(s) are not clean: %s",
        ", ".join(dirty_targets),
    )


def _dassert_all_targets_on_master(
    repo_targets: List[str], original_branch: str
) -> None:
    """
    Assert that every repo target is on `master`, before creating a branch in
    any of them.

    Reuses `original_branch` (already captured by the caller) for the outer
    repo instead of issuing a redundant `hgit.get_branch_name()` call.

    :param repo_targets: repo directories to check (outer repo first)
    :param original_branch: current branch name of the outer repo
    """
    non_master_targets = []
    for target in repo_targets:
        branch = (
            original_branch
            if target == "."
            else hgit.get_branch_name(dir_name=target)
        )
        if branch != "master":
            non_master_targets.append(f"{target} (on '{branch}')")
    hdbg.dassert(
        not non_master_targets,
        "The following repo(s) are not on 'master': %s",
        ", ".join(non_master_targets),
    )


# #############################################################################
# Core workflow
# #############################################################################


def _get_issue_body(body_text: str, body_file: str) -> str:
    """
    Get issue body from either text or file.

    :param body_text: Body text provided as string
    :param body_file: Path to file containing body text
    :return: Issue body content
    """
    if body_file:
        hdbg.dassert_file_exists(body_file, "Issue body file does not exist")
        body = hio.from_file(body_file)
        _LOG.info("Loaded issue body from file '%s'", body_file)
        return body
    return body_text


def _commit_issue_files(branch_name: str, original_branch: str) -> None:
    """
    Copy and commit issue files to the new branch.

    Extracts `todo_janitor.current_issue.md` and `todo_janitor.template.md`
    from the original branch and commits them to the new branch.

    :param branch_name: Name of the branch to commit files to
    :param original_branch: Name of the original branch to extract files from
    """
    _LOG.info("Extracting issue files from branch '%s'", original_branch)
    # Extract files from original branch using git show.
    cmd = f"git show {shlex.quote(original_branch)}:todo_janitor.current_issue.md > ISSUE.md"
    hsystem.system(cmd)
    cmd = f"git show {shlex.quote(original_branch)}:todo_janitor.template.md > WORKFLOW.md"
    hsystem.system(cmd)
    _LOG.info("Copying extracted files to branch '%s'", branch_name)
    # Stage and commit the files.
    cmd = "git add ISSUE.md WORKFLOW.md"
    hsystem.system(cmd)
    cmd = 'git commit -m "Add issue description and workflow template"'
    rc = hsystem.system(cmd, abort_on_error=False)
    if rc != 0:
        _LOG.warning("Failed to commit issue files (may already exist)")
    # Push the commit to remote.
    cmd = "git push"
    hsystem.system(cmd)


def _create_branch_and_pr(
    issue_id: int,
    original_branch: str,
    *,
    create_pr: bool = True,
    gh_issue_id_provided: bool = False,
    no_abort_if_not_master: bool = False,
) -> str:
    """
    Create a git branch using invoke git_branch_create task.

    :param issue_id: GitHub issue ID
    :param original_branch: Name of the original branch to extract files from
    :param create_pr: Whether to create a draft PR (default: True)
    :param gh_issue_id_provided: True if issue ID was provided (not newly created)
    :param no_abort_if_not_master: if True, allow branching from a non-'master'
        branch instead of aborting (the underlying invoke task switches to
        'master' first)
    :return: Created branch name
    """
    # Get the branch name from GitHub issue title.
    if gh_issue_id_provided:
        title, _ = hltltagh._get_gh_issue_title(issue_id, "current")
        branch_name = title
        _LOG.info(
            "Issue %d corresponds to branch name '%s'", issue_id, branch_name
        )
        # If issue ID was provided and branch already exists, just checkout the existing branch.
        if hgit.does_branch_exist(branch_name, mode="all"):
            _LOG.info("Branch '%s' already exists, checking it out", branch_name)
            cmd = f"git checkout {shlex.quote(branch_name)}"
            hsystem.system(cmd, log_level=logging.INFO)
            return branch_name
    # Build invoke command to create new branch.
    cmd = f"invoke git_branch_create --issue-id {issue_id}"
    if not create_pr:
        cmd += " --no-create-pr"
    if no_abort_if_not_master:
        # Let git_branch_create switch to 'master' itself instead of
        # aborting when the current branch isn't 'master'.
        cmd += " --no-abort-if-not-master"
    _LOG.info("Creating branch via invoke: %s", cmd)
    hsystem.system(cmd, log_level=logging.INFO)
    # Get the current branch name (invoke git_branch_create creates and checks out the branch).
    branch_name = hgit.get_branch_name()
    _LOG.info("Branch created: %s", branch_name)
    # Commit issue files to the new branch.
    if False:
        # TODO(gp): Consider if it's useful to inject some files passed from
        # command line to the branch (e.g., instructions).
        _commit_issue_files(branch_name, original_branch)
    return branch_name


def _create_branch_in_submodule(
    submodule_path: str,
    branch_name: str,
    *,
    create_pr: bool = True,
    no_abort_if_not_master: bool = False,
) -> None:
    """
    Create (or check out) `branch_name` inside a submodule.

    There is only one GH issue, in the outer repo's tracker, so `branch_name`
    is reused verbatim (as a literal `--branch-name`, not `--issue-id`):
    re-resolving an issue ID from inside the submodule would look it up
    against the submodule's own, disjoint GitHub repo.

    :param submodule_path: path to the submodule (e.g., "helpers_root")
    :param branch_name: literal branch name, already computed from the outer
        repo's GH issue
    :param create_pr: whether to create a draft PR (default: True)
    :param no_abort_if_not_master: if True, allow branching from a non-'master'
        branch instead of aborting (the underlying invoke task switches to
        'master' first)
    """
    if hgit.does_branch_exist(branch_name, mode="all", dir_name=submodule_path):
        _LOG.info(
            "Branch '%s' already exists in '%s', checking it out",
            branch_name,
            submodule_path,
        )
        cmd = f"cd {submodule_path} && git checkout {shlex.quote(branch_name)}"
        hsystem.system(cmd, log_level=logging.INFO)
        return
    cmd = (
        f"cd {submodule_path} && invoke git_branch_create "
        f"--branch-name {shlex.quote(branch_name)}"
    )
    if not create_pr:
        cmd += " --no-create-pr"
    if no_abort_if_not_master:
        # Let git_branch_create switch to 'master' itself instead of
        # aborting when the current branch isn't 'master'.
        cmd += " --no-abort-if-not-master"
    _LOG.info("Creating branch in '%s' via invoke: %s", submodule_path, cmd)
    hsystem.system(cmd, log_level=logging.INFO)


def _create_worktree(
    branch_name: str,
    issue_id: int,
    original_branch: str,
    submodule_paths: Optional[List[str]] = None,
) -> str:
    """
    Create a git worktree for the given branch.

    When `submodule_paths` is passed, the submodules are initialized inside
    the new worktree and checked out on `branch_name` too (matching the outer
    repo), instead of being left uninitialized / on a detached HEAD.

    :param branch_name: Name of the branch to create worktree for
    :param issue_id: GitHub issue number (for path naming)
    :param original_branch: Original branch to checkout before creating worktree
    :param submodule_paths: paths of submodules (relative to the outer repo)
        to initialize and check out on `branch_name` inside the worktree
    :return: Path to the created worktree
    """
    # Checkout original branch first to free up the new branch.
    _LOG.info(
        "Checking out original branch '%s' before creating worktree",
        original_branch,
    )
    cmd = f"git checkout {shlex.quote(original_branch)}"
    hsystem.system(cmd, log_level=logging.INFO)
    # Determine worktree path (parent directory of current repo).
    current_dir = os.getcwd()
    parent_dir = os.path.dirname(current_dir)
    repo_name = os.path.basename(current_dir)
    worktree_path = os.path.join(parent_dir, f"{repo_name}_worktree_{issue_id}")
    _LOG.info("Creating worktree at: '%s'", worktree_path)
    # Create worktree.
    cmd = f"git worktree add {worktree_path} {branch_name}"
    hsystem.system(cmd, log_level=logging.INFO)
    if submodule_paths:
        # Initialize the submodules inside the new worktree and land each of
        # them on `branch_name` (not a detached HEAD), matching the outer repo.
        cmd = f"git -C {worktree_path} submodule update --init --recursive"
        hsystem.system(cmd, log_level=logging.INFO)
        for submodule_path in submodule_paths:
            submodule_worktree_path = os.path.join(worktree_path, submodule_path)
            cmd = (
                f"git -C {submodule_worktree_path} checkout "
                f"{shlex.quote(branch_name)}"
            )
            hsystem.system(cmd, log_level=logging.INFO)
    return worktree_path


def _print_usage_instructions(
    worktree_path: str,
    issue_id: int,
    branch_name: str,
    repo_targets: List[str],
) -> None:
    """
    Print instructions on how to use the created worktree.

    Also reports, for every repo target, whether the branch was created there
    and whether that repo is currently clean (e.g., after the "Draft PR" empty
    commit / push).

    :param worktree_path: Path to the created worktree
    :param issue_id: GitHub issue number
    :param branch_name: name of the branch created in every repo target
    :param repo_targets: repo directories the branch was created in (outer
        repo first)
    """
    # Build the per-repo summary (branch name is identical everywhere).
    summary_lines = []
    for target in repo_targets:
        is_clean = hgit.is_client_clean(
            dir_name=target, abort_if_not_clean=False
        )
        status = "clean" if is_clean else "dirty"
        repo_label = "outer repo" if target == "." else f"submodule '{target}'"
        summary_lines.append(
            f"    - {repo_label}: branch '{branch_name}' ({status})"
        )
    summary = "\n".join(summary_lines)
    # Extract worktree suffix (e.g., "1_worktree_1325" from "helpers1_worktree_1325").
    worktree_dir = os.path.basename(worktree_path)
    # TODO(ai_gp2): We should get the basename of the repo from the config.
    # Strip "helpers" prefix from repo name to get suffix.
    worktree_suffix = (
        worktree_dir.replace("helpers", "", 1)
        if worktree_dir.startswith("helpers")
        else worktree_dir
    )
    msg = f"""
    Worktree created successfully for issue #{issue_id}!

    {summary}

    To open tmux session:
    > cd {worktree_path}; dev_scripts_helpers/thin_client/tmux.py --index {worktree_suffix}
    """
    msg = hprint.dedent(msg)
    msg = hprint.color_highlight(msg, "green")
    print(msg)


# #############################################################################
# CLI
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments.

    :return: ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    # Issue source: mutually exclusive (create new or use existing).
    issue_group = parser.add_mutually_exclusive_group()
    issue_group.add_argument(
        "--gh_issue_title",
        type=str,
        default="",
        help="Title for the GitHub issue to create",
    )
    issue_group.add_argument(
        "--gh_issue_id",
        type=int,
        default=0,
        help="Existing GitHub issue ID (skip creating new issue if provided)",
    )
    # Body source: mutually exclusive (text or file).
    body_group = parser.add_mutually_exclusive_group()
    body_group.add_argument(
        "--gh_issue_body",
        type=str,
        default="",
        help="Body text for the GitHub issue (plain text, not a file path)",
    )
    body_group.add_argument(
        "--gh_issue_body_file",
        type=str,
        default="",
        help="Path to file containing GitHub issue body",
    )
    parser.add_argument(
        "--gh_assignee",
        type=str,
        default="@me",
        help="GitHub user to assign the issue to",
    )
    parser.add_argument(
        "--create_worktree",
        action="store_true",
        default=False,
        help="Create git worktree (default: False, only create branch)",
    )
    parser.add_argument(
        "--no_create_pr",
        action="store_false",
        dest="create_pr",
        default=True,
        help="Skip creating a draft PR for the branch (default: create a draft PR)",
    )
    parser.add_argument(
        "--no_submodules",
        action="store_true",
        default=False,
        help=(
            "Disable symmetric submodule handling and only operate on the "
            "outer repo, even if submodules are present"
        ),
    )
    parser.add_argument(
        "--no_abort_if_not_master",
        action="store_true",
        default=False,
        help="Skip checking that every repo target is on 'master'",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main_workflow(
    args: argparse.Namespace, original_branch: str, repo_targets: List[str]
) -> None:
    """
    Main workflow implementation.

    :param args: Parsed command-line arguments
    :param original_branch: Original git branch name for restoration
    :param repo_targets: repo directories to operate on symmetrically (outer
        repo first, then every submodule, unless `--no_submodules` was passed)
    """
    # Load issue body from file or use provided text.
    gh_issue_body = _get_issue_body(args.gh_issue_body, args.gh_issue_body_file)
    _LOG.debug(
        "gh_issue_id=%s gh_issue_title=%s gh_issue_body=%s gh_issue_body_file=%s "
        "gh_assignee=%s create_worktree=%s create_pr=%s repo_targets=%s",
        args.gh_issue_id,
        args.gh_issue_title,
        gh_issue_body,
        args.gh_issue_body_file,
        args.gh_assignee,
        args.create_worktree,
        args.create_pr,
        repo_targets,
    )
    # Determine issue ID.
    if args.gh_issue_id:
        # Skip GitHub issue creation if ID is provided.
        issue_id = args.gh_issue_id
        _LOG.info("Using existing GitHub issue: %s", issue_id)
    else:
        # Create new GitHub issue via invoke.
        hdbg.dassert(
            args.gh_issue_title,
            "Issue title is required when creating a new issue",
        )
        cmd = "invoke gh_issue_create"
        cmd += f" --title {shlex.quote(args.gh_issue_title)}"
        if gh_issue_body:
            cmd += f" --body {shlex.quote(gh_issue_body)}"
        if args.gh_assignee:
            cmd += f" --assignees {shlex.quote(args.gh_assignee)}"
        _LOG.info("Creating GitHub issue via invoke: %s", cmd)
        _, output = hsystem.system_to_string(cmd)
        _LOG.debug("Invoke output:\n%s", output)
        # Parse issue ID from output.
        match = re.search(r"Created issue #(\d+)", output)
        match = hdbg.dassert_re_match(
            match, "Could not extract issue ID from output: %s", output
        )
        issue_id = int(match.group(1))
        _LOG.info("Created issue #%s", issue_id)
    # Create branch and PR via invoke, in the outer repo.
    branch_name = _create_branch_and_pr(
        issue_id,
        original_branch,
        create_pr=args.create_pr,
        gh_issue_id_provided=bool(args.gh_issue_id),
        no_abort_if_not_master=args.no_abort_if_not_master,
    )
    _LOG.info("Branch name: '%s'", branch_name)
    # Symmetrically create the same branch (by name) in every submodule.
    submodule_targets = repo_targets[1:]
    for submodule_path in submodule_targets:
        _create_branch_in_submodule(
            submodule_path,
            branch_name,
            create_pr=args.create_pr,
            no_abort_if_not_master=args.no_abort_if_not_master,
        )
    # Create worktree, if requested.
    if args.create_worktree:
        worktree_path = _create_worktree(
            branch_name, issue_id, original_branch, submodule_targets
        )
        # Print usage instructions.
        _print_usage_instructions(
            worktree_path, issue_id, branch_name, repo_targets
        )


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main entry point for the script.
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level)
    # Determine which repos to operate on symmetrically (outer + submodules,
    # unless `--no_submodules` was passed).
    repo_targets = _get_repo_targets(args.no_submodules)
    # Assert that every repo target is clean (no uncommitted changes), before
    # mutating any of them.
    _dassert_all_targets_clean(repo_targets)
    # Capture original branch to restore on failure.
    original_branch = hgit.get_branch_name()
    if len(repo_targets) > 1 and not args.no_abort_if_not_master:
        # Assert that every repo target is on 'master' before creating a
        # branch in any of them, to avoid a half-done state across repos.
        _dassert_all_targets_on_master(repo_targets, original_branch)
    try:
        _main_workflow(args, original_branch, repo_targets)
    finally:
        # Return to original branch if we switched away.
        current_branch = hgit.get_branch_name()
        if current_branch != original_branch:
            _LOG.info("Returning to original branch: '%s'", original_branch)
            cmd = f"git checkout {shlex.quote(original_branch)}"
            hsystem.system(cmd)


if __name__ == "__main__":
    _main(_parse())
