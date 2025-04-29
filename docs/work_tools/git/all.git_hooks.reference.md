<!-- toc -->

- [Git hooks](#git-hooks)
  * [Overview](#overview)
  * [Pre-commit hook](#pre-commit-hook)
  * [Commit-msg hook](#commit-msg-hook)
  * [Usage](#usage)
  * [Configuration](#configuration)

<!-- tocstop -->

# Git hooks

## Overview

- A Git hook is a script that Git automatically executes before or after certain
  events such as committing code, merging branches, or pushing changes

- `dev_scripts_helpers/git/git_hooks`: contains our custom Git hooks
  - `./install_hooks.py`: can be used to install or remove the hooks
  - `./pre-commit.py`: runs before a commit is created
  - `./commit-msg.py`: checks and/or edits the commit message

## Pre-commit hook

- The `pre-commit.py` script enforces a set of invariants before allowing a
  `git commit` to succeed
- It ensures that essential quality checks are passed, such as verifying the
  branch, author information, file size limits, forbidden words, Python file
  compilations, and secret leaks via `gitleaks`

## Commit-msg hook

- The `commit-msg.py` script enforces rules related to git commit messages
  before allowing a commit to succeed
- It checks that commit messages follow required conventions
- It also adds the pre-commit checks that were run and passed to the commit
  messages

## Usage

- To manually install the hooks, run
  ```bash
  > dev_scripts_helpers/git/git_hooks/install_hooks.py --action install
  ```
- To manually remove the hooks, run
  ```bash
  > dev_scripts_helpers/git/git_hooks/install_hooks.py --action remove
  ```

## Configuration

- Git hooks are installed by default when the user activates the thin
  environment via the `setenv.sh` script

- Although not recommended, users can explicitly disable the hooks for the
  entire repo by adding the the following configuration in the
  `repo_config.yaml`:
  ```yaml
  repo_info:
    ...
    # Enable git-commit hooks.
    enable_git_commit_hook: True
  ...
  ```
