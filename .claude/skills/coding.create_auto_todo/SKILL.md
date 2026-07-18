---
description: Create a plan for fixing TODOs
---

# Goal
- Given a list of TODOs provided by the user in the form
  ```
  ./helpers/hmarkdown_coloring.py:235:def colorize_bullet_points_in_slide(
  ```

# Workflow

## Step 1
- Read each TODO and understand the problem
- If it's a bug make sure to understand the root cause, running experiments to
  verify that you understood the issue
- Come up with a plan to verify that the problem is fixed

## Step 2
- Create a plan in the format 

- Create a plan `plan.todo_janitor.md` for fixing the tests based on the template
  below
  ```
  # [ ] 1: <short description>

  ## Type: [feature|bug|improvement|cosmetic]

  ## Reason: ...
    - ...

  ## Potential fix: ...
    - ...

  ## Fix complexity: [low / medium / high]

  ## How to verify the problem is fixed
  - 

  # [ ] Group 2: ...
  ...
  ```
- Write the comments as bullet points according to `.claude/skills/markdown.rules.md`
  with minimal text

- Do not make any change to the code, but only propose the fixes

### 
- When writing code, follow instructions in `.claude/skills/coding.rules.md`
  - Refer to skills in `.claude/skills/coding.*/SKILL.md` to follow the repo best
    practices
- For bugs
  - Add unit tests to check that the problem was present and then it's fixed
  - Follow instructions in `.claude/skills/testing.rules.md`
  - Refer to skills in `.claude/skills/testing.*/SKILL.md` to follow the repo
    best practices
- For renaming, make sure the entire code base is checked to make sure everything
  is updated
  - Follow `.claude/skills/coding.rename/SKILL.md`
- For change of function signature, make sure all the calling instances have been
  updated

## Step 3
- Wait for the user to review and approve this file
