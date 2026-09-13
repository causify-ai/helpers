---
description: Add a rule to the set of rules
model: haiku
---

# Goal
- The user passes:
  - The description of a rule / behavior `<CONTENT>` to be added to a rule file
  - (Optional) The target rule file to update `<TARGET_RULE_FILE>` in the format
    `.claude/skills/*.rules.md`

# Workflow

## Read Skill Rules
- Read `.claude/skills/skill.rules.md` about conventions and rules to write
  skills

## Determine Target Rule File
- If the user didn't specify `<TARGET_RULE_FILE>`, decide which of the files
  `<TARGET_RULE_FILE>` the new rule needs to be added to, based on the
  content of `<CONTENT>`
- The available rules are:
  ```bash
  > ls -1 .claude/skills/*.rules.md
  ```

## Read Target Rule File
- Read the target rules file `<TARGET_RULE_FILE>` to understand its structure
  and existing rules

## Draft the New Rule
- Draft the proposed rule `<CONTENT>` to be added, following the conventions
  in:
  - `.claude/skills/markdown.rules.md`
  - `.claude/skills/text.rules.md`

## Add the New Rule
- Find the proper H1 header that is related to `<CONTENT>`
  - See `.claude/skills/skill.rules.md` `## Keep Rules Organized in the Rule File`
- Add the rule `<CONTENT>` to `<TARGET_RULE_FILE>`, following the conventions
  in `.claude/skills/skill.rules.md`
- Make sure there is no overlap with other rules

# Verification
- [ ] `<CONTENT>` is added under the correct H1 header in `<TARGET_RULE_FILE>`
- [ ] No existing rule in `<TARGET_RULE_FILE>` already covers `<CONTENT>`
