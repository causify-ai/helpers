---
description: Format the content of agentic skill files in SKILL.md 
---

- Apply the conventions and rules in `.claude/skills/skill.rules.md` to the
  `SKILL.md` passed by the user
- Review and improve prompts and skills in the file passed `<SKILL_FILE>`
- Make sure that the intent and the behavior of the skill is not changed

## Rewrite for clarity
- Remove ambiguity
- Use direct instructions
- Make behavior reliably executable
- Avoid superficial wording edits without improving execution

## Add structure (if missing)
- Purpose
- When to use
- When NOT to use
- Output format

## Preserve intent
- Do not change the skill's core behavior
- Do not add opinions instead of rules
