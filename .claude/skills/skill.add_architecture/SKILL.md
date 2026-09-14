---
description: Add a rule to the set of architecture rules
model: haiku
---

# Goal
- The user passes the description of a rule or behavior `<RULE>` to add to
  the architecture rules file `<RULE_FILE>` (`.claude/skills/architecture.rules.md`)

# Workflow

## Read the Rule File
- Read `<RULE_FILE>` (`.claude/skills/architecture.rules.md`)

## Report the Proposed Rule
- Report the proposed rule `<RULE>` to be added to `<RULE_FILE>`, following
  the conventions in:
  - `.claude/skills/markdown.rules.md`
  - `.claude/skills/text.rules.md`

## Find the Target Section
- Find the level 1 header related to `<RULE>`, per
  `.claude/skills/skill.rules.md` `## Keep Rules Organized in the Rule File`

## Add the Rule
- Add the rule `<RULE>` to `<RULE_FILE>`, following the conventions in
  `.claude/skills/skill.rules.md`

# Verification
- [ ] `<RULE>` is added under the correct level 1 header in `<RULE_FILE>`
- [ ] No existing rule in `<RULE_FILE>` already covers the same behavior
