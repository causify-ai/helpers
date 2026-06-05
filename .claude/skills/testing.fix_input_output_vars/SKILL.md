---
description: Fix the input / output variables of a test
model: haiku
---

# Goal
- Transform test method so that:
  - The inputs and outputs are strings with """ and dedent
  - The output being checked with `self.assert_equal()`
  - Follow the directions in `.claude/skills/testing.rules.md`
    - `# Test Input and Output Handling`
    - `## String Formatting for Test Inputs and Assertions`
    - `## Use an Expected Output`

- Factor out as much code as possible in helper functions
  - Follow the directions in `.claude/skills/testing.rules.md`
    - `## Use Helper Methods When You Have Repetitive Tests`

- Do not change the intent of the test

# Verify
- Run the tests to make sure that the tests are passing
