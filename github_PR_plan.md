# PR Split Plan for Gp_scratch_29

## Info
- **Branch**: gp_scratch_29
- **Base Branch**: origin/master
- **Dir**: /Users/saggese/src/umd_classes1/helpers_root
- **Task**: Documentation pipeline refactoring and test infrastructure updates

## Summary
- **Total changed files**: 95
- **Proposed PRs**: 4
- **Strategy**: Group changes by functional domain (documentation pipeline,
  helpers utilities, test framework)

## Proposed PRs

### PR1: Helpers Utilities & Core Fixes
- Merged: [ ]
- Complexity: Low-Medium
- Risk: Low
- Tests included: Yes
- Files:
  - `helpers/hdocker.py`
  - `helpers/hintrospection.py`
  - `helpers/hmarkdown_coloring.py`
  - `helpers/hmarkdown_toc.py`
  - `helpers/hselect_input_output.py`
  - `helpers/hsystem.py`
  - `helpers/hunit_test_utils.py`
  - `helpers/lib_tasks/lib_tasks_git.py`
  - `helpers/test/test_hmarkdown_coloring.py`
  - `helpers/test/test_hmarkdown_select.py`
  - `linters2/test/test_linter_utils.py`
- Reasoning:
  - Core utility fixes across multiple helpers modules
  - All tests included
  - Low risk, self-contained changes
  - Can merge first as foundation

### PR2: Documentation Pipeline - Core Components
- Merged: [ ]
- Complexity: High
- Risk: High (complex pipeline changes)
- Tests included: Yes
- Files:
  - `dev_scripts_helpers/documentation/notes_to_pdf.py`
  - `dev_scripts_helpers/documentation/lib_notes_to_pdf.py`
  - `dev_scripts_helpers/documentation/preprocess_notes.py`
  - `dev_scripts_helpers/documentation/open_md.py`
  - `dev_scripts_helpers/documentation/convert_pandoc_divved_fence.py`
  - `dev_scripts_helpers/documentation/pandoc.latex`
  - `dev_scripts_helpers/documentation/pandoc_touying.typ`
  - `dev_scripts_helpers/documentation/latex_abbrevs.sty`
  - `dev_scripts_helpers/documentation/typst_abbrevs.typ`
  - `dev_scripts_helpers/documentation/notes_to_pdf.README.md`
  - `dev_scripts_helpers/documentation/notes_to_pdf.README.md.figs/*`
  - `dev_scripts_helpers/documentation/generate_images.README.md`
  - `.claude/templates/github_PR_plan.template.md`
- Reasoning:
  - Core documentation pipeline refactoring
  - Notes-to-PDF converter updates with new lib extraction
  - Pandoc template and LaTeX/Typst formatting updates
  - High complexity due to pipeline interdependencies

### PR3: Documentation Tool Tests & Outcomes
- Merged: [ ]
- Complexity: Medium
- Risk: Medium (test infrastructure changes)
- Tests included: Yes
- Files:
  - `dev_scripts_helpers/documentation/generate_images.py`
  - `dev_scripts_helpers/documentation/test/test_clean_markdown.py`
  - `dev_scripts_helpers/documentation/test/test_convert_pandoc_divved_fence.py`
  - `dev_scripts_helpers/documentation/test/test_count_words.py`
  - `dev_scripts_helpers/documentation/test/test_extract_gdoc_map.py`
  - `dev_scripts_helpers/documentation/test/test_extract_from_md.py`
  - `dev_scripts_helpers/documentation/test/test_extract_toc_from_txt.py`
  - `dev_scripts_helpers/documentation/test/test_generate_images.py`
  - `dev_scripts_helpers/documentation/test/test_lib_notes_to_pdf.py`
  - `dev_scripts_helpers/documentation/test/test_notes_to_pdf.py`
  - `dev_scripts_helpers/documentation/test/test_open_md.py`
  - `dev_scripts_helpers/documentation/test/test_piper_markdown_reader.py`
  - `dev_scripts_helpers/documentation/test/test_preprocess_notes.py`
  - `dev_scripts_helpers/documentation/test/test_render_images.py`
  - `dev_scripts_helpers/documentation/test/test_replace_latex.py`
  - `dev_scripts_helpers/documentation/test/test_standardize_book_filename.py`
  - `dev_scripts_helpers/documentation/test/test_check_links.py`
  - `dev_scripts_helpers/documentation/test/test_summarize_chapters.py`
  - `dev_scripts_helpers/documentation/test/outcomes/Test__extract_columns.*`
  - `dev_scripts_helpers/documentation/test/outcomes/Test__transform_ast.*`
  - `dev_scripts_helpers/documentation/test/outcomes/Test__transform_elem.*`
  - `dev_scripts_helpers/documentation/test/outcomes/Test_end_to_end.*`
  - `dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf_typst_abbrevs.*`
  - `dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/output/outside_docker.arm64.txt`
  - `dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test3/output/outside_docker.arm64.txt`
  - `dev_scripts_helpers/documentation/test/outcomes/Test_preprocess_notes_executable1.test3/output/test.txt`
  - `dev_scripts_helpers/documentation/test/outcomes/Test_extract_toc_from_txt_script1.test*/`
  - `dev_scripts_helpers/documentation/test/outcomes/Test_preprocess_notes_end_to_end1.test1/output/test.txt`
- Reasoning:
  - Comprehensive test suite for documentation tools
  - Test outcomes reorganization and consolidation
  - Many new test files added for improved coverage
  - Can be merged after core pipeline PR
  - Depends on PR2 (core components)

### PR4: Cleanup & Temporary Files
- Merged: [ ]
- Complexity: Low
- Risk: Low
- Tests included: No
- Files:
  - `dev_scripts_helpers/coding_tools/copy_across_clients.py`
  - `dev_scripts_helpers/coding_tools/test/test_copy_across_clients.py`
  - `.claude/try_openrouter_api.py`
  - `.claude/skills/github.split_branch_in_PRs/SKILL.md` (updated)
  - `plan.fixing_unittests.md`
  - `TODO.HelpersTasl1273.Get_Mac_tests_to_pass.txt`
  - `TODO.increase_coverage.md`
  - `run_multiple_builds.sh`
  - `github_PR_plan.md`
  - **Deleted files**:
    - `.claude/skills/github.fix_failing_tests/SKILL.md`
    - `dev_scripts_helpers/documentation/generate_readme_index.py`
    - `dev_scripts_helpers/documentation/test/test_generate_readme_index.py`
    - `docs/code_guidelines/all.reading_other_people_code.how_to_guide.md`
    - `dev_scripts_helpers/documentation/test/outcomes/Test_generate_readme_index.*`
- Reasoning:
  - Miscellaneous updates and cleanup
  - Skill update for improved diff tracking
  - Removed obsolete generate_readme_index tool
  - Temporary test files and planning documents
  - Can be merged last

## Merge Order
1. **PR1** - Helpers utilities (foundation, low risk)
2. **PR2** - Documentation pipeline core (complex, but foundational)
3. **PR3** - Documentation tool tests (depends on PR2)
4. **PR4** - Cleanup & misc (last)

## Important Notes

### Test Coverage
All documentation tools have comprehensive test coverage with golden file
outcomes in `test/outcomes/`. Test outcomes have been reorganized from named
tests (e.g., `test_md1`, `test_ipynb1`) to numbered tests (e.g., `test1`,
`test2`, `test3`)

### Deleted Files
The following files have been removed:

- `generate_readme_index.py` - Tool appears to be replaced or obsoleted
- `test_generate_readme_index.py` - Corresponding test file
- `github.fix_failing_tests/SKILL.md` - Old skill, functionality moved
- `all.reading_other_people_code.how_to_guide.md` - Documentation cleanup

Verify these deletions are intentional before merging

### File Reorganizations
Several test outcome directories have been renamed and reorganized:

- `Test_extract_toc_from_txt_script1.test_md1/` → `test1/`
- `Test_extract_toc_from_txt_script1.test_tex1/` → `test2/`
- `Test_extract_toc_from_txt_script1.test_txt1/` → `test3/`
- `Test_extract_toc_from_txt_script1.test_ipynb1/` → `test4/`
- `Test_extract_toc_from_txt_script1.test_md_with_counts/` → `test5/`

This aligns test naming with project conventions (test1, test2, etc.)
