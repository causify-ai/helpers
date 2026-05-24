---
description: Apply the conventions usually not followed in the unit test
---

- When the user passes a test file `<FILE>`

- Apply the following transformations to the code in `<FILE>` from
  `.claude/skills/testing.rules.md`:
  - `## Dedent Strings to the Code`
  - `## Test Method Names`
  - `## Use Helper Methods When You Have Repetitive Tests`
  - `## Avoid Replicated Assignment`
  - `## Consolidate inputs and outputs`
  - `## Assign Variables and Then Call Functions`

- Run the skill `/coding.factor_common_code` on the file

- Make sure that there is no change in behavior in the code

# Important
- For all the code you must follow the instructions in
  - `.claude/skills/coding.rules.md`
  - `.claude/skills/testing.rules.md`
