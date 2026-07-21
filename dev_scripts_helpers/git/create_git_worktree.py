#!/usr/bin/env python3

"""
Create a GitHub issue and corresponding git worktree.

Workflow:
1. Creates a GitHub issue with the provided title and body
2. Extracts the issue number from the created issue
3. Creates a git branch and worktree based on the issue
4. Prints instructions for using the worktree

Import as:

import dev_scripts_helpers.git.create_git_worktree as dscgicgw
"""

import argparse
import logging
import os
import re
import shlex
from typing import Tuple

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# #############################################################################
# Formatting helpers
# #############################################################################


def _format_title_for_branch(raw_title: str, issue_id: int) -> str:
    """
    Format a GitHub issue title as a git branch name.

    Removes special characters, replaces spaces with underscores, and adds
    the issue prefix.

    :param raw_title: Original GitHub issue title
    :param issue_id: GitHub issue number
    :return: Formatted branch name (e.g., HelpersTask1290_Issue_Title)
    """
    title = raw_title
    # Remove special characters.
    for char in ": + ( ) / ` *".split():
        title = title.replace(char, "")
    # Replace multiple spaces with one.
    title = re.sub(r"\s+", " ", title)
    title = title.replace(" ", "_")
    # Remove more special chars.
    for char in "- ' ` \"".split():
        title = title.replace(char, "_")
    # Add the prefix with issue number.
    # TODO(ai_gp): Generalize this to other repos.
    task_prefix = "HelpersTask"
    branch_name = f"{task_prefix}{issue_id}_{title}"
    return branch_name


def _parse_issue_number_from_url(url: str) -> int:
    """
    Extract issue number from a GitHub issue URL.

    :param url: Full GitHub issue URL (e.g., https://github.com/owner/repo/issues/1290)
    :return: Issue number as integer
    """
    # Extract the last path segment which is the issue number.
    parts = url.rstrip("/").split("/")
    issue_id = int(parts[-1])
    return issue_id


# #############################################################################
# Core workflow
# #############################################################################


def _create_github_issue(
    title: str,
    body_file: str,
    assignee: str,
) -> Tuple[int, str]:
    """
    Create a GitHub issue and return its number and URL.

    :param title: Issue title
    :param body_file: Path to file containing issue body
    :param assignee: GitHub username to assign the issue to
    :return: Tuple of (issue_number, issue_url)
    """
    # Verify body file exists.
    hdbg.dassert_file_exists(body_file, "Body file does not exist")
    # Build and execute gh issue create command.
    cmd = [
        "gh",
        "issue",
        "create",
        f"--title {shlex.quote(title)}",
        f"--body-file {shlex.quote(body_file)}",
        f"--assignee {shlex.quote(assignee)}",
    ]
    cmd_str = " ".join(cmd)
    _LOG.info("Creating GitHub issue: %s", cmd_str)
    _, output = hsystem.system_to_string(cmd_str)
    _LOG.debug("GitHub create output:\n%s", output)
    # Output is the URL directly
    issue_url = output.strip()
    _LOG.info("Created issue at: '%s'", issue_url)
    # Extract issue number from URL.
    issue_number = _parse_issue_number_from_url(issue_url)
    return issue_number, issue_url


# TODO(ai_gp): Inline
def _check_no_subrepos() -> None:
    """
    Assert that the repository does not have any submodules.

    Raises an error if subrepos are detected.
    """
    has_subrepos = hgit.has_submodules()
    hdbg.dassert(
        not has_subrepos,
        "Repository has submodules; worktree not supported yet",
    )


def _branch_exists(branch_name: str) -> bool:
    """
    Check if a git branch already exists.

    :param branch_name: Name of the branch to check
    :return: True if branch exists, False otherwise
    """
    cmd = f"git show-ref --verify refs/heads/{branch_name}"
    try:
        hsystem.system(cmd, suppress_output=True)
        return True
    except Exception:
        return False


def _commit_issue_files(branch_name: str) -> None:
    """
    Copy and commit issue files to the new branch.

    Copies `todo_janitor.current_issue.md` and `todo_janitor.template.md`
    from the repository root to the current branch and commits them.

    :param branch_name: Name of the branch to commit files to
    """
    # Check if issue files exist in repo root.
    repo_root = hgit.get_client_root(super_module=False)
    # current_issue -> todo_janitor.ISSUE.md
    # template -> todo_janitor.WORKFLOW.md
    current_issue_file = os.path.join(repo_root, "todo_janitor.current_issue.md")
    template_file = os.path.join(repo_root, "todo_janitor.template.md")
    hdbg.dassert_file_exists(current_issue_file)
    _LOG.info("Copying issue files to branch '%s'", branch_name)
    cmd = f"cp {shlex.quote(current_issue_file)} ISSUE.md"
    hsystem.system(cmd)
    hdbg.dassert_file_exists(template_file)
    cmd = f"cp {shlex.quote(template_file)} WORKFLOW.md"
    hsystem.system(cmd)
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


def _create_branch(branch_name: str, create_pr: bool = True) -> None:
    """
    Create a git branch from master using invoke git_branch_create.

    Delegates to `invoke git_branch_create` which handles:
    - Creating the branch from master
    - Pushing to upstream
    - Optionally creating a draft PR

    :param branch_name: Name for the new branch
    :param create_pr: Whether to create a draft PR (default: True)
    """
    # Skip if branch already exists (invoke will also check this).
    if _branch_exists(branch_name):
        _LOG.warning(
            "Branch '%s' already exists, skipping creation", branch_name
        )
        return
    # Use invoke git_branch_create to create branch and optionally PR.
    cmd = f"invoke git_branch_create --branch-name {shlex.quote(branch_name)}"
    if not create_pr:
        cmd += " --no-create-pr"
    _LOG.info("Creating branch via invoke: %s", cmd)
    hsystem.system(cmd, log_level=logging.INFO)
    # Commit issue files to the new branch.
    _commit_issue_files(branch_name)


def _create_worktree(branch_name: str, issue_id: int) -> str:
    """
    Create a git worktree for the given branch.

    :param branch_name: Name of the branch to create worktree for
    :param issue_id: GitHub issue number (for path naming)
    :return: Path to the created worktree
    """
    # Determine worktree path (parent directory of current repo).
    current_dir = os.getcwd()
    parent_dir = os.path.dirname(current_dir)
    repo_name = os.path.basename(current_dir)
    worktree_path = os.path.join(parent_dir, f"{repo_name}_worktree_{issue_id}")
    _LOG.info("Creating worktree at: '%s'", worktree_path)
    # Create worktree.
    cmd = f"git worktree add {worktree_path} {branch_name}"
    hsystem.system(cmd, log_level=logging.INFO)
    return worktree_path


def _print_usage_instructions(worktree_path: str, issue_id: int) -> None:
    """
    Print instructions on how to use the created worktree.

    :param worktree_path: Path to the created worktree
    :param issue_id: GitHub issue number
    """
    msg = f"""
    Worktree created successfully!

    To open tmux session:
    > cd {worktree_path}; dev_scripts_helpers/thin_client/tmux.py --index {issue_id}
    """
    msg = hprint.dedent(msg)
    msg = hprint.color_highlight(msg, "green")
    print(msg)


# #############################################################################
# Entry point
# #############################################################################


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main entry point for the script.
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level)
    _LOG.debug(
        "gh_issue_id=%s gh_issue_title=%s gh_issue_body_file=%s gh_assignee=%s "
        "create_worktree=%s create_pr=%s",
        args.gh_issue_id,
        args.gh_issue_title,
        args.gh_issue_body_file,
        args.gh_assignee,
        args.create_worktree,
        args.create_pr,
    )
    # Check optional instr_file parameter.
    if args.instr_file:
        hdbg.dassert_file_exists(
            args.instr_file,
            "Instruction file does not exist",
        )
        _LOG.info("Using instruction file: '%s'", args.instr_file)
    # Determine issue ID.
    if args.gh_issue_id:
        # Skip GitHub issue creation if ID is provided.
        issue_id = args.gh_issue_id
        _LOG.info("Using existing GitHub issue: %s", issue_id)
    else:
        # Create new GitHub issue.
        issue_id, _ = _create_github_issue(
            args.gh_issue_title,
            args.gh_issue_body_file,
            args.gh_assignee,
        )
    # Get issue title for branch naming.
    cmd = f"gh issue view {issue_id} --json title --jq .title"
    _, issue_title = hsystem.system_to_string(cmd)
    issue_title = issue_title.strip()
    _LOG.info("Issue title: '%s'", issue_title)
    # Format branch name.
    branch_name = _format_title_for_branch(issue_title, issue_id)
    _LOG.info("Branch name: '%s'", branch_name)
    # Assert no subrepos.
    _check_no_subrepos()
    # Create branch.
    _create_branch(branch_name, create_pr=args.create_pr)
    # Create worktree if requested.
    if args.create_worktree:
        worktree_path = _create_worktree(branch_name, issue_id)
        # TODO(ai_gp): cp the instr_file to the dir.
        # Print usage instructions.
        _print_usage_instructions(worktree_path, issue_id)


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
        "--gh_issue_id",
        type=int,
        default=0,
        help="Existing GitHub issue ID (skip creating new issue if provided)",
    )
    parser.add_argument(
        "--gh_issue_title",
        type=str,
        default="",
        help="Title for the GitHub issue to create",
    )
    parser.add_argument(
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
        "--instr_file",
        type=str,
        default="",
        help="Optional path to instruction file",
    )
    parser.add_argument(
        "--create_worktree",
        action="store_true",
        default=False,
        help="Create git worktree (default: False, only create branch)",
    )
    # TODO(ai_gp): Use one
    parser.add_argument(
        "--create_pr",
        action="store_true",
        default=True,
        help="Create a draft PR for the branch (default: True)",
    )
    parser.add_argument(
        "--no_create_pr",
        action="store_false",
        dest="create_pr",
        help="Skip creating a draft PR for the branch",
    )
    hparser.add_verbosity_arg(parser)
    return parser


if __name__ == "__main__":
    _main(_parse())
