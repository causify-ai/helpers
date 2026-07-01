---
description: Move the general content from a skill to the corresponding rule file
model: haiku
---

# Goal
- Given the skill file `<SKILL_FILE>` passed by the user, move the general
  content of the skill to the corresponding rule file so that it is refactored,
  executing the following steps

# Workflow

## Step 1
- Read `.claude/skills/skill.rules.md`
- Print the name of the skill and rule file
  ```
  Skill file: <SKILL_FILE>
  Rule file: <RULE_FILE>
  ```

## Step 2
- Find the parts that refer to general rules that should go in `<RULE_FILE>`

## Step 3
- Move those parts from `<SKILL_FILE>` to `<RULE_FILE>` in the right section

## Step 4
- Add a reference to the section in `<RULE_FILE>` like:
  ```
  - Follow the section `XYZ` from the file `<RULE_FILE>`
  ```
