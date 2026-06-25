---
description: Check the format of a blog file
model: haiku
---

# Goal
- Check that all the actual and the draft blogs have the correct format

# Step 1: Find Files
- Look for all the markdown files both `SKILL.md` and `<TOPIC>.rules.md`
  ```
  > find website/docs/blog/post -name "*.md"
  ```

# Step 2: Read Context

- Read context about rules from
  - `.claude/skills/blog.rules.md`
  - `.claude/skills/markdown.rules.md`
  - `.claude/skills/text.rules.md`

# Step 3: Check Rules
- For each file apply all the following rules and report violations as described
  below

## Check Front Matter
- Make sure to follow the section `# Blog Document Structure` from the file
  `.claude/skills/blog.rules.md`

## Check That Has a TL;DR
- Make sure to follow the section `# Blog Document Structure` from the file
  `.claude/skills/blog.rules.md`

## Check for Other Violations
- Use the rules in `.claude/skills/blog.rules.md` to look for clear violations
- Report them only if you are really sure about it

# Step 4: Report Violations

- Report all the violations in a file `cfile` using the format in
  `.claude/skills/cfile.rules.md`

# Step 5: Ask Users Whether to Fix the Problems
- Ask for the user which problems should be fixed by printing a list of problem
  with indices
