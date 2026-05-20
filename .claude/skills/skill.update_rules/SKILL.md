---
description: Update the agent rules for a type of skill
model: haiku
---

- Given the instructions `<SKILL_RULE>` given by user execute

# Step 1
- Understand what type of file `<SKILL_TYPE>` the instructions refer to, if the
  user didn't specify that
  - E.g., coding, testing, notebook, markdown, readme, slides, latex, blog

# Step 2
- Read `.claude/skills/rules.md` and find which files `<SKILL_FILES>` correspond to
  `<SKILL_TYPE>`

- Print
  ```
  Skill type: <SKILL_TYPE>
  File to modify: <SKILL_FILES>
  ```

# Step 3
- Update the `<SKILL_FILES>` with the content of `<SKILL_RULES>`
- Find the right place among the headers to insert the `<SKILL_RULES>` so that
  the headers are cohesive
- Follow the rules and conventions in `.claude/skills/skill.rules.md`
