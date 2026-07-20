Update the steps of this issue as they are completed successfully with [x]),
are in progress [.], or failed [v]

# Step 1: [ ] Fix Issue
- Fix the following issue following the conventions

- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- When testing code you must always follow the instructions in
  `.claude/skills/testing.rules.md`

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a `plan.md` with 5 bullet points explaining
    what the plan is

## Issue

```
## [ ] Issue3: Use Filter_text From Helpers/hprint.py

### Info
- Original description:
  `./helpers/hunit_test.py:744:# TODO(ai_gp): Use the copy in helpers/hprint.py`

### Proposed Fix
- Type: code reuse/deduplication
- Reason: `filter_text()` is duplicated - better to import from single source
- Proposed fix:
  - Check if `hprint.filter_text()` exists and is compatible
  - Replace `hunit_test.filter_text()` with import from `hprint`
  - Update all callers to use `hprint.filter_text()`
- Confidence in the fix: high
- Fix complexity: low
- Verification plan:
  - Run tests in `test_hunit_test.py` to verify filter_text still works
  - Grep codebase for uses of `hunit_test.filter_text` and verify they work

## [ ] Issue5: Move Assertion Into Test Helper

### Info
- Original description:
  `./dev_scripts_helpers/testing/test/test_pytest_failed.py:48:# TODO(ai_gp): Move the assertion into the helper.`

### Proposed Fix
- Type: refactoring/test improvement
- Reason: Moving assertion into helper consolidates test logic and reduces
  duplication
- Proposed fix:
  - Modify `self.helper()` to include the assertion
  - Remove assertion from test method
  - Update other test methods that use this helper
- Confidence in the fix: high
- Fix complexity: medium
- Verification plan:
  - Run all tests in `test_pytest_failed.py` to verify they still pass
  - Verify assertion still catches errors

## [ ] Issue6: Move Coverage Action to \_run_python_linting_actions

### Info
- Original description:
  `./linters2/lint.py:316:# TODO(ai_gp): Move this to _run_python_linting_actions`

### Proposed Fix
- Type: refactoring/code organization
- Reason: Coverage is a Python linting action and should be part of the unified
  linting flow
- Proposed fix:
  - Move coverage handling from `_lint_python_files()` into
    `_run_python_linting_actions()`
  - Update action list handling to include "coverage"
  - Remove duplicate coverage check from `_lint_python_files()`
- Confidence in the fix: high
- Fix complexity: medium
- Verification plan:
  - Run `invoke run_coverage` to verify it still works
  - Test lint with coverage action included
  - Verify coverage metrics are generated correctly
```

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

- If GitHub CI is passing: 
  ```
  > gh pr comment $GH_PR_NUM --body "✅ GitHub CI checks passing. Local tests running..."
  ```
- If any failures, document error and post:
  ```
  > gh pr comment $GH_PR_NUM --body "⚠️ Test failures found: [error summary]. Investigating..."
  ```

# Step 3: [ ] Run Local Regressions
  
## [ ] Run and Monitor Local Regressions
- Run full test suite locally:
  ```
  > pytest_multi_build.py --target . 2>&1 --timeout -1 | tee tmp.todo_janitor.pytest_multi_build.log
  ```
- Wait for the script to terminate

- Check the output of the local regressions with:
  ```
  > pytest_failed_multi_build.py 2>&1 | tee tmp.todo_janitor.pytest_failed_multi_build.log
  ```

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

