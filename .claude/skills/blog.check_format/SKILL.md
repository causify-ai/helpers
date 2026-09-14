---
description: Check the format of a blog file
model: haiku
---

# Goal
- Check that all the actual and the draft blogs have the correct format

# Workflow

## Find Files
- Look for all the markdown files both `SKILL.md` and `<TOPIC>.rules.md`
  ```bash
  > find website/docs/blog/posts -name "*.md"
  ```

## Read Context

- Read context about rules from
  - `.claude/skills/blog.rules.md`
  - `.claude/skills/markdown.rules.md`
  - `.claude/skills/text.rules.md`

## Check Rules
- For each file apply all the following rules and report violations as described
  below

### Check Front Matter
- Make sure to follow the section `# Blog Document Structure` from the file
  `.claude/skills/blog.rules.md`

### Check that Has a TL;DR
- Make sure to follow the section `# Blog Document Structure` from the file
  `.claude/skills/blog.rules.md`

### Check for Other Violations
- Use the rules in `.claude/skills/blog.rules.md` to look for clear violations
- Report a violation only when confident about it

## Report Violations

- Report all the violations in a file `cfile` using the format in
  `.claude/skills/cfile.rules.md`

## Ask Users Whether to Fix the Problems
- Ask for the user which problems should be fixed by printing a list of problem
  with indices

# Verification
- [ ] Confirm `cfile` lists concrete file and line references for each
      violation
- [ ] Confirm each reported violation maps to a rule in
      `.claude/skills/blog.rules.md`
