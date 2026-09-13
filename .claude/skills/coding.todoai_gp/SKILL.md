---
description: Implement TODO(ai_gp) items in a file: renames, code updates, references
model: haiku
---

# Goal
Implement all the `TODO(ai_gp)` items in the passed file `<FILE>`.

# Workflow

## Renaming and Moving Objects
- When renaming an object make sure to update all the references to those objects
  in the code base
  - When renaming or moving files update imports
  - For functions, find the callers in notebooks ipynb, Python files, and other
    files and update those references (use `grep` to make sure all the
    references are updated)
  - Update documentation in txt and md files

- In a `TODO(...):` the sign `-> XYZ` means "rename to XYZ"

- When moving a function among files, move also the tests to the corresponding
  file `.../test/test_...`

## Fix TODOs Around the Code
- When fixing a TODO check whether there are more instances of the same TODO
  in the same file and fix also those

## Remove TODOs
- Remove the `TODO` only if the TODO was implemented
- If you can't implement a TODO, leave the TODO in place and add a comment
  shortly explaining why can't be done

# Conventions
- Depending on the file type, follow the corresponding instructions in
  `.claude/rules.md`

# Verification
- [ ] Run the corresponding unit tests to make sure the code works
- [ ] Grep in the repo for the renamed or removed objects to confirm there are
      no hanging references
