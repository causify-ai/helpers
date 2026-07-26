# Unit Test Failure Analysis & Fix Plan

## Summary
**Total Failing Tests**: 31  
**Test Suites Affected**: 7  
**Issue Categories**: 2 (directory purification, mock function call representation)

---

## Category 1: Directory Path Purification Failures (8 tests)

### Issue Description
Test fixtures expect purification logic to handle directory paths like `/home/user` and `/home/user/project/src` which don't exist in the CI container environment.

### Failing Tests
- `helpers/test/test_hunit_test_purification.py::Test_purify_text1::test5`
- `helpers/test/test_hunit_test_purification.py::Test_purify_text1::test6`
- `helpers/test/test_hunit_test_purification.py::Test_purify_text1::test7`
- `helpers/test/test_hunit_test_purification.py::Test_purify_text1::test8`
- `helpers/test/test_hunit_test_purification.py::Test_purify_directory_paths1::test1`
- `helpers/test/test_hunit_test_purification.py::Test_purify_directory_paths1::test2`
- `helpers/test/test_hunit_test_purification.py::Test_purify_directory_paths1::test3`
- `helpers/test/test_hunit_test_purification.py::Test_purify_directory_paths1::test4`

### Error Pattern
```
AssertionError: Dir '/home/user' doesn't exist
file_name='./tmp.initial.actual.txt'
```

### Reason
- Test code assumes directories `/home/user` and `/home/user/project/src` exist
- CI environment (Docker container) doesn't have these directories
- Purification logic validates that directories exist before processing them
- Expected test outcome was generated on system where these paths existed

### Potential Fix
- **Option A (recommended)**: Mock the `os.path.exists()` checks in the purification logic for test paths to simulate existence without requiring actual directories
- **Option B**: Update test expected outcomes using `--update_outcomes` flag if test code logic is correct and expected values should match new behavior
- **Option C**: Skip tests requiring non-existent directories in CI environment

### Fix Complexity
**Low** - The fix involves either:
1. Adding test fixtures to create mock directories
2. Mocking `os.path.exists()` in affected tests
3. Updating expected test outcomes if logic is correct

---

## Category 2: Mock Function Call Record Mismatches (23 tests)

### Issue Description
Tests that mock system calls record function calls in expected output. The comparison shows "FUZZY ACTUAL vs FUZZY EXPECTED" meaning the printed representations differ, likely due to function name display truncation or formatting changes.

### Failing Test Suites

#### 2.1 Documentation/PDF Generation Tests (3 tests)
- `dev_scripts_helpers/documentation/test/test_lib_notes_to_pdf.py::Test_run_pandoc_to_pdf::test1`
- `dev_scripts_helpers/documentation/test/test_lib_notes_to_pdf.py::Test_run_pandoc_to_pdf::test2`
- `dev_scripts_helpers/documentation/test/test_lib_notes_to_pdf.py::Test_run_pandoc_to_pdf::test3`

**Error Pattern**: Mock record comparison for `hsystem.system` calls  
**Expected**: Full qualified function name representation  
**Reason**: Code under test executes `hsystem.system()` calls for pandoc/pdflatex commands. Mock record format changed or representation is truncated.

#### 2.2 Markdown Rendering Tests (3 tests)
- `dev_scripts_helpers/documentation/test/test_open_md.py::Test_open_file::test1`
- `dev_scripts_helpers/documentation/test/test_open_md.py::Test_open_file::test2`
- `dev_scripts_helpers/documentation/test/test_open_md.py::Test_render_with_grip_daemon::test1`

**Error Pattern**: Mock record comparison for `subprocess.run()` calls  
**Issue**: Actual vs expected formatting of mock function records differs

#### 2.3 Notes Preprocessing Tests (1 test)
- `dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_preprocess_notes_executable1::test3`

**Error Pattern**: String comparison using `check_string()` method  
**Issue**: Actual output differs from expected (LaTeX command formatting)

#### 2.4 LaTeX Replacement Tests (2 tests)
- `dev_scripts_helpers/documentation/test/test_replace_latex.py::Test_replace_latex_py::test1`
- `dev_scripts_helpers/documentation/test/test_replace_latex.py::Test_replace_latex_py::test2`

**Error Pattern**: Mock record comparison for system calls

#### 2.5 Git Worktree Tests (5 tests)
- `dev_scripts_helpers/git/test/test_create_git_worktree.py::Test_create_branch::test1`
- `dev_scripts_helpers/git/test/test_create_git_worktree.py::Test_create_branch::test3`
- `dev_scripts_helpers/git/test/test_create_git_worktree.py::Test_create_worktree::test1`
- `dev_scripts_helpers/git/test/test_create_git_worktree.py::Test_create_git_worktree_py::test3`
- `dev_scripts_helpers/git/test/test_create_git_worktree.py::Test_create_git_worktree_py::test4`

**Error Pattern**: Mock record comparison for system calls

#### 2.6 Unit Test Framework Tests (1 test)
- `helpers/test/test_hunit_test.py::Test_AssertEqual1::test_not_equal1`

**Error Pattern**: Mock record format mismatch

#### 2.7 Linting Tests (6+ tests)
- `linters2/test/test_lint.py::Test_run_common_linting_actions::test1`
- `linters2/test/test_lint.py::Test_run_python_linting_actions::test1`
- `linters2/test/test_lint.py::Test_run_python_linting_actions::test2`
- `linters2/test/test_lint.py::Test_lint_python_files::test2`
- `linters2/test/test_lint.py::Test_lint_python_files::test3`
- `linters2/test/test_lint.py::Test_lint_jupyter_files::test2,test3,test4`
- `linters2/test/test_lint.py::Test_lint_markdown_files::test2`

**Error Pattern**: Mock record formatting for `hsystem.system()` and `subprocess` calls

### Root Cause Hypothesis
The common pattern across all Category 2 failures is that tests use `assert_equal()` to compare mock function call records. The error message "FUZZY ACTUAL vs FUZZY EXPECTED" suggests the fuzzy comparison logic isn't matching because:

1. **Most likely**: A recent change to how mock function call records are printed/formatted
   - Changed from `'function': hsystem.system,` to abbreviated format
   - Or changed representation of the function reference itself

2. **Less likely**: 
   - Code under test changed to call different functions
   - Test expected outcomes are outdated

### Potential Fixes
- **Option A (recommended)**: Investigate and update the mock record formatting/printing logic in test fixtures
- **Option B**: Update all test expected outcomes using `pytest ... --update_outcomes`
- **Option C**: Review code changes to understand if logic actually changed

### Fix Complexity
**Medium** - Requires:
1. Identifying the mock formatting change
2. Either reverting the change OR updating all affected test outcomes
3. Verifying no actual logic regression occurred

---

## Recommended Fix Order

1. **[Priority 1]** Fix directory path purification tests (Category 1)
   - Low complexity, clearly isolated issue
   - Dependencies: None

2. **[Priority 2]** Fix mock function call record format (Category 2)
   - Medium complexity, affects many tests across multiple suites
   - Dependencies: Likely a single root cause affecting all Category 2 tests

---

## Verification Steps

After implementing fixes:

1. Run purification tests locally:
   ```bash
   pytest helpers/test/test_hunit_test_purification.py::Test_purify_text1 -v
   pytest helpers/test/test_hunit_test_purification.py::Test_purify_directory_paths1 -v
   ```

2. Run documentation tests locally:
   ```bash
   pytest dev_scripts_helpers/documentation/test/test_lib_notes_to_pdf.py -v
   pytest dev_scripts_helpers/documentation/test/test_open_md.py -v
   ```

3. Run git worktree tests locally:
   ```bash
   pytest dev_scripts_helpers/git/test/test_create_git_worktree.py -v
   ```

4. Run linting tests locally:
   ```bash
   pytest linters2/test/test_lint.py -v
   ```

5. Re-run full fast test suite:
   ```bash
   invoke run_fast_tests
   ```

---

## Next Steps
Await user decision to proceed with implementation.
