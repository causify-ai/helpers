---
description: Reorganize rules in a agent skill rule file
model: haiku
---

- Given a file `<RULE_FILE>` in the format `<topic>.rules.md` passed by the user

# Step 1
- Read `<RULE_FILE>` content

# Step 2
- Apply `.claude/skills/skill.rules.md` to `<RULE_FILE>`

- Propose changes to the user if you see:
  - A H2 sections or text that is redundant
  - A better organization of H1 sections that is more cohesive and simpler
  - A H2 section that belongs to a better H1 section so that it's more cohesive

- Do not change the content and intention of the `<RULE_FILE>` file

# Step 3
- Save the result in the same file `<RULE_RULE>`
