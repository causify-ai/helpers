- This file contains the conventions for creating, queuing, and executing an
  `auto_task`: a unit of work an agent completes end to end (spec, branch, PR) with
  minimal supervision

# Plan Format

## Follow the Plan Template

- Write a GitHub issue's problem/solution plan using the template
  `.claude/templates/auto_task.template.md`
- State the problem and the goal before proposing a solution
- Break the solution into one `PR<NUM>` section per PR when the issue spans more than
  one PR

## Ask for Clarification Before Executing an Unclear Plan

- If the problem or the solution is not perfectly clear:
  - You MUST NOT perform the task
  - Ask for clarification
  - Create a `plan.Issue<GH ISSUE NUM>.PR<PR NUM>.md` in the same directory with 5
    bullet points explaining the plan and wait for confirmation

## Follow the Coding and Testing Rules

- When writing code, follow `.claude/skills/coding.rules.md`
- When writing testing code, follow `.claude/skills/testing.rules.md`
- Follow the specs in 

# The Unit of Work

## One GitHub Issue Is the Unit of Work

- An `auto_task` normally maps to one GitHub issue, implemented as one Git branch and
  one PR
- A large refactor can span multiple branches/PRs for the same issue, e.g. split into
  chunks for safety and ease of review

## Name Branches and PRs After the Issue

- Name the branch and PR after the issue title:
  `<RepoPrefix>Task<IssueNum>_<Description>`
  - E.g., issue 123 "Do this and that" becomes `HelpersTask123_Do_this_and_that`
- Decorate with a numeric suffix when an issue has more than one branch/PR:
  `<RepoPrefix>Task<IssueNum>_<Description>_<Id>`
  - Get the next free suffix with `invoke git_branch_next_name`
- `invoke git_branch_create` enforces this pattern (`{RepoPrefix}Task\d+_\S+`) and
  rejects any other branch name

# Writing and Reviewing Specs

## Keep a Single Queue File

- Maintain one markdown file, e.g. `.claude/ai_task_queue.md`, listing every task an
  agent should eventually do
- Organize it into `Ready`, `Backlog`, and `Done` sections, each holding a checklist
  of `## [ ] <Title>` items followed by their specs

## Write Specs Before Queuing a Task

- Use `/auto_task.create_specs_from_todos` to turn a list of TODOs or issues into specs with a
  problem, a solution, a confidence level, and a complexity estimate
- Consider a task ready only once it states: problem, solution, complexity, and
  importance

## Review Specs Before Executing

- Use `/auto_task.criticize` to read a plan or GitHub issue and confirm both the
  problem and the solution are clear before assigning it to an agent
- Prioritize tasks with high confidence in the fix and low complexity first

# Choosing How to Execute the Queue

## Use Stacked PRs When Tasks Are Well-Defined and Sequential

- Write all specs upfront, let the agent complete the whole sequence, then review the
  resulting stack of PRs in one batch
- Prefer this when tasks are well-specified, form a genuine dependency chain, and a
  single focused review session beats repeated interruptions
- Follow `.claude/skills/auto_task.execute_with_stacked_prs/SKILL.md` for how to run
  this
- A longer uninterrupted run raises the cost of a misunderstanding: an error in an
  early task compounds into every task stacked on top of it, so only stack tasks
  whose specs are already trusted

# Feeding Tasks to an Agent

## Create the Issue and Branch Together

- Use `git_create_issue_and_branch.py` to create the GitHub issue and its branch in
  one step:

  ```bash
  > git_create_issue_and_branch.py --gh_issue_title "<Title>" \
      --gh_issue_body_file <specs_file>
  ```

- Reuse an existing issue with `--gh_issue_id <Num>` instead of `--gh_issue_title`
- Add `--create_worktree` when the task should run in an isolated worktree

## Use a Worktree for Local, Interactive Work

- Run tasks that need local regressions or tighter interactivity in a worktree
  created alongside the issue and branch:

  ```bash
  > git_create_issue_and_branch.py --gh_issue_title "<Title>" \
      --gh_issue_body_file <specs_file> --create_worktree
  ```

## Enable Direct Commits Deliberately

- Let an agent commit directly to its branch, via `control_cc_commit.py`, only for
  tasks that are not being driven interactively
- Keep it disabled while actively pairing with the agent on a branch

## Close the Loop

- After a PR merges:
  - Close the GitHub issue
  - Move the task's entry from `Ready`/`Backlog` to `Done` in the queue file
  - Run the tests touched by the merge, e.g

    ```bash
    > pytest_log $(i git_files --mode test_files --on-one-line --only-print-files)
    ```

# Automating the Mechanical Steps

## Script LLM Calls Instead of Copy-Pasting

- Use `llm_transform.py -i <file> -o cfile -p code_review` to turn a code review into
  a structured `cfile` instead of a one-off chat prompt
- Review the `cfile` before applying any of its suggested changes
- Use `llm_cli.py` for one-off text/doc transformations inside a task, e.g. drafting
  a description or fixing style in a single file

## Track Cost Per Batch Run

- Save stats per call with `--stat_file <path>` and sum them across a queue run
  instead of trusting a single call's number, since a queue run makes many small LLM
  calls



# 
- Instructions to execute a PR are in `.claude/instr.md`

- Each PR should have a descr `./pr_instr.md` of what needs to be done (which comes
  from the .claude/templates/auto_task.template.md)

- `/auto_task.execute_one_task`
```
- Execute the prompt in pr_instr.md

- Follow the instructions
  - `@.claude/instr.md`
```

- Instructions to test a PR are in `.claude/test_pr.md`


# 
- Once everything is clear

git_create_issue_and_branch.py --gh_issue_title "Improve msml610/3.2 and 3.3 slides"

Close the wrong PR

gh pr close UmdTask557_Improve_msml6103_2_and_3_3_slides -c "Wrong" --delete-branch
