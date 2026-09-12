---
description: Propose a plan for unit testing a file and then implement it
model: haiku
---

# Goal
- Propose a unit test plan for a given file, then implement it after the user
  approves

# Workflow

## Propose a Unit Test Plan
- Given a file `<FILE>`, create a comprehensive unit test plan according to
  the rules in `.claude/skills/testing.rules.md`
- Create a file with a summary of what is going to be tested

## Implement the Unit Test Plan
- Wait for the user to review the plan and approve or modify it
- Then implement it

# Important
- All invariants and conventions for unit tests are documented in
  `.claude/skills/testing.rules.md`
- For all code you must follow the instructions in
  `.claude/skills/coding.rules.md`

# Verification
- [ ] Make sure everything in `# Verification` in
  `.claude/skills/testing.rules.md` is verified
