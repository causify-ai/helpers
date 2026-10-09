#!/usr/bin/env python

"""
Merge `origin/master` into the current branch.

If local `master` has commits that `origin/master` does not have (e.g., empty
"Merge branch 'master' of ..." commits created by a `git pull` on `master`),
fetching `master` is rejected as "non-fast-forward". When all those commits are
empty (they change no file), local `master` is reset to `origin/master` and the
merge continues. Otherwise the script aborts without discarding any commit.

# Usage Example

- Merge master into the current branch, aborting if the merge is not a
  fast-forward or the client is not clean, then auto-commit and push:
> git_merge_master.py

- Only preview which files would conflict, without touching the working
  tree, the index, or history:
> git_merge_master.py --dry_run

- Merge without auto-committing/pushing:
> git_merge_master.py --no_auto_merge

- Also fetch master in the submodules (they are skipped by default):
> git_merge_master.py --submodules
"""

import argparse
import logging
import re
from typing import List

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# #############################################################################
# Fetch
# #############################################################################


def _get_tree_hash(ref: str) -> str:
    """
    Return the hash of the root tree of a commit.

    Two commits with the same tree hash have identical file contents,
    regardless of their history.

    :param ref: commit-ish to resolve (e.g., `master`)
    :return: hash of the root tree
    """
    _LOG.debug(hprint.to_str("ref"))
    cmd = f"git show --no-patch --format=%T {ref}"
    _, tree_hash = hsystem.system_to_string(cmd)
    tree_hash = tree_hash.strip()
    _LOG.debug("return=%s", tree_hash)
    return tree_hash


def _reset_master_if_local_commits_empty(*, dry_run: bool) -> None:
    """
    Reset local `master` to `origin/master` if its extra commits are empty.

    `git fetch origin master:master` is rejected as "non-fast-forward" when
    local `master` has commits that `origin/master` does not have. A common
    cause is a `git pull` run on `master`, which creates empty "Merge branch
    'master' of ..." commits that are never pushed.

    The local-only commits are empty when `master` has the same files as the
    merge-base of `master` and `origin/master`, i.e., together they introduce
    no change (even if some of them are merge commits). Then `master` can
    follow `origin/master` without losing any content. Otherwise abort, since
    the commits hold real work.

    :param dry_run: if True, only report that `master` would be reset
    """
    _LOG.debug(hprint.to_str("dry_run"))
    # Update `origin/master` alone, since the fetch into `master` was rejected.
    hsystem.system("git fetch origin master", suppress_output=False)
    # Find the commits that block the fetch.
    cmd = "git rev-list --oneline --reverse origin/master..master"
    _, txt = hsystem.system_to_string(cmd)
    local_commits = txt.splitlines()
    hdbg.dassert_lt(
        0,
        len(local_commits),
        "Fetching 'master' failed, but 'master' has no commits missing from "
        "'origin/master': see the git error above",
    )
    # Check that the local-only commits do not change any file, i.e., `master`
    # has the same content as the point where it forked from `origin/master`.
    _, merge_base = hsystem.system_to_string(
        "git merge-base master origin/master"
    )
    master_tree = _get_tree_hash("master")
    merge_base_tree = _get_tree_hash(merge_base.strip())
    commits_str = "\n".join(local_commits)
    hdbg.dassert_eq(
        master_tree,
        merge_base_tree,
        "Local 'master' has %d commit(s) missing from 'origin/master' that "
        "change files, so they can't be dropped:\n%s\nPush them or save them "
        "on a branch (e.g., 'git branch backup_master master'), then reset "
        "'master' manually",
        len(local_commits),
        commits_str,
    )
    # Drop the empty commits by making `master` point to `origin/master`. The
    # dropped commits stay reachable through `git reflog`.
    if dry_run:
        _LOG.warning(
            "[DRY_RUN] Would reset local 'master' to 'origin/master', dropping "
            "%d empty commit(s):\n%s",
            len(local_commits),
            commits_str,
        )
    else:
        _LOG.warning(
            "Resetting local 'master' to 'origin/master', dropping %d empty "
            "commit(s):\n%s",
            len(local_commits),
            commits_str,
        )
        hsystem.system("git branch -f master origin/master")


def _fetch_master(submodules: bool, *, dry_run: bool) -> None:
    """
    Fetch master branch from remote without switching to it.

    Updates the local master branch to track the latest remote master
    without affecting the current branch.

    If local master has commits that the remote does not have, the fetch is
    rejected. When all those commits are empty (see
    `_reset_master_if_local_commits_empty()`), local master is reset to the
    remote master so that the merge can continue.

    :param submodules: also fetch master in all submodules (e.g.,
        `helpers_root`). It is off by default to avoid errors like "refusing
        to fetch into branch ... checked out" when a submodule has its
        master branch checked out in its own git dir (e.g., when the
        submodule is used as a standalone repo)
    :param dry_run: if True, do not reset local master when it has empty
        local-only commits, only report it
    """
    # Fetch remote master directly into local master ref (colon syntax).
    cmd = "git fetch origin master:master"
    rc = hsystem.system(cmd, abort_on_error=False, suppress_output=False)
    if rc != 0:
        # The fetch is rejected when local master has commits missing on the
        # remote: try to fix it if they are empty, otherwise abort.
        _LOG.warning(
            "'%s' failed with rc='%s': checking if local 'master' only has "
            "empty commits",
            cmd,
            rc,
        )
        _reset_master_if_local_commits_empty(dry_run=dry_run)
    if submodules:
        # Run the same command on all submodules.
        cmd = "git submodule foreach 'git fetch origin master:master'"
        hsystem.system(cmd, suppress_output=False)


def _add_all_untracked_files(*, exclude_tmp: bool = False) -> None:
    """
    Add all untracked files to Git.

    :param exclude_tmp: skip `tmp.*` files (e.g.,
        `tmp.precommit_output.txt`) generated by the pre-commit hook
    """
    cmd = "git ls-files -o --exclude-standard -z"
    if exclude_tmp:
        cmd += " | grep -zv '^tmp\\.'"
    cmd += " | xargs -0 git add"
    hsystem.system(cmd, suppress_output=False)


# #############################################################################
# Preview
# #############################################################################


def _print_file_list(title: str, files: List[str], *, max_files: int = 50) -> None:
    """
    Print a titled, bulleted list of file paths, truncating if very long.

    :param title: header printed before the list (with the count
        appended)
    :param files: file paths to list
    :param max_files: max number of files to print before eliding the
        rest
    """
    print(f"\n{title} ({len(files)}):")
    if not files:
        print("  (none)")
        return
    for f in files[:max_files]:
        print(f"  - {f}")
    if len(files) > max_files:
        print(f"  ... and {len(files) - max_files} more")


def _preview_git_merge_master(current_branch: str, target_branch: str) -> bool:
    """
    Report, without merging, which files would conflict if `target_branch`
    were merged into `current_branch`.

    This runs an in-memory 3-way merge via `git merge-tree --write-tree`:
    nothing is written to the working tree, the index, or history, and no
    branch is checked out or modified.

    :param current_branch: branch that would receive the merge (e.g.,
        the branch currently checked out)
    :param target_branch: branch to be merged in (e.g., `master`)
    :return: `True` if the merge would be conflict-free, `False` if some
        files would conflict
    """
    # Determine which files each side touched since the merge-base: files
    # touched on only one side always merge trivially, so they don't need a
    # real 3-way content merge.
    _, merge_base = hsystem.system_to_string(
        f"git merge-base {current_branch} {target_branch}"
    )
    merge_base = merge_base.strip()
    _, current_txt = hsystem.system_to_string(
        f"git diff --name-only {merge_base} {current_branch}"
    )
    _, target_txt = hsystem.system_to_string(
        f"git diff --name-only {merge_base} {target_branch}"
    )
    current_files = set(current_txt.splitlines())
    target_files = set(target_txt.splitlines())
    both_sides_files = current_files & target_files
    # Run the in-memory 3-way merge. `git merge-tree` exits with a non-zero
    # code when there are conflicts, so we don't abort on error.
    cmd = f"git merge-tree --write-tree {current_branch} {target_branch}"
    _, txt = hsystem.system_to_string(cmd, abort_on_error=False)
    conflict_files = sorted(
        set(
            re.findall(
                r"^CONFLICT \([^)]*\): Merge conflict in (.*)$",
                txt,
                re.MULTILINE,
            )
        )
    )
    auto_merged_files = set(
        re.findall(r"^Auto-merging (.*)$", txt, re.MULTILINE)
    )
    # Changed on both sides, but the 3-way content merge succeeds.
    clean_merge_files = sorted(auto_merged_files - set(conflict_files))
    # Changed on both sides with no message at all from `git merge-tree`
    # (e.g., both sides made the identical change): also conflict-free.
    other_clean_files = sorted(
        both_sides_files - auto_merged_files - set(conflict_files)
    )
    trivial_files = sorted(
        (current_files | target_files) - both_sides_files
    )
    print(
        "\n" + hprint.frame(f"Preview: merge `{target_branch}` into `{current_branch}`")
    )
    print(
        "(dry run via `git merge-tree`: no files, index, or history touched)"
    )
    _print_file_list("Conflicting files", conflict_files)
    _print_file_list(
        "Files changed on both branches, merge cleanly",
        clean_merge_files + other_clean_files,
    )
    _print_file_list(
        "Files changed on only one branch (always merge trivially)",
        trivial_files,
    )
    is_clean = not conflict_files
    if is_clean:
        print("\nNo conflicts: `invoke git_merge_master` can merge cleanly")
    else:
        print(
            f"\n{len(conflict_files)} file(s) would conflict; resolve "
            "manually or plan for conflict resolution before running "
            "`invoke git_merge_master`"
        )
    return is_clean


# #############################################################################
# Merge
# #############################################################################


def _git_merge_master(
    *,
    abort_if_not_ff: bool = False,
    abort_if_not_clean: bool = True,
    skip_fetch: bool = False,
    auto_merge: bool = True,
    submodules: bool = False,
    dry_run: bool = False,
) -> None:
    """
    Merge `origin/master` into the current branch.

    :param abort_if_not_ff: abort if fast-forward is not possible
    :param abort_if_not_clean: abort if the client is not clean
    :param skip_fetch: skip fetching master
    :param auto_merge: automatically commit and push if merge is
        successful
    :param submodules: also fetch master in submodules (see
        `_fetch_master`)
    :param dry_run: instead of merging, run a dry-run 3-way merge and
        report which files would conflict, which would merge cleanly,
        and which change on only one side. No merge is attempted and
        nothing is written to the working tree, the index, or history
    """
    if dry_run:
        # Fetch so the preview reflects the latest remote master, but never
        # touch the working tree, the index, the current branch, or history.
        if not skip_fetch:
            _fetch_master(submodules, dry_run=dry_run)
        current_branch = hgit.get_branch_name()
        _preview_git_merge_master(current_branch, "master")
        return
    # Verify working directory is clean before merging to avoid losing changes.
    hgit.is_client_clean(dir_name=".", abort_if_not_clean=abort_if_not_clean)
    # Fetch latest master from remote to ensure we merge the latest changes.
    if not skip_fetch:
        _fetch_master(submodules, dry_run=dry_run)
    # Perform merge, optionally restricting to fast-forward only to maintain linear history.
    cmd = "git merge master"
    if abort_if_not_ff:
        cmd += " --ff-only"
    hsystem.system(cmd, suppress_output=False)
    # Commit and push automatically if merge succeeded and user requested it.
    if auto_merge:
        # Add any remaining untracked files, skipping tmp files generated by
        # this script itself (e.g., `tmp.precommit_output.txt` from the
        # pre-commit hook).
        _add_all_untracked_files(exclude_tmp=True)
        _LOG.info("Auto-merge enabled: committing and pushing changes")
        cmd = 'git commit -am "Merge master" && git push'
        hsystem.system(cmd, suppress_output=False)


# #############################################################################
# CLI
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    parser.add_argument(
        "--abort_if_not_ff",
        action="store_true",
        help="Abort if fast-forward is not possible",
    )
    parser.add_argument(
        "--no_abort_if_not_clean",
        action="store_true",
        help="Do not abort if the Git client is not clean",
    )
    parser.add_argument(
        "--skip_fetch",
        action="store_true",
        help="Skip fetching master",
    )
    parser.add_argument(
        "--no_auto_merge",
        action="store_true",
        help="Do not automatically commit and push after a successful merge",
    )
    hparser.add_bool_arg(
        parser,
        "submodules",
        default_value=False,
        help_="Also fetch master in submodules",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Instead of merging, report which files would conflict without "
        "touching the working tree, the index, or history",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    _git_merge_master(
        abort_if_not_ff=args.abort_if_not_ff,
        abort_if_not_clean=not args.no_abort_if_not_clean,
        skip_fetch=args.skip_fetch,
        auto_merge=not args.no_auto_merge,
        submodules=args.submodules,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    _main(_parse())
