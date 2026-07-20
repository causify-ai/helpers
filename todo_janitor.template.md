# Instructions
- Fix the following issue following the conventions
  - When writing code you must always follow the instructions in
    `.claude/skills/coding.rules.md`

  - When testing code you must always follow the instructions in
    `.claude/skills/testing.rules.md`

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a `plan.md` with 5 bullet points explaining
    what the plan is

## Keep this File Updated
- For every part of this instructions that are complete, update the steps as they:
  - Are completed successfully with [x]
  - Are in progress with [.]
  - Fail with [v]

# Step 1: [x] Fix Issue

## Issue Description

The issue is:

`@todo_janitor.current_issue.md`

# Step 2: [ ] Run CI Regressions

## [ ] Create PR and start monitoring
- Create PR in draft mode first:
  ```
  > gh pr create --draft --title "Rename invocations to sys_calls throughout codebase"
  ```

- Get PR number from output (e.g., #123)

- Extract the PR number as 
  ```
  > GH_PR_NUM=$(gh pr view --json number -q .number); echo $GH_PR_NUM
  1293
  ```

## [ ] Run and Monitor GitHub CI
- Start monitoring GitHub CI checks:
  ```
  > gh pr checks --watch $GH_PR_NUM
  ```
- Monitor for any failures

## [ ] Verify CI Regressions

- If GitHub CI is passing: 
  ```
  > gh pr comment $GH_PR_NUM --body "✅ GitHub CI checks passing. Local tests running..."
  ```
- If any failures, document error and post:
  ```
  > gh pr comment $GH_PR_NUM --body "⚠️ Test failures found: [error summary]. Investigating..."
  ```

# Step 3: [ ] Run Local Regressions
  
## [ ] Run Full Local Regressions
- Run full test suite locally:
  ```
  > pytest_multi_build.py --target . 2>&1 --timeout -1 | tee tmp.todo_janitor.pytest_multi_build.log
  ```
- Wait for the script to terminate

- Check the output of the local regressions with:
  ```
  > pytest_failed_multi_build.py 2>&1 | tee tmp.todo_janitor.pytest_failed_multi_build.log
  ```

## [ ] Verify Full Local Regressions

- If local tests pass:
  ```
  > gh pr comment $GH_PR_NUM --body "✅ All tests passing locally. Ready for review."
  ```
- If any failures, document error and post:
  ```
  > gh pr comment $GH_PR_NUM --body "⚠️ Test failures found: [error summary]. Investigating..."
  ```
  
# Step 4: [ ] Submit PR for Review

## [ ] Convert to ready-for-review
- Once all checks (GitHub CI + local tests) are passing

- Mark the PR ready for review
  ```
  > gh pr ready $GH_PR_NUM
  ```

- Request review from codeowner:
  ```
  > gh pr request-review $GH_PR_NUM
  ```

- Update the GitHub issue with the info
  ```
  > GH_ISSUE_NUM=$(git branch --show-current | sed 's/.*Task\([0-9]*\).*/\1/')
  > gh issue comment $GH_ISSUE_NUM --body "PR ${GH_PR_NUM} ready to review and merge"
  https://github.com/causify-ai/helpers/issues/1292#issuecomment-5024710557
  ```
