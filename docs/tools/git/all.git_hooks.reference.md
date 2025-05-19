<!-- toc -->

- [Git hooks](#git-hooks)
  * [Overview](#overview)
  * [Pre-commit hook](#pre-commit-hook)
  * [Commit-msg hook](#commit-msg-hook)

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
- It ensures that essential checks are passed, such as verifying the branch,
  author information, file size limits, forbidden words, Python file
  compilations, and secret leaks

## Commit-msg hook

- The `commit-msg.py` script enforces rules related to git commit messages
  before allowing a commit to succeed
- It checks that commit messages follow required conventions
- It also adds the pre-commit checks that were run and passed to the commit
  messages
