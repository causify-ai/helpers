# PR Split Plan for HelpersTask1273_Get_Mac_tests_to_pass

## Info
- **Branch**: HelpersTask1273_Get_Mac_tests_to_pass
- **Base Branch**: master
- **Dir**: /Users/saggese/src/csfy1/helpers_root
- **Task**: Fix macOS test failures
- **Total PRs**: 8 (4 merged, 4 remaining)
- **Last Updated**: 2026-07-08

## Current Status Summary

**Progress**: 4 of 8 PRs merged, 4 ready for review/merge

**Merged PRs** (now in master):
- PR2 (#1277): Unit test infrastructure improvements
- PR3 (#1280): Import checking infrastructure
- PR4 (#1281): Remove obsolete amp_normalize_import linter (breaking change)
- PR5 (#1282): Linter test suite updates (depended on PR4)

**Next Steps** (4 independent PRs ready):
1. Create and merge PR1 (Docker utilities - hdocker, hlatex)
2. Create and merge PR6 (Docker script library updates)
3. Create and merge PR7 (Git utilities and LLM script updates)
4. Create and merge PR8 (Documentation and test outcome updates)
5. Clean up temporary files before final merge

**Key Notes**:
- All critical, blocking changes are complete
- Remaining 4 PRs have no dependencies on each other
- All can be merged in parallel or sequence
- Temporary build/report files should be cleaned up

## Proposed PRs

### PR1: Docker Utilities Fix (hdocker, Hlatex)
- **Merged**: [ ] (Ready)
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
- **Merged**: [x] (#1277)
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

### PR3: Import Checking Infrastructure
- **Merged**: [x] (#1280)
- **Complexity**: Medium
- **Risk**: Low
- **Tests included**: Yes
- **Dependencies**: None
- **Blocks**: PR4, PR5

**Reasoning**:
- Import checking and validation infrastructure improvements
- Independent changes to support better import tooling
- Well-isolated changes to development utilities

### PR4: Remove normalize_imports Linter ⚠️ BREAKING
- **Merged**: [x] (#1281)
- **Complexity**: High
- **Risk**: Medium-High (breaking change)
- **Tests included**: Yes
- **Dependencies**: PR3 (for context)
- **Blocks**: PR5

**Reasoning**:
- Removes obsolete amp_normalize_import linter
- Breaking change to linter infrastructure
- Requires downstream test updates (handled in PR5)
- Must be coordinated with PR5 merge

### PR5: Linter Test Suite Updates ⚠️ DEPENDS ON PR4
- **Merged**: [x] (#1282)
- **Complexity**: High
- **Risk**: Medium
- **Tests included**: Yes
- **Dependencies**: PR4 (amp_normalize_import removal) - SATISFIED
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
- **Merged**: [ ] (Ready)
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
- **Merged**: [ ] (Ready)
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
- **Merged**: [ ] (Ready)
- **Complexity**: Low
- **Risk**: Very Low
- **Tests included**: No
- **Dependencies**: None (should come after PR1-PR7)
- **Blocks**: None

**Files**:

- `.claude/settings.local.json`
- `.claude/skills/github.split_branch_in_PRs/SKILL.md`
- `helpers/test/outcomes/Test_check_string_debug1.test1/output/test.txt`
- `docs/tools/all.invoke_workflows.how_to_guide.md`
- `docs/tools/linter/all.developing_linter.how_to_guide.md`

**Reasoning**:

- Documentation updates and test golden file updates
- Mechanical updates that reflect changes in earlier PRs
- Can be merged last as they're dependent on earlier PRs
- Very low risk as these are documentation/outcome files

**Test Command**: N/A (documentation only)

## Merge Order

### Status Summary (as of 2026-07-08)

**Already Merged into master**:
- PR2 (#1277): Unit test infrastructure ✓
- PR3 (#1280): Import checking ✓
- PR4 (#1281): Remove normalize_imports linter ✓
- PR5 (#1282): Linter test updates ✓

**Remaining to Merge**:
- PR1: Docker utilities - READY
- PR6: Docker script libraries - READY
- PR7: Git/LLM utilities - READY
- PR8: Documentation updates - READY

### Recommended Merge Sequence for Remaining PRs
Can merge in any order (all independent):
1. PR1 (Docker utilities)
2. PR6 (Docker script libraries)
3. PR7 (Git/LLM utilities)
4. PR8 (Documentation updates)

All remaining PRs are ready and have no dependencies.

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

| PR  | Status   | Complexity | Risk     | Impact              |
| --- | -------- | ---------- | -------- | ------------------- |
| PR1 | Ready    | Med        | Low      | Isolated utilities  |
| PR2 | ✓ Merged | Med        | Med      | Test infrastructure |
| PR3 | ✓ Merged | Med        | Low      | Import tooling      |
| PR4 | ✓ Merged | High       | Med-High | Breaking change     |
| PR5 | ✓ Merged | High       | Med      | Depends on PR4      |
| PR6 | Ready    | Low        | Low      | Docker libraries    |
| PR7 | Ready    | Low        | Low      | Dev utilities       |
| PR8 | Ready    | Low        | V.Low    | Documentation       |

**Overall Risk**: Low (all critical/blocking PRs merged, remaining PRs are independent)

## Testing Strategy
1. **Remaining PRs can merge in parallel**: No dependencies between PR1, PR6, PR7, PR8
2. **Tests for remaining PRs**:
   - PR1: `pytest helpers/test/test_hdocker.py helpers/test/test_hlatex.py -v`
   - PR6: No tests
   - PR7: No tests
   - PR8: No tests (documentation)
3. **Documentation**: PR8 has no executable impact
4. **Verify on macOS**: All changes target macOS test compatibility

All test commands use `-v` flag for verbose output and are Python pytest commands
