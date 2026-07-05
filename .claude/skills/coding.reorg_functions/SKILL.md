---
description: Reorganize the Python functions in a file
model: haiku
---

# Reorganize Python Functions Within a File

- Reorganize the Python functions in the user-provided file according to the
  general rules in the `coding.rules.md` file for organizing code

  - Follow the section `## Organize Functions Into Logical Layers` from the file
    `.claude/skills/coding.rules.md`
  - Follow the section `## Order Layers by Abstraction Level` from the file
    `.claude/skills/coding.rules.md`
  - Follow the section `## Order Functions Within Each Layer` from the file
    `.claude/skills/coding.rules.md`
  - Follow the section `## Keep Related Functions Together` from the file
    `.claude/skills/coding.rules.md`
  - Follow the section `## Mark Private Functions` from the file
    `.claude/skills/coding.rules.md`


## Additional Guidance

- Avoid circular ordering where possible
- Preserve existing comments and docstrings
- Keep public entry points easy to locate near the end of the file
- Prefer cohesion and readability over strict categorization

# Constraints

## Preserve Behavior Exactly

- Do not modify functionality, logic, signatures, control flow, side effects, or
  semantics
- The resulting code must behave identically to the original.

## Move Code Only

- The refactor must be structural only

- Allowed changes:
  - Reordering functions
  - Adding section headers
  - Renaming internal/private functions consistently

- Disallowed changes:
  - Rewriting logic
  - Simplifying implementations
  - Changing APIs
  - Changing imports unnecessarily
  - Modifying formatting beyond what is required for reorganization
