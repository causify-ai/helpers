---
description: Annotate file with TODOs based on the convention and rule violations
---

# Goal
- The user will give you a file `<FILE>` and you will annotate the file with
  TODOs based on the violated rules and conventions

# Workflow

## Step 1: Determine the Rules to Apply

- If `<FILE>` is a Python file use `<RULES>`
  - `.claude/skills/coding.rules.md`

- If `<FILE>` is a Python testing file (e.g., `test/test_*.py`) use `<RULES>`
  - `.claude/skills/coding.rules.md`
  - `.claude/skills/testing.rules.md`

- Print the rule files `<RULES>` to be used for each file in `<FILE>`

- Read the rule files `<RULES>` carefully

## Step 2: Annotate with TODOs

- Annotate all the points in `<FILE>` with violations to rules in `<RULES>`
  adding a TODO, like
  ```
  # TODO(ai_gp): Apply <rule> before the point with violation
  ```
- E.g.,
  ```
  # TODO(ai_gp): Apply "Replace Checking Invariants with `assert_equal` - Do not use multiple `assertIn()` calls to check individual pieces of a string output; instead compare the entire output with `assert_equal()`"
  self.assertIn("Failed Tests Summary", actual)
  self.assertIn("test_method1", actual)
  self.assertIn("test_method2", actual)
  self.assertIn("Total failing tests: 2", actual)
  ```

## Step 3: Verification
- Make sure that all the violations of the `<RULES>` in `<FILE>` are caught
  and commented

## Step 4: Ask User to Continue
- Ask the user to commit and then ask to continue
- If the user says to continue run the skill `/coding.todoai_gp` on `<FILE>`
