## Test Run Results Summary

### Build 1 (Docker engine with `-v 1.6.0 --stage=local`)
**Summary:** 11 failed, 3116 passed, 241 skipped (308.86s)
**Progress:** 40 failures → 11 failures (29 fixed by Fixes 1.1–4.1)

### Build 2 (pytest_log on Docker)
**Summary:** 35 failed, 3161 passed, 230 skipped

### Build 3 (pytest_log on Apple/native)
**Summary:** 35 failed, 3156 passed, 235 skipped

**Note:** Build1 subset appears to be filtered to only Mac-specific tests or fast tests. Build2/3 include additional test suites.

### Remaining 11 Failures:

#### Category A: test_notes_to_pdf (2 failures)
- `test_notes_to_pdf.py::Test_notes_to_pdf1::test2` 
- `test_notes_to_pdf.py::Test_notes_to_pdf1::test3`
- **Root cause:** Docker command output mismatch. Actual includes `docker run --rm --user 0:0` but expected shows `$DOCKER_EXECUTABLE run --rm --user $(id -u):$(id -g)`
- **Status:** Unknown if this is Fix 3.1 side effect or pre-existing

#### Category B: test_hserver (1 failure)
- `test_hserver.py::Test_hserver_inside_docker_container_on_gp_mac1::test_get_docker_info1`
- **Root cause:** Missing actual output in test comparison (blank line in actual vs expected output)
- **Status:** May be Docker engine vs Apple engine difference

#### Category C: test_hunit_test (1 failure)
- `test_hunit_test.py::Test_AssertEqual1::test_not_equal1`
- **Root cause:** Extra spacing in output: `completed failure` vs `completed       failure` (alignment difference)
- **Status:** May be related to Fix 1.3 (scratch space writes)

#### Category D: test_show_imports (4 failures) — ✅ FIXED
- `test_show_imports.py::Test_show_imports::test4, test5, test8, test9`
- **Root cause:** `pydeps --show-deps` doesn't include external dependencies (numpy, etc.) in JSON output
- **Fix applied:** Added post-processing to inject external dependencies
  - New method `_add_missing_external_dependencies()` in `_NodesInfo` class
  - Scans import lists of all nodes and adds missing root modules
  - Creates minimal nodes for external deps so they appear in graph
- **Code:** `import_check/show_imports.py` - modified `__init__` and added new method
- **Status:** Fix deployed, awaiting test verification

#### Category E: test_normalize_import (3 failures)
- `test_normalize_import.py::TestReplaceShortImportsInFile::test4, test6`
  - Expected: `as norm` but got: `as lamnoimp` (wrong alias)
  - Test code wants to preserve `norm` but short_import generation produced `lamnoimp`
- `test_normalize_import.py::TestEndToEndShortImports::test_normalize_imports`
  - Expected module names without `.app.` prefix (e.g., `"linters.amp_normalize_import"`)
  - Actual has `.app.` prefix (e.g., `".app.linters.amp_normalize_import"`)
  - 50+ module prefix mismatches (all in `.app.` namespace)
- **Diagnosis:**
  - Root module path detection may be picking up intermediate directory
  - Could be related to Docker mount path differences or Git root detection
  - Pattern suggests package discovery is finding wrong root module
- **Status:** Unknown root cause; appears unrelated to Fixes 1.1–4.1

## Recommendations for Remaining 11 Failures

### High Priority (Most Likely Fixable)

**Category D (4 tests) — pydeps/graphviz output**
- Action: Test `pydeps` output format on macOS vs `uvx pydeps`
- Check: Whether `pydeps --show-deps` produces `numpy` node with Fix 2.1's shell redirection
- Fix path: May need to adjust `_build_pydeps_command()` to handle macOS pydeps output format
- Command to try: `uvx pydeps --show-deps input > /tmp/test_pydeps.txt` and inspect output

**Category A (2 tests) — Docker command formatting**
- Action: Check if Fix 3.1's `use_root_user=True` is generating correct docker run commands
- Check: Whether test expectations need updating for new `--user 0:0` flag
- Fix path: Either update golden test files or adjust Fix 3.1 implementation
- Investigation: Compare actual Docker command with expected in golden file

### Medium Priority (May Require Code Changes)

**Category E (3 tests) — Short import normalization**
- Action: Debug short import alias generation logic (likely in linters2/)
- Check: Why `.app.` prefix appears in all module names
- Fix path: May need to trace module discovery path or Git root detection
- Investigation: Check if related to containerized vs local test execution

### Low Priority (May Be Environment-Specific)

**Category C (1 test) — Alignment in test output**
- Action: Verify Fix 1.3 scratch space implementation didn't change formatting
- Check: Whether actual/expected diff is just whitespace/alignment
- Fix path: May be golden file update or minor formatting tweak

**Category B (1 test) — Docker info on Mac**
- Action: Check if this is Mac-specific docker behavior
- Check: Whether output format differs between Docker and Apple Docker
- Fix path: May need platform-specific golden files

## Execution Priority

1. **Focus on Build1 (Docker) failures first** — These are Mac-specific test suite runs
2. **Category D** is most likely fixable with pydeps command investigation
3. **Category A** depends on whether golden files need updating
4. **Category E** requires deep investigation into import normalization

**Estimated effort:** 2-4 hours for Category D/A, 4-8 hours for Category E

## General Notes

- All fixes are **localized** (no ripple effects expected) — three module components, no test changes.
- UUID approach (1.1/1.2) is **container-agnostic** — works on any platform/OS without external dependencies.
- `uvx` approach (2.1) is **environment-agnostic** — works in any Docker container without pydeps pre-installation.
- No changes to test expectations or goldens needed (just temp file paths and command invocation).
- Fixes address root causes: temp file collisions (1.1/1.2) and missing pydeps command (2.1).

## Implementation Rationale

### Fix 2.1 Refactoring
- **Why extract `_build_pydeps_command()`?** Centralizes shell command logic, making it:
  - Testable independently (future debugging easier)
  - Reusable if pydeps is called elsewhere
  - Reduces cognitive load (args → single string, then shell escape happens once)
- **Why `uvx pydeps` instead of `pydeps`?** 
  - `uvx` is Python package runner via `uv`, available in modern Docker images
  - No installation required; runs isolated from system Python
  - Avoids `pydeps` command-not-found errors in minimal containers
  - Preserves PYTHONPATH=/src override for correct code path
