# TODO Janitor Plan

## [ ] Issue2: Use System_to_one_line() in Hgit.py

### Info
- Original description:
  `./helpers/hgit.py:406:# TODO(ai_gp): Use system_to_one_line().`

### Proposed Fix
- Type: code reuse/simplification
- Reason: `system_to_one_line()` is designed exactly for this use case - run
  command and get single line output
- Proposed fix:
  - Replace manual `hsystem.system_to_string()` + `.rstrip()` + assertion with
    single `system_to_one_line()` call
  - Simplifies error handling and makes intent clearer
- Confidence in the fix: high
- Fix complexity: low
- Verification plan:
  - Run tests in `test_hgit.py` to verify get_client_root still works
  - Test with both regular repo and superproject cases

### Status
- Status: proposed
- GitHub issue title:
- GitHub issue link:
- PR link:
- Git worktree:

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

### Status
- Status: proposed
- GitHub issue title:
- GitHub issue link:
- PR link:
- Git worktree:

## [ ] Issue4: Use Conditional Import for PIL in Hgraphviz.py

### Info
- Original description:
  `./helpers/hgraphviz.py:19:# TODO(ai_gp): Use import PIL if possible.`

### Proposed Fix
- Type: improvement/dependency
- Reason: PIL may not be available in all environments - conditional import
  allows graceful degradation
- Proposed fix:
  - Wrap PIL import in try/except block
  - Provide clear error message if PIL is needed but not available
  - Mark which functions require PIL
- Confidence in the fix: medium
- Fix complexity: low
- Verification plan:
  - Run tests for `hgraphviz.py` (if PIL available)
  - Test behavior when PIL is not available

### Status
- Status: proposed
- GitHub issue title:
- GitHub issue link:
- PR link:
- Git worktree:

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

### Status
- Status: proposed
- GitHub issue title:
- GitHub issue link:
- PR link:
- Git worktree:

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

### Status
- Status: proposed
- GitHub issue title:
- GitHub issue link:
- PR link:
- Git worktree:

## [ ] Issue7: Update Test Mocks to Use Capture_system_calls (test_hmodule.py)

### Info
- Original description:
  `./helpers/test/test_hmodule.py:67:# TODO(ai_gp): Use the new mock for system capture_system_calls and assert_invocations`

### Proposed Fix
- Type: test improvement/modernization
- Reason: New `capture_system_calls()` mock is more readable and maintainable
  than manual mocking
- Proposed fix:
  - Replace manual mock setup with `capture_system_calls()` context manager
  - Use `assert_invocations()` helper for assertions
  - Update test assertions to use new mock output format
- Confidence in the fix: medium
- Fix complexity: medium
- Verification plan:
  - Run tests in `test_hmodule.py` to verify they still pass
  - Verify captured calls match expected system invocations

### Status
- Status: proposed
- GitHub issue title:
- GitHub issue link:
- PR link:
- Git worktree:

## [ ] Issue8: Update Test Mocks in Test_lint.py

### Info
- Original description:
  `./linters2/test/test_lint.py:218:# TODO(ai_gp): Use the new mock for system capture_system_calls and assert_invocations in all this file instead of patching helpers.system`

### Proposed Fix
- Type: test improvement/modernization
- Reason: Replace all manual patching of `helpers.system` with
  `capture_system_calls()` for consistency
- Proposed fix:
  - Find all places where `@umock.patch("helpers.hsystem.system")` is used
  - Replace with `capture_system_calls()` context manager
  - Update assertions to use captured invocations
- Confidence in the fix: medium
- Fix complexity: medium
- Verification plan:
  - Run all tests in `test_lint.py` to verify they still pass
  - Verify test coverage is maintained

### Status
- Status: proposed
- GitHub issue title:
- GitHub issue link:
- PR link:
- Git worktree:

## [ ] Issue9: Apply Factor_common_code to Test_filter_files_by_type

### Info
- Original description:
  `./linters2/test/test_lint.py:18:# TODO(ai_gp): Run skill /coding.factor_common_code`

### Proposed Fix
- Type: refactoring/code deduplication
- Reason: Test class likely has repeated setup or test patterns that can be
  consolidated
- Proposed fix:
  - Run `/coding.factor_common_code` skill on this test class
  - Extract common test patterns into helper methods
  - Reduce code duplication in test methods
- Confidence in the fix: medium
- Fix complexity: medium
- Verification plan:
  - Run tests in `Test_filter_files_by_type` to verify all pass
  - Verify test behavior unchanged despite refactoring

### Status
- Status: proposed
- GitHub issue title:
- GitHub issue link:
- PR link:
- Git worktree:

## [ ] Issue10: Use Existing \_to_pbcopy From Hsystem.py

### Info
- Original description:
  `./helpers/lib_tasks/lib_tasks_utils.py:242:# TODO(ai_gp): Use the one in ./helpers/hsystem.py`

### Proposed Fix
- Type: code reuse/deduplication
- Reason: `_to_pbcopy()` is duplicated - import from single authoritative
  location
- Proposed fix:
  - Check if `hsystem._to_pbcopy()` exists and is compatible
  - Replace version in `lib_tasks_utils.py` with import from `hsystem`
  - Update any callers to use `hsystem._to_pbcopy()`
- Confidence in the fix: high
- Fix complexity: medium
- Verification plan:
  - Run pbcopy tests to verify functionality unchanged
  - Verify both copy-to-clipboard and print-to-stdout paths work

### Status
- Status: proposed
- GitHub issue title:
- GitHub issue link:
- PR link:
- Git worktree:

## [ ] Issue11: Make Docker_cmd[2] Modification More Robust

### Info
- Original description:
  `./helpers/hdocker.py:771:# TODO(ai_gp): Check that docker_cmd[2] starts with --user or use a more robust approach.`

### Proposed Fix
- Type: bug/robustness improvement
- Reason: Direct array index assumption is fragile and could break with docker
  base command changes
- Proposed fix:
  - Search for `--user` flag in docker_cmd by index or value
  - Replace it if found, append if not found
  - Or refactor to pass `use_root_user` to `get_docker_base_cmd()` instead
- Confidence in the fix: medium
- Fix complexity: medium
- Verification plan:
  - Run docker tests to verify user flag is correctly set
  - Test both with and without override
  - Test that command structure is preserved

### Status
- Status: proposed
- GitHub issue title:
- GitHub issue link:
- PR link:
- Git worktree:

## [ ] Issue12: Skip Build If Image Was Pulled Successfully

### Info
- Original description:
  `./helpers/hdocker.py:786:# TODO(ai_gp): If it was pulled then skip building it.`

### Proposed Fix
- Type: optimization/improvement
- Reason: If pull was successful, building is redundant and wastes
  time/resources
- Proposed fix:
  - Capture return value of `pull_image()` call
  - If pull succeeded, skip the build step
  - Only build if pull failed/image wasn't found
- Confidence in the fix: medium
- Fix complexity: medium
- Verification plan:
  - Run docker image creation tests
  - Verify that build is skipped when image is pulled
  - Verify fallback to build when pull fails

### Status
- Status: proposed
- GitHub issue title:
- GitHub issue link:
- PR link:
- Git worktree:

## [ ] Issue13: Use System_to_one_line() Simplification and Minor Refactor

### Info
- Original description: Multiple small code movements and cleanups

### Proposed Fix
- Type: refactoring/code organization
- Reason: Consolidate related code movements before major renames
- Proposed fix:
  - Complete items 1-12 first
  - These provide foundation for larger refactors
- Confidence in the fix: high
- Fix complexity: high
- Verification plan:
  - Run full test suite after all refactors

### Status
- Status: proposed
- GitHub issue title:
- GitHub issue link:
- PR link:
- Git worktree:

## [ ] Issue14: Move Text_to_list() to Helpers/printing.py

### Info
- Original description:
  `./helpers/hsystem.py:419:# TODO(ai_gp): Move it to \`helpers/printing.py\``

### Proposed Fix
- Type: code movement/reorganization
- Reason: `text_to_list()` is text/string utility, not system utility - belongs
  in printing module
- Proposed fix:
  - Create `helpers/printing.py` if it doesn't exist, or use `hprint.py`
  - Move `text_to_list()` function to appropriate module
  - Update import in `hsystem.py` or remove if no longer needed in that module
  - Grep codebase for all imports and usages of `hsystem.text_to_list()`
  - Update all imports to use new location
- Confidence in the fix: high
- Fix complexity: high
- Verification plan:
  - Run full test suite to verify all imports work
  - Verify `text_to_list()` output unchanged
  - Check no circular imports introduced

### Status
- Status: proposed
- GitHub issue title:
- GitHub issue link:
- PR link:
- Git worktree:

## [ ] Issue15: Move Find_file_with_dir() to Hio.py

### Info
- Original description: `./helpers/hsystem.py:948:# TODO(ai_gp): Move to hio.py`

### Proposed Fix
- Type: code movement/reorganization
- Reason: File finding utilities belong in I/O module, not system module
- Proposed fix:
  - Move `find_file_with_dir()` function to `hio.py`
  - Update import in `hsystem.py` if still needed internally
  - Grep codebase for all imports and usages of `hsystem.find_file_with_dir()`
  - Update all imports to use new location (`hio.find_file_with_dir()`)
- Confidence in the fix: high
- Fix complexity: high
- Verification plan:
  - Run full test suite to verify all imports work
  - Verify `find_file_with_dir()` output unchanged
  - Check no circular imports introduced

### Status
- Status: proposed
- GitHub issue title:
- GitHub issue link:
- PR link:
- Git worktree:

## [ ] Issue16: Rename "echo" → "PRINT" and "echo_frame" → "PRINT_FRAME"

### Info
- Original description:
  `./helpers/hsystem.py:191:# TODO(ai_gp): Rename "echo" -> "PRINT" and "echo_frame" -> "PRINT_FRAME"`

### Proposed Fix
- Type: refactoring/renaming
- Reason: PRINT\_\* is more consistent naming convention and clearer
- Proposed fix:
  - Global rename: "echo" → "PRINT" and "echo_frame" → "PRINT_FRAME"
  - Search all files for uses of `log_level="echo"` or `log_level="echo_frame"`
  - Update all occurrences
  - Update validation logic in `hsystem.py`
- Confidence in the fix: high
- Fix complexity: high
- Verification plan:
  - Grep entire codebase for "echo" in context of log_level
  - Run tests to verify all print operations still work
  - Verify no hardcoded string comparisons break

### Status
- Status: proposed
- GitHub issue title:
- GitHub issue link:
- PR link:
- Git worktree:

## [x] Issue17: Rename "invocations" → "sys_calls" Throughout Codebase

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

### Status
- Status: completed
- GitHub issue title: HelpersTask1292_Rename_invocations_to_sys_calls_Throughout_Codebase
- GitHub issue link: https://github.com/causify-ai/helpers/issues/1292
- PR link: https://github.com/causify-ai/helpers/pull/1293
- Git worktree: b2934832
