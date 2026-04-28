---
description: Format the content of agentic skill files in SKILL.md 
---

- Review and improve prompts and skills in the file passed `<SKILL.md>`
- Apply the conventions and rules in `.claude/skills/skill.rules.md` to the
  `<SKILL>.md` passed by the user
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

## Add examples
- When useful add good and bad examples
  ````
  - `**Bad**`
    ```
    ...
    ```
  - `**Good**`
    ```
    ...
    ```
  ````

## Create a TODO list
- Create a TODO list with the list of all the planned transformations

## Style
- Make sure it follows the conventions in
  - `.claude/skills/markdown.rules.md`
  - `.claude/skills/text.rules.bullet_points.md`

## Lint the updated file
- Run `lint_txt.py -i` on `<SKILL.md>`
