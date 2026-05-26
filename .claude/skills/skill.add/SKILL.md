---
description: Add a rule to the set of rules
---

- The user passes:
  - The description of a 
  - (Optional) `<FILE>` in the format `.claude/skills/*.rules.md`

# Step 1
- Read `.claude/skills/skill.rules.md`

# Step 2
- If the user didn't specify `<FILE>`, decide in which of the files `<FILE>`
  the new rule needs to be added
  ```bash
  > ls -1 .claude/skills/*.rules.md
  ```
- Report the proposed file

# Step 3
- Report the proposed rule `<RULE>` to be added, following the conventions in:
  - `.claude/skills/markdown.rules.md`
  - `.claude/skills/text.rules.md`

# Step 3
- Find the proper header 1 (see `.claude/skills/skill.rules.md`
  `## Keep Rules Organized in the Rule File`) that is related to the `<RULE>`

# Step 4
- Then add the rule `<RULE>` to the file `<FILE>` following the conventions in
  `.claude/skills/skill.rules.md`
