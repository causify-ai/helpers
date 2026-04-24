---
description: Reorganize rules in a agent skill rule file
model: haiku
---

- Read `.claude/skills/skill.rules.md`

- Given a file `<RULE_FILE>` `<topic>.rules.md` passed by the user
  - Read its content
  - Keep the rules organized as per `## Keep Rules organized in the Rule File`
  - Do not change rules in the text but only move them in the `<RULE_FILE>` file
  - Save the result in the same file
