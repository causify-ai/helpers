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
- If the result is checked with `self.check_string()`
  - Run the test adding the pytest option `--update_golden` to refresh the output
- If the result is checked with `self.assert_equal()` or similar assertion
  (e.g., `hunteuti.assert_sys_calls()`, `self.assertEqual()`)
  read the file `tmp.final.actual.txt` containing the actual variable and update
  `expected` variable
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
