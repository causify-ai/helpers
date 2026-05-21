---
description: Move constants to have the right scope
---

- When there is a constant used only in one place move it close to where it is
  used (instead of keeping it in the global space)

- Only constants that are shared across multiple places should be in the global
  space

- If a constant is only used in a file and not used outside of it, it should be
  made private
