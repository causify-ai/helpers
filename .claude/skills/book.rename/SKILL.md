---
description: Rename a file storing a book or paper into a standard format
model: haiku
---

# Goal
- Given the name of a file storing a book or a paper, rename it to match the
  format in `.claude/skills/references.rules.md`
  `# Format to Use in File Names`

# Workflow
- Use `git mv` if the file is under source control

# Verification
- [ ] Confirm the new file name follows
      `<Year>.<Last_name_of_first_author>_[et_al].<Title>`
- [ ] Confirm the file extension is unchanged
