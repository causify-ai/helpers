---
description: Improve rule or skill file without changing the content
model: sonnet
---

# Goal
- Improve a rule or skill file's style and formatting using our conventions,
  without changing its content or intent

# Inputs
- The user passes either:
  - A rule file `<RULE_FILE>` in the format `.claude/skills/<TOPIC>.rules.md`
  - A skill file `<SKILL_FILE>` in the format
    `.claude/skills/<TOPIC>.<ACTION>/SKILL.md`

# Workflow

## Read the Skill Rules
- Read `.claude/skills/skill.rules.md` to understand the conventions to
  follow

## Improve the Text
- Improve the content without changing the intent, following the conventions
  in:
  - `.claude/skills/markdown.rules.md`
  - `.claude/skills/text.rules.md`

# Constraints
- Do not change the header organization

# Verification
- [ ] The file's header organization is unchanged
- [ ] The content and intent of the file are unchanged
