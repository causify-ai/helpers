#!/usr/bin/env python3

"""
Create a GitHub issue and corresponding git worktree.

Workflow:
1. Creates a GitHub issue with the provided title and body (or uses existing
   issue ID)
2. Creates a git branch and worktree based on the issue ID
3. Commits workflow template files to the branch
4. Prints instructions for using the worktree

Uses invoke tasks for issue and branch creation:
- `invoke gh_issue_create` to create issues
- `invoke git_branch_create --issue-id` to create branches

Import as:

import dev_scripts_helpers.git.git_create_issue_and_branch as dsggiab
"""

import argparse
import logging
import os
import re
import shlex

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

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
        # TODO(ai_gp): Use hio.from_file.
        with open(body_file, "r") as f:
            body = f.read()
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
    issue_id: int, original_branch: str, *, create_pr: bool = True
) -> str:
    """
    Create a git branch using invoke git_branch_create task.

    :param issue_id: GitHub issue ID
    :param original_branch: Name of the original branch to extract files from
    :param create_pr: Whether to create a draft PR (default: True)
    :return: Created branch name
    """
    # Build invoke command.
    cmd = f"invoke git_branch_create --issue-id {issue_id}"
    if not create_pr:
        cmd += " --create-pr=False"
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
    # Capture original branch to restore on failure.
    original_branch = hgit.get_branch_name()
    try:
        # Load issue body from file or use provided text.
        gh_issue_body = _get_issue_body(
            args.gh_issue_body, args.gh_issue_body_file
        )
        _LOG.debug(
            "gh_issue_id=%s gh_issue_title=%s gh_issue_body=%s gh_issue_body_file=%s "
            "gh_assignee=%s create_worktree=%s create_pr=%s",
            args.gh_issue_id,
            args.gh_issue_title,
            gh_issue_body,
            args.gh_issue_body_file,
            args.gh_assignee,
            args.create_worktree,
            args.create_pr,
        )
        # Assert that the repository does not have any submodules, since
        # worktrees are not supported with subrepos yet.
        hdbg.dassert(
            not hgit.has_submodules(),
            "Repository has submodules; worktree not supported yet",
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
            hdbg.dassert_is_not(
                match,
                None,
                "Could not extract issue ID from output: %s",
                output,
            )
            issue_id = int(match.group(1))  # type: ignore[union-attr]
            _LOG.info("Created issue #%s", issue_id)
        # Create branch and PR via invoke.
        branch_name = _create_branch_and_pr(
            issue_id, original_branch, create_pr=args.create_pr
        )
        _LOG.info("Branch name: '%s'", branch_name)
        # Create worktree, if requested.
        if args.create_worktree:
            worktree_path = _create_worktree(branch_name, issue_id)
            # Print usage instructions.
            _print_usage_instructions(worktree_path, issue_id)
    finally:
        # Return to original branch if we switched away.
        current_branch = hgit.get_branch_name()
        if current_branch != original_branch:
            _LOG.info("Returning to original branch: '%s'", original_branch)
            cmd = f"git checkout {shlex.quote(original_branch)}"
            hsystem.system(cmd)


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments.

    :return: ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
    hparser.add_verbosity_arg(parser)
    return parser


if __name__ == "__main__":
    _main(_parse())
