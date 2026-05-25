---
description: Apply the conventions usually not followed in the unit test
---

- When the user passes a test file `<FILE>`

# Step 1
- Apply the following transformations one at the time to the code in `<FILE>`
- The transformations are from `.claude/skills/testing.rules.md` in the headers
  - `## Dedent Strings to the Code`
  - `## Test Method Names`
  - `## Use Helper Methods When You Have Repetitive Tests`
  - `## Avoid Replicated Assignment`
  - `## Consolidate inputs and outputs`
  - `## Assign Variables and Then Call Functions`

# Step 2
- After step 1, run the skill `/coding.factor_common_code` on the file `<FILE>`
  to factor out common code

# Important
- Make sure that there is no change in behavior in the code
- For all the code you must follow the instructions in:
  - `.claude/skills/coding.rules.md`
  - `.claude/skills/testing.rules.md`
