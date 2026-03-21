---
description: Merge git conflicts
---

# Step 1: Find the files with conflicts
- Find the files with conflicts running
  ```
  > git diff --name-only --diff-filter=U
  ```

# Step 2: Propose fixes
- For each file with conflict:
  - Explain why the conflict happened
  - Propose what needs to be done

- If you are not sure on what to do, give priority to the branch change

- Example
  ```verbatim
  1. tutorials/GitHub_Stats/Master_GitHub_analysis.py
     - Issue: Jupytext version conflict.
     - Resolution: Use master, it's the newer version.

  2. tutorials/GitHub_Stats/docker_jupyter.sh
     - Issue: HEAD adds -e GITHUB_ACCESS_TOKEN to Docker env; master removes it.
     - Resolution: Use master (remove the line)
  ```

# Step 3
- Ask user which changes should be done
- Perform the changes
- Resolve the git conflict
