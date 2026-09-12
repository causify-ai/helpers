---
description: Make the CI pass for the current PR
model: haiku
---

# Goal
- Run, monitor, and fix GitHub CI checks for the current PR

# Workflow

## Create and Update a Plan
- Create a file `plan_pr.get_ci_to_pass.md` with a plan in the form of a bullet
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

## Make Sure the PR is Ready

- Run
  ```bash
  > gh pr view $GH_PR_NUM
  ```
- If the PR is a draft and not ready
  ```bash
  > gh pr view $GH_PR_NUM
  gp_5 causify-ai/helpers#1353
  Draft • gpsaggese (GP Saggese) wants to merge 2 commits into master from gp_5 • about 10 minutes ago
  +1499 -240 • ✓ Checks passing
  ```
  run
  ```bash
  > gh pr ready
  ```

## Run and Monitor GitHub CI
- Start monitoring GitHub CI checks:
  ```bash
  > gh pr checks --watch $GH_PR_NUM
  All checks were successful
  0 cancelled, 0 failing, 5 successful, 2 skipped, and 0 pending checks

     NAME                                                  DESCRIPTION  ELAPSED  URL
  ✓  CodeQL/Analyze (actions) (dynamic)                                 37s      https://github.com/causify-ai/helpers/actions/runs/34052614245/job/101538799648
  ✓  CodeQL                                                             3s       https://github.com/causify-ai/helpers/runs/101538870379
  ✓  Gitleaks Scan/Run gitleaks (pull_request)                          11s      https://github.com/causify-ai/helpers/actions/runs/34052615814/job/101538802083
  ✓  Claude Code Review/claude-review (pull_request)                    56s      https://github.com/causify-ai/helpers/actions/runs/34052615817/job/101538802077
  -  Fast tests/run_fast_tests / run_tests (pull_request)                        https://github.com/causify-ai/helpers/actions/runs/34052615896/job/101538803046
  -  Slow tests/run_slow_tests / run_tests (pull_request)                        https://github.com/causify-ai/helpers/actions/runs/34052615907/job/101538803253
  ✓  CodeQL/Analyze (python) (dynamic)                                  1m0s     https://github.com/causify-ai/helpers/actions/runs/34052614245/job/101538799529
  ```
- Monitor for any failures
- Make sure that all the checks run and and they completely successfully

## Report Status on the PR
- If GitHub CI is passing, update the corresponding PR with
  ```bash
  > gh pr comment $GH_PR_NUM --body "GitHub CI checks passing"
  ```
- If any failures, document error and post:
  ```bash
  > gh pr comment $GH_PR_NUM --body "GitHub CI failed: [error summary]. Investigating..."
  ```

## Fix the Failures
- If failures were found, use `/pytest.triage_github_unit_tests` to analyze and fix
  them
  - If the fix is simple, just fix it and commit again
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
- Keep repeating until the PR is passing all the CI tests

# Constraints
- This skill runs both when executed locally on a dev computer and remotely on cloud
  (e.g., on GitHub or Anthropic infrastructure)

# Verification

- [ ] `gh pr checks --watch $GH_PR_NUM` reports all checks successful
- [ ] A PR comment reports the final CI status
- [ ] `git status --short` shows only the intended files staged before commit
