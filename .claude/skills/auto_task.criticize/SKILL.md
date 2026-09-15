---
description: Review a plan or GitHub issue for an `auto_task` before execution
model: haiku
---

# Goal

- The user will pass you a file `<FILE>` (e.g., `tasks.md`) or a GitHub issue number
  `<GITHUB_ISSUE_NUM>`
- You will read carefully the passed content and make sure both the problem and the
  solution is clear and complete

# Workflow

## Read Context

- Read the content of the plan (file or GitHub issue)
- Analyze the problem and the solution, reviewing it carefully

## Create a Plan, If Needed

- When analyzing the problem, make sure to understand which repos are affected by the
  change, since this influences creating a PR for multiple repos
  - Update the `* Repo:` checklist in `.claude/templates/auto_task.template.md`,
    following `.claude/skills/auto_task.rules.md` section "Multi-Repo Issues,
    Branches, and PRs"
  - When more than one repo is checked, confirm each `PR<NUM>` block in
    "Solution" states which repo it targets: an unlabeled `PR<NUM>` for a
    multi-repo task is an unclear plan (see "Ask for Clarification Before
    Executing an Unclear Plan" in `.claude/skills/auto_task.rules.md`)
  - Do not add or edit a `## Companion PRs` section: `git_create_issue_and_branch.py`
    generates it automatically once PRs exist, per
    `.claude/skills/auto_task.rules.md` "Multi-Repo Issues, Branches, and PRs"

- If the task is not perfectly clear, follow `.claude/skills/auto_task.rules.md`
  section "Ask for Clarification Before Executing an Unclear Plan"

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
