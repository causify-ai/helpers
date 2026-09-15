---
description: Execute a sequence of tasks by dispatching them to Claude on GitHub
model: haiku
---

# Goal

- Execute a well-specified task `<FILE>` by delegating it to Claude running remotely
  on GitHub (the `claude-code-action` GitHub Action), instead of implementing it in
  this session
- The task becomes its own GitHub issue, branch, and draft PR, so the remote run is
  independent and proceed asynchronously, without a local checkout doing the work
- A task's whole spec lands in a single PR: Claude on GitHub may push multiple
  commits for different parts of the spec, but must never open a second PR for the
  same task
- Follow `.claude/skills/auto_task.rules.md` for how tasks are queued, specified, and
  named before they reach this skill

## Inputs
- `<FILE>` or a GitHub issue already filed (e.g., #580 or
  https://github.com/gpsaggese/gpsaggese.github.io/issues/580)

# When to Use This Skill

- Use it when tasks are specified clearly enough to hand to an unattended agent and
  do not need local interactivity, a local Docker container, or hands-on debugging
- Prefer `.claude/skills/auto_task.execute_interactively/SKILL.md` when tasks are
  exploratory or need a tight local feedback loop between runs
- Prefer `.claude/skills/auto_task.execute_with_stacked_prs/SKILL.md` when tasks form
  a real dependency chain and must be branched from each other, not run independently
- Follow `.claude/skills/auto_task.rules.md` section "Ask for Clarification Before
  Executing an Unclear Plan" when a task's spec is unclear or incomplete: do not let
  a remote run build on top of a guess

# Conventions

- Follow `.claude/skills/auto_task.rules.md` for queue, spec, and naming conventions
- Follow `.claude/skills/coding.rules.md` and `.claude/skills/testing.rules.md`: they
  apply to whatever code Claude on GitHub writes, even though it runs remotely and
  not in this session
- Claude on GitHub only starts on an explicit `@claude` mention in an issue's title
  or body, or in a comment on an issue or PR, per
  `helpers_root/.github/workflows/claude.yml`
  - Assigning the GH issue (`--gh_assignee`) does not by itself trigger a run

# Constraints

- Do not implement a task's code yourself: dispatch it to Claude on GitHub, then only
  monitor and report on the resulting run and PR
- Do not commit, push, or amend the branch created for a task: that branch is Claude
  on GitHub's to push to, and merging it is the user's decision
- Keep one PR per task: multiple commits on that PR's branch are fine when the spec
  has several parts, but never open a second issue/branch/PR for a task already
  dispatched

# Workflow

## Create Issue, if Needed

- If the GitHub issue has not been filed, then create it

### Confirm the Task List

- Read `<FILE>`, wrapped around the task list like

  ```text
  # Title
  <TITLE>

  # Goal
  <High level goal>

  # Workflow

  ### [ ] <Goal of first task>
  - <Change 1>
  - <Change 2>

  ### [ ] <Goal of second task>
  - <Change 1>
  - <Change 2>
  ```

- Follow `.claude/skills/auto_task.rules.md` section "Confirm the Task List Before
  Executing" for the task list format and the problem/solution check
- Keep `<FILE>` updated per that file's section "Track Task Status": `[-]` means
  dispatched with the remote run not finished, `[x]` means the PR is ready for human
  review


### Create the Issue, Branch, and Draft PR

- On the local checkout create the issue and a draft PR for the task, named per
  `.claude/skills/auto_task.rules.md`

  ```bash
  > git_create_issue_and_branch.py \
      --gh_issue_title "<TITLE>" \
      --gh_issue_body_file <FILE>
  ```

  - By default this only opens a branch/PR in the outer repo; pass `--submodules`
    when the task also touches a submodule, per `.claude/skills/auto_task.rules.md`
  - With `--submodules`, once a PR exists in more than one repo this call also
    refreshes the issue's `## Companion PRs` section automatically: no separate
    `--update_pr_links` step is needed here since the PR is created immediately,
    not deferred
- Return to `master` once the branch and draft PR exist: the implementation happens
  on GitHub, not in this checkout

  ```bash
  > git checkout master
  ```

## Trigger Claude on GitHub

- Post the task's spec as a PR comment with an explicit `@claude` mention, so
  `helpers_root/.github/workflows/claude.yml` picks it up

  ```bash
  > gh pr comment <PR_NUM> --body "Assigned to @claude"
  ```

## Monitor Each Remote Run

- Find the `claude.yml` run that the comment triggered

  ```bash
  > gh run list --workflow=claude.yml --branch <BRANCH> --limit 1
  ```

- Watch it to completion

  ```bash
  > gh run watch <RUN_ID>
  ```

- If a run fails, read its log and decide whether the fix belongs in a follow-up
  `@claude` comment or needs the user's input, and report which

## Verify Each Resulting PR

- Once a run succeeds, confirm the PR actually changed, not just replied in a comment

  ```bash
  > gh pr view <PR_NUM> --json commits,additions,deletions
  ```

  - Multiple commits on this one PR are fine, e.g. one per part of a multi-part spec
  - If a follow-up `@claude` comment ever produces a second PR for the same task,
    close the extra PR and keep the original: one PR per task, no exceptions
- Get the PR's CI to pass following
  `.claude/skills/github.get_pr_to_pass_ci/SKILL.md`
- Mark the task `[x]` in `<FILE>` only once its PR is ready for human review

## Report the Queue

- Report one list back to the user: task, issue, PR link, and run status, for every
  task in `<FILE>`, so the whole batch can be reviewed at once

# Verification

- [ ] Every dispatched task has its own GH issue, branch, and exactly one PR
- [ ] No task ended up with more than one PR (multiple commits on the same PR are
      fine)
- [ ] Every dispatch comment contains an explicit `@claude` mention
- [ ] No task's code was implemented locally in this session
- [ ] Every task's status in `<FILE>` reflects its actual remote progress (`[ ]`,
      `[-]`, or `[x]`)
- [ ] The final report lists every task with its issue, PR link, and run status
