---
description: Add a rule to the set of rules
model: haiku
---

# Goal
- The user passes:
  - The description of a rule / behavior `<CONTENT>` to be added to a rule file
  - (Optional) The target rule file to update `<RULE_FILE>` in the format
    `.claude/skills/*.rules.md`

# Workflow

## Step 1: Read Skill Rules
- Read `.claude/skills/skill.rules.md` about conventions and rules to write
  skills

## Step 2: Determine Target Rule File
- If the user didn't specify `<RULE_FILE>`, decide in which of the files `<RULE_FILE>`
  the new rule needs to be added based on the content of `<CONTENT>`
- The available rules are:
  ```bash
  > ls -1 .claude/skills/*.rules.md
  ```

## Step 3: Read Target Rule File
- Read the target rules file `<RULE_FILE>` to understand its structure and
  existing rules

## Step 4
- Report the proposed rule `<RULE>` to be added, following the conventions in:
  - `.claude/skills/markdown.rules.md`
  - `.claude/skills/text.rules.md`

## Step 5
- Find the proper header 1 that is related to the `<RULE>`
  - See `.claude/skills/skill.rules.md` `## Keep Rules Organized in the Rule File`

## Step 6
- Add the rule `<RULE>` to the file `<RULE_FILE>` following the conventions in
  `.claude/skills/skill.rules.md`
