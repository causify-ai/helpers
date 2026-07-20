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

# Step 2: [x] Run CI Regressions

## [x] Create PR and start monitoring
- PR #1300 created

## [x] Run and Monitor GitHub CI
- GitHub CI checks passing ✅

## [x] Verify CI Regressions
- Posted comment: GitHub CI checks passing

# Step 3: [x] Run Local Regressions
  
## [x] Run Full Local Regressions
- Test suite: 130 passed, 7 skipped ✅

## [x] Verify Full Local Regressions
- Posted comment: All tests passing locally
  
# Step 4: [x] Submit PR for Review

## [x] Convert to ready-for-review
- PR #1300 marked ready for review ✅
- Issue #1299 updated with PR information ✅
- All checks passing: GitHub CI ✅ + Local tests ✅

## Summary
All three TODO items successfully fixed and tested:
- Issue2: hgit.py - Use system_to_one_line() instead of manual rstrip
- Issue4: hgraphviz.py - Add conditional PIL import with error handling  
- Issue7: test_hmodule.py - Refactored test mocks for better capture

Verification: 130 tests passed, 7 skipped
