---
description: Write or update a README.md for a directory with sections for structure, files, and executable descriptions
model: haiku
---

# Goal

- You are an expert technical writer specializing in software documentation.
- Given a directory path <DIR>, write a `README.md` in that directory following the
  conventions and structure in `.claude/skills/readme.rules.md`

# Workflow

## Step 1: Examine the directory
- List all subdirectories, files (Python/Markdown), and executables

## Step 2: Write the README
- Structure the README with sections from `readme.rules.md`:
   - Summary
   - Structure of the Dir
   - Description of Files
   - Description of Executables
   - Description of Workflows (if applicable)

- Follow all formatting rules from `.claude/skills/readme.rules.md`:
   - Description limits (e.g., <20 words for subdirs, 1-line for files)
   - Command formatting with `> ` prefix and proper code blocks
   - Example ordering (simple → complex)
   - Table format for command references

## Examples

- `dev_scripts_helpers/documentation/README.md`
- `dev_scripts_helpers/llms/README.md`
- `dev_scripts_helpers/ai/README.md`
- `dev_scripts_helpers/coding_tools/README.md`
