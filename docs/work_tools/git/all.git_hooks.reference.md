<!-- toc -->

- [Git hooks](#git-hooks)
  * [Overview](#overview)
    + [Pre-commit hook](#pre-commit-hook)
    + [Commit-msg hook](#commit-msg-hook)
  * [Usage](#usage)
  * [Configuration](#configuration)
  * [Git hooks in action](#git-hooks-in-action)

<!-- tocstop -->

# Git hooks

## Overview

- A Git hook is a script that Git automatically executes before or after certain
  events such as committing code, merging branches, or pushing changes

- `dev_scripts_helpers/git/git_hooks`: contains our custom Git hooks
  - `./install_hooks.py`: can be used to install or remove the hooks
  - `./pre-commit.py`: runs before a commit is created
  - `./commit-msg.py`: checks and/or edits the commit message

### Pre-commit hook

- The `pre-commit.py` script enforces a set of invariants before allowing a
  `git commit` to succeed
- It ensures that essential quality checks are passed, such as verifying the
  branch, author information, file size limits, forbidden words, Python file
  compilations, and secret leaks via `gitleaks`

### Commit-msg hook

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
    enable_git_commit_hook: False
  ...
  ```

## Git hooks in action

- Once installed, the hooks will be run automatically when a user tries to
  commit changes
- If the pre-commit and the commit-msg checks pass, the commit will be created

  ```bash
  > git commit -m "Lint"
  # Running git pre-commit hook ...

  ##### check_master ######
  > git rev-parse --abbrev-ref HEAD
  Branch is 'CmampTask11073_Document_git_hooks'
  'check_master' passed

  ##### check_author ######
  > git config user.name
  > git config --show-origin user.name
  > git config user.email
  > git config --show-origin user.email
  user_email='dummy@gmail.com'
  'check_author' passed

  ##### check_file_size ######
  max file size=512 KB
  'check_file_size' passed

  ##### check_python_compile ######
  Compiling 'dev_scripts_helpers/git/git_hooks/install_hooks.py'...
  'check_python_compile' passed

  ##### check_gitleaks ######
  'check_gitleaks' passed

  ##### All pre-commit hooks passed: committing ######

  Run git commit-msg hook ...

  ##### commit-msg hook passed: committing ######
  [CmampTask11073_Document_git_hooks 02f2c08] Lint
  1 file changed, 11 insertions(+), 9 deletions(-)
  ```

- The pre-commit checks that were run and passed to the commit are also
  automatically added to the commit messages

  ```bash
  > git log 02f2c08
  commit 02f2c08b1677627a95a43c21246219462f9ae339 (HEAD -> CmampTask11073_Document_git_hooks, origin/CmampTask11073_Document_git_hooks)
  Author: Dummy <dummy@gmail.com>
  Date:   Mon Apr 28 22:36:50 2025 -0400

      Lint

      Pre-commit checks:
      - 'check_master' passed
      - 'check_author' passed
      - 'check_file_size' passed
      - 'check_python_compile' passed
      - 'check_gitleaks' passed
      All checks passed ✅
  ```
