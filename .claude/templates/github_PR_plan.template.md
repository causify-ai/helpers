# PR Split Plan for HelpersTask1273_Get_Mac_tests_to_pass

## Info
- **Branch**: HelpersTask1273_Get_Mac_tests_to_pass
- **Base Branch**: master
- **Dir**: /Users/saggese/src/csfy1/helpers_root
- **Task**: Fix macOS test failures

## Proposed PRs

### PR1: Docker Utilities Fix (hdocker, Hlatex)
- Merged: [ ]
- Complexity: Low-Medium
- Risk: Low
- Tests included: Yes
- Files:
  - `helpers/hdocker.py`
  - `helpers/test/test_hdocker.py`
  - `helpers/hlatex.py`
  - `helpers/test/test_hlatex.py`
- Reasoning:
  - Independent utility fixes for Docker and LaTeX integration on macOS
  - Changes are self-contained and testable

### PR2: Unit Test Purification and Introspection Utilities
- Merged: [ ]
- Complexity: Medium
- Risk: Medium (affects test infrastructure)
- Tests included: Yes
- Files:
  - `helpers/hunit_test_purification.py`
  - `helpers/test/test_hintrospection.py`
  - `helpers/test/test_hnumpy.py`
  - `helpers/test/test_hunit_test.py`
- Reasoning:
  - Refactors test infrastructure used across the codebase
  - Grouped together because they're all related to test utilities and have been
    updated together
  - Moderate complexity due to test infrastructure changes but well-isolated

### PR3: Import Checking Utilities Improvements
- Merged: [ ]
- Complexity: Low-Medium
- Risk: Low-Medium
- Tests included: Yes
- Files:
  - `import_check/show_imports.py`
  - `import_check/test/test_show_imports.py`
  - `import_check/test/test_detect_import_cycles.py`
  - `import_check/test/outcomes/Test_show_imports.*`
- Reasoning:
  - Changes to import cycle detection and display
  - Self-contained module with all tests included
  - Fixes import checking on macOS

## Important Notes

### Files NOT Included in Any PR (should Be Removed Before Commit)
- These files are build artifacts and temporary outputs that should NOT be
  committed:
  - `build1.txt` (637 lines) - Docker build output
  - `build2.txt` (1078 lines) - Docker build output
  - `build3.txt` (5547 lines) - Docker build output
  - `HelpersTask1273_report.md` (empty file)
  - `TODO.HelpersTasl1273.Get_Mac_tests_to_pass.txt` (task tracking file)

**Action Required**: These should be removed from git before any PRs are
created:
```bash
> git rm --cached build*.txt HelpersTask1273_report.md TODO.HelpersTasl1273.Get_Mac_tests_to_pass.txt
```
