---
description: Execute a sequence of tasks as one stack of branches and PRs
model: haiku
---

# Goal

- Execute one GitHub issue as a stack of sequential branches and PRs, each named
  `<BASE>_<ID>` (`ID` = 1, 2, 3, ...) and each branched from the previous one, so
  the PRs stack in review order
- Create the whole stack without stopping for review between branches
  - The user then reviews, edits, and merges each PR bottom-up at their own pace,
    after this skill's job is done
- Follow `.claude/skills/auto_task.rules.md` for how tasks are queued, specified, and
  named before they reach this skill

## Input
- The user will pass you a task in the format 

# When to Use This Skill

- Use it only when the tasks favor stacked execution: specs are complete, tasks form
  a real dependency chain, and the user prefers one batch review over interruptions

- If a task's spec is unclear or incomplete:
  - Stop before stacking it
  - Ask for clarification on that task
  - Do not guess and keep building downstream tasks on top of a guess

- Make sure that once you start implementing the stack all the doubts have been
  clarified by asking to the user, so that you can proceed without interruptions

# Workflow

## Confirm the Task List

- Read the ordered tasks that will become the stack's branches and check each one
  states a problem and a solution
  ```text
  ### [ ] <Goal of first task>
  - <Change 1>
  - <Change 2>

  ### [ ] <Goal of second task>
  - <Change 1>
  - <Change 2>
  ```
- Confirm task `<ID+1>` depends only on task `<ID>`, not on `master` and not on an
  earlier task in the list
- If the order or a dependency is unclear, ask before starting: fixing a wrong
  dependency after the stack is built means rebasing everything above it

## Create the Issue and the First Branch (`_1`)

- One GH issue covers the whole stack, not one issue per branch

- Create the issue and the first branch / PR `<BASE>_1`

  ```bash
  > git_create_issue_and_branch.py \
      --title "<TITLE>" --body "<Description of entire stack>"
      --suffix 1
  ```
- The description of the entire task is 

- Commit the file passed by the user (e.g., `tasks.md`)

- Implement task 1, run the tests it touches, commit, push

## Stack Each Following Branch (`_<ID>`)

- For `ID` from 2 to `N`, while still checked out on branch `<BASE>_<ID-1>`:
  - Derive branch `<BASE>_<ID>` fresh from the issue, not from the current branch
    name, and branch it from `<BASE>_<ID-1>` instead of `master`:

    ```bash
    > invoke git_branch_create --issue-id <NUM> --suffix <ID> \
        --no-only-branch-from-master --no-abort-if-not-master --no-create-pr
    ```

    - Do not use `invoke git_branch_next_name` for this: it appends its own
      `_1`, `_2`, ... onto whatever branch is currently checked out, so run from
      `<BASE>_<ID-1>` it produces `<BASE>_<ID-1>_1`, not `<BASE>_<ID>`; only
      `--issue-id --suffix <ID>` derives `<BASE>_<ID>` correctly
    - Pass both `--no-only-branch-from-master` and `--no-abort-if-not-master`:
      with `only_branch_from_master` left at its default (`True`), the task
      switches to `master` before branching regardless of `abort_if_not_master`
  - Implement task `<ID>`, following `.claude/skills/coding.rules.md`
  - Run the tests it touches, following `.claude/skills/testing.rules.md`
  - Commit and push
  - Open the PR against the previous branch in the stack, not against `master`:

    ```bash
    > gh pr create --base <BASE>_<ID-1> --head <BASE>_<ID> --title "<TITLE>"
    ```

  - Do not stop for review between branches: move straight to `<BASE>_<ID+1>`
    once `<BASE>_<ID>`'s tests pass

## Report the Stack

- Confirm each PR's base with `gh pr view <BASE>_<ID> --json baseRefName`
- Report one ordered list back to the user: branch, PR link, base branch, for every
  `ID` in the stack, so the whole sequence can be reviewed at once

# How the Stack Gets Merged

- This is the user's process, downstream of this skill; it is documented here so a
  later run of this skill picks up an in-progress stack correctly
- The user reviews, edits, and merges PRs bottom-up, one at a time, not the whole
  stack at once
- After `<BASE>_<ID-1>`'s PR merges into `master`:
  - Retarget `<BASE>_<ID>`'s PR base to `master`, if GitHub did not already do it
    when the merged branch was deleted: `gh pr edit <BASE>_<ID> --base master`
  - Sync `<BASE>_<ID>` with the now-updated `master`:

    ```bash
    > invoke git_merge_master
    ```

    then resolve whatever conflicts come up, commit, push
    - This is a merge, not a rebase: if `<BASE>_<ID-1>` was squash-merged, expect
      a conflict even on identical content, since Git cannot tell the squashed
      commit and the original commits are the same change
  - Repeat for `<BASE>_<ID+1>` once `<BASE>_<ID>`'s PR merges, continuing
    bottom-up until the stack is gone
- Never force-push a branch whose PR has unresolved review comments without
  telling the user first

# Conventions

- Follow `.claude/skills/auto_task.rules.md` for queue, spec, and naming conventions
- Follow `.claude/skills/coding.rules.md` when implementing each task
- Follow `.claude/skills/testing.rules.md` for the tests each task adds or runs
- Follow the template `.claude/templates/auto_task.template.md` if a task in the
  stack turns out to need splitting mid-run
- Unlike a single-PR task in `.claude/skills/auto_task.rules.md`, a stack shares one
  issue across every branch

# Constraints

- Do not merge any PR in the stack: merging is the user's decision
- Do not move to the next task before the tests touched by the current one pass: an
  untested task compounds into everything stacked on top of it
- Do not squash or reorder commits across tasks without being asked
- Keep one task mapped to one branch and one PR: do not fold two queued tasks into a
  single branch to save steps
- One GH issue covers the whole stack: do not open a separate issue per branch

# Verification

- [ ] Every branch is named `<BASE>_<ID>`, including the first, with `ID` increasing
  by 1 up the stack
- [ ] Every branch's Git merge base is the previous branch in the stack, not
  `master`, except `<BASE>_1`, whose base is `master`
- [ ] Every PR's base matches its parent branch in the stack, not the repo's default
  branch, except `<BASE>_1`'s PR, whose base is `master`
- [ ] Every branch and PR in the stack was created under the one shared GH issue
  created alongside `<BASE>_1`
- [ ] The tests touched by each task passed before that task's branch was pushed
- [ ] The final report lists every branch and PR in dependency order with links
