---
description: Implement all TODO(ai_gp) items in a file including renames, code updates, and update references
model: haiku
---

# Goal
- Implement all the `TODO(ai_gp)` in the passed file

- In a `TODO:` the sign `-> XYZ` means "rename to XYZ"

- When renaming an object make sure to update all the references to those objects
  in the code base
    - E.g., for files, look for and update imports
    - E.g., for functions, find the callers in notebooks ipynb, Python files,
      and other files and update those references
    - Update documentation in txt and md files

# Verification
- Run corresponding unit tests to make sure the code works

# Conventions
- Depending on the file type follow the instructions for the right file type
  based on `@.claude/rules.md`
