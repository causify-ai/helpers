- Increase unit test coverage to approach 100 percent for a given function.

- Context and constraints:
  - You will be given a specific function to work on.
  - All tests and code must strictly follow:
    - `docs/ai_prompts/testing.format_rules.md` for tests
    - `docs/ai_prompts/coding.format_rules.md` for any code
  - Focus on meaningful behavior and correctness rather than superficial
    coverage.
  - If any part of the task is unclear or underspecified, stop and ask for
    clarification before proceeding.

## Step 1: Establish Current Coverage

- Identify the test file corresponding to the target function Example:
  helpers/hllm_cli.py → helpers/test/test_hllm_cli.py
- Run the following command and record the results:
  ```
  pytest --cov=yourpkg --cov-report=term-missing --cov-report=html
  ```

- Summarize which lines and branches are not covered.

## Step 2: Design a Testing Plan

- Analyze uncovered code paths and behaviors.
- Propose a clear testing plan that:
  - Tests functions modularly before testing interactions.
  - Prioritizes end-to-end and user-visible behavior over incidental
    implementation details.
  - Avoids testing assertions, defensive checks, or invalid inputs unless they
    are critical to correctness.
- Explicitly map each uncovered area to one or more proposed tests.

## Step 3: Specify Tests Without Implementation

- Define test classes and test method names.
- For each proposed test:
  - Describe the input data.
  - Describe the expected output or observable behavior.
- Do not write executable test code at this stage.

## Step 4: Implement After Approval

- Wait for user confirmation or feedback on the testing plan.
- After approval:
  - Implement the tests according to the approved plan.
  - Re-run coverage and verify that coverage for the target function is near 100
    percent.
  - Report final coverage results and remaining gaps, if any.

Important rules:

- Do not implement tests before the plan is approved.
- Do not proceed if instructions or requirements are ambiguous.
- Always adhere to the formatting and style guides referenced above.
