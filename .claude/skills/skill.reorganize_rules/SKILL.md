---
description: Reorganize rules in a agent skill rule file
model: haiku
---

- Given a file `<RULE_FILE>` in the format `<topic>.rules.md` passed by the user

# Step 1
- Read `<RULE_FILE>` content

# Step 2
- Read `.claude/skills/skill.rules.md`

# Step 3
- Propose changes to the user if you see:
  - A H2 sections or text that is redundant
  - A better organization of H1 sections that is more cohesive and simpler
  - A H2 section that belongs to a better H1 section so that it's more cohesive
- Do not change the content and intention of the `<RULE_FILE>` file

# Step 4
- Print the new organization in terms of H1 and H2
- Ask the user to confirm

# Step 5
- Save the result in the same file `<RULE_FILE>`

# Step 6
- Look for all the files referring to `<RULE_FILE>` and update them to refer
  to the updated structure of `<RULE_FILE>`
  - E.g., update chunks of code like
    ```
    - Add end-to-end tests for command-line tools using the rules in
      `.claude/skills/testing.rules.md` 
        `# End-to-end Unit Tests for Executables`
    ```
    to match the new organization
