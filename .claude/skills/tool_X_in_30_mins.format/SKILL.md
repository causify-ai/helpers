---
description: Format a blog document in the "tool_X_in_30_mins" format.
model: haiku
---

- Given the document passed by the user, apply the conventions and rules from
  `@.claude/skills/tool_X_in_30_mins.rules.md`

- At the end run `lint_txt.py -i` to format the file
