---
description: Apply the conventions usually not followed in the unit test
---

- When the user passes a test file `<file>`
  - Apply the following transformations to the code, making sure that there is
    no change in behavior

- All invariants and conventions are documented in
  `.claude/skills/testing.rules.md`

## Key Transformations

- See `.claude/skills/testing.rules.md`
  - "## Dedent Strings to the Code"
  - "## Test Method Names"
  - "## Use Helper Methods When You Have Repetitive Tests"
  - "## Avoid Replicated Assignment"
  - "## Consolidate inputs and outputs"
  - "## Assign Variables and Then Call Functions"

- Run the skill `/coding.factor_common_code` on the file

# Important
- For all the code you must follow the instructions in
  `.claude/skills/coding.rules.md`
