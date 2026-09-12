---
description: Execute a sequence of tasks in a loop "execute -> review -> commit"
model: haiku
---

# Goal

- Execute an ordered list of well-specified, sequential tasks `<FILE>` specified by
  the user by alternating agent execution, human review, and commit in a branch
- Follow `.claude/skills/auto_task.rules.md` for how tasks are queued, specified, and
  named before they reach this skill

# When to Use This Skill

- Follow `.claude/skills/auto_task.rules.md` section "Ask for Clarification
  Before Executing an Unclear Plan" when a task's spec is unclear or incomplete

# Conventions

- Follow `.claude/skills/auto_task.rules.md` for queue, spec, and naming conventions
- Follow `.claude/skills/coding.rules.md` when implementing each task
- Follow `.claude/skills/testing.rules.md` for the tests each task adds or runs

# Constraints

- Do not commit any change: committing is user's decision
- Do not merge any PR: merging is the user's decision

# Workflow

## Confirm the Task List

- Read `<FILE>` and follow `.claude/skills/auto_task.rules.md` section "Confirm
  the Task List Before Executing" for the task list format and the
  problem/solution check
- Make sure each task is clear and create a plan in 5 markdown bullets in `<FILE>`
  under each task
- If the order or a dependency is unclear, ask before starting: fixing a wrong
  dependency after the stack is built means rebasing everything above it

## Loop over the Tasks

### Execute Each Task

- Execute each task following the instructions in `@.claude/task_instructions.md`
- Keep `<FILE>` updated per `.claude/skills/auto_task.rules.md` section "Track
  Task Status"

### Verify Each Task

- If the N-th task requires writing code, test the code both locally and in the CI
  following the procedures here
  - `.claude/skills/pr.get_ci_to_pass/SKILL.md`
  - `.claude/skills/pr.get_local_tests_to_pass/SKILL.md`
  - `.claude/skills/pr.get_to_commit_state/SKILL.md`

### Wait for User to Confirm
- After each task is complete, wait for the user to confirm, validate, review the
  changes and then commit
- Once the user confirms that the N-th task is complete, move to the N+1 following
  the same procedure as per `Loop over the Tasks`

# Verification
- [ ] Every task's status in `<FILE>` reflects its actual progress (`[ ]`, `[-]`,
  or `[x]`)
- [ ] The tests touched by each task pass locally and in CI before that task is
  marked done
- [ ] No task started before its spec was clarified with the user
- [ ] No commit was made without the user's confirmation
