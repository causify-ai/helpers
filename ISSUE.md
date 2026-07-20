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
