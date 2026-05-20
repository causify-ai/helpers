---
description: Format the content of agentic skill files in SKILL.md 
---

- Review and improve prompts and skills in the file `<SKILL.md>` passed by the
  user
- Apply the conventions and rules in `.claude/skills/skill.rules.md` to the
  `<SKILL>.md`

# Rewrite for Clarity
- Remove ambiguity
- Use direct instructions and examples
- Make behavior reliably executable
- Avoid superficial wording edits without improving execution

# Preserve Intent
- Do not change the skill's core behavior
- Do not add opinions instead of rules

# Lint the Updated File
- Run `lint_txt.py -i <SKILL.md>`
