---
description: Analyze and fix failure of tests in GitHub CI
model: haiku
---

# Goal

- Given a run of the GitHub CI analyze the failures and fix the failing tests

# Workflow

- Read `.claude/skills/pytest.rules.md`

## Parse Logs From CI

- Parse the output of `invoke gh_workflow_list` which contains information on the
  failing tests
- The log of the failing tests on the CI is stored in a file `<CI_LOG>` like:

  ```bash
  # Log is in 'tmp.failure.check_if_the_linter_was_run.gp_scratch_19.txt'
  ```

- The list of failing tests `<FAILING_TESTS>` is in a file `<REPRO_SCRIPT>` like:

  ```bash
  ... # To run the tests:
  ... > ./tmp.pytest_repro.fast_tests.sh
  ```

## Check Whether the Failure Reproduces Locally

- Parse `<CI_LOG>`
- Run the script `<REPRO_SCRIPT>` locally to check whether `<FAILING_TESTS>` fail
  there too
  - For the tests that involve running Docker / Apple containers run the same tests
    with different builds, as per `## Analyze the Effect of Container Builds` in
    `.claude/skills/pytest.rules.md`
- Note any difference in behavior between CI and local: e.g., environment
  variables, secrets, container build, or flakiness. `/pytest.fix_local_tests`
  cannot see this CI-specific context, so capture it here

## Diagnose and Fix

- Use `/pytest.fix_local_tests` passing `<REPRO_SCRIPT>` as `<FAILURE_INFO>` to
  diagnose the root cause and fix the failing tests
  - If a failure only reproduces on CI (not locally), diagnose the CI-specific
    cause directly instead (env, secrets, container build, flakiness) and fix it
- Report a table with the information of what tests are passing in the CI, locally,
  and why they are failing in the CI and locally, in the file
  `plan-pytest.fix_ci_tests.md` in the current dir
- Verify the fixes work correctly as per `# Verification of the Fix` from
  `.claude/skills/pytest.rules.md`

## Ask the User to Commit
- Ask the user to review and commit the changes
- Wait for the CI to pick up the changes and run the tests, and repeat the workflow

# Verification

- [ ] `plan-pytest.fix_ci_tests.md` lists a fix for every failing test
- [ ] Every fix follows `# Verification of the Fix` in
      `.claude/skills/pytest.rules.md`
- [ ] The failing tests pass both on the CI and locally after the fix
