---
description: Add a rule to the set of rules
model: haiku
---

- The user passes:
  - The description of a rule / behavior to be added to a rule file
  - (Optional) `<RULE_FILE>` in the format `.claude/skills/*.rules.md`

# Step 1
- Read `.claude/skills/skill.rules.md`

# Step 2
- If the user didn't specify `<RULE_FILE>`, decide in which of the files `<RULE_FILE>`
  the new rule needs to be added
- The available rules are:
  ```bash
  > ls -1 .claude/skills/*.rules.md
  ```
- Read the rules file `<RULE_FILE>` to understand its structure and existing rules

# Step 3
- Report the proposed rule `<RULE>` to be added, following the conventions in:
  - `.claude/skills/markdown.rules.md`
  - `.claude/skills/text.rules.md`

# Step 3
- Find the proper header 1 (see `.claude/skills/skill.rules.md`
  `## Keep Rules Organized in the Rule File`) that is related to the `<RULE>`

# Step 4
- Then add the rule `<RULE>` to the file `<RULE_FILE>` following the conventions in
  `.claude/skills/skill.rules.md`
