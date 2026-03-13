# Summary

Git utility commands and scripts for development workflows. Provides shortcuts
for common git operations, conflict resolution, submodule management, and branch
analysis.

# Git Commands Reference

## Status and Log Commands

| Command | Description |
| :------- | :------- |
| `gs` | Print git status of client and submodules |
| `gss` | Print git status in short format with submodule info |
| `gll` | List commits in fancy format with author, timestamp, and branch info |
| `gllmy` | List only your own commits in fancy format |
| `git_branch.sh` | Show information about branches with author and date |
| `git_hash_head.sh` | Show the commit hash that HEAD is at |
| `git_branch_name.sh` | Print name of the current branch |

## Diff Commands

| Command | Description |
| :------- | :------- |
| `gd` | Run git difftool on specified files |
| `gdc` | Run git difftool on cached/staged changes |
| `gdpy` | Git diff all Python files in the repository |
| `gd_master.sh` | Diff current branch against master (shows commits in both directions) |
| `gd_names.sh` | Shortcut for `git diff --name-only master...` |
| `gd_notebook.py` | Diff a notebook against HEAD, removing notebook artifacts for clarity |

## Checkout and Branch Commands

| Command | Description |
| :------- | :------- |
| `gco` | Checkout a branch and pull with submodules |
| `git_branch_point.sh` | Show information about the branch point (common ancestor) |

## Push and Pull Commands

| Command | Description |
| :------- | :------- |
| `gp` | Sync client with pull (autostash + rebase) and push local commits |
| `gpa` | Pull with autostash (without pushing) |
| `gup.py` | Update git client by stashing, rebasing, and reapplying changes |

## Conflict Resolution Commands

| Command | Description |
| :------- | :------- |
| `gcours` | Accept our version of conflicted files (checkout --ours) |
| `gctheirs` | Accept their version of conflicted files (checkout --theirs) |
| `git_conflict_files.sh` | Find files with git conflicts |
| `git_conflict_show.sh` | Generate base, ours, and theirs files for conflict visualization |

## Rebase Commands

| Command | Description |
| :------- | :------- |
| `grc` | Continue a rebase operation |
| `grs` | Skip the current commit during a rebase |

## Stash Commands

| Command | Description |
| :------- | :------- |
| `gsl` | List stashed changes |
| `gss` | Print git status in short format (note: same abbreviation as above) |
| `gsp.py` | Stash changes in git client (creates backup via gsp.py then cleans) |
| `gcl` | Clean the client making a backup (stashes and cleans untracked files) |

## Utility Commands

| Command | Description |
| :------- | :------- |
| `git_root.sh` | Report the path of the git repository root |
| `git_files.sh` | Report git cached and modified files |
| `git_hash_head.sh` | Show the short commit hash that HEAD is at |
| `git_graph.sh` | Plot a graphical view of branches (modes 1, 2, 3 for different detail levels) |
| `git_backup.sh` | Create a tarball backup of all modified/added files |
| `git_revert.sh` | Force a revert of files to HEAD |
| `git_clone.sh` | Clone repo and configure git hooks |
| `git_previous_commit_files.sh` | Get files from previous commit |
| `git_untracked_files.sh` | Report untracked files |
| `git_shrink_repo.sh` | Remove large files from repository history |

## Submodule Commands

| Command | Description |
| :------- | :------- |
| `git_submodules.py` | Implement git workflows on multiple repos (pull, commit, status, etc.) |
| `git_submodules_are_updated.sh` | Check if all submodules are up to date |
| `git_submodules_clean.sh` | Clean all submodules |
| `git_submodules_commit.sh` | Commit changes in all submodules |
| `git_submodules_pull.sh` | Pull updates for all submodules |
| `git_submodules_roll_fwd.sh` | Roll forward submodule references |
| `git_submodules_stash.sh` | Stash changes in all submodules |

## Git Hooks Commands

| Command | Description |
| :------- | :------- |
| `install_hooks.py` | Install git hooks in repository |
| `pre-commit.py` | Pre-commit hook implementation |
| `pre-commit-dry-run.py` | Dry-run version of pre-commit hook |
| `commit-msg.py` | Commit message validation hook |
| `gitleaks.py` | Secret detection hook (prevents committing secrets) |

## GitHub Commands

| Command | Description |
| :------- | :------- |
| `gh_watch.sh` | Watch GitHub workflow status with auto-updating display (60 second intervals) |

## Security

| Directory | Description |
| :------- | :------- |
| `gitleaks/` | Configuration for secret scanning (gitleaks-rules.toml) |
