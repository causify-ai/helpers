# PR Split Plan for HelpersTask1273_Get_Mac_tests_to_pass

## Info
- **Branch**: HelpersTask1273_Get_Mac_tests_to_pass
- **Base Branch**: master
- **Dir**: /Users/saggese/src/csfy1/helpers_root
- **Task**: Fix macOS test failures
- **Total PRs**: 8 (2 dependent, 6 independent)

## Proposed PRs

### PR1: Docker Utilities Fix (hdocker, Hlatex)
- **Merged**: [ ]
- **Complexity**: Low-Medium
- **Risk**: Low
- **Tests included**: Yes
- **Dependencies**: None
- **Blocks**: None

**Files**:

- `helpers/hdocker.py`
- `helpers/test/test_hdocker.py`
- `helpers/hlatex.py`
- `helpers/test/test_hlatex.py`

**Reasoning**:

- Independent utility fixes for Docker and LaTeX integration on macOS
- Changes fix DinD (Docker-in-Docker) detection and LaTeX handling
- Changes are self-contained and testable
- Low risk as these are isolated utility modules

**Test Command**:
```bash
pytest helpers/test/test_hdocker.py helpers/test/test_hlatex.py -v
```

### PR2: Unit Test Infrastructure (purification, Introspection, Numpy, Base)
- **Merged**: [ ]
- **Complexity**: Medium
- **Risk**: Medium (affects test infrastructure)
- **Tests included**: Yes
- **Dependencies**: None
- **Blocks**: None

**Files**:

- `helpers/hunit_test_purification.py`
- `helpers/test/test_hunit_test_purification.py`
- `helpers/test/test_hintrospection.py`
- `helpers/test/test_hnumpy.py`
- `helpers/test/test_hunit_test.py`

**Reasoning**:

- Adds new test purification module and updates test infrastructure
- All changes are related to test utilities and improvements
- Medium risk as it affects test infrastructure used across codebase
- Well-isolated changes to testing subsystem

**Test Command**:
```bash
pytest helpers/test/test_hunit_test_purification.py helpers/test/test_hintrospection.py helpers/test/test_hnumpy.py helpers/test/test_hunit_test.py -v
```

### PR3: Import Checking Utilities
- **Merged**: [ ]
- **Complexity**: Low-Medium
- **Risk**: Low-Medium
- **Tests included**: Yes
- **Dependencies**: None
- **Blocks**: None

**Files**:

- `import_check/show_imports.py`
- `import_check/test/test_show_imports.py`
- `import_check/test/test_detect_import_cycles.py`
- `import_check/test/outcomes/Test_show_imports.*` (test golden files)

**Reasoning**:

- Improvements to import cycle detection and display
- Self-contained module with all related tests included
- Fixes import checking on macOS
- Low-medium risk as it's isolated to import tooling

**Test Command**:
```bash
pytest import_check/test/test_show_imports.py import_check/test/test_detect_import_cycles.py -v
```

### PR4: Remove Deprecated Normalize_import Linter ⚠️ BREAKING
- **Merged**: [ ]
- **Complexity**: High
- **Risk**: Medium-High (breaking change, large deletion)
- **Tests included**: Yes (removal only)
- **Dependencies**: None
- **Blocks**: PR5 (must merge before PR5)

**Files**:

- `linters/amp_normalize_import.py` (DELETED)
- `linters/test/test_amp_normalize_import.py` (DELETED)
- `linters/base.py` (refactored to remove normalize_imports references)
- `linters/test/outcomes/TestEndToEndShortImports.test_normalize_imports/`
  (outcome updated)

**Reasoning**:

- Large, focused deletion of deprecated linter no longer needed
- Must come BEFORE PR5 since PR5 references the removal
- Clear scope: removing one complete linter module and its tests
- Breaking change but necessary cleanup
- Migration impact: users relying on `amp_normalize_import` should use
  `amp_isort` or `amp_black`

**Migration Notes**:

- `amp_normalize_import` linter is removed from the system
- Use `amp_isort` or `amp_black` for import normalization instead
- Update any automation/CI that called this linter

**Test Command**:
```bash
pytest linters/test/ -v -k "not slow and not superslow"
```

### PR5: Linter Test Suite Updates ⚠️ DEPENDS ON PR4
- **Merged**: [ ]
- **Complexity**: High
- **Risk**: Medium
- **Tests included**: Yes
- **Dependencies**: PR4 (amp_normalize_import removal)
- **Blocks**: None

**Files**:

- `linters/base.py` (additional cleanup from PR4 removal)
- `linters/test/test_amp_dev_scripts.py`
- `linters/test/test_amp_check_md_toc_headers.py`
- Various test outcome files

**Reasoning**:

- Depends on PR4 (amp_normalize_import removal)
- Updates tests affected by linter refactoring
- Removes or updates superslow tests that were failing on macOS
- Consolidates linter test infrastructure
- MUST be merged after PR4 to avoid test failures

**Test Command**:
```bash
pytest linters/test/test_amp_dev_scripts.py linters/test/test_amp_check_md_toc_headers.py -v
```

### PR6: Docker Script Library Updates
- **Merged**: [ ]
- **Complexity**: Low
- **Risk**: Low
- **Tests included**: No
- **Dependencies**: None
- **Blocks**: None

**Files**:

- `dev_scripts_helpers/dockerize/lib_graphviz.py`
- `dev_scripts_helpers/dockerize/lib_latex.py`
- `dev_scripts_helpers/dockerize/lib_markdown_toc.py`
- `dev_scripts_helpers/dockerize/lib_mermaid.py`
- `dev_scripts_helpers/dockerize/lib_pandoc.py`
- `dev_scripts_helpers/dockerize/lib_plantum.py`
- `dev_scripts_helpers/dockerize/lib_png.py`
- `dev_scripts_helpers/dockerize/lib_prettier.py`
- `dev_scripts_helpers/dockerize/lib_svg.py`
- `dev_scripts_helpers/dockerize/lib_typst.py`

**Reasoning**:

- Very minor isolated changes to Docker containerization libraries
- All changes are consistent across `lib_*.py` files (minor fixes)
- No tests affected by these changes
- Can be reviewed and merged independently
- Low risk as changes are minimal and localized

**Test Command**: N/A (no tests)

### PR7: Git Utilities and LLM Script Updates
- **Merged**: [ ]
- **Complexity**: Low
- **Risk**: Low
- **Tests included**: No
- **Dependencies**: None
- **Blocks**: None

**Files**:

- `dev_scripts_helpers/git/gs`
- `dev_scripts_helpers/git/gss`
- `dev_scripts_helpers/llms/llm_transform.py`

**Reasoning**:

- Small isolated fixes to development utilities
- `gs`/`gss`: Git helper scripts updates
- `llm_transform.py`: LLM transformation utility updates
- No tests affected, independent changes
- Low risk as changes are to utility scripts

**Test Command**: N/A (no tests)

### PR8: Documentation and Test Outcome Updates
- **Merged**: [ ]
- **Complexity**: Low
- **Risk**: Very Low
- **Tests included**: No
- **Dependencies**: None (should come after PR1-PR7)
- **Blocks**: None

**Files**:

- `.claude/settings.local.json`
- `docs/tools/all.invoke_workflows.how_to_guide.md`
- `docs/tools/linter/all.developing_linter.how_to_guide.md`
- `.claude/skills/github.split_branch_in_PRs/SKILL.md`
- `helpers/test/outcomes/Test_check_string_debug1.test1/output/test.txt`

**Reasoning**:

- Documentation updates and test golden file updates
- Mechanical updates that reflect changes in earlier PRs
- Can be merged last as they're dependent on earlier PRs
- Very low risk as these are documentation/outcome files

**Test Command**: N/A (documentation only)

## Merge Order

### Sequential Dependencies
1. **First**: PR4 (Remove normalize_imports linter)
2. **Second**: PR5 (Linter test updates) - DEPENDS ON PR4

### Can Merge in Parallel (Independent)
- PR1: Docker utilities
- PR2: Unit test infrastructure
- PR3: Import checking
- PR6: Docker script libraries
- PR7: Git/LLM utilities
- PR8: Documentation (best after others)

### Recommended Merge Sequence
1. PR1 (Docker utilities)
2. PR2 (Unit test infrastructure)
3. PR3 (Import checking)
4. PR4 (Remove normalize_imports) - BREAKING
5. PR5 (Linter tests) - DEPENDS ON PR4
6. PR6 (Docker script libraries)
7. PR7 (Git/LLM utilities)
8. PR8 (Documentation updates)

## Pre-PR Cleanup

### Files to Remove (Build Artifacts and Temporary Files)
These should be deleted before creating any PRs:
```bash
git rm --cached build1.txt build2.txt build3.txt
git rm --cached HelpersTask1273_report.md
git rm --cached TODO.HelpersTasl1273.Get_Mac_tests_to_pass.txt
git rm --cached run.sh
git commit -m "Clean up build artifacts and temporary files"
```

**Files affected**:

- `build1.txt` (637 lines) - Docker build output
- `build2.txt` (1078 lines) - Docker build output
- `build3.txt` (5547 lines) - Docker build output
- `HelpersTask1273_report.md` (empty file) - Report artifact
- `TODO.HelpersTasl1273.Get_Mac_tests_to_pass.txt` (task tracking)
- `run.sh` - Script artifact

These are temporary files created during development and should not be
committed

## Risk Assessment Summary
| PR  | Complexity | Risk     | Impact              |
| --- | ---------- | -------- | ------------------- |
| PR1 | Med        | Low      | Isolated utilities  |
| PR2 | Med        | Med      | Test infrastructure |
| PR3 | Med        | Low      | Import tooling      |
| PR4 | High       | Med-High | Breaking change     |
| PR5 | High       | Med      | Depends on PR4      |
| PR6 | Low        | Low      | Docker libraries    |
| PR7 | Low        | Low      | Dev utilities       |
| PR8 | Low        | V.Low    | Documentation       |

**Overall Risk**: Medium (mainly from PR4 breaking change and PR5 dependency)

## Testing Strategy
1. **Fast tests first**: Run PR1, PR2, PR3, PR6, PR7 tests in parallel
2. **Sequential critical path**: PR4 → PR5 (must maintain order)
3. **Documentation last**: PR8 has no executable impact
4. **Verify on macOS**: All changes target macOS test compatibility

All test commands use `-v` flag for verbose output and are Python pytest
commands
