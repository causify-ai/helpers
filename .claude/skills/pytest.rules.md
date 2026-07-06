# Diagnosis of the Root Cause

## Analyze the Effect of Container Builds

- For unit tests that involve running Docker / Apple containers run the same tests
  with different builds 

  1) Run inside the Docker Dev container:
     ```
     > manage_cache.py --action clear_all
     > (export CSFY_DOCKER_ENGINE="docker"; i docker_cmd --stage=local -v 1.6.0 --cmd "pytest $TARGET") 2>&1 | tee build1.txt
     ```

  2) Run outside the Dev container but using Docker:
     ```
     > manage_cache.py --action clear_all
     > (export CSFY_DOCKER_ENGINE="docker"; pytest_log $TARGET) 2>&1 | tee build2.txt
     ```

  3) Run outside the Dev container but using Apple Containers:
     ```
     > manage_cache.py --action clear_all
     > (export CSFY_DOCKER_ENGINE="apple"; pytest_log $TARGET) 2>&1 | tee build3.txt
     ```

- Think carefully to see if the root cause and solution is the same for all the 3
  builds

# Format for Unit Test Fixing Plan

## Prepare A Plan to Fix Failures
- Create a plan `plan.fixing_unittests.md` for fixing the tests based on common
  issues
  ```
  # [ ] Group1: short description
  dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_actions::test1
  dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_actions::test2
  dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_edge_cases::test1

  - Reason: ...
    - ...

  - Potential fix: ...
    - ...

  # [ ] Group2: ...
  ...
  ```
- Write the comments as bullet points according to `.claude/skills/markdown.rules.md`
- Do not make any change to the code, but only propose the fixes

## Rank the Issues by Complexity
- At the end of the plan, create a table ranking the issues in terms of
  complexity for a fix

# Verification of the Fix

## For Renaming / Missing Functions

- When there is a missing function, e.g.,
  ```
  AttributeError: module 'helpers.hunit_test_purification' has no attribute 'TextPurifier'
  ```
  run grep to make sure there is no instance leftover

## Run the Tests
- Always re-run the tests that have been fixed to confirm that they work
  ```
  > pytest ...
  ```
- If the test includes Docker / Apple containers, run it with the differnt
  builds, as per `## Analyze the Effect of Container Builds`
