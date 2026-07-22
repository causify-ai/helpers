In dev_scripts_helpers/documentation/test/test_notes_to_pdf.py
verify this invariants

- [ ] No use of `self.check_string`
  - Follow `## Never Use self.check_string()`
- [ ] No `self.assertIn` but check the entire output value with an assert_equal
  - Follow `## Only use assert_equal`
- [ ] No function is called with hardwired parameters, but they are assigned to a
  variable and then used
  - Follow `## Assign Variables and Then Call Functions`
- [ ] No repeated code, use at least one `def helper()` per class
  - Follow `## Use Helper Methods When You Have Repetitive Tests`
- [ ] All unit tests pass

# Conventions
- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- When writing testing code you must always follow the instructions in
  `.claude/skills/testing.rules.md`

# Create a plan, if needed
- If the task is not perfectly clear:
  - You MUST not perform it
  - Ask for clarifications
  - Create a `plan.md` in the same directory with 5 bullet points explaining what
    the plan is
  - Wait for the user to confirm

