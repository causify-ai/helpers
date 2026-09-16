---
description: Propagate reviewed changes down an existing PR stack, keeping every PR mergeable
model: sonnet
---

# Goal

- Given the current PR is one branch in an existing stack of sequential PRs, each
  based on the previous one's branch, propagate the changes reviewed/modified in an
  earlier PR down into every PR stacked on top of it
- Preserve full history: propagate by merging forward and committing, never by
  rebasing or force-pushing
- End with every PR in the stack mergeable, with CI green

# When to Use This Skill

- Use after a PR in the middle (or bottom) of an existing stack was reviewed and
  changed (e.g. review feedback addressed), and the branches stacked on top of it now
  need those changes
- Do not use this to build a new stack from scratch: use
  `/auto_task.execute_with_stacked_prs` for that
- Follow `.claude/skills/auto_task.rules.md` section "Ask for Clarification Before
  Executing an Unclear Plan" whenever a PR's description does not make clear what it
  is meant to do: do not guess and merge blind

# Workflow

## Discover the Full Stack

- Get the current PR:
  ```bash
  > gh pr view --json number,title,baseRefName,headRefName,url
  ```
- Walk upward from the current PR's `baseRefName`, following each branch's own PR
  (`gh pr list --head <base> --state all`), until reaching the repo's default branch
  (`master`), to find the bottom of the stack
- Walk downward from the current PR's `headRefName`, repeatedly finding the open PR
  whose `baseRefName` equals the previous PR's `headRefName`
  (`gh pr list --base <branch> --state open`), to find the top of the stack
- Order the discovered PRs bottom (based on `master`) to top

## Print the Stack

- Print one table with columns `#`, `Branch`, `PR` (`#<NUM> — <title>`), `Base`, e.g.:
  ```
  │  #  │       Branch       │                            PR                            │  Base  │
  ├─────┼────────────────────┼──────────────────────────────────────────────────────────┼────────┤
  │ 1   │ ..._invoke_tasks   │ #1423 — auto-pick suffix in git_branch_create            │ master │
  ├─────┼────────────────────┼──────────────────────────────────────────────────────────┼────────┤
  │ 2   │ ..._invoke_tasks_2 │ #1424 — unit tests for git_*/gh_* tasks                  │ #1423  │
  ```

## Create and Confirm the Propagation Plan

- Create `plan-auto_task.restack.md` listing, for every consecutive pair
  `(PR_i, PR_i+1)` in the stack:
  - What `PR_i` changed, from its GH description and
    `git diff <base_i>...<head_i>`
  - What needs to merge into `PR_i+1`, and which files are likely to conflict
    (touched by both `PR_i` and `PR_i+1`)
- Wait for the user to confirm this plan before touching any branch
- Follow `.claude/skills/auto_task.rules.md` section "Ask for Clarification Before
  Executing an Unclear Plan" if a PR's own description does not explain its changes
  well enough to resolve conflicts correctly

## Propagate Changes Down the Stack

- Process pairs bottom-up, one at a time, so each merge already includes everything
  propagated so far
- For each pair `(PR_i, PR_i+1)`:
  - Read `PR_i`'s description (`gh pr view <PR_i> --json body,title`) so conflicts
    get resolved in line with its intent, not blindly
  - ```bash
    > git checkout <branch_i+1>
    > git pull
    > git merge <branch_i>
    ```
  - Resolve any conflicts by hand, favoring the intent of `PR_i`'s change; do not use
    `git rebase` and do not force-push, so history stays intact
  - Follow `.claude/skills/coding.rules.md` and `.claude/skills/testing.rules.md`
    while resolving conflicts in code and tests
  - Commit the merge and push: `git push`
- Repeat up through the top of the stack

## Make Every PR Mergeable

- For every PR in the stack, in order, run `/github.get_pr_ready_to_merge` to get its
  CI green
- After propagation, confirm mergeability:
  ```bash
  > gh pr view <NUM> --json mergeable,mergeStateStatus
  ```

## Report Only Failures

- Do not post a comment on a PR that merged cleanly and passed CI
- If a PR hits an unresolved conflict or a CI failure that needs human input, post
  one comment on it explaining the problem:
  ```bash
  > gh pr comment <NUM> --body "<what failed and why>"
  ```
- Also stop and describe the problem to the user directly rather than leaving it only
  in a PR comment

# Conventions

- Follow `.claude/skills/auto_task.rules.md` for clarification conventions
- Follow `.claude/skills/coding.rules.md` and `.claude/skills/testing.rules.md` when
  resolving conflicts
- Follow `.claude/skills/github.get_pr_ready_to_merge/SKILL.md` to get each PR's CI
  green

# Constraints

- Never rebase or force-push a branch in the stack: propagate with merge commits
  only, to preserve review history
- Never merge any PR: merging remains the user's decision
- Never skip a PR in the stack or reorder the propagation: always go strictly
  bottom-up
- Never guess the intent of an unclear PR when resolving a conflict: stop and ask
  instead

# Verification

- [ ] The full stack was discovered from `master` up through the top PR, matching
      GitHub's actual base chain
- [ ] `plan-auto_task.restack.md` lists every consecutive pair and was confirmed by
      the user before any branch was touched
- [ ] Every merge between stacked branches is a merge commit, not a rebase; no branch
      was force-pushed
- [ ] `gh pr view <NUM> --json mergeable` reports `MERGEABLE` for every PR in the
      stack
- [ ] `/github.get_pr_ready_to_merge` ran on every PR and its CI is green
- [ ] A PR comment exists only for PRs that hit a conflict or CI failure needing
      human input
