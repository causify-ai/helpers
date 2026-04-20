---
description: Rename files, functions, and variables across a codebase and update all references
---

I will give a list of files, functions, variable to rename in a codebase

In `TODO: ->` means rename

For files use `git mv`

Make sure to update all the references to those objects in the code base

- E.g., for files, look for and update imports
- E.g., for functions, find the callers in notebooks ipynb, Python files, and
  other files and update those references
- Update documentation in txt and md files
- If needed, run corresponding unit tests to make sure the code works

- For Python code follow the rules in @.claude/skills/coding.rules.md

- For Python code with unit tests, follow the rules in the rules from
  @.claude/skills/testing.format_rules/SKILL.md
