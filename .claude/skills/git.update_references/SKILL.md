---
description: Find and update the references to moved, renamed, or deleted files in the Git repo
---

# Step 1
- Find all the files moved, renamed, or deleted in the current repo using a
  command line
  ```bash
  (
  git ls-files -m || true
  git submodule foreach --quiet '
  git ls-files -m | sed "s|^|$sm_path/|"
  '
  ) | sort -u > tmp.files.txt
  ```

# Step 2
- For each file <FILE>, look for all the references to <FILE> in the repos
  - `helper`: the current repo
  - `umd_classes`: located at `~/src/umd_classes1`
  - `csfy`: located at `~/src/csfy1`
  - `orange`: located at `~/src/orange1`
  - `lemonade`: located at `~/src/lemonade1`

- Print the references in a table organized by repos, and files

- Pause and ask the user to continue

# Step 3
- Update the references
