---
description: Reorganize the rules in a skill rules file
model: haiku
---

# Goal
- Given a rule file `<RULE_FILE>` in the format `<TOPIC>.rules.md` passed by
  the user, propose and apply a better organization of its sections

# Workflow

## Read the Rule File
- Read `<RULE_FILE>` content

## Read Skill Rules
- Read `.claude/skills/skill.rules.md`

## Propose the Reorganization
- Propose changes to the user if you see:
  - A better organization of H1 sections that is more cohesive and simpler
  - An H2 section or text that is redundant
  - An H2 section that belongs under a different H1 section for better
    cohesion
- Do not change the content or intention of `<RULE_FILE>`

## Present the New Organization
- Print the new organization in terms of H1 and H2 headers
- Ask the user to confirm

## Save the Result
- Save the result in the same file `<RULE_FILE>`

## Update References
- Look for all the files referring to `<RULE_FILE>` and update them to refer
  to the updated structure of `<RULE_FILE>`
  - E.g., update chunks of code like
    ```markdown
    - Add end-to-end tests for command-line tools using the rules in
      `.claude/skills/testing.rules.md`
        `# End-to-end Unit Tests for Executables`
    ```
    to match the new organization

# Verification
- [ ] The user confirmed the new organization before `<RULE_FILE>` was saved
- [ ] The content and intention of `<RULE_FILE>` are unchanged
- [ ] Every file referencing `<RULE_FILE>`'s old structure was updated
