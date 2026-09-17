---
description: Monitor GitHub CI checks for the current PR and fix any failures until they pass
model: haiku
---

# Goal
- Monitor GitHub CI checks for the current PR, fix any failures found, and report
  status back on the PR

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

## Make Sure the PR Is Ready

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

## Make Sure Local Tests Pass

- Use `/github.get_pr_to_pass_local_tests` to run and fix the local unit tests for
  the branch

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
- Make sure that all the checks run and complete successfully

## Report Status on the PR
- If GitHub CI is passing:
  ```bash
  > gh pr comment $GH_PR_NUM --body "GitHub CI checks passing"
  ```
- If there are failures, document them and post:
  ```bash
  > gh pr comment $GH_PR_NUM --body "GitHub CI failures found: [error summary]. Investigating..."
  ```

## Fix the Failures
- If failures were found, use `/pytest.fix_ci_tests` to analyze and fix them
- Commit and push the fix, then repeat "Run and Monitor GitHub CI" until it is green

## Loop
- Keep repeating until all GitHub CI checks pass

# Constraints
- This skill runs both when executed locally on a dev computer and remotely when
  executed on cloud (e.g., on GitHub or Anthropic infrastructure)

# Verification

- [ ] `gh pr checks --watch $GH_PR_NUM` reports all checks successful
- [ ] A PR comment reports the final CI status
