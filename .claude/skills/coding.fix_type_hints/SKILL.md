---
description: Fix type hints in a file to follow the typing module conventions
model: haiku
---

# Goal
Fix type hints in the passed file `<FILE>` to follow the project's type-hint
conventions.

# Conventions
- Follow all the type-hint rules in `.claude/skills/coding.rules.md`

# Verification
- [ ] Confirm type hints use the `typing` module style, not PEP 604 syntax
- [ ] Run `pyright` on the file to confirm no new type errors
