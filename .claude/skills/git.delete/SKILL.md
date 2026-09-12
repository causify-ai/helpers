---
description: Remove a function, file, or directory from the repo and clean up all references
model: haiku
---

# Goal
- Given a target `<SRC>` (function, file, or directory), remove it from the repo
  cleanly with no dangling references or dead code
- Identify what `<SRC>` is before proceeding

# If `<SRC>` Is a Function
- **Remove the function definition** from its source file
- **Find all callers**: search the entire codebase for any call sites and remove
  or refactor them
- **Remove orphaned helpers**: recursively find functions that are now only
  called by `<SRC>` (or each other) and remove them too
- **Remove tests**: delete all unit tests that exclusively test `<SRC>` or its
  orphaned helpers
- **Clean up imports**: remove any imports that were only needed by the deleted
  code

# If `<SRC>` Is a File or Directory
- **Remove the file/directory** from the repo
- **Find all references**: search for any `import`, `from ... import`,
  `require`, or path strings pointing to `<SRC>`
- **Remove or refactor each reference**: delete the import and any code that
  depended on it, or replace it with an alternative if a substitute exists
- **Remove related tests**: delete test files that exclusively test the removed
  file/directory
- **Update configs**: check and update any config files (e.g. `pyproject.toml`,
  `setup.py`, `__init__.py`, `MANIFEST.in`) that reference `<SRC>`

# After Removal (all Cases)
- Summarize the changes
- Do not commit any change

# Verification
- [ ] Run the test suite to confirm nothing is broken
- [ ] Run a final grep for the removed name to catch any remaining references

# Ask for Help If Unsure How to Do
- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a `plan.md` with 5 bullet points explaining
    what the plan is
