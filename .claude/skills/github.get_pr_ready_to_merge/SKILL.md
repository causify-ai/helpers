---
description: Get the current PR to a state where it can be reviewed and merged
model: sonnet
---

# Goal

- Run the AI lint, the standard linter, the local tests, and GitHub CI for the
  current PR, fixing anything that comes up, so the PR is ready to be reviewed and
  merged

# Workflow

## Create and Update a Plan

- Create a file `plan-github.get_pr_ready_to_merge.md` with a plan in the form of a
  bullet list of actions and maintain it updated, by marking each action
  - [.] when something is in progress
  - [x] when something is done
  - [F] when something failed

- E.g.,
  ```
  # Plan: get PR #... ready to merge

  - [ ] Get PR number and branch name
  - [ ] Make sure PR is ready (not draft)
  - [ ] Run AI lint with --add_todos, commit TODOs
  - [ ] Resolve added TODO(ai_gp) items
  - [ ] Run standard linter, fix issues
  - [ ] Make local tests pass
  - [ ] Run and monitor GitHub CI
  - [ ] Report status on PR
  - [ ] Fix any CI failures
  ```

## Get the PR Number and Branch Name

- Get the PR number

  ```bash
  > GH_PR_NUM=$(gh pr view --json number -q .number)
  ```

- Get the branch name

  ```bash
  > BRANCH_NAME=$(git branch --show-current)
  ```

## Run the AI Lint and Add TODOs

- Run the AI-based linter on the branch, asking it to leave `TODO`s instead of
  silently rewriting the code

  ```bash
  > linters2/cc_lint.py --branch --add_todos
  ```

- Commit the added `TODO`s together with any other pending changes, following "Never
  Commit Junk Files" below

## Resolve the Added TODOs

- For each file that `cc_lint.py` annotated, use `/coding.todoai_gp` to implement the
  `TODO(ai_gp)` items it added
- Commit the fixes, following "Never Commit Junk Files" below

## Run the Standard Linter

- Run the repo's standard linter on the branch

  ```bash
  > linters2/lint.py --branch
  ```

- Commit any resulting changes, following "Never Commit Junk Files" below

## Fix Pyright Issues
- Fix the pyright warnings and errors in the branch
  ```bash
  > linters2/lint.py --clear_actions --action "pyright" --branch
  ```
- Commit any resulting changes, following "Never Commit Junk Files" below

## Make Sure Local Tests Pass
- Use `/github.get_pr_to_pass_local_tests` to run and fix the local unit tests for
  the branch

## Make Sure GitHub CI Passes
- Use `/github.get_pr_to_pass_ci_tests` to monitor GitHub CI, fix any failures, and
  report status on the PR

## Never Commit Junk Files

- Never run `git add -A` or `git add .` to stage a fix: it sweeps in every untracked
  file sitting in the working tree (logs, `tmp.*` scratch files, test-run artifacts
  like `.pkl`/`.json` caches, etc.), not just the files you intended to fix
- Always stage files explicitly by path, e.g. `git add <file1> <file2>`
- Before committing, run `git status --short` and review every listed file; drop
  anything that is not part of the intended fix
- If junk files were already committed and pushed, fix it by amending the commit to
  contain only the intended files and force-pushing (`git push --force-with-lease`),
  rather than leaving the junk in history

## Loop

- Keep repeating until the branch has no outstanding `cc_lint.py` `TODO`s, the
  standard linter is clean, and the local tests and the GitHub CI checks are all
  passing

# Constraints

- This skill runs both when executed locally on a dev computer and remotely on cloud
  (e.g., on GitHub or Anthropic infrastructure)

# Verification

- [ ] `linters2/cc_lint.py --branch --add_todos` adds no new `TODO`s
- [ ] No unresolved `TODO(ai_gp)` items remain in the branch's modified files
- [ ] `linters2/lint.py --branch` reports no issues
- [ ] Local unit tests pass (per `/github.get_pr_to_pass_local_tests`)
- [ ] `gh pr checks --watch $GH_PR_NUM` reports all checks successful (per
      `/github.get_pr_to_pass_ci_tests`)
- [ ] A PR comment reports the final CI status
- [ ] `git status --short` shows only the intended files staged before commit
