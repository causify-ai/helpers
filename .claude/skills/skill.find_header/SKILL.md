---
description: Search rules related to what user asks
model: haiku
---

- The user gives you a description of something to look for
  - E.g., "how to write Python scripts"

- Find the markdown headers of level 1 or 2 in files `.claude/*rules*.md` that
  refers to what the user has requested

- Do not write any comment but only report the result as
  ```
  file:markdown header (of level 1 or 2)
  ```
  - E.g.,
  ```
  .claude/skills/coding.rules.md:## Use Script Template
  ```
