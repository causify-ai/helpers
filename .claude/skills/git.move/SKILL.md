---
description: Move a file or directory in the Git repo and update all references to it
---

- Given a source path `<src>` and destination path `<dst>` in the current Git
  repository:

# Validate inputs
- Confirm `<src>` exists in the repository
- Confirm `<dst>` does not already exist (to prevent accidental overwrites)
- Ensure the parent directory of `<dst>` exists, creating it if necessary

# Move the file or directory
- Run `git mv <src> <dst>` to preserve Git history

# Update all references
- Search the entire repository for any occurrences of `<src>`
- Replace each occurrence with `<dst>`
- This includes source code imports, configuration files, documentation, and any
  other plaintext files
- Skip binary files and the `.git/` directory

# Summarize changes
- Report the move that was performed
- List every file that had references updated, with a count of replacements per
  file
- Flag any ambiguous matches that may need manual review

# Ask for help if unsure how to do
- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a plan.md with 5 bullet points explaining
    what the plan is
