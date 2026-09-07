---
description: Get a PR in a committable state
model: haiku
---

# Goal
- Monitor GitHub CI checks for the current PR and report status back on the PR

# Workflow

## Constraints
- This skill runs both when executed locally on a dev computer and remotely when
  executed on cloud (e.g., on GitHub or Anthropic infrastructure)

## Get the PR Number and Branch Name
- Get the PR number
  ```
  > GH_PR_NUM=$(gh pr view --json number -q .number)
  ```

- Get the branch name
  ```
  > BRANCH_NAME=$(git branch --show-current)
  ```

## Fix Pyright Issues
- Fix the pyright warnings and errors in the branch
  ```
  > linters2/lint.py --clear_actions --action "pyright" --branch
  ```

## Run Linter
- Run the linter
  ```
  > linters2/lint.py 
  ```
