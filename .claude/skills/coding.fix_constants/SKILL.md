---
description: Move constants to their correct scope based on usage
model: haiku
---

Move constants to match their usage scope and visibility requirements. Constants
should be placed where they are used and made private when not part of the
module's public interface

# Conventions
- Follow the section `# Constants` from the file `.claude/skills/coding.rules.md`

Apply the conventions in `.claude/skills/coding.rules.md` when writing constant
definitions and names

# Verification
- [ ] Confirm each constant sits in the smallest scope that uses it (local,
      module-private, or module-public)
- [ ] Confirm module-private constants are prefixed with `_`
