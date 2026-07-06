# Unit Test Failure Analysis & Fix Plan

## Summary
- **Total failures**: 76
- **Total passed**: 3233
- **Tests skipped**: 182
- **CI run time**: 4942.36s (1:22:22)

## Failure Categories

### Group 1: TextPurifier class removed from helpers.hunit_test_purification module
**Status**: ✅ FIXED
**Count**: ~36 tests
**Tests affected**:
- dev_scripts_helpers/documentation/test/test_lib_notes_to_pdf.py::Test_preprocess_notes::test1
- dev_scripts_helpers/documentation/test/test_lib_notes_to_pdf.py::Test_render_images::test1
- dev_scripts_helpers/documentation/test/test_lib_notes_to_pdf.py::Test_run_pandoc_to_pdf::test1,test2,test3
- dev_scripts_helpers/documentation/test/test_lib_notes_to_pdf.py::Test_run_pandoc_to_html::test1,test2,test3
- dev_scripts_helpers/documentation/test/test_lib_notes_to_pdf.py::Test_run_pandoc_to_slides::test1,test2
- dev_scripts_helpers/documentation/test/test_lib_notes_to_pdf.py::Test_run_pandoc_to_typst_slides::test1,test2,test3
- dev_scripts_helpers/documentation/test/test_lib_notes_to_pdf.py::Test_copy_to_output::test1
- dev_scripts_helpers/documentation/test/test_lib_notes_to_pdf.py::Test_copy_to_gdrive::test1
- dev_scripts_helpers/documentation/test/test_lib_notes_to_pdf.py::Test_compress_pdf::test1
- dev_scripts_helpers/documentation/test/test_notes_to_pdf.py (multiple test classes)

**Root cause**: 
- The `TextPurifier` class was removed from `helpers/hunit_test_purification.py`
- The module now only exports functions like `purify_txt_from_client()`, not a class
- Tests still try to instantiate `TextPurifier()` and call `.purify_txt_from_client()`

**Error message**:
```
AttributeError: module 'helpers.hunit_test_purification' has no attribute 'TextPurifier'
```

**Fix applied**:
- Replaced all 8 occurrences of `huntepur.TextPurifier().purify_txt_from_client()` 
  with `huntepur.purify_txt_from_client()` in:
  - `dev_scripts_helpers/documentation/test/test_lib_notes_to_pdf.py` (8 replacements)
  - test_notes_to_pdf.py had no TextPurifier usage (failures are from other causes)

### Group 2: _build_pandoc_cmd function renamed to _build_pandoc_latex_cmd
**Status**: ✅ FIXED
**Count**: ~4 tests
**Tests affected**:
- dev_scripts_helpers/documentation/test/test_lib_notes_to_pdf.py::Test_build_pandoc_cmd::test1,test2,test3,test4

**Root cause**:
- Function `_build_pandoc_cmd()` in `dev_scripts_helpers/documentation/lib_notes_to_pdf.py` was renamed to `_build_pandoc_latex_cmd()`
- Tests still reference the old function name

**Error message**:
```
AttributeError: module 'dev_scripts_helpers.documentation.lib_notes_to_pdf' has no attribute '_build_pandoc_cmd'. Did you mean: '_build_pandoc_latex_cmd'?
```

**Fix applied**:
- Updated `dev_scripts_helpers/documentation/test/test_lib_notes_to_pdf.py`:
  - Replaced function call: `dshdlntpd._build_pandoc_cmd` → `dshdlntpd._build_pandoc_latex_cmd`
  - Updated class docstring reference
  - Updated helper method docstring reference

### Group 3: _run_linting_actions function renamed to _run_common_linting_actions
**Count**: ~5 tests
**Tests affected**:
- linters2/test/test_lint.py::Test_run_linting_actions::test1,test2,test3,test4,test5
- linters2/test/test_lint.py::Test_lint_python_files::test1,test2
- linters2/test/test_lint.py::Test_lint_jupyter_files::test1,test2

**Root cause**:
- Function `_run_linting_actions()` in `linters2/lint.py` was renamed to `_run_common_linting_actions()`
- Tests still reference the old function name

**Error message**:
```
AttributeError: module 'linters2.lint' has no attribute '_run_linting_actions'. Did you mean: '_run_common_linting_actions'?
```

**Potential fix**:
- Update `linters2/test/test_lint.py`
  - Replace `lilint._run_linting_actions` with `lilint._run_common_linting_actions`

### Group 4: Other assertion/logic failures
**Count**: ~31 tests
**Sample failures**:
- helpers/test/test_hmarkdown_select.py failures (markdown header extraction issues)
- helpers/test/test_hpandas_io.py failures (S3 data access issues)
- linters2/test/test_lint.py failures (None type assertions)
- dev_scripts_helpers/documentation/test/test_notes_to_pdf.py (various assertion failures)
- dev_scripts_helpers/documentation/test/test_extract_toc_from_txt.py (markdown header extraction)

**Root cause**: 
- These appear to be actual logic failures, not simple import/reference issues
- Many relate to function return values being None when list is expected
- Some relate to S3 path validation failures
- Markdown parsing logic changes

## Complexity Ranking

| Complexity | Count | Issues |
|-----------|-------|--------|
| Low | ~4 | Group 2: _build_pandoc_cmd rename - simple string replacement in one file |
| Low | ~5 | Group 3: _run_linting_actions rename - simple string replacement in one file |
| Medium | ~36 | Group 1: TextPurifier class removal - simple refactor in 2 files, ~40+ replacements |
| High | ~31 | Group 4: Logic failures - requires investigation and actual code fixes |

## Next Steps
1. **Immediate fixes (Low complexity)**: Fix Groups 2 & 3 (rename issues)
2. **Medium complexity fix**: Fix Group 1 (TextPurifier usage)
3. **Investigation needed**: Analyze Group 4 failures to understand underlying logic changes
