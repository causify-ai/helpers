---
description: Check the references in all the skill files
model: haiku
---

# Goal
- Check that all the skill and rule files have references

# Step 1: Find Files
- Look for all the markdown files both `SKILL.md` and `<TOPIC>.rules.md`
  ```
  > find .claude/skills -name "*.md"
  ```

# Step 2: Read Context
- Read context about rules from `.claude/skills/skill.rules.md`

# Step 3: Check Rules
- For each file apply all the following rules and report violations as described
  below

## Check Files Existence
- Make sure that the file follows the section `## File Format` from the file
  `.claude/skills/skill.rules.md`

## Check Header References
- Make sure that the file follows the section `## References and Dependencies` from the file
  `.claude/skills/skill.rules.md`

## Check for Other Violations
- Use the rules in `.claude/skills/skill.rules.md` to look for clear violations
- Report them only if you are really sure about it

# Step 4: Report Violations

- Report all the violations in a file `cfile` using the format
  `.claude/skills/cfile.rules.md`

# Step 5: Ask Users Whether to Fix the Problems
- Ask for the user which problems should be fixed by printing a list of problem
  with indices
