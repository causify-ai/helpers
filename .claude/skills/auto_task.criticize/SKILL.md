---
description: Review a plan or GitHub issue for an `auto_task` before execution
model: haiku
---

# Goal
- The user will pass you a file `<FILE>` or a GitHub issue number
  `<GITHUB_ISSUE_NUM>`
- You will read carefully the passed content and make sure both the problem and the
  solution is clear and complete

# Workflow

## Read Context
- Read the content (file or GitHub issue)
- Analyze the problem and the solution, reviewing it carefully

## Create a Plan, if Needed
- When analyzing the problem, make sure to understand which repos are affected by the
  change, since this influences creating a PR for multiple repos
  - Update the section in `.claude/templates/auto_task.template.md`
    ```
    * Repo: <Which repos are affected>
    - [ ] helpers (https://github.com/causify-ai/helpers)
    - [ ] umd_classes (https://github.com/gpsaggese/gpsaggese.github.io)
    - ...
    ```

- If the task is not perfectly clear:
  - Ask for clarifications
  - Propose changes to the file to clarify

## Output Results
- Follow the rules in `.claude/skills/auto_task.rules.md`
- The output is a file in the format `.claude/templates/auto_task.template.md`

# Conventions
- Follow `.claude/skills/coding.rules.md` when writing code
- Follow `.claude/skills/testing.rules.md` when writing testing code

# Verification
- [ ] The problem statement is clear and unambiguous
- [ ] The proposed solution is clear and unambiguous
- [ ] Any needed clarification was requested before the task moves to execution
