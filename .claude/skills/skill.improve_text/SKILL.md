---
description: Improve rule or skill file without changing the content
model: haiku
---

# Goal
- Improve rule or skill file without changing the content using our conventions,
  without changing the content of the file

## Inputs
- The user passes either:
  - A rule file `<RULE_FILE>` in the format `.claude/skills/<TOPIC>.rules.md`
  - A skill file `<SKILL_FILE>` in the format
    `.claude/skills/<TOPIC>.<ACTION>/skill.md`

## Read the Skill Rules
- Read `.claude/skills/skill.rules.md`

## Improve Text
- Improve the content without changing the intent following the conventions in:
  - `.claude/skills/markdown.rules.md`
  - `.claude/skills/text.rules.md`

## Constraints
- Do not change the same organization in terms of headers
