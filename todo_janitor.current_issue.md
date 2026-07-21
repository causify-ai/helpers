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
