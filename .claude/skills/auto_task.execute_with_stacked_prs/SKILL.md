---
description: Execute a sequence of tasks as one stack of branches and PRs
model: haiku
---

# Goal

- Execute an ordered list of well-specified, sequential tasks as one stack of
  branches and PRs
- Let the agent work through the whole sequence without stopping for review between
  tasks, then hand the user a single stack to review in one batch
- Follow `.claude/skills/auto_task.rules.md` for how tasks are queued, specified, and
  named before they reach this skill

# When to Use This Skill

- Use it only when the tasks favor stacked execution: specs are complete, tasks form
  a real dependency chain, and the user prefers one batch review over interruptions
- If a task's spec is unclear or incomplete:
  - Stop before stacking it
  - Ask for clarification on that task
  - Do not guess and keep building downstream tasks on top of a guess

# Workflow

## Step 1: Confirm the Task List

- Read the ordered tasks and check each one states a problem and a solution
- Confirm task `<N+1>` depends only on task `<N>`, not on `master` and not on an
  earlier task in the list
- If the order or a dependency is unclear, ask before starting: fixing a wrong
  dependency after the stack is built means rebasing everything above it

## Step 2: Pick the Stacking Mechanism

- Choose between:
  - GitHub-native stacked PRs: chain branches with `git` and
    `gh pr create --base <parent_branch>`

## Step 3: Create the First Branch

- Branch task 1 from `master`
  - `invoke git_branch_create` is correct here unmodified: it defaults to
    `only_branch_from_master=True` and `abort_if_not_master=True`
  - Name the branch per `.claude/skills/auto_task.rules.md`
    `## Name Branches and PRs After the Issue`
- Implement task 1, run the tests it touches, commit, push

## Step 4: Stack Each Following Task

- For task `<N>` where `<N>` is greater than 1:
  - Branch from task `<N-1>`'s branch, not from `master`
    - `invoke git_branch_create` cannot do this: it always forces `master` unless
      called with `--no-only-branch-from-master --no-abort-if-not-master`
    - It is simpler to branch manually:

      ```bash
      > git checkout -b <branch_N> <branch_N-1>
      > git push -u origin <branch_N>
      ```

  - Implement task `<N>`, following `.claude/skills/coding.rules.md`
  - Run the tests it touches, following `.claude/skills/testing.rules.md`
  - Commit and push
  - Open the PR against its parent branch, not against `master`:
    - `invoke gh_create_pr` always targets the repo's default branch, so it cannot
      express a stacked base; call `gh` directly:

      ```bash
      > gh pr create --base <branch_N-1> --head <branch_N> --title "<title>"
      ```

    - With `git-spice`: `gs branch create <branch_N> -m "<msg>"` stacks automatically
      on the branch checked out
  - Do not stop for review between tasks: move straight to task `<N+1>` once task
    `<N>`'s tests pass

## Step 5: Submit and Report the Stack

- GitHub-native: the PRs already exist from Step 4; confirm each base with
  `gh pr view <branch_N> --json baseRefName`
- `git-spice`: run `gs stack submit` once, after every branch exists, to open or
  update all PRs in the stack together
- Report one ordered list back to the user: branch, PR link, base branch, for every
  task in the stack, so the whole sequence can be reviewed at once

## Step 6: Handle a Fix Requested Mid-Stack

- If feedback lands on task `<K>` where `<K>` is earlier than `<N>`:
  - GitHub-native: fix on branch `<K>`, commit, push, then for every downstream
    branch from `<K+1>` to `<N>`, in order: `git rebase <parent>` followed by
    `git push --force-with-lease`
  - `git-spice`: fix on branch `<K>`, run `gs commit amend`, then `gs stack submit`;
    it restacks everything downstream automatically
- Never force-push without `--force-with-lease`
- Never rewrite a branch's history once its PR has unresolved review comments without
  telling the user first

# Conventions

- Follow `.claude/skills/auto_task.rules.md` for queue, spec, and naming conventions
- Follow `.claude/skills/coding.rules.md` when implementing each task
- Follow `.claude/skills/testing.rules.md` for the tests each task adds or runs
- Follow the template `.claude/templates/github_PR_plan.template.md` if a task in the
  stack turns out to need splitting mid-run

# Constraints

- Do not merge any PR in the stack: merging is the user's decision
- Do not move to the next task before the tests touched by the current one pass: an
  untested task compounds into everything stacked on top of it
- Do not squash or reorder commits across tasks without being asked
- Keep one task mapped to one branch and one PR: do not fold two queued tasks into a
  single branch to save steps

# Verification

- Every branch in the stack, after the first, has its parent branch as its Git merge
  base, not `master`
- Every PR's base matches its parent branch in the stack, not the repo's default
  branch
- The tests touched by each task passed before that task's branch was pushed
- The final report lists every branch and PR in dependency order with links
