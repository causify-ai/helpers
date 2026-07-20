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
