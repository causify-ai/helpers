# Auto_task Workflow: From Task List to Merged PR

- This document explains the flow for running an `auto_task`, an approach / framework
  to delegate work to agentic coding AIs

## What Is an Auto_task

- An `auto_task` is a unit of work an agent completes end to end with minimal
  supervision, made of:
  - A spec (a task list, or a GitHub issue)
  - One or more Git branches
  - One or more pull requests
- One GitHub issue is always the unit of work, even when the solution spans multiple
  branches, PRs, or repos
  - See `.claude/skills/auto_task.rules.md` section "The Unit of Work"

## Commands at a Glance

| Stage   | Command                                      | Purpose                                          |
| :------ | :------------------------------------------- | :----------------------------------------------- |
| Create  | `/auto_task.create_specs_from_todos`         | Turn a cfile of TODOs into a `tasks.md` plan     |
| Review  | `/auto_task.criticize`                       | Review a plan or GitHub issue before execution   |
| Execute | `/auto_task.execute_interactively`           | Run tasks in a local execute-review-commit loop  |
| Execute | `/auto_task.execute_with_stacked_prs`        | Run tasks as one stack of dependent branches/PRs |
| Execute | `/auto_task.execute_remotely_with_single_pr` | Dispatch tasks to Claude on GitHub               |

## Step 1: Create a Task List

- Two ways to get a `tasks.md`:
  - Write it by hand from `.claude/templates/auto_task.template.md`
  - Generate it from a list of TODOs with `/auto_task.create_specs_from_todos`
- See `.claude/skills/auto_task.create_specs_from_todos/SKILL.md` for the
  TODO-to-plan skill

## Step 2: Criticize the Plan

- Review the task list before execution:

  ```text
  claude> /auto_task.criticize tasks.md
  ```

- The skill checks:
  - The problem and the solution are both clear and unambiguous
  - Every affected repo is identified, and multi-repo `PR<NUM>` blocks are labeled by
    repo
  - Any needed clarification is requested before execution starts
- See `.claude/skills/auto_task.criticize/SKILL.md`

## Step 3: Choose an Execution Mode

- The three execution modes trade off supervision, review granularity, and PR shape
- **Interactively** (`/auto_task.execute_interactively`):
  - Runs locally in a loop: execute, review, commit, one task at a time
  - Best for exploratory tasks that need a tight local feedback loop
  - See `.claude/skills/auto_task.execute_interactively/SKILL.md`
- **Stacked PRs** (`/auto_task.execute_with_stacked_prs`):
  - Builds a whole stack of dependent branches and PRs without stopping for review
    between them
  - Best when tasks form a real dependency chain and specs are already complete
  - See `.claude/skills/auto_task.execute_with_stacked_prs/SKILL.md`
- **Remotely with a single PR** (`/auto_task.execute_remotely_with_single_pr`):
  - Dispatches the task to Claude on GitHub (`claude-code-action`) and runs
    asynchronously, without a local checkout doing the work
  - Best for clearly specified tasks that do not need local interactivity, Docker, or
    hands-on debugging
  - See `.claude/skills/auto_task.execute_remotely_with_single_pr/SKILL.md`

## Creating the Issue and Branch Manually

- Every execution mode creates the GitHub issue, branch, and (draft) PR through
  `git_create_issue_and_branch.py`
  - E.g.,

    ```bash
    > git_create_issue_and_branch.py \
        --gh_issue_title "Replace pathlib.Path uses with os.path" \
        --gh_issue_body_file tasks.md
    ```

- Pass `--submodules` when the task also touches a submodule (e.g., `helpers_root`),
  and `--update_pr_links` to refresh the issue's companion PR links afterward
- See `.claude/skills/auto_task.rules.md` section "Multi-Repo Issues, Branches, and
  PRs" for when and how to use `--submodules`

## Reference

- `.claude/skills/auto_task.rules.md`: naming, multi-repo handling, task list format,
  and clarification conventions
- `.claude/templates/auto_task.template.md`: template for a GitHub issue's
  problem/solution plan
