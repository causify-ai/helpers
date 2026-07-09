# PR Split Plan for HelpersTask1273_Get_Mac_tests_to_pass

## Info
- **Branch**: gp_scratch
- **Base Branch**: master
- **Dir**: /Users/saggese/src/umd_classes1/helpers_root
- **Task**: Fix macOS test failures (HelpersTask1273_Get_Mac_tests_to_pass)
- **Last Updated**: 2026-07-09 (after master merge on 2026-06-08)

## Status Summary

**Current State**: All 5 PRs pending submission. Master was merged into gp_scratch on 2026-06-08 with no conflicts.
- PR1 (Config/Docs): Ready to create
- PR2-PR5 (Core work): Depend on PR1 merge

**Next Steps**: Create and merge PR1, then proceed with PR2-PR5 in order per the merge dependency chain below.

## Proposed PRs

### PR1: Configuration & Documentation Updates
- Status: Not Started
- Merged: [ ]
- Complexity: Very Low
- Risk: Very Low
- Tests included: No (documentation/config only)
- Files:
  - `.claude/skills/`
  - `.claude/templates/`
  - `.claude/notify.sh`
  - `.claude/settings.local.json`

- Reasoning:
  - Pure configuration and documentation updates with no runtime code changes
  - No test dependencies or execution required
  - Low risk, enables visual inspection of skill/template improvements
  - Can merge independently first without blocking other PRs

### PR2: Helper Module Core Refactors
- Status: Blocked (waiting for PR1)
- Merged: [ ]
- Complexity: Low
- Risk: Low
- Tests included: Yes
- Files:
  - `helpers/hunit_test_purification.py`
  - `helpers/hsystem.py`
  - `helpers/hmarkdown_toc.py`
  - `helpers/hselect_input_output.py`
  - `helpers/hmarkdown_coloring.py`
  - `helpers/hjunit_reporter.py`
  - `helpers/hintrospection.py`
  - `helpers/hdocker.py`
  - `helpers/hlatex.py`
  - `helpers/hpytest.py`
  - `helpers/hunit_test_utils.py`
  - `helpers/lib_tasks/lib_tasks_pytest.py`
  - `helpers/lib_tasks/lib_tasks_git.py`
  - `helpers/README.md`
  - Test files: test_hunit_test_purification.py, test_hunit_test.py,
    test_hmarkdown_coloring.py, test_hmarkdown_select.py, test_hnumpy.py,
    test_hpytest.py, test_hintrospection.py, test_hdocker.py,
    test_hjunit_reporter.py
  - Test outcomes

- Test command:
  ```bash
  invoke docker_cmd --cmd "pytest helpers/test/ -v"
  ```

- Reasoning:
  - Foundation module refactors used by downstream code
  - Well-tested and isolated to helpers/ directory
  - Changes are well-contained with matching test files
  - Necessary before PR3, PR4, PR5 work correctly (esp. TextPurifier removal)
  - Low complexity: straightforward function refactors and logic improvements

### PR3: Linter Module Updates
- Status: Blocked (waiting for PR2)
- Merged: [ ]
- Complexity: Low
- Risk: Low
- Tests included: Yes
- Files:
  - `linters/base.py`
  - `linters/test/conftest.py`
  - `linters2/lint.py`
  - `linters2/lint_cc.py`
  - `linters2/normalize_import.py`
  - `import_check/show_imports.py`
  - Test files: test_amp_check_md_toc_headers.py, test_amp_dev_scripts.py,
    test_lint.py, test_detect_import_cycles.py, test_show_imports.py
  - Test outcomes

- Test command:
  ```bash
  invoke docker_cmd --cmd "pytest linters/test/ linters2/test/ import_check/test/ -v"
  ```

- Reasoning:
  - Isolated domain with no external dependencies beyond helpers (PR2)
  - Self-contained in linters/ and import_check/ modules
  - Function rename (\_run_linting_actions) is straightforward refactor
  - All tests included in same PR as source changes
  - Can merge independently after PR2

### PR4: Development Scripts - Utilities & Tools
- Status: Blocked (waiting for PR2)
- Merged: [ ]
- Complexity: Low
- Risk: Low
- Tests included: Partial
- Files:
  - `dev_scripts_helpers/ai/cc`
  - `dev_scripts_helpers/coding_tools/`
  - `dev_scripts_helpers/dockerize/`
  - `dev_scripts_helpers/llms/`
  - `dev_scripts_helpers/git/`
  - `dev_scripts_helpers/misc/capture_last_cmd.sh`
  - `dev_scripts_helpers/scraping/download_link_articles.py`
  - `dev_scripts_helpers/system_tools/`
  - `dev_scripts_helpers/testing/`
  - `dev_scripts_helpers/thin_client/thin_client_utils.sh`
  - `dev_scripts_helpers/README.md`
  - Build/automation
  - Documentation
  - Other

- Test command:
  ```bash
  invoke docker_cmd --cmd "pytest dev_scripts_helpers/llms/test/ -v"
  # Manual: bash -n dev_scripts_helpers/testing/pytest_failed.py
  # Manual: bash -n dev_scripts_helpers/git/git_sync_between_branches.sh
  ```

- Reasoning:
  - Utility scripts and automation updates
  - Low risk: does not affect core library or main test suite
  - Improvements to CI/build infrastructure and developer tools
  - Can merge independently after PR1-2
  - Limited test coverage (mainly LLM module) but scripts are syntactically
    valid

### PR5: Documentation Tools Refactor
- Status: Blocked (waiting for PR2)
- Merged: [ ]
- Complexity: Medium-High
- Risk: Medium
- Tests included: Yes
- Files:
  - Core tools
  - Test files
  - Test outcomes

- Test command:
  ```bash
  invoke docker_cmd --cmd "pytest dev_scripts_helpers/documentation/test/ -v"
  ```

- Reasoning:
  - Largest single change group (68 files) but well-contained in
    dev_scripts_helpers/documentation/
  - Depends on PR2 (helpers) for TextPurifier refactor and markdown logic
  - Function renames (\_build_pandoc_cmd → \_build_pandoc_latex_cmd) require
    test updates
  - Comprehensive test coverage with extensive golden file updates
  - Medium complexity due to size and test outcome validation required
  - All related tests grouped in same PR

## Merge Order & Dependencies
1. **PR1** (Config) → No dependencies, merge first
2. **PR2** (Helpers) → Foundation for PR3, PR4, PR5
3. **PR3** (Linters) → Depends on PR2, independent of others
4. **PR4** (DevScripts) → Depends on PR2, independent of others
5. **PR5** (Docs) → Depends on PR2, largest group, highest risk
