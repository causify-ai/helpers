---
description: Refactor unit test files by aligning strings, renaming methods, and factoring out common test code
---

- When the user passes a test file, apply the following transformations to the
  code, making sure that there is no change in behavior. All invariants and
  conventions are documented in `@.claude/skills/testing.rules.md`.

## Key Transformations

- Align Strings to the Code
  - See `@.claude/skills/testing.rules.md` section "Code Formatting in Tests" → "Align Strings to the Code"

- Rename Test Methods as `test1`, `test2`, ...
  - See `@.claude/skills/testing.rules.md` section "Test Method Names"

- Factor Out Common Code
  - See `@.claude/skills/testing.rules.md` section "Use Helper Methods When You
    Have Repetitive Tests"
  - Aggressively factor out common code in helper methods so that each test
    method sets the inputs and expected value, then calls the helper function.

- Avoid Replicated Assignment
  - See `@.claude/skills/testing.rules.md` section "Avoid Replicated Assignment"

# Important

- For all the code you must follow the instructions in
  `@.claude/skills/coding.rules.md`
