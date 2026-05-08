---
description: Refactors unit test files to align with project conventions. Use when test files have inconsistent string alignment, non-standard method names, repeated code that should be factored out, or mixed input/output organization.
---

- When the user passes a test file `<file>`, apply the following transformations
  to the code, making sure that there is no change in behavior
- All invariants and conventions are documented in `@.claude/skills/testing.rules.md`

## Key Transformations
- Dedent Strings to the Code
  - See `@.claude/skills/testing.rules.md` section "Code Formatting in Tests" → "Dedent Strings to the Code"

- Rename Test Methods as `test1`, `test2`, ...
  - See `@.claude/skills/testing.rules.md` section "Test Method Names"

- Factor Out Common Code
  - See `@.claude/skills/testing.rules.md` section "Use Helper Methods When You
    Have Repetitive Tests"
  - Aggressively factor out common code in helper methods so that each test
    method sets the inputs and expected value, then calls the helper function

- Avoid Replicated Assignment
  - See `@.claude/skills/testing.rules.md` section "Avoid Replicated Assignment"

- Consolidate Inputs and Outputs
  - See `@.claude/skills/testing.rules.md` section "Consolidate inputs and
    outputs"

- Assign Variables and Then Call Functions
  - See `@.claude/skills/testing.rules.md` section "Assign Variables and Then
    Call Functions"

- Run the skill `/coding.factor_common_code` on the file

# Verify
- Run the refactored test file to confirm no tests broke:
  ```bash
  pytest <test_file> -v
  ```
- Fix any failures before reporting done

# Important
- If the file uses mocking, ensure patching follows
  `@.claude/skills/testing.mocking/SKILL.md`
- For all the code you must follow the instructions in
  `@.claude/skills/coding.rules.md`
