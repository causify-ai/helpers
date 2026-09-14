---
description: Increase unit test coverage toward 100 percent for a function or file
model: haiku
---

# Goal
- Given the passed function, file, or files `<FILES>`, increase unit test
  coverage from the corresponding files `<TEST_FILES>` to approach 100 percent
  using a plan-then-implement approach

# Workflow

## Establish Current Coverage
- Identify the test files corresponding to the target function, file, files
  `<TEST_FILES>` using the rules
  - E.g.,
    ```text
    helpers/hllm_cli.py -> helpers/test/test_hllm_cli.py
    ```
- Print the files to test
  ```text
  Target files: <FILES>
  Test files: <TEST_FILES>
  ```
- Run the following command and record the results:
  ```bash
  # Using invoke (preferred):
  > i run_coverage --suite fast --generate-html-report
  # Or directly with pytest inside Docker:
  > pytest --cov=<PKG> --cov-report=term-missing --cov-report=html <TEST_FILE>
  ```

- Summarize which lines and branches are not covered

## Design a Testing Plan
- Analyze uncovered code paths and behaviors
- Propose a clear testing plan that:
  - Tests functions modularly before testing interactions
  - Prioritizes end-to-end and user-visible behavior over incidental
    implementation details
  - Avoids testing assertions, defensive checks, or invalid inputs unless they
    are critical to correctness
- Explicitly map each uncovered area to one or more proposed tests

## Specify Tests Without Implementation
- Define test classes and test method names
- For each proposed test:
  - Describe the input data
  - Describe the expected output or observable behavior
- Do not write executable test code at this stage

## Implement After Approval
- Wait for user confirmation or feedback on the testing plan
- After approval:
  - Implement the tests according to the approved plan
  - Re-run coverage and verify that coverage for the target function is near
    100 percent
  - Report final coverage results and remaining gaps, if any

# Important Rules
- Do not implement tests before the plan is approved
- Do not proceed if instructions or requirements are ambiguous
- Always adhere to the formatting and style guides referenced above
- Focus on meaningful behavior and correctness rather than superficial coverage
- All tests and code must strictly follow:
  - `.claude/skills/coding.rules.md` for any Python code
  - `.claude/skills/testing.rules.md` for tests
- If any part of the task is unclear or underspecified, stop and ask for
  clarification before proceeding

# Verification
- [ ] Confirm coverage for the target function or file is near 100 percent
- [ ] Confirm every proposed test was implemented and passes
- [ ] Confirm no uncovered critical branch remains unexplained
