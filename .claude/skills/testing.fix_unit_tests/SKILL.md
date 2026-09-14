---
description: Apply the conventions usually not followed in the unit test
model: haiku
---

# Goal
- The user passes one or more test files `<FILE>` and you need to apply the
  corresponding conventions and rules.

# Workflow

## Read Rules
- Read the transformations from `.claude/skills/testing.rules.md` in the
  following headers
  - `### Dedent Strings to the Code`
  - `## Test Method Names`
  - `## Use Helper Methods When You Have Repetitive Tests`
  - `### Avoid Replicated Assignment`
  - `## Consolidate Inputs and Outputs`
  - `## Assign Variables and Then Call Functions`
  - `## Compare Whole Output with assert_equal, Not Piecewise`
  - ``## Do Not Use `hdbg.dassert` to Test Assertions``

## Draft a Plan
- Given the code passed in `<FILE>` and the list of all the transformations
  create a list of transformations and code lines to apply them, since the
  code violates them

## Implement the Plan
- Apply the transformations one at the time to the parts of the code

## Refactor the Code
- Run the skill `/coding.factor_common_code` on the file `<FILE>` to factor out
  common code

# Important
- Make sure that there is no change in behavior in the code
- For all the code you must follow the instructions in:
  - `.claude/skills/coding.rules.md`
  - `.claude/skills/testing.rules.md`

# Verification
- [ ] Check that no remaining part of the code violates the list of
  transformations
- [ ] Run the tests and confirm behavior is unchanged
