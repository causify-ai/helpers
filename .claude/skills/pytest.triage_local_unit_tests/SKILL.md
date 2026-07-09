---
description: Analyze and fix failure of local tests
model: haiku
---

# Goal
- Given a pytest target `<TARGET>` (e.g., dev_scripts_helpers/documentation/test/test_notes_to_pdf.py)
  run the tests, create a plan to fix the tests

# Workflow

- Read `.claude/skills/pytest.rules.md`

## Step 1: Run Tests
- Run the tests locally:
  ```
  > pytest_log `<TARGET>`
  ```

## Step 2: Analyze Failures
- Collect the failing tests from the run
  ```
  > i pytest_failed
  ...
  Failed tests: 25/7
  dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_actions::test1
  dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_actions::test2
  dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_edge_cases::test1
  dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_edge_cases::test2
  dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_edge_cases::test3
  dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_edge_cases::test4
  dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_filters::test1
  dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_filters::test2
  dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_filters::test3
  dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_filters::test4
  dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_filters::test5
  ...
  13:07:36 - WARN  lib_tasks_pytest.py pytest_failed:1745                 To run the failed tests run: tmp.pytest_failed.sh
  ...
  ```

- For the tests that involve running Docker / Apple containers run the same tests
  with different builds, as per `## Analyze the Effect of Container Builds`
  in `.claude/skills/pytest.rules.md`

- Carefully consider if the root cause and the solution is the same for all the 3
  builds

## Step 4: Prepare A Plan to Fix Failures
- Prepare a plan following `# Format for Unit Test Fixing Plan` from
  `.claude/skills/pytest.rules.md`

## Step 5: Wait for User Feedback
- Do not make any change to the code, but only propose the fixes
- Ask the user to continue or not with the fixes

## Step 6: Implement and Verify the Fix
- If the user says to continue, implement the fixes
- Verify that they work correctly as per `# Verification of the Fix` from
  `.claude/skills/pytest.rules.md`
