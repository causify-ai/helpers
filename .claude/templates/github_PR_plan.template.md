# PR Split Plan for HelpersTask1273_Get_Mac_tests_to_pass

## Info
- **Branch**: HelpersTask1273_Get_Mac_tests_to_pass
- **Base Branch**: master
- **Dir**: /Users/saggese/src/csfy1/helpers_root
- **Task**: Fix macOS test failures

## Proposed PRs

### [ ] PR1: Docker utilities fix (hdocker, hlatex)

**Complexity**: Low-Medium  
**Risk**: Low  
**Tests included**: Yes

**Files**:
- `helpers/hdocker.py`
- `helpers/test/test_hdocker.py`
- `helpers/hlatex.py`
- `helpers/test/test_hlatex.py`

**Reasoning**: These changes are independent utility fixes for Docker and LaTeX integration on macOS. Changes are self-contained and testable.

### [ ] PR2: Unit test purification and introspection utilities

**Complexity**: Medium  
**Risk**: Medium (affects test infrastructure)  
**Tests included**: Yes

**Files**:
- `helpers/hunit_test_purification.py` - Core refactoring of test output purification logic
- `helpers/test/test_hunit_test_purification.py` - Comprehensive test updates
- `helpers/test/test_hintrospection.py` - Related test updates
- `helpers/test/test_hnumpy.py` - Related test updates
- `helpers/test/test_hunit_test.py` - Related test updates

**Reasoning**: These changes refactor test infrastructure used across the codebase. Grouped together because they're all related to test utilities and have been updated together. Moderate complexity due to test infrastructure changes but well-isolated.

### [ ] PR3: Import checking utilities improvements

**Complexity**: Low-Medium  
**Risk**: Low-Medium  
**Tests included**: Yes

**Files**:
- `import_check/show_imports.py` - Enhanced output formatting
- `import_check/test/test_show_imports.py` - Updated tests
- `import_check/test/test_detect_import_cycles.py` - Updated tests
- `import_check/test/outcomes/Test_show_imports.*` - Test golden files

**Reasoning**: Changes to import cycle detection and display. Self-contained module with all tests included. These changes fix import checking on macOS.

### [ ] PR4: Remove deprecated normalize_import linter (BREAKING)

**Complexity**: High  
**Risk**: Medium-High (breaking change, large deletion)  
**Tests included**: Yes (removals)

**Files**:
- `linters/amp_normalize_import.py` - DELETED (~1100 lines)
- `linters/test/test_amp_normalize_import.py` - DELETED (~1600 lines)
- `linters/base.py` - Removed import and reference to amp_normalize_import
- `linters/test/outcomes/TestEndToEndShortImports.*` - Removed test golden files

**Reasoning**: 
- Large, focused deletion of deprecated linter
- Must come BEFORE PR5 since test updates depend on this
- Clear scope: removing one linter module entirely
- Tests are also removed (no test updates needed)
- This is a breaking change but necessary cleanup

**Migration Notes**: 
- `amp_normalize_import` linter is removed from the system
- Use `amp_isort` or `amp_black` for import normalization instead
- Update any automation that called this linter

---

### [ ] PR5: Linter test suite updates (after normalize_import removal)

**Complexity**: High  
**Risk**: Medium  
**Tests included**: Yes

**Files**:
- `linters/base.py` - Minor import cleanup (already in PR4)
- `linters/test/test_amp_dev_scripts.py` - Removed superslow tests and updated test framework calls
- `linters/test/test_amp_check_md_toc_headers.py` - Minor updates

**Reasoning**:
- Depends on PR4 (amp_normalize_import removal)
- Updates tests that were affected by linter refactoring
- Removes superslow tests that are failing on macOS (replaced by faster alternatives)
- Consolidates linter test infrastructure

**Dependencies**: Must follow PR4

---

### [ ] PR6: Docker script library updates

**Complexity**: Low  
**Risk**: Low  
**Tests included**: No

**Files**:
- `dev_scripts_helpers/dockerize/lib_graphviz.py` - Minor change (+1 line)
- `dev_scripts_helpers/dockerize/lib_latex.py` - Minor change (+1 line)
- `dev_scripts_helpers/dockerize/lib_markdown_toc.py` - Minor change (+1 line)
- `dev_scripts_helpers/dockerize/lib_mermaid.py` - Minor change (+1 line)
- `dev_scripts_helpers/dockerize/lib_pandoc.py` - Minor change (+1 line)
- `dev_scripts_helpers/dockerize/lib_plantum.py` - Minor change (+1 line)
- `dev_scripts_helpers/dockerize/lib_png.py` - Minor change (+2 lines)
- `dev_scripts_helpers/dockerize/lib_prettier.py` - Changes (+10 lines, -0 lines)
- `dev_scripts_helpers/dockerize/lib_svg.py` - Minor change (+2 lines)
- `dev_scripts_helpers/dockerize/lib_typst.py` - Minor change (+1 line)

**Reasoning**: Very minor isolated changes to Docker containerization libraries. All changes are consistent across lib_*.py files (likely adding a missing import or fixing a path). Can be reviewed and merged independently.

### [ ] PR7: Git utilities and LLM script updates

**Complexity**: Low  
**Risk**: Low  
**Tests included**: No

**Files**:
- `dev_scripts_helpers/git/gs` - Updates (+7 lines, -0 lines)
- `dev_scripts_helpers/git/gss` - Updates (+6 lines, -0 lines)
- `dev_scripts_helpers/llms/llm_transform.py` - Updates (+3 lines)

**Reasoning**: Small isolated fixes to development utilities. gs/gss are Git helper scripts and llm_transform handles LLM transformations. No tests affected, independent changes.

### [ ] PR8: Documentation and test outcome updates

**Complexity**: Low  
**Risk**: Very Low  
**Tests included**: No

**Files**:
- `.claude/settings.local.json` - Configuration update
- `docs/tools/all.invoke_workflows.how_to_guide.md` - Documentation fix
- `docs/tools/linter/all.developing_linter.how_to_guide.md` - Documentation update (removal of deprecated linter reference)
- `helpers/test/outcomes/Test_check_string_debug1.test1/output/test.txt` - Test golden file update
- `.claude/skills/github.split_branch_in_PRs/SKILL.md` - Added (NEW FILE)

**Reasoning**: Documentation updates and test golden file updates. These are mechanical updates that reflect changes in earlier PRs. Can be merged last.

## Important Notes

### Files NOT Included in Any PR (should be removed before commit)

These files are build artifacts and temporary outputs that should NOT be committed:
- `build1.txt` (637 lines) - Docker build output
- `build2.txt` (1078 lines) - Docker build output  
- `build3.txt` (5547 lines) - Docker build output
- `HelpersTask1273_report.md` (empty file)
- `TODO.HelpersTasl1273.Get_Mac_tests_to_pass.txt` (task tracking file)

**Action Required**: These should be removed from git before any PRs are created:
```bash
git rm --cached build*.txt HelpersTask1273_report.md TODO.HelpersTasl1273.Get_Mac_tests_to_pass.txt
```
