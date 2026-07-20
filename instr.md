# Step 1: Fix Issue
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

# Step 2: Run Regressions

## Create PR and start monitoring
- Create PR in draft mode first:
  > gh pr create --draft --title "Rename invocations to sys_calls throughout codebase"

- Get PR number from output (e.g., #123)

## Monitor GitHub CI + run local tests in parallel
- Start monitoring GitHub CI checks:
  > gh pr checks --watch <PR#>
  
- In parallel, run full test suite locally:
  > invoke run_coverage --suite fast --generate-html-report
  
- Monitor both for any failures

## Update GitHub issue with progress
- If GitHub CI is passing: 
  > gh pr comment <PR#> --body "✅ GitHub CI checks passing. Local tests running..."

- If local tests pass:
  > gh pr comment <PR#> --body "✅ All tests passing locally. Ready for review."
  
- If any failures, document error and post:
  > gh pr comment <PR#> --body "⚠️ Test failures found: [error summary]. Investigating..."

# Step 3: [ ] Submit PR for Review

## Convert to ready-for-review
- Once all checks (GitHub CI + local tests) are passing:
  > gh pr ready <PR#>
  
- Request review from codeowner:
  > gh pr request-review <PR#>
