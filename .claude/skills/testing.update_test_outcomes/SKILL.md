---
description: Update the outcome of unit tests
model: haiku
---

# Goal
- The user passes you a list of tests or a repro script with tests failing
  `<FAILING_TESTS>` because of mismatching actual vs expected outputs

## Important
- For all code you must follow the instructions in
  `.claude/skills/coding.rules.md`
- Follow the invariants and conventions for unit tests in
  `.claude/skills/testing.rules.md`

# Workflow

## Step 1
- Run the tests one at the time in the way the user suggested to verify that the
  tests are failing due to mismatching outputs

## Step 2
- Check each failing test method and find out if the result is checked with
  - `self.check_string()`
  - `self.assert_equal()` or similar assertion (e.g.,
    `hunteuti.assert_sys_calls()`, `self.assertEqual()`)

- Print a table with the following info:
  path of test | fail / pass | check_string or assert_equal
  ```
  | Path | Test | Status | Assertion Method |
  |------|------|--------|------------------|
  | dev_scripts_helpers/documentation/test/test_notes_to_pdf.py | Test_notes_to_pdf_latex_options::test1 | FAIL | self.assert_equal() with fuzzy_match=True |
  | dev_scripts_helpers/documentation/test/test_notes_to_pdf.py | Test_notes_to_pdf_latex_options::test2 | FAIL | self.assert_equal() with fuzzy_match=True |
  | dev_scripts_helpers/documentation/test/test_notes_to_pdf.py | Test_notes_to_pdf_output_types::test1 | FAIL | self.assert_equal() with fuzzy_match=True |
  ```

- Save this to a file `tmp.update_test_outcomes.failing_tests.md`

## Step 3
- For each failing test method:
  - If the result is checked with `self.check_string()`
    - Run the test adding the pytest option `--update_golden` to refresh the output
  - If the result is checked with `self.assert_equal()` or similar assertions
    (e.g., `hunteuti.assert_sys_calls()`) read the file
    `{test_dir}/tmp.initial.actual.txt` 
    (e.g., `dev_scripts_helpers/documentation/test/outcomes/Test_run_pandoc_to_html.test1`)
    containing the actual variable and update the `expected` variable
    - E.g.,
      ```
      expected = """
      [{'args': (f'jupytext --to ipynb --update {py_file}',),
        'function': 'hsystem.system',
        'kwargs': {}},
       {'args': (f'jupytext --sync {py_file}',),
        'function': 'hsystem.system',
        'kwargs': {}}]
      """
      ```

- Follow the `## Code Formatting in Tests` in .claude/skills/testing.rules.md
  - `# Test Input and Output Handling`

- Do not change way of checking results
  - E.g., do not replace `self.assert*()` with `self.check_string()` and vice
    versa
  - E.g., do not replace `self.assert*()` with `self.assertIn()`

## Verification
- Run all the tests to make sure they are passing
