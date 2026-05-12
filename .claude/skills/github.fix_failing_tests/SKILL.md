---
description: Analyze and fix failure of tests in GitHub CI
---

# Step 1: Parse logs
- Parse the output of `invoke gh_workflow_list` which contains information on the
  failing tests

- The log of the failing tests on the CI is stored in a file `<ci_log>` like:
  ```
  # Log is in 'tmp.failure.check_if_the_linter_was_run.gp_scratch_19.txt'
  ```

- The list of failing tests `<failing_tests>` is in a file `<repro_script>` like:
  ```
  ... # To run the tests:
  ... > ./tmp.pytest_repro.fast_tests.sh
  ```

# Step 2: Understand why tests fail in the CI / locally
- Read `<ci_log>` and understand why the tests `<failing_tests>` are failing
  remotely

- Run the script `<repro_script>` to understand if the failing tests
  `<failing_tests`> are passing locally

- Report a table with the information of what tests are passing in the CI,
  locally, and why they are failing in the CI and locally

# Step 3: Propose fixes 
- Propose a set of fixes so that the failing tests pass both on the CI and
  locally
- Do not make any change, only propose the fixes
- Ask the user to continue or not

# Step 4: Implement fixes
- If the user says to continue, implement the fixes
- Do not commit the changes to Git
