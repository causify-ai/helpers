---
description: Create a plan for fixing a list of TODOs
model: sonnet
---

# Goal
- Given a list of TODOs provided by the user in the form of a cfile create a plan
  to fix them

# Workflow

## Understand Each TODO
- Each TODO is in the form
  ```text
  <FILE>:<LINE_NUM>:<TODO description>
  ```
  - E.g., 
    ```
    ./helpers/hmarkdown_coloring.py:235:def colorize_bullet_points_in_slide(...
    ```
- Read each TODO and understand the problem
- If it's a bug:
  - Make sure to understand the root cause
  - Run experiments to verify that you understood the issue and its root cause
- Devise a plan to fix the problem
- Devise a plan to verify that the problem is fixed

## Write the Fix Plan
- Create a plan `tasks.md` for fixing the tests using the template below
  `.claude/templates/auto_task.template.md`
- Fill in the template's `* Repo:` checklist per
  `.claude/skills/auto_task.rules.md` section "Multi-Repo Issues, Branches,
  and PRs" (how to tell which repo a `<FILE>` belongs to, and how to handle
  TODOs spanning more than one repo)
- Write the comments as bullet points according to `.claude/skills/markdown.rules.md`
  and `.claude/skills/text.rules.md` with minimal text
- Do not make any change to the code, but only propose the fixes

### Follow the Conventions
- Follow `.claude/skills/auto_task.rules.md` section "Follow the Coding and
  Testing Rules"
  - Refer to skills in `.claude/skills/coding.*/SKILL.md` and
    `.claude/skills/testing.*/SKILL.md` to follow the repo's best practices
- For bugs, add unit tests to check that the problem was present and then it's
  fixed (red/green approach)
- For renaming, make sure the entire code base is checked to make sure everything
  is updated
  - Follow `.claude/skills/coding.rename/SKILL.md`
- For change of function signature, make sure all the calling instances have been
  updated

## Rank the Issues
- Reorder the issues in increasing complexity, starting from the issues with high
  confidence in the fix

# Verification
- [ ] `tasks.md` contains one issue block per input TODO
- [ ] Every issue block has type, reason, proposed fix, confidence, complexity, and
  verification plan filled in
- [ ] Issues are ordered by increasing complexity, starting from the highest
  confidence fixes
- [ ] No code was changed, only the plan file was written
