# Test Failure Analysis and Fix Plan

## [ ] Group 1: Formatting mismatch in Test_run_pandoc_to_pdf tests
- **Failing tests**:
  - `dev_scripts_helpers/documentation/test/test_lib_notes_to_pdf.py::Test_run_pandoc_to_pdf::test1`
  - `dev_scripts_helpers/documentation/test/test_lib_notes_to_pdf.py::Test_run_pandoc_to_pdf::test2`
  - `dev_scripts_helpers/documentation/test/test_lib_notes_to_pdf.py::Test_run_pandoc_to_pdf::test3`

- **Reason**:
  - The expected strings in the test file use compact formatting: `[ {'function': ..., 'args': (...), 'kwargs': {...}, }, ...]`
  - The actual output now has formatted output: `[ { 'function': ..., 'args': (...), 'kwargs': {...}, }, { ... }, ]`
  - Differences: space after opening bracket `[`, space before opening brace `{`, space before closing bracket `]`
  - This indicates a change in how system calls are being converted to strings (likely in `_sys_calls_to_str` in `hunit_test_utils.py`)

- **Potential fix**:
  - The expected strings in test_lib_notes_to_pdf.py need to be reformatted to match the new output format
  - Update test lines 376-390, 402-407, 419-424 in test_run_pandoc_to_pdf helper function to use the new formatting with proper spacing
  - Alternatively: Update the `_sys_calls_to_str` function to match the expected format (if this is a regression)

- **Fix complexity**: Low - Just update the expected strings in the test code

## [ ] Group 2: Missing render_images command in script generation test
- **Failing tests**:
  - `dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_script_generation::test2`

- **Reason**:
  - The expected output file is missing the render_images command that is now being generated
  - Looking at notes_to_pdf.py lines 188-191, render_images is part of the DEFAULT_ACTIONS
  - The actual output now includes: `$GIT_ROOT/dev_scripts_helpers/documentation/render_images.py --input ... --output ... --action render`
  - The expected file doesn't have this line

- **Potential fix**:
  - Run: `pytest dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_script_generation::test2 --update_outcomes`
  - This will regenerate the expected outcome files with the correct render_images command included

- **Fix complexity**: Low - Just update the test outcome using pytest flag

## Verification Plan
- After fixes, rerun all failing tests to confirm they pass
- Run with different builds (docker, apple, dev_container) to ensure consistency
