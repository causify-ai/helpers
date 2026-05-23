# Summary

This directory provides Git utility commands and scripts for streamlined development workflows. It offers convenient shortcuts for common Git operations including status checks, diff visualization, conflict resolution, submodule management, branch analysis, and repository maintenance. The tools are designed to improve developer productivity by automating frequent Git tasks and providing cleaner output formats.

# Structure of the Dir

- **git_hooks/**: Git hooks system for enforcing code quality and preventing secrets from being committed. Includes pre-commit validation, commit message checking, and secret detection via gitleaks.
- **gitleaks/**: Secret scanning configuration and rules for detecting sensitive information (API keys, credentials, etc.) in commits.

# Description of Files

This directory contains several categories of Git utilities:

## Shortcut Commands (bash aliases/scripts)

| Command | Description |
| :------- | :------- |
| `gc` | Commit with interactive message |
| `gcl` | Clean the client by stashing and removing untracked files, creating a backup |
| `gcours` | Accept our version of conflicted files (checkout --ours) |
| `gctheirs` | Accept their version of conflicted files (checkout --theirs) |
| `gco` | Checkout a branch and pull with submodule updates |
| `gd` | Run git difftool on specified files |
| `gdc` | Run git difftool on cached/staged changes |
| `gdpy` | Git diff for all Python files in the repository |
| `gll` | List commits in fancy format with author, timestamp, and branch info |
| `gllmy` | List only your own commits in fancy format |
| `gp` | Sync client and then push local commits |
| `gpa` | Pull with autostash (without pushing) |
| `grc` | Continue a rebase operation |
| `grs` | Skip the current commit during a rebase |
| `gs` | Print git status of client and submodules |
| `gs_to_files.sh` | Convert git status output to file listing |
| `gsl` | List stashed changes |
| `gss` | Print git status in short format with submodule info |

## Python Utilities

| Script | Description |
| :------- | :------- |
| `gd_notebook.py` | Diff a notebook against HEAD, removing artifacts for clearer comparison |
| `gsp.py` | Stash changes in git client with automatic backup |
| `git_submodules.py` | Implement git workflows on multiple repos (pull, commit, status, etc.) |
| `gup.py` | Update git client by stashing, rebasing, and reapplying changes |

## Shell Utilities

| Script | Description |
| :------- | :------- |
| `git_backup.sh` | Create a tarball backup of all modified/added files |
| `git_branch.sh` | Show information about branches with author and date |
| `git_branch_name.sh` | Print name of the current branch |
| `git_branch_point.sh` | Show information about the branch point (common ancestor with main) |
| `git_clone.sh` | Clone repo and configure git hooks |
| `git_conflict_files.sh` | Find files with git conflicts |
| `git_conflict_show.sh` | Generate base, ours, and theirs files for conflict visualization |
| `git_files.sh` | Report git cached and modified files |
| `git_graph.sh` | Plot a graphical view of branches (modes 1, 2, 3 for different detail levels) |
| `git_hash_head.sh` | Show the short commit hash that HEAD is at |
| `gd_master.sh` | Diff current branch against master (shows commits in both directions) |
| `gd_names.sh` | Shortcut for `git diff --name-only master...` |
| `git_previous_commit_files.sh` | Get files from previous commit |
| `git_revert.sh` | Force a revert of files to HEAD |
| `git_root.sh` | Report the path of the git repository root |
| `git_shrink_repo.sh` | Remove large files from repository history |
| `git_untracked_files.sh` | Report untracked files |

## Submodule Management

| Script | Description |
| :------- | :------- |
| `git_submodules_are_updated.sh` | Check if all submodules are up to date |
| `git_submodules_clean.sh` | Clean all submodules |
| `git_submodules_commit.sh` | Commit changes in all submodules |
| `git_submodules_pull.sh` | Pull updates for all submodules |
| `git_submodules_roll_fwd.sh` | Roll forward submodule references |
| `git_submodules_stash.sh` | Stash changes in all submodules |

## Configuration and Maintenance

| Script | Description |
| :------- | :------- |
| `fix_repo_perms.sh` | Fix repository permissions for proper git operations |

# Description of Executables

## Status and Monitoring

### `gs` / `gss`

- **What It Does**
  - `gs`: Print the status of the client and submodules using `git status`
  - `gss`: Same as `gs` but in short format for quicker overview
  - Useful for understanding the state of your working directory and all submodules

### `gll` / `gllmy`

- **What It Does**
  - Display commit history in a fancy, readable format
  - Include author, commit timestamp, and branch information
  - `gllmy` filters to show only your own commits
  - Helpful for understanding recent work and commit history

## Diff and Comparison

### `gd` / `gdc` / `gdpy`

- **What It Does**
  - `gd`: Run git difftool on specified files for visual comparison
  - `gdc`: Show only cached/staged changes using difftool
  - `gdpy`: Diff all Python files in the repository
  - Use visual difftools (vimdiff by default) for better understanding of changes

### `gd_master.sh`

- **What It Does**
  - Compare current branch against master/main branch
  - Shows commits that exist in both branches (in both directions)
  - Useful for understanding the divergence between branches

### `gd_names.sh`

- **What It Does**
  - Shortcut for `git diff --name-only master...`
  - List only the names of files that differ between current branch and master
  - Quick way to see what files have changed

### `gd_notebook.py`

- **What It Does**
  - Diff a Jupyter notebook against HEAD version in git
  - Remove notebook metadata and execution artifacts for clearer differences
  - Compare using vimdiff for visual inspection
  - Focus on actual content changes rather than notebook formatting changes

- **Examples**
  - Diff current notebook against HEAD:
    ```bash
    > gd_notebook.py notebook.ipynb
    ```
  - Diff notebook with specific revision:
    ```bash
    > gd_notebook.py --rev HEAD~1 notebook.ipynb
    ```

## Branch Management

### `git_branch.sh` / `git_branch_name.sh` / `git_branch_point.sh`

- **What It Does**
  - `git_branch.sh`: Show detailed information about branches including author and date
  - `git_branch_name.sh`: Print just the name of the current branch (useful in scripts)
  - `git_branch_point.sh`: Show information about the branch point (common ancestor with main)

### `gco`

- **What It Does**
  - Checkout a branch and automatically pull updates with submodule support
  - Replaces the standard `git checkout` with enhanced functionality
  - Ensures submodules are also updated when switching branches

- **Examples**
  - Switch to an existing branch:
    ```bash
    > gco branch_name
    ```

## Stashing and Cleaning

### `gsp.py` / `gcl`

- **What It Does**
  - `gsp.py`: Stash changes in the git client while maintaining working state
  - `gcl`: Clean the entire client by stashing changes and removing untracked files with backup
  - Both create backups to prevent accidental loss of work

- **Examples**
  - Stash current changes:
    ```bash
    > gsp.py
    ```
  - Clean client with backup:
    ```bash
    > gcl
    ```

### `gsl`

- **What It Does**
  - List all stashed changes with their descriptions
  - Quick way to see what has been stashed

## Push and Pull Operations

### `gp` / `gpa` / `gup.py`

- **What It Does**
  - `gp`: Sync client (pull with autostash and rebase) then push local commits
  - `gpa`: Pull only with autostash, without pushing
  - `gup.py`: Update git client by stashing, rebasing, and reapplying stashed changes
  - All use autostash to prevent loss of uncommitted work during pull/rebase

- **Examples**
  - Full sync and push:
    ```bash
    > gp
    ```
  - Pull only without pushing:
    ```bash
    > gpa
    ```
  - Manual update with stash and rebase:
    ```bash
    > gup.py
    ```

### `git_submodules_pull.sh`

- **What It Does**
  - Pull updates for all submodules in the repository
  - Ensures all submodules are synchronized with their remote branches

## Conflict Resolution

### `gcours` / `gctheirs`

- **What It Does**
  - Quick shortcuts to resolve merge conflicts
  - `gcours`: Accept our version of conflicted files (`checkout --ours`)
  - `gctheirs`: Accept their version of conflicted files (`checkout --theirs`)

### `git_conflict_files.sh`

- **What It Does**
  - Find and list all files that have git merge conflicts
  - Useful for identifying work needed during a merge

### `git_conflict_show.sh`

- **What It Does**
  - Generate separate files for base, ours, and theirs versions of conflicted files
  - Enables visual comparison of all three versions
  - Helpful for understanding the nature of conflicts

- **Examples**
  - Show conflict versions:
    ```bash
    > git_conflict_show.sh conflicted_file.py
    ```

## Rebase Operations

### `grc` / `grs`

- **What It Does**
  - `grc`: Continue a rebase operation after resolving conflicts
  - `grs`: Skip the current commit during a rebase
  - Shortcuts for common rebase actions

## Submodule Management

### `git_submodules.py`

- **What It Does**
  - Implement git workflows on multiple repositories with submodules
  - Support operations: status, pull, commit, stash, clean, etc.
  - Useful for projects with multiple git submodules

- **Examples**
  - Show status of all submodules:
    ```bash
    > git_submodules.py --action status
    ```
  - Pull all submodules:
    ```bash
    > git_submodules.py --action pull
    ```
  - Commit changes in all submodules:
    ```bash
    > git_submodules.py --action commit --message "Update submodules"
    ```

### Submodule Helpers

- `git_submodules_are_updated.sh`: Check if all submodules are synchronized
- `git_submodules_clean.sh`: Clean all submodules
- `git_submodules_commit.sh`: Commit changes across all submodules
- `git_submodules_roll_fwd.sh`: Advance submodule references forward

## Repository Utilities

### `git_root.sh`

- **What It Does**
  - Report the path of the git repository root directory
  - Useful in scripts to navigate to the repository root

### `git_files.sh`

- **What It Does**
  - Report cached and modified files in the repository
  - List both staged and unstaged changes

### `git_untracked_files.sh`

- **What It Does**
  - List all untracked files in the working directory
  - Useful for identifying files that should be added to .gitignore

### `git_hash_head.sh`

- **What It Does**
  - Show the short commit hash of the current HEAD
  - Useful for identifying the current commit in scripts

### `git_graph.sh`

- **What It Does**
  - Display a graphical view of repository branches and commit history
  - Support different modes (1, 2, 3) for varying levels of detail
  - Helpful for visualizing branch structure and relationships

- **Examples**
  - Show basic branch graph:
    ```bash
    > git_graph.sh 1
    ```
  - Show detailed branch information:
    ```bash
    > git_graph.sh 2
    ```
  - Show most detailed view:
    ```bash
    > git_graph.sh 3
    ```

### `git_backup.sh`

- **What It Does**
  - Create a tarball backup of all modified and added files
  - Preserve work before major operations
  - Include directory structure in backup

### `git_revert.sh`

- **What It Does**
  - Force revert files to their HEAD version
  - Discard local changes to specified files
  - Use with caution as this is destructive

### `git_shrink_repo.sh`

- **What It Does**
  - Remove large files from the repository history
  - Reduce repository size by cleaning up past large commits
  - Useful for cleaning up accidentally committed large binaries or data files

### `git_clone.sh`

- **What It Does**
  - Clone a repository and configure git hooks
  - Automatically sets up pre-commit hooks and security checks
  - Ensures new clones have proper development environment setup

### `git_previous_commit_files.sh`

- **What It Does**
  - Retrieve files from the previous commit
  - Useful for accessing content that was changed in the last commit

## Git Hooks and Security

### `git_hooks/` Directory

The git_hooks subdirectory contains the implementation of custom git hooks:

- **`install_hooks.py`**: Install git hooks in the repository's `.git/hooks/` directory
- **`pre-commit.py`**: Pre-commit hook that runs checks before commits are allowed
- **`pre-commit-dry-run.py`**: Dry-run version of pre-commit hook for testing
- **`commit-msg.py`**: Validate commit message format and content
- **`gitleaks.py`**: Secret detection hook preventing sensitive data from being committed
- **`translate.py`**: Helper script for hook translations/transformations
- **`utils.py`**: Shared utilities for hook implementations

### `gitleaks/` Directory

Configuration for gitleaks secret scanning:

- **`gitleaks-rules.toml`**: Custom rules for detecting sensitive information patterns (API keys, credentials, tokens, etc.)

# Description of Workflows

## Daily Sync Workflow

For keeping your branch up-to-date with the main branch:

- Use `gp` to simultaneously sync (pull + rebase) and push:
  ```bash
  > gp
  ```
- Or pull without pushing using `gpa`:
  ```bash
  > gpa
  ```

## Handling Merge Conflicts

When merge conflicts occur:

1. Run `git_conflict_files.sh` to identify files with conflicts
2. Use `git_conflict_show.sh` to view all versions (base, ours, theirs)
3. Resolve conflicts manually in your editor
4. Use `gcours` to accept your version or `gctheirs` for theirs
5. Continue with `grc` once resolved

## Working with Submodules

For projects with git submodules:

1. Use `git_submodules.py --action status` to check submodule status
2. Use `git_submodules_pull.sh` to update all submodules
3. Use `git_submodules_commit.sh` to commit submodule changes
4. Use `gco` to checkout branches (handles submodule updates automatically)

## Branch Analysis and Comparison

Compare your branch with main:

- View commits in both directions: `gd_master.sh`
- List only changed files: `gd_names.sh`
- Visualize branch relationships: `git_graph.sh`

## Notebook Development

When working with Jupyter notebooks:

- Use `gd_notebook.py` to see actual content changes vs metadata changes
- This removes notebook artifacts like execution counters and output cells
- Makes it easier to understand what actually changed in the notebook

## Repository Maintenance

For large repositories that have accumulated large files:

1. Use `git_shrink_repo.sh` to remove large files from history
2. Use `git_backup.sh` before major operations
3. Use `git_revert.sh` to discard unwanted changes
4. Use `git_clone.sh` with hooks for fresh, properly configured clones
