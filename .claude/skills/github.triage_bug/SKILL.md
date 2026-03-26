---
description: Triage GitHub Issue
---

I will give you a GitHub issue ${ISSUE_NUM} and optionally a repo

# Step 1
- Read the issue description
  ```
  > gh issue view {ISSUE_NUM}
  ```

# Step 2: Check if it's already done
- Check if it's already implemented

# Step 3: Triage
Tasks:
- Estimate difficulty (easy/medium/hard)
- Identify which files are likely involved
- Determine root cause
- Suggest possible fixes
- Suggest labels

- Use bullet points, do not use page separator, limit the amount of markdown
  formatting (e.g., bold)

- The output should have the following format
  ```
  ## Status: **PARTIALLY RESOLVED**

  ## Root Cause

  ## Current State Analysis

  ## Difficulty Estimate: **MEDIUM**

  ## Recommended Fix Strategy

  ## Suggested Labels

  ## Additional Notes
  ```

- Do not solve or write any code, only study the problem and propose a solution
- Do not update GitHub
