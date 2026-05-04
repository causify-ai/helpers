---
description: Safely remove a Python function, file, or directory from the Git repo and clean up all references
---

- Given a target `<src>` (function, file, or directory), remove it from the repo
  cleanly with no dangling references or dead code

- Identify what `<src>` is before proceeding

# If `<src>` is a function
- **Remove the function definition** from its source file
- **Find all callers**: search the entire codebase for any call sites and remove
  or refactor them
- **Remove orphaned helpers**: recursively find functions that are now only
  called by `<src>` (or each other) and remove them too
- **Remove tests**: delete all unit tests that exclusively test `<src>` or its
  orphaned helpers
- **Clean up imports**: remove any imports that were only needed by the deleted
  code

# If `<src>` is a file or directory
- **Remove the file/directory** from the repo
- **Find all references**: search for any `import`, `from ... import`, `require`,
  or path strings pointing to `<src>`
- **Remove or refactor each reference**: delete the import and any code that
  depended on it, or replace it with an alternative if a substitute exists
- **Remove related tests**: delete test files that exclusively test the removed
  file/directory
- **Update configs**: check and update any config files (e.g. `pyproject.toml`,
  `setup.py`, `__init__.py`, `MANIFEST.in`) that reference `<src>`

# After removal (all cases)
- Run the test suite to confirm nothing is broken
- Run a final grep for the removed name to catch any remaining references
- Summarize the changes
- Do not commit any change

# Ask for help if unsure how to do
- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a plan.md with 5 bullet points explaining
    what the plan is
