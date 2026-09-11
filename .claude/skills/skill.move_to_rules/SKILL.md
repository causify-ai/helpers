---
description: Move the general content from a skill to the corresponding rule file
model: haiku
---

# Goal
- Given the skill file `<SKILL_FILE>` passed by the user, move its general
  content into the corresponding rule file `<RULE_FILE>`

# Workflow

## Read Skill Rules and Identify Files
- Read `.claude/skills/skill.rules.md`
- Print the name of the skill and rule file
  ```text
  Skill file: <SKILL_FILE>
  Rule file: <RULE_FILE>
  ```

## Find General Content
- Find the parts that refer to general rules that belong in `<RULE_FILE>`

## Move the Content
- Move those parts from `<SKILL_FILE>` to `<RULE_FILE>`, in the right section

## Add a Reference
- Add a reference to the moved section in `<SKILL_FILE>`, e.g.:
  ```markdown
  - Follow the section `XYZ` from the file `<RULE_FILE>`
  ```

# Verification
- [ ] `<RULE_FILE>` contains the moved general content, in the right section
- [ ] `<SKILL_FILE>` references the moved section instead of restating it
- [ ] No content was lost or duplicated between `<SKILL_FILE>` and
      `<RULE_FILE>`
