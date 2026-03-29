---
description: Update the references to moved, renamed, or deleted files in the Git repo
---

# Step 1
- Find all the files moved, renamed, or deleted in the current repo and its
  subrepos
  ```bash
  (
  git ls-files -m || true
  git submodule foreach --quiet '
  git ls-files -m | sed "s|^|$sm_path/|"
  '
  ) | sort -u > tmp.files.txt
  ```

# Step 2
- For each file $FILE, look for all the references in the repo to $FILE

# Step 3
- Update the references
