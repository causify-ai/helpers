---
description: Create a plan for fixing TODOs
---

# Goal
- Given a list of TODOs provided by the user in the form 
  ```
  <FILE>:<LINE_NUM>:<TODO description>
  ./helpers/hmarkdown_coloring.py:235:def colorize_bullet_points_in_slide(
  ```

# Workflow

## Step 1
- Read each TODO and understand the problem
- If it's a bug:
  - Make sure to understand the root cause
  - Run experiments to verify that you understood the issue and its root cause
- Devise a plan to fix the problem
- Devise a plan to verify that the problem is fixed

## Step 2
- Create a plan `plan.todo_janitor.md` for fixing the tests using the template
  below:
  ```
  ## [ ] 1: <short description of the issue>

  ### Info
  - Original description: <FILE>:<LINE_NUM>:<TODO description>

  ### Proposed fix
  - Type: [feature|bug|improvement|cosmetic]
  - Reason of the problem: ...
  - Proposed fix: ...
    - ...
  - Confidence in the fix: [low|medium|high]
  - Fix complexity: [low|medium|high]
  - Verification plan
    - <How to verify that the problem is fixed>

  ### Status
  - Status: [proposed|approved|issue_filed|working|PR_ready|merged]
  - GitHub issue title: ...
  - GitHub issue link: ...
  - PR link: ...
  - Git worktree: ...

  # [ ] 2: ...
  ...
  ```
- Write the comments as bullet points according to `.claude/skills/markdown.rules.md`
  and `.claude/skills/text.rules.md` with minimal text
- Do not make any change to the code, but only propose the fixes

### Follow the Conventions
- When writing code, follow instructions in `.claude/skills/coding.rules.md`
  - Refer to skills in `.claude/skills/coding.*/SKILL.md` to follow the repo best
    practices
- For bugs:
  - Add unit tests to check that the problem was present and then it's fixed
    (red/green approach)
  - Follow instructions in `.claude/skills/testing.rules.md`
  - Refer to skills in `.claude/skills/testing.*/SKILL.md` to follow the repo
    best practices
- For renaming, make sure the entire code base is checked to make sure everything
  is updated
  - Follow `.claude/skills/coding.rename/SKILL.md`
- For change of function signature, make sure all the calling instances have been
  updated

## Step 3: Rank the Issues
- Reorder the issues in increasing complexity, starting from the issues with high
  confidence in the fix

## Step 4: Lint the file
- Run
  ```
  > lint_txt.py -i plan.todo_janitor.md
  ```
