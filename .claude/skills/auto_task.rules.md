- This file contains the conventions for creating, queuing, and executing an
  `auto_task`: a unit of work an agent completes end to end (spec, branch, PR) with
  minimal supervision

# Plan Format

## Follow the Plan Template

- A GitHub issue's problem/solution plan follows the template in
  `.claude/templates/auto_task.template.md`
- It states the problem and the goal before proposing a solution
- It breaks the solution into one `PR<NUM>` section per PR when the issue spans more
  than one PR

## Ask for Clarification Before Executing an Unclear Plan

- If the problem or the solution is not perfectly clear:
  - You MUST NOT perform the task
  - Ask for clarification
  - Create a `plan.Issue<GH ISSUE NUM>.PR<PR NUM>.md` in the same directory with 5
    bullet points explaining the plan and wait for confirmation
- This applies per task when executing a task list (below): stop before that task,
  ask for clarification on it, and do not guess and build (or dispatch) further work
  on top of a guess

## Follow the Coding and Testing Rules

- When writing code, follow `.claude/skills/coding.rules.md`
- When writing testing code, follow `.claude/skills/testing.rules.md`
- Follow the specs in `.claude/rules.md` for other types of files

# Executing a Task List

## Confirm the Task List Before Executing

- A task list is an ordered set of tasks, each with a goal and its changes
  following the format in `.claude/templates/auto_task.template.md`
- Check that each task states a problem and a solution before starting on it
- If a task's spec is unclear or incomplete, follow "Ask for Clarification Before
  Executing an Unclear Plan" above instead of guessing

## Track Task Status

- Mark each task's status in the task list file as work proceeds
  - `[ ]` not started
  - `[-]` in progress (e.g., dispatched, or a run in progress)
  - `[x]` done

## The User Owns Commit and Merge Decisions

- An agent never commits a code change without the user reviewing and confirming it
  first
- An agent never merges a PR: merging (and force-pushing over unresolved review
  comments) is always the user's call
- This applies regardless of execution mode (interactive, stacked, or remote): an
  agent may push commits to a task's own branch, but the decision to land them
  belongs to the user

# The Unit of Work

## One GitHub Issue Is the Unit of Work

- An `auto_task` normally maps to one GitHub issue, implemented as one or more Git
  branches and as one or more PRs
- A large refactor can span multiple branches/PRs for the same issue, e.g. split into
  chunks for safety and ease of review

## Name Branches and PRs After the Issue

- Name the branch and PR after the issue title:
  `<RepoPrefix>Task<IssueNum>_<Description>`
  - E.g., issue 123 "Do this and that" becomes `HelpersTask123_Do_this_and_that`
- Decorate with a numeric suffix when an issue has more than one branch/PR:
  `<RepoPrefix>Task<IssueNum>_<Description>_<Id>`
  - Get the next free suffix with `invoke git_branch_next_name`
- `invoke git_branch_create` enforces this pattern (`{RepoPrefix}Task\d+_\S+`)

## Multi-Repo Issues, Branches, and PRs

- When a task's solution spans more than one repo (e.g., an outer repo and its
  `helpers_root` submodule), there is still only one GitHub issue, filed in the
  outermost repo's tracker: a submodule has its own, disjoint issue numbering and is
  never where the issue lives
- The task description explicitly clarifies this through

  ```
  * Repo: <Which repos are affected>
  ```

  - Determine which repo a changed file belongs to before filling this in: a
    `<FILE>` path under `helpers_root/` is the `helpers` repo, everything
    else is `umd_classes`
- The branch and the PR opened in every affected repo share one name, derived once
  from that single issue (see "Name Branches and PRs After the Issue" above), not a
  separate name per repo
- `git_create_issue_and_branch.py` creates the branch (and draft PR) in the outer
  repo only by default
  - Pass `--submodules` to also create the same branch/PR, by name, in every
    submodule, so the issue, the branches, and the PRs all stay aligned
- When a PR ends up existing in more than one repo,
  `git_create_issue_and_branch.py` appends a `## Companion PRs` section to the
  issue body listing every repo's PR link, so the one issue stays the source of
  truth for the whole task, instead of opening a second issue per repo
  - This runs automatically at the end of a `--submodules` call that also
    creates the PRs
  - If a PR is opened later instead (e.g., a draft PR opened after the first
    commit, per
    `.claude/skills/auto_task.execute_interactively/SKILL.md`), refresh the
    section on its own:

    ```bash
    > git_create_issue_and_branch.py --gh_issue_id <NUM> --submodules \
        --update_pr_links
    ```

  - Never hand-edit the `## Companion PRs` section: it is regenerated, not
    appended to, so a hand edit is overwritten on the next refresh

## Review Specs Before Executing

- Use `/auto_task.criticize` to read a plan or GitHub issue and confirm both the
  problem and the solution are clear before assigning it to an agent
- Prioritize tasks with high confidence in the fix and low complexity first
