---
description: Analyze and fix failure of tests in GitHub CI
model: haiku
---

# Step 1: Parse Logs
- Parse the output of `invoke gh_workflow_list` which contains information on
  the failing tests

- The log of the failing tests on the CI is stored in a file `<CI_LOG>` like:
  ```
  # Log is in 'tmp.failure.check_if_the_linter_was_run.gp_scratch_19.txt'
  ```

- The list of failing tests `<FAILING_TESTS>` is in a file `<REPRO_SCRIPT>`
  like:
  ```
  ... # To run the tests:
  ... > ./tmp.pytest_repro.fast_tests.sh
  ```

# Step 2: Understand Why Tests Fail in the CI / Locally
- Read `<CI_LOG>` and understand why the tests `<FAILING_TESTS>` are failing
  remotely

- Run the script `<REPRO_SCRIPT>` to understand if the failing tests
  `<FAILING_TESTS`> are passing locally

- Report a table with the information of what tests are passing in the CI,
  locally, and why they are failing in the CI and locally

# Step 3: Propose Fixes
- Propose a set of fixes so that the failing tests pass both on the CI and
  locally
- Do not make any change, only propose the fixes
- Ask the user to continue or not

# Step 4: Implement Fixes
- If the user says to continue, implement the fixes
- Do not commit the changes to Git
