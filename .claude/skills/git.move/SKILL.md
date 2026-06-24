---
description: Move a file or directory in the Git repo and update all references to it
model: haiku
---

# Goal
- Given a source path `<SRC>` and destination path `<DST>` move a file or
  directory in the Git repo and update all references to it

# Workflow

## Validate Inputs
- Confirm `<SRC>` exists in the repository
- Confirm `<DST>` does not already exist (to prevent accidental overwrites)
- Ensure the parent directory of `<DST>` exists, creating it if necessary

## Move the File or Directory
- Run `git mv <SRC> <DST>` to preserve Git history
- If the file is in a subrepo (e.g., `helpers_root`), descend in that dir to use
  `git mv`
  - E.g., `cd helpers_root && git mv <SRC> <DST>` adjusting the paths
    accordingly

## Update All References
- Search the entire repository for any occurrences of `<SRC>`
  ```
  > grep -r -i <SRC> .
  ```
- Replace each occurrence of `<SRC>` with `<DST>`
- This includes:
  - Source code imports in Python
  - Unit test code in Python
  - Configuration files in YAML and JSON
  - Documentation in markdown and text
  - Any other plaintext files
- Skip binary files and the `.git/` directory

## Summarize Changes
- Report what changes were performed
  - List every file that had references updated, with a count of replacements
    per file
  - Flag any ambiguous matches that may need manual review

## Ask for Help If Unsure How to Do
- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a plan.md with 5 bullet points explaining
    what the plan is

## Verify Results
- Make sure that there is no reference left over about file `<SRC>`
  ```
  > grep -r -i <SRC> .
  ```
