---
description: Format markdown files according to conventions for clarity, structure, and consistency
model: haiku
---

- Given the file passed by the user, apply the guide for creating well-formatted
  markdown documents from:
  - `@.claude/skills/markdown.rules`
  - `@.claude/skills/text.rules.bullet_points.md`

- After all the transformations apply the linter
  ```
  > lint_txt.py -i <file>
  ```
