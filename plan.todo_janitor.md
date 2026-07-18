# TODO Janitor Plan

## [x] Group 1: Code Refactoring - Move Assertions and Logic

### [ ] 1.1: Move Assertion Into Test Helper
**File**: `dev_scripts_helpers/testing/test/test_pytest_failed.py:48`

**Type**: cosmetic

**Reason**:

- Comment suggests assertion should be in `helper()` method, not test body
- Improves test readability and reusability

**Potential fix**:

- Extract `self.assert_equal(actual, expected)` into `helper()` method
- Remove assertion line from test

**Fix complexity**: low

**How to verify**: Run test, ensure assertion still passes

### [ ] 1.2: Move Coverage Logic to \_run_python_linting_actions
**File**: `linters2/lint.py:316`

**Type**: refactoring

**Reason**:

- Coverage runs on all Python files including paired jupytext (should be grouped
  with other actions)
- Centralizes linting action orchestration

**Potential fix**:

- Move coverage block (lines 318-322) into `_run_python_linting_actions()`
  function
- Add "coverage" to actions list handling

**Fix complexity**: medium

**How to verify**: Run lint actions, coverage still executes for all Python
files

### [ ] 1.3: Use Pbcopy Function From Hsystem.py
**File**: `helpers/lib_tasks/lib_tasks_utils.py:242`

**Type**: refactoring (eliminate duplication)

**Reason**:

- `_to_pbcopy()` is a duplicate of existing `hsystem.py` utility
- Single source of truth for clipboard operations

**Potential fix**:

- Remove `_to_pbcopy()` function (lines 242-254)
- Replace call: `_to_pbcopy(txt, pbcopy)` → `hsystem.to_pbcopy(txt, pbcopy)`
- Verify `hsystem.to_pbcopy()` exists and has same signature

**Fix complexity**: low

**How to verify**: Import `hsystem.to_pbcopy()`, run clipboard operation

### [ ] 1.4: Use Hprint.filter_text Instead of Local Copy
**File**: `helpers/hunit_test.py:744`

**Type**: refactoring (eliminate duplication)

**Reason**:

- `filter_text()` is copied from `hprint.py`
- Single source of truth for filtering

**Potential fix**:

- Remove `filter_text()` function (lines 744-758)
- Replace calls: `filter_text(...)` → `hprint.filter_text(...)`
- Verify `hprint.filter_text()` exists with same behavior

**Fix complexity**: low

**How to verify**: Run test, verify text filtering works identically

## [ ] Group 2: Import and Dependency Management

### [ ] 2.1: Conditional PIL Import
**File**: `helpers/hgraphviz.py:19`

**Type**: improvement

**Reason**:

- PIL (Pillow) should be conditionally imported (not always required)
- Reduces hard dependency for users who don't need image features

**Potential fix**:

- Move PIL import inside functions that use it
- Add try/except wrapper for graceful error if PIL unavailable
- Document required dependency

**Fix complexity**: medium

**How to verify**: Verify import doesn't break if PIL missing, test image
functions

## [ ] Group 3: Variable and Function Naming

### [ ] 3.1: Rename Invocations → Sys_calls
**File**: `helpers/hunit_test_utils.py:598`

**Type**: improvement (naming clarity)

**Reason**:

- "sys_calls" more clearly describes system calls vs generic "invocations"
- Improves code readability and consistency

**Potential fix**:

- Rename variable `invocations` → `sys_calls` in `capture_system_calls()` and
  callers
- Update docstrings referencing "invocations"
- Find all calls to this context manager and update variable names

**Fix complexity**: high (requires grep/search across codebase)

**How to verify**: Run tests using `capture_system_calls()`, verify renamed
variables work

### [ ] 3.2: Rename Echo/echo_frame → PRINT/PRINT_FRAME
**File**: `helpers/hsystem.py:191`

**Type**: improvement (naming consistency)

**Reason**:

- Function names should be uppercase for log level constants
- Better matches Python logging conventions (DEBUG, INFO, etc.)

**Potential fix**:

- Rename string constant `"echo"` → `"PRINT"`
- Rename string constant `"echo_frame"` → `"PRINT_FRAME"`
- Update all references in validation (line 193)
- Update all references in `system()` function calls

**Fix complexity**: high (requires grep/search across codebase)

**How to verify**: Run system calls with both log levels, verify output
formatting

## [ ] Group 4: Code Movement (consolidation)

### [ ] 4.1: Move Text_to_list to Printing.py
**File**: `helpers/hsystem.py:419`

**Type**: refactoring (module organization)

**Reason**:

- `text_to_list()` is text formatting utility, belongs in `printing.py` not
  `hsystem.py`
- Better module cohesion (hsystem should focus on system operations)

**Potential fix**:

- Move `text_to_list()` function to `helpers/hprint.py`
- Remove from `hsystem.py` (lines 419-426)
- Update imports in `hsystem.py` if needed
- Find all callers, update imports

**Fix complexity**: high (requires grep/search across codebase)

**How to verify**: Run tests, verify text conversion works with new import path

### [ ] 4.2: Move Find_file_with_dir to Hio.py
**File**: `helpers/hsystem.py:948`

**Type**: refactoring (module organization)

**Reason**:

- `find_file_with_dir()` is file I/O operation, belongs in `hio.py` not
  `hsystem.py`
- Better module cohesion

**Potential fix**:

- Move `find_file_with_dir()` function to `helpers/hio.py`
- Remove from `hsystem.py` (lines 948-960+)
- Update imports in `hsystem.py` if needed
- Find all callers, update imports

**Fix complexity**: high (requires grep/search across codebase)

**How to verify**: Run tests, verify file finding works with new import path

## [ ] Group 5: Test Refactoring

### [ ] 5.1: Use Capture_system_calls Mock in Test_lint.py
**File**: `linters2/test/test_lint.py:218`

**Type**: improvement (testing infrastructure)

**Reason**:

- Use new `capture_system_calls()` mock instead of patching
  `helpers.hsystem.system`
- Cleaner, more maintainable test code
- Consistent test patterns across codebase

**Potential fix**:

- Replace `@umock.patch("helpers.hsystem.system")` with context manager approach
- Use `capture_system_calls()` to capture calls
- Use `assert_invocations()` to verify calls

**Fix complexity**: high (entire test class needs refactoring)

**How to verify**: Run test, verify all assertions pass with new mocking
approach

### [ ] 5.2: Use Capture_system_calls Mock in Test_hmodule.py
**File**: `helpers/test/test_hmodule.py:67`

**Type**: improvement (testing infrastructure)

**Reason**:

- Same as 5.1: replace manual mock with `capture_system_calls()`
- Cleaner test code

**Potential fix**:

- Replace manual `system_calls` list and `mock_system_to_string()`
- Use `capture_system_calls()` context manager
- Use `assert_invocations()` to verify calls

**Fix complexity**: medium (single test method)

**How to verify**: Run test, verify pip install calls captured correctly

### [ ] 5.3: Factor Common Code in Test_lint.py
**File**: `linters2/test/test_lint.py:18`

**Type**: refactoring (test code organization)

**Reason**:

- Multiple test classes have duplicated setup/helper code
- Should use /coding.factor_common_code skill to consolidate

**Potential fix**:

- Identify common patterns in `Test_filter_files_by_type` class
- Extract shared methods (e.g., `_create_files()`) to base class or helper
  function

**Fix complexity**: medium

**How to verify**: Run tests, ensure factored code behavior unchanged

## [ ] Group 6: Code Improvements

### [ ] 6.1: Use re.VERBOSE for Regex Pattern
**File**: `helpers/hmarkdown_coloring.py:227`

**Type**: improvement (code readability)

**Reason**:

- Regex pattern is complex, hard to read
- `re.VERBOSE` allows inline comments for clarity
- Pattern explanation already exists in comment block

**Potential fix**:

- Convert regex to multi-line with `re.VERBOSE` flag
- Add inline comments explaining each part:
  - `(?<!\w)` - negative lookbehind for non-word char
  - `@` - literal @
  - `([^@\n]+)` - capture group: non-@ chars
  - `@` - literal closing @
- Update regex compile: `re.compile(_COLOR_MARKER_REGEX, re.VERBOSE)`

**Fix complexity**: low

**How to verify**: Test regex still matches same patterns as before

### [ ] 6.2: Robust Docker_cmd[2] Validation
**File**: `helpers/hdocker.py:771`

**Type**: improvement (robustness)

**Reason**:

- Current approach assumes `docker_cmd[2]` is user flag (fragile)
- Should validate or use more robust method

**Potential fix**:

- Option A: Validate that `docker_cmd[2]` starts with `--user` before modifying
- Option B: Find `--user` flag by searching entire list, replace its value
- Option C: Pass `use_root_user` to `get_docker_base_cmd()` and handle there

**Fix complexity**: medium

**How to verify**: Test with root/non-root users, verify flag correctly set

### [ ] 6.3: Skip Building If Image Was Pulled
**File**: `helpers/hdocker.py:786`

**Type**: improvement (optimization)

**Reason**:

- If image successfully pulled, building is redundant
- Can save time and resource usage

**Potential fix**:

- Capture return value from `pull_image()`
- Only proceed to build if pull returned failure/false
- Add comment explaining logic

**Fix complexity**: low

**How to verify**: Test image pull success path, verify build skipped

## [ ] Group 7: Simplification (use Existing Utils)

### [ ] 7.1: Use System_to_one_line() Helper
**File**: `helpers/hgit.py:406`

**Type**: improvement (code reuse)

**Reason**:

- Lines 407-409 manually implement what `system_to_one_line()` does
- Should use existing utility function

**Potential fix**:

- Replace lines 407-409:
  ```python
  _, out = hsystem.system_to_string(cmd)
  out = out.rstrip("\n")
  hdbg.dassert_eq(len(out.split("\n")), 1, msg=f"Invalid out='{out}'")
  ```
  with:
  ```python
  _, out = hsystem.system_to_one_line(cmd)
  ```
- Remove assertion (already in `system_to_one_line()`)

**Fix complexity**: low

**How to verify**: Test git root finding, verify same output
