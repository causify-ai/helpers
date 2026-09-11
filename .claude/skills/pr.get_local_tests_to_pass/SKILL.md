---
description: Make the local unit tests pass for the current PR
model: sonnet
---

# Goal
- Run, monitor, and fix the local unit tests for the current PR

# Workflow

## Create and Update a Plan
- Create a file `plan.pr_get_local_tests_to_pass.md` with a plan in the form of a bullet
  list of actions and maintain it updated, by marking each action
  - [.] when something is in progress
  - [x] when something is done
  - [F] when something failed

## Get the PR Number and Branch Name
- Get the PR number
  ```bash
  > GH_PR_NUM=$(gh pr view --json number -q .number)
  ```

- Get the branch name
  ```bash
  > BRANCH_NAME=$(git branch --show-current)
  ```

## Run Local Regressions
- Run full test suite locally:
  ```bash
  > pytest_multi_build.py --target . 2>&1 --timeout -1 | tee tmp.auto_task.pytest_multi_build.log
  ```
- Wait for the script to terminate

## Check Regressions to Complete

- Check the output of the local regressions with:
  ```bash
  > pytest_failed_multi_build.py 2>&1 | tee tmp.auto_task.pytest_failed_multi_build.log
  ```

## Report Status on the PR
- If local regressions are passing:
  ```bash
  > gh pr comment $GH_PR_NUM --body "Local tests passing"
  ```
- If any failures, document error and post:
  ```bash
  > gh pr comment $GH_PR_NUM --body "Local test failures found: [error summary]. Investigating..."
  ```

## Fix the Failures
- If failures were found, run `tmp.pytest_failed_multi_build.repro.sh` to understand
  what failed and use `/pytest.triage_github_unit_tests` to analyze and fix them
  - If the fix is simple, just fix it and commit
  - If the fix is not clear, stop and ask for the user to help

## Never Commit Junk Files
- Never run `git add -A` or `git add .` to stage a fix: it sweeps in every
  untracked file sitting in the working tree (logs, `tmp.*` scratch files,
  test-run artifacts like `.pkl`/`.json` caches, etc.), not just the files you
  intended to fix
- Always stage files explicitly by path, e.g. `git add <file1> <file2>`
- Before committing, run `git status --short` and review every listed file;
  drop anything that is not part of the intended fix
- If junk files were already committed and pushed, fix it by amending the
  commit to contain only the intended files and force-pushing
  (`git push --force-with-lease`), rather than leaving the junk in history

## Loop
- Keep repeating until the PR is passing all the local tests

# Constraints
- This skill runs both when executed locally on a dev computer and remotely on cloud
  (e.g., on GitHub or Anthropic infrastructure)

# Verification

- [ ] `pytest_failed_multi_build.py` reports no failing tests
- [ ] A PR comment reports the final local test status
- [ ] `git status --short` shows only the intended files staged before commit
