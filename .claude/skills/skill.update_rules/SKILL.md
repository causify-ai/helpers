---
description: Add or update rules for a skill topic in the appropriate rules file
model: haiku
---

Add new rules or update existing rules in the skill topic's corresponding rules
file

# Step 1: Determine the Skill Topic
1. Identify the skill topic `<TOPIC>` from user input
   - E.g., `coding`, `testing`, `notebook`, `markdown`
2. If the user didn't specify a topic, infer it from context or ask the user

# Step 2: Locate the Rules File
1. Find the corresponding rules file: `.claude/skills/<TOPIC>.rules.md`
   - For a `coding` skill, update `.claude/skills/coding.rules.md`
   - For a `testing` skill, update `.claude/skills/testing.rules.md`
2. Report the target file:
   ```text
   Skill topic: <TOPIC>
   Rules file: .claude/skills/<TOPIC>.rules.md
   ```

## Update the Rules File
1. Read the rules file to understand its structure and existing rules
2. Add or update the rules according to user instructions
3. Follow the structure in `.claude/skills/skill.rules.md`:
   - Organize rules with level 2 headers (`##`) grouped under level 1 headers
     (`#`)
   - Use imperative language ("Do X", not "You should X")
   - Include concrete examples with "Good" and "Bad" patterns
   - Reference related files where appropriate
4. Run `lint_txt.py -i .claude/skills/<TOPIC>.rules.md` to lint the file
