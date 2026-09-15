# Todo Janitor Workflow

## Overview
- `todo_janitor` automates finding, branching, fixing, and committing TODO
  items across repos
- Steps:
  - Update the issue list
  - Pick an issue and create a branch/worktree
  - Fix the issue with CC
  - Commit the changes

## 1. Update the Issue List
- Before picking an issue, make sure `plan.todo_janitor.md` is current
  ```text
  claude> Look at the last merged git PRs in master and in the current repo
  and mark the completed issues in plan.todo_janitor.md
  ```
- See `todo_janitor.prompt.update_plan.md` for the full update prompt

## 2. Pick an Issue and Create CC Instructions
- Work from the `helpers1` tree: this is the tree that orchestrates
  everything
- Pick an issue from `plan.todo_janitor.md`
- Create `todo_janitor.issue.md` for the picked issue
- Create CC instructions from `todo_janitor.instr.md`

## 3. Create the Branch and Worktree
- Use `create_git_worktree.py` to create the branch and worktree:
  ```bash
  > create_git_worktree.py \
    --gh_issue_title 'Clean up' \
    --gh_issue_body_file todo_janitor.current_issue.md

  > create_git_worktree.py \
    --gh_issue_title "Rename invocations to sys_calls Throughout Codebase" \
    --gh_issue_body body.txt \
    --instr_file instr2.md

  > create_git_worktree.py \
    --gh_issue_id 1292 \
    --instr_file instr2.md
  ```
- `instr2.md` drives the worktree until the PR is ready:
  - Wait for GitHub checks to pass
  - Run `pytest_multi_build.py --target .` locally
  - Mark the PR ready once local tests pass
  - Ask for review
- Check the PR is ready to review:
  ```bash
  > gh pr view
  ```
  ```text
  gp_scratch_36 causify-ai/helpers#1330
  Draft - gpsaggese (GP Saggese) wants to merge 2 commits into master from
  gp_scratch_36 - about 4 minutes ago
  +2359 -836 - Checks passing
  ```

## 4. Fix the Issue
- Check out the branch:
  ```bash
  > git checkout HelpersTask1299_TODO_clean_up
  ```
- Enable CC to commit:
  ```bash
  > .claude/control_cc_commit.py --enable
  ```
- Run the fix flow:
  ```text
  claude> Execute todo_janitor.template.md
  ```
- See `dev_scripts_helpers/ai/todo_janitor.template.md` for the full
  fix-to-PR checklist (CI, local tests, ready-for-review)

## 5. Commit the Changes
- Commit once the fix flow completes and tests pass

## Future Automation
- Automate steps 2-3 with `orchestrate_task.py`
  - `--action stage_todo` would call `create_git_worktree.py` to:
    - Create the issue body and `instr.md`
    - Update `plan.todo_janitor.md`

## Open Items
- [ ] Convert `todo_janitor.template.md` into a single script: CC does not
  always follow the markdown template's directions
