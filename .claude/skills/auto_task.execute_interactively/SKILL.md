---
description: Execute a sequence of tasks in a loop "execute -> review -> commit"
model: haiku
---

# Goal

- Execute an ordered list of well-specified, sequential tasks `<FILE>` specified by
  the user by alternating agent execution, human review, and commit in a branch
- Create the GH issue, branch, and PR for `<FILE>` before starting the task loop:
  every `auto_task` maps to one GH issue implemented in one branch/PR (see
  `.claude/skills/auto_task.rules.md`)
- Follow `.claude/skills/auto_task.rules.md` for how tasks are queued, specified, and
  named before they reach this skill

# When to Use This Skill

- Follow `.claude/skills/auto_task.rules.md` section "Ask for Clarification Before
  Executing an Unclear Plan" when a task's spec is unclear or incomplete

# Conventions

- Follow `.claude/skills/auto_task.rules.md` for queue, spec, and naming conventions
- Follow `.claude/skills/coding.rules.md` when implementing each task
- Follow `.claude/skills/testing.rules.md` for the tests each task adds or runs

# Constraints

- Do create the GH issue, branch, and (draft) PR for `<FILE>` up front: this is part
  of this skill's job, not the user's
- Do not commit any code change for a task: committing is user's decision
- Do not merge any PR: merging is the user's decision

# Workflow

## Confirm the Task List

- Read `<FILE>` and follow `.claude/skills/auto_task.rules.md` section "Confirm the
  Task List Before Executing" for the task list format and the problem/solution check
- Make sure each task is clear and create a plan in 5 markdown bullets in `<FILE>`
  under each task
- If the order or a dependency is unclear, ask before starting: fixing a wrong
  dependency after the stack is built means rebasing everything above it

## Create the Issue and the Branch

- One GH issue covers the whole task list in `<FILE>`; do not open a separate issue
  per task (see `.claude/skills/auto_task.rules.md`, "One GitHub Issue Is the Unit of
  Work")
- Create the issue and the branch named after it
  (`<RepoPrefix>Task<IssueNum>_<Description>`) in one shot with
  `git_create_issue_and_branch.py`: it is more general than the raw
  `invoke gh_issue_create` / `invoke git_branch_create` tasks since it also branches
  submodules (e.g., `helpers_root`) symmetrically

  ```bash
  > git_create_issue_and_branch.py \
      --gh_issue_title "<TITLE>" --gh_issue_body "<Description of the task list>" \
      --no_create_pr
  ```

  - Pass `--gh_issue_id <NUM>` instead of `--gh_issue_title` to reuse an existing
    issue rather than creating a new one
  - `--no_create_pr`: a PR needs at least one commit ahead of `master`, so do not
    open it yet here; open it after the first task's changes are committed (see "Wait
    for User to Confirm" below)
- `git add` (do not commit) `<FILE>` on the new branch so its plan is tracked from
  the start, per `@.claude/task_instructions.md`

## Loop Over the Tasks

### Execute Each Task

- Execute each task following the instructions in `@.claude/task_instructions.md`
- Keep `<FILE>` updated per `.claude/skills/auto_task.rules.md` section "Track Task
  Status"

### Verify Each Task

- If the N-th task requires writing code, test the code both locally and in the CI
  following the procedures here
  - `.claude/skills/github.get_pr_to_pass_ci/SKILL.md`
  - `.claude/skills/github.get_pr_to_pass_local_tests/SKILL.md`
  - `.claude/skills/github.get_pr_to_commit_state/SKILL.md`

### Wait for User to Confirm

- After each task is complete, wait for the user to confirm, validate, review the
  changes and then commit
- Push the commit; if the branch has no PR yet (first task), open the draft PR now
  that there is a commit to diff against `master`
  - If the task spans more than one repo (see `.claude/skills/auto_task.rules.md`
    "Multi-Repo Issues, Branches, and PRs"), open the draft PR in every affected
    repo, then refresh the issue's companion PR links:

    ```bash
    > git_create_issue_and_branch.py --gh_issue_id <NUM> --submodules \
        --update_pr_links
    ```

- Once the user confirms that the N-th task is complete, move to the N+1 following
  the same procedure as per `Loop over the Tasks`

# Verification

- [ ] One GH issue and one branch/PR were created for `<FILE>` before the task loop
      started, named per `.claude/skills/auto_task.rules.md`
- [ ] Every task's status in `<FILE>` reflects its actual progress (`[ ]`, `[-]`, or
      `[x]`)
- [ ] The tests touched by each task pass locally and in CI before that task is
      marked done
- [ ] No task started before its spec was clarified with the user
- [ ] No commit was made without the user's confirmation