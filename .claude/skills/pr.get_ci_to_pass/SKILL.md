---
description: Make the CI pass for the current PR
model: haiku
---

# Goal
- Monitor GitHub CI checks for the current PR and report status back on the PR

# Workflow

## Constraints
- This skill runs both when executed locally on a dev computer and remotely when
  executed on cloud (e.g., on GitHub or Anthropic infrastructure)

## Step 1: Get the PR Number and Branch Name
- Get the PR number
  ```
  > GH_PR_NUM=$(gh pr view --json number -q .number)
  ```

- Get the branch name
  ```
  > BRANCH_NAME=$(git branch --show-current)
  ```

## Step 2: Run and Monitor GitHub CI
- Start monitoring GitHub CI checks:
  ```
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

## Step 3: Report CI Status on the PR
- If GitHub CI is passing:
  ```
  > gh pr comment $GH_PR_NUM --body "✅ GitHub CI checks passing. Local tests running..."
  ```
- If any failures, document error and post:
  ```
  > gh pr comment $GH_PR_NUM --body "⚠️ Test failures found: [error summary]. Investigating..."
  ```
- If failures were found, use `.claude/skills/pytest.triage_github_unit_tests/SKILL.md`
  to analyze and fix them
