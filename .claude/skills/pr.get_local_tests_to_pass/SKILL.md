---
description: Make the local unit tests pass for the current PR
model: sonnet
---

# Goal
- Run and fix the local unit tests for the current PR

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

## Run Local Regressions
- Run full test suite locally:
  ```
  > pytest_multi_build.py --target . 2>&1 --timeout -1 | tee tmp.auto_task.pytest_multi_build.log
  ```
- Wait for the script to terminate

## Check Regressions to Complete

- Check the output of the local regressions with:
  ```
  > pytest_failed_multi_build.py 2>&1 | tee tmp.auto_task.pytest_failed_multi_build.log
  ```

## Report Status
- If local regressions are passing:
  ```
  > gh pr comment $GH_PR_NUM --body "Local tests passing"
  ```
- If any failures, document error and post:
  ```
  > gh pr comment $GH_PR_NUM --body "Test failures found: [error summary]. Investigating..."
  ```
- If failures were found, use `.claude/skills/pytest.triage_local_unit_tests/SKILL.md`
  to analyze and fix them
