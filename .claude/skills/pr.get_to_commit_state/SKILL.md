---
description: Get a PR in a committable state
model: haiku
---

# Goal
- Monitor GitHub CI checks for the current PR and report status back on the PR

# Workflow

## Get the PR Number and Branch Name
- Get the PR number
  ```bash
  > GH_PR_NUM=$(gh pr view --json number -q .number)
  ```

- Get the branch name
  ```bash
  > BRANCH_NAME=$(git branch --show-current)
  ```

## Fix Pyright Issues
- Fix the pyright warnings and errors in the branch
  ```bash
  > linters2/lint.py --clear_actions --action "pyright" --branch
  ```

## Run Linter
- Run the linter
  ```bash
  > linters2/lint.py
  ```

# Constraints
- This skill runs both when executed locally on a dev computer and remotely when
  executed on cloud (e.g., on GitHub or Anthropic infrastructure)

# Verification

- [ ] `linters2/lint.py --clear_actions --action "pyright" --branch` reports
      no pyright errors
- [ ] `linters2/lint.py` reports no lint issues
