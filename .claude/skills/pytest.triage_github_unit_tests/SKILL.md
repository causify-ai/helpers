---
description: Analyze and fix failure of tests in GitHub CI
model: haiku
---

# Goal
- Given a run of the GitHub CI analyze the failures and create a plan to fix the
  tests

# Workflow

- Read `.claude/skills/pytest.rules.md`

## Step 1: Parse Logs from CI
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

## Step 2: Understand Why Tests Fail in the CI / Locally
- Parse `<CI_LOG>`
- Understand why the tests `<FAILING_TESTS>` are failing remotely
- Run the script `<REPRO_SCRIPT>` locally to understand whether the failing tests
  `<FAILING_TESTS`> are passing locally
  - For the tests that involve running Docker / Apple containers run the same tests
    with different builds, as per `## Analyze the Effect of Container Builds`
    in `.claude/skills/pytest.rules.md`

## Step 3: Prepare A Plan to Fix Failures
- Report a table with the information of what tests are passing in the CI,
  locally, and why they are failing in the CI and locally
- Prepare a plan following `# Format for Unit Test Fixing Plan` from
  `.claude/skills/pytest.rules.md`
- Propose a set of fixes so that the failing tests pass both on the CI and
  locally

## Step 4: Wait for User Feedback
- Do not make any change to the code, but only propose the fixes
- Ask the user to continue or not
- If the user says to continue, implement the fixes

## Step 5: Implement and Verify the Fix
- If the user says to continue, implement the fixes
- Verify that they work correctly as per `# Verification of the Fix` from
  `.claude/skills/pytest.rules.md`
