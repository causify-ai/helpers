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

**Reasoning**:
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

**Reasoning**:
- Refactors test infrastructure used across the codebase
- Grouped together because they're all related to test utilities and have been updated together
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

**Reasoning**:
- Changes to import cycle detection and display
- Self-contained module with all tests included
- Fixes import checking on macOS

### PR4: Remove Deprecated Normalize_import Linter (BREAKING)
- Merged: [ ]
- Complexity: High
- Risk: Medium-High (breaking change, large deletion)
- Tests included: Yes (removals)
- Files:
  - `linters/amp_normalize_import.py`
  - `linters/test/test_amp_normalize_import.py`
  - `linters/base.py`
  - `linters/test/outcomes/TestEndToEndShortImports.*`

**Reasoning**:
- Large, focused deletion of deprecated linter
- Must come BEFORE PR5 since test updates depend on this
- Clear scope: removing one linter module entirely
- Tests are also removed (no test updates needed)
- Breaking change but necessary cleanup
- Migration notes:
  - `amp_normalize_import` linter is removed from the system
  - Use `amp_isort` or `amp_black` for import normalization instead
  - Update any automation that called this linter

### PR5: Linter Test Suite Updates (after Normalize_import Removal)
- Merged: [ ]
- Complexity: High
- Risk: Medium
- Tests included: Yes
- Files:
  - `linters/base.py`
  - `linters/test/test_amp_dev_scripts.py`
  - `linters/test/test_amp_check_md_toc_headers.py`

**Reasoning**:
- Depends on PR4 (amp_normalize_import removal)
- Updates tests that were affected by linter refactoring
- Removes superslow tests that are failing on macOS (replaced by faster alternatives)
- Consolidates linter test infrastructure
- Dependencies: Must follow PR4

### PR6: Docker Script Library Updates
- Merged: [ ]
- Complexity: Low
- Risk: Low
- Tests included: No
- Files:
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
- All changes are consistent across `lib_*.py` files (likely adding a missing import or fixing a path)
- Can be reviewed and merged independently

### PR7: Git Utilities and LLM Script Updates
- Merged: [ ]
- Complexity: Low
- Risk: Low
- Tests included: No
- Files:
  - `dev_scripts_helpers/git/gs`
  - `dev_scripts_helpers/git/gss`
  - `dev_scripts_helpers/llms/llm_transform.py`

**Reasoning**:
- Small isolated fixes to development utilities
- `gs`/`gss`: Git helper scripts; `llm_transform`: handles LLM transformations
- No tests affected, independent changes

### PR8: Documentation and Test Outcome Updates
- Merged: [ ]
- Complexity: Low
- Risk: Very Low
- Tests included: No
- Files:
  - `.claude/settings.local.json`
  - `docs/tools/all.invoke_workflows.how_to_guide.md`
  - `docs/tools/linter/all.developing_linter.how_to_guide.md`
  - `helpers/test/outcomes/Test_check_string_debug1.test1/output/test.txt`
  - `.claude/skills/github.split_branch_in_PRs/SKILL.md`

**Reasoning**:
- Documentation updates and test golden file updates
- Mechanical updates that reflect changes in earlier PRs
- Can be merged last

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
