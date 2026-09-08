- This file contains the conventions for creating, queuing, and executing an
  `auto_task`: a unit of work an agent completes end to end (spec, branch, PR) with
  minimal supervision

# Plan Format

## Follow the Plan Template

- A GitHub issue's problem/solution plan follows the template in
  `.claude/templates/auto_task.template.md`
- It states the problem and the goal before proposing a solution
- It breaks the solution into one `PR<NUM>` section per PR when the issue spans more
  than one PR

## Ask for Clarification Before Executing an Unclear Plan

- If the problem or the solution is not perfectly clear:
  - You MUST NOT perform the task
  - Ask for clarification
  - Create a `plan.Issue<GH ISSUE NUM>.PR<PR NUM>.md` in the same directory with 5
    bullet points explaining the plan and wait for confirmation

## Follow the Coding and Testing Rules

- When writing code, follow `.claude/skills/coding.rules.md`
- When writing testing code, follow `.claude/skills/testing.rules.md`
- Follow the specs in `.claude/rules.md` for other types of files

# The Unit of Work

## One GitHub Issue Is the Unit of Work

- An `auto_task` normally maps to one GitHub issue, implemented as one or more Git
  branches and as one or more PRs
- A large refactor can span multiple branches/PRs for the same issue, e.g. split into
  chunks for safety and ease of review

## Name Branches and PRs After the Issue

- Name the branch and PR after the issue title:
  `<RepoPrefix>Task<IssueNum>_<Description>`
  - E.g., issue 123 "Do this and that" becomes `HelpersTask123_Do_this_and_that`
- Decorate with a numeric suffix when an issue has more than one branch/PR:
  `<RepoPrefix>Task<IssueNum>_<Description>_<Id>`
  - Get the next free suffix with `invoke git_branch_next_name`
- `invoke git_branch_create` enforces this pattern (`{RepoPrefix}Task\d+_\S+`)

## Review Specs Before Executing

- Use `/auto_task.criticize` to read a plan or GitHub issue and confirm both the
  problem and the solution are clear before assigning it to an agent
- Prioritize tasks with high confidence in the fix and low complexity first
