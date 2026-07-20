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

### Info
- Original description:
  `./helpers/hunit_test_utils.py:598:# TODO(ai_gp): Rename variables and functions using invocations -> sys_calls`

### Proposed Fix
- Type: refactoring/renaming (consistency)
- Reason: "sys_calls" is shorter and more consistent with existing naming
  patterns
- Proposed fix:
  - Global rename: all uses of "invocations" (variable, parameter, return) →
    "sys_calls"
  - Update function docstrings and comments
  - Rename any functions/methods that include "invocation" to use "sys_call"
  - Examples: `capture_system_calls()`, `assert_invocations()` → needs careful
    consideration
- Confidence in the fix: high
- Fix complexity: high
- Verification plan:
  - Grep codebase for "invocation" and "sys_call" to understand current usage
  - Run full test suite after renaming
  - Verify all system call capturing still works

# Step 2: [ ] Run CI Regressions

## [ ] Create PR and start monitoring
- Create PR in draft mode first:
  ```
  > gh pr create --draft --title "Rename invocations to sys_calls throughout codebase"
  ```

- Get PR number from output (e.g., #123)

## [ ] Run and Monitor GitHub CI
- Start monitoring GitHub CI checks:
  ```
  > gh pr checks --watch <PR#>
  ```

- Monitor for any failures

- If GitHub CI is passing: 
  ```
  > gh pr comment <PR#> --body "✅ GitHub CI checks passing. Local tests running..."
  ```
- If any failures, document error and post:
  ```
  > gh pr comment <PR#> --body "⚠️ Test failures found: [error summary]. Investigating..."
  ```

# Step 3: [ ] Run Local Regressions
  
## [ ] Run and Monitor Local Regressions
- Run full test suite locally:
  ```
  > pytest_multi_build.py --target .
  ```

- Monitor for any failures

- If local tests pass:
  ```
  > gh pr comment <PR#> --body "✅ All tests passing locally. Ready for review."
  ```
- If any failures, document error and post:
  ```
  > gh pr comment <PR#> --body "⚠️ Test failures found: [error summary]. Investigating..."
  ```
  
# Step 4: [ ] Submit PR for Review

## [ ] Convert to ready-for-review
- Once all checks (GitHub CI + local tests) are passing:
  > gh pr ready <PR#>
  
- Request review from codeowner:
  > gh pr request-review <PR#>
