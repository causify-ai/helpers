---
description: Rename files, functions, and variables and update all references
model: haiku
---

# Goal
I will give a list of files, functions, variables to rename in a codebase.

- In `TODO: -> <NEW_NAME>` the `->` means rename
- For files use `git mv`

# Workflow
- Update all the references to those objects in the code base
  - E.g., for files, look for and update imports
  - E.g., for functions, find the callers in notebooks ipynb, Python files, and
    other files and update those references
- Update documentation in txt and md files
- If needed, run corresponding unit tests to make sure the code works

# Conventions
- For Python code follow the rules in `.claude/skills/coding.rules.md`
- For Python code with unit tests, follow the rules in
  `.claude/skills/testing.rules.md`

# Verification
- [ ] Grep the codebase to confirm no references to the old name remain
- [ ] Run the corresponding unit tests to confirm nothing broke
