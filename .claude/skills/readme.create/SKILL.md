---
description: Write or update a directory's README.md with structure, files, and executables
model: haiku
---

# Goal

- You are an expert technical writer specializing in software documentation.
- Given a directory path `<DIR>`, write a `README.md` in that directory following the
  conventions and structure in `.claude/skills/readme.rules.md`

# Workflow

## Examine the Directory
- List all subdirectories, files (Python/Markdown), and executables

## Write the README
- Structure the README with sections from `.claude/skills/readme.rules.md`:
   - Summary
   - Structure of the Dir
   - Description of Files
   - Description of Executables (if applicable)
   - Description of Workflows (if applicable)
   - Description of Architecture (if applicable)

- Follow all formatting rules from `.claude/skills/readme.rules.md`:
   - Description limits (e.g., <20 words for subdirs, 1-line for files)
   - Command formatting with `> ` prefix and proper code blocks
   - Example ordering (simple to complex)
   - Table format for command references

# Verification

- [ ] `README.md` exists in the target directory `<DIR>`
- [ ] Every required section from `.claude/skills/readme.rules.md` is present
- [ ] Description length limits and command formatting rules are followed
