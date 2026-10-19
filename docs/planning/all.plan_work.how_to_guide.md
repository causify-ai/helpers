# Plan Work

## Summary

- This document describes how we plan and track the work of a project:
  - Write one end-to-end plan that says what to build and in which order
  - Execute the plan one small, reviewable PR at a time
  - Keep a log of everything done, including decisions
- The process is the same for any project in any repo
  - Rules specific to one repo (e.g., fork flow, naming) live in the docs of that
    repo
  - This is "how we do things": other projects follow the same process
    - A new project copies the structure of the example below and points to this
      document, see [Write a Project Meta-Doc](#write-a-project-meta-doc)
- Example:
  - the `Noesis` project in the `umd_classes` repo
  - `research/Noesis/docs/plans/plan.Noesis.md`: end-to-end plan
  - `research/Noesis/docs/plans/mvp_progress.md`: log of what was done
  - `research/Noesis/docs/how_we_work.md`: what `Noesis` adds to this process
- This document points to the existing docs instead of repeating them
  - See [Resources](#resources)

## Planning Hierarchy

- Work flows from abstract to concrete:
  ```text
  Idea -> Project -> Task (GitHub issue) -> PR
  ```
- Idea, Project, and Task are defined in
  [`all.issue_workflow.explanation.md`](../work_organization/all.issue_workflow.explanation.md)
- This document covers what is below the idea level:
  - How to write the plan of a project
  - How to cut the plan into PRs
  - How to log the progress
- One task maps to one or more PRs
  - A PR is the unit of review

## Plan Documents

- A project uses a few documents, each one answering one question:

  | Document                 | Question it answers           | Noesis example     |
  | :----------------------- | :---------------------------- | :----------------- |
  | `plan.<Project>.md`      | What to build, in which order | `plan.Noesis.md`   |
  | `<project>_plan.md`      | Who does what, by when        | `mvp_plan.md`      |
  | `<project>_progress.md`  | What is done, learned, next   | `mvp_progress.md`  |
  | `<project>_decisions.md` | Why it is built this way      | `mvp_decisions.md` |
  | `spec.<PR_ID>.md`        | How one complex PR is built   | `spec.PR_P2.md`    |
  | `how_we_work.md`         | How the team works on it      | `how_we_work.md`   |

- Start with `plan.<Project>.md`, the progress log, and `how_we_work.md`
  - Add the others only when needed
- `how_we_work.md` is the meta-doc of the project
  - See [Write a Project Meta-Doc](#write-a-project-meta-doc)
- `<project>_plan.md` is the execution plan
  - It splits the PRs of the plan into smaller tasks with owners, dates, and
    acceptance criteria
  - Create it only when several people work in parallel
- `spec.<PR_ID>.md` is an implementation spec for one complex PR
  - Follow the template `.claude/templates/specs.template.md`

## The Loop

- Every change follows the same loop:
  1. Pick a task from the plan, or propose one
  2. Plan before code: write a short design and get a teammate's OK
     - What changes, which files, which interfaces, which tests, which choices are
       still open
     - Put a non-trivial design in the GitHub issue
  3. Open a GitHub issue, see "Naming an Issue" in
     [`all.use_github.how_to_guide.md`](../work_organization/all.use_github.how_to_guide.md#naming-an-issue)
     - Write the issue number down: it goes in the branch name, the commits, and the
       PR
     - Point to the section of the plan or of the spec in the issue, do not copy it
       (DRY)
  4. Branch from the latest `master`, named after the issue
     - See "Branch workflow best practices" in
       [`all.git.how_to_guide.md`](../tools/git/all.git.how_to_guide.md#branch-workflow-best-practices)
  5. Write the code and the tests following the conventions in `.claude/rules.md`
     - Run the tests locally
  6. Commit specific files, never `git add .`
     - See "Write helpful commit messages" in
       [`all.git.how_to_guide.md`](../tools/git/all.git.how_to_guide.md#write-helpful-commit-messages)
  7. Open a PR with the [PR description template](#pr-description-template)
     - See "Filing a New PR" in
       [`all.use_github.how_to_guide.md`](../work_organization/all.use_github.how_to_guide.md#filing-a-new-pr)
  8. Review: a teammate first, then the integrator
     - Address the comments in new commits on the same branch
  9. Merge, then update the plan and the log, see
     [Keep Docs in Sync](#keep-docs-in-sync)
- Keep PRs reviewable
  - One component or one milestone task per PR
  - If a PR needs more than ~400 lines of non-test code, split it
  - See
    [`all.submit_code_for_review.how_to_guide.md`](../coding/all.submit_code_for_review.how_to_guide.md#stick-to-smaller-prs)
    and the template `.claude/templates/github_PR_plan.template.md`
- Do a task step by step with Claude Code
  - See
    [`all.create_pr_with_claude_code.how_to_guide.md`](../tools/ai/all.create_pr_with_claude_code.how_to_guide.md)
- Delegate a task list to an AI agent with the `auto_task` flow
  - See [`all.auto_task.how_to_guide.md`](../tools/ai/all.auto_task.how_to_guide.md)

## Create an End-to-End Plan

- Goal: one canonical file that says what to build and in which order, so that
  anyone can pick the next PR without asking
- Create the file `plan.<Project>.md` in the `docs/plans/` dir of the project
  - E.g., `research/Noesis/docs/plans/plan.Noesis.md`
- Steps to create it:
  1. Write the goal and point to the background (paper, PRD, architecture doc)
  2. List the components and their open questions
  3. Split the work into versions, where each version can be run and demoed
  4. Write the PR entries of the next version in detail
     - Later versions can stay as a few bullets until they are close
     - File GitHub issues only for the immediate work (the next version)
       - The plan often changes after the first iteration
       - Issues for later versions would go stale and need to be rewritten
  5. Review the plan before executing it
     - See `/auto_task.criticize`
- To break a complex feature into an ordered PR plan with a spec per complex PR, see
  `/auto_task.create_plan_for_feature`

### Structure of the Plan File

- Mirror the structure of `plan.Noesis.md`:
  - `# <Project> Implementation Plan`
  - `## Goal`
    - What we build
    - Pointers to the background, not a copy of it
  - `## Plan Hierarchy`
    - How this file relates to the execution plan and to the progress log
    - What a checked and an unchecked PR mean
  - `## Roadmap`
    - One bullet per version (`v0.1`, `v0.2`, ...) with its deliverable
    - Under each version, a checkbox list of the PR ids it needs
    - State that releases are cumulative: a version also needs the PRs of the
      versions before it
  - `# Component Specs`
    - One `## <Component>` section per component
    - Each with `### Goal` and `### Open Questions`
    - Number the open questions and tag with `-> Project` those that need their
      own project
  - `# PRs`
    - One `## <version>: <Title>` section per version, in roadmap order
    - Then one `## Unscheduled: <Component>` section per component
  - `## Conventions`
    - Pointers to the coding and testing rules, not a copy

### Format of a PR Entry

- Use one H3 per PR, with the PR id and a checkbox:
  ```markdown
  ### `PR_M10`: [ ] <Title>

  - Background: <what exists today, with file paths, and the gap>
  - <Change 1>
  - <Change 2>
  - Unit tests: <what the tests check>
  - Result: <what a user can do after this PR that was not possible before>
  ```
- Fill the entry like this:
  - **Background**: the current state and the problem, with file and function names
  - **Changes**: concrete and testable, one bullet per change
  - **Unit tests**: the behavior to check, not only "add tests"
  - **Result**: the capability that exists after the PR

### Rules for the Plan

- Name each PR `PR_<component letter><number>`
  - The id is stable: never reuse it and never renumber it
  - List the PRs in roadmap order, not in id order
- Check `[x]` a PR only when it is merged
  - For a partly done PR, state the status in its entry
- Make each version a deliverable that a person can run or demo
- Write a spec for a complex PR instead of growing its entry
  - Follow `.claude/templates/specs.template.md`
- Do not copy content that lives elsewhere (papers, PRD, architecture): point to it
- Change the plan in a PR, like code
  - Log why it changed in the progress log

## Keep a Progress Log

- Goal: one file that records everything done, including decisions
  - A new person sees what happened and why without asking
- Create the file `<project>_progress.md` next to the plan
  - E.g., `research/Noesis/docs/plans/mvp_progress.md`

### Structure of the Log File

- Mirror the structure of `mvp_progress.md`:
  - `## Status`
    - One row per milestone with target date and status
    - Link the PR that closed it
  - `## Built`
    - One bullet per component that exists
    - Point to its design doc instead of describing it
  - `## Findings`
    - Numbered facts learned, each with the measured number
    - Link the raw data (e.g., a `findings/` dir)
  - `## Next`
    - The next tasks in order, taken from the plan
  - `## History`
    - One row per date, with what was done and the PRs merged
- Use this skeleton for the history:
  ```markdown
  ## History

  | Date   | Done                                              |
  | :----- | :------------------------------------------------ |
  | <date> | <What was done, PR merged, decision taken>        |
  ```

### Rules for the Log

- Append to the history, do not rewrite the past rows
  - The newest row is the last one
- Log all the work
  - Merged PRs
  - Findings, including negative results
  - Decisions
  - Work that was cancelled, and why
- Log facts, not plans
  - Plans live in `plan.<Project>.md`
- Give each finding its evidence
  - What was measured, where, and the number with its unit
- Record each experiment so that others can reproduce it
  - The configuration and the commands
  - The model or provider identity, when relevant
  - The observed results and the limitations
  - The links to the evidence
- Write dates in UTC, as GitHub reports them
- Link the record from its issue and PR
- Do not commit secrets, private data, or large raw artifacts without an agreed
  storage approach
- Update the log in the PR that finishes the task

### Log Entry per PR

- When a History row is too short for a PR, replace the table with one section
  per merged PR
  - Add each new section after the older ones, so the newest is the last
- Use this skeleton for each section:
  ```markdown
  ## <date>: <PR title>

  - **Issue**: <link>, closed by the PR
  - **PR**: <link>, by <author>, opened <date>, merged <date>
  - **Milestone**: <milestone, or none>
  - **What was done**: <one bullet per change>
  - **Testing**: <what was run, with the results>
  - **CI note**: <failing checks that the PR did not cause, and why>
  - **Note**: <how AI was used, and that the author reviewed every change>
  ```
- Keep an `## Open Work` section above the entries
  - List the open issues and PRs, with one line on each

### Record Decisions

- Record every non-obvious choice in `<project>_decisions.md`
  - Keep the newest decision at the bottom of its section
  - E.g., `research/Noesis/docs/specs/mvp_decisions.md`
- Use this format, one `### D-<N>. <Decision title>` per decision:
  ```markdown
  ### D-1. <Decision title>

  - **Decision**: <what was chosen>
  - **Why**: <the reason, with evidence>
  - **Alternatives**: <what else was considered>
  - **Status**: <proposed | accepted | superseded>
  ```
- Add a one-line pointer to the decision in the history row of the log
- Link the decision in the description of the PR that implements it

## Keep Docs in Sync

- Change a module -> update its design doc (or the README of its component)
- Make a decision -> add it to `<project>_decisions.md`
- Finish a task -> tick it in `plan.<Project>.md` and add a row to the history of
  `<project>_progress.md`
- Change the scope or the order of the work -> edit the plan and log why
- Change the way the team works -> edit `how_we_work.md`

## Write a Project Meta-Doc

- Goal: a new student or RA reads one file and knows how we work on the project
  - Test: after reading it, the newcomer can deliver work of the same quality as
    the current contributors
- Create the file `how_we_work.md` in the project dir
  - E.g., `research/Noesis/docs/how_we_work.md`
- Keep it short: point to the existing docs instead of repeating them
  - Add only what is specific to the project
  - Point to an example PR or issue that follows the process well
- State in it:
  1. **Resources**: the GitHub project, the Slack channel, the Google Drive dir,
     and the Google Doc of the project
  2. **Master plan**: the file name of the plan, see
     [Create an End-to-End Plan](#create-an-end-to-end-plan)
  3. **Log**: where the log is and its format, see
     [Keep a Progress Log](#keep-a-progress-log)
  4. **Task rule**: execute only the tasks that are in the master plan
     - Create the GitHub issue for a task before starting it
     - Post an ETA in the issue when you take the task, and update it when it
       changes, see
       [Sync-ups](../work_organization/all.team_collaboration.how_to_guide.md#sync-ups)
  5. **AI rule**: which Claude skills to use in which step of the loop, see
     [`all.ai_workflows.how_to_guide.md`](../tools/ai/all.ai_workflows.how_to_guide.md)
     - Using AI is fine, but the author must be able to explain every line of
       the AI-written code
  6. **Communication rule**: GitHub for technical discussion, Slack for quick
     pings, office hours for the rest
  7. **Paper rule**: update the paper when there is new or important research
     (e.g., once a week), so that it reflects the state of the code
  8. **Records rule**: keep every decision and communication in a non-ephemeral
     system
     - Prefer markdown in the repo
     - Never keep a decision only in Slack
- Treat a bulleted task list in an issue or in a review comment as work to do
  - Track each item in GitHub and mark it as done there
  - Tick each box with a short link to the result, e.g.,
    `- [x] Update the master plan: PR #123`
  - Create a separate issue for each large item
- Update the meta-doc when the process changes

## PR Description Template

- Copy this into every PR:
  ```markdown
  ## What
  - One bullet: what this PR adds or changes, and which plan PR(s) it closes
    (e.g., `PR_M10`)

  ## Why
  - The problem it solves, with a link to the plan or spec section

  ## How It Works
  - The main flow in a few bullets
  - Point to the README or doc section that was updated

  ## Decisions
  - Each non-obvious choice: decision, why, alternatives considered
  - Add it to `<project>_decisions.md` and link it here

  ## Evidence
  - Tests added (count, what they cover) and the command to run them
  - Pass and fail counts of the full test suite, before and after the change
  - Any live check (what was called, result, cost)

  ## Not in This PR
  - Deliberately deferred items, and where they are tracked
  - Problems found in existing code that this PR does not fix

  ## Questions for Reviewers
  - Anything you want the reviewer's opinion on
  ```
- Link the PR to its issue as described in "Filing Process" in
  [`all.use_github.how_to_guide.md`](../work_organization/all.use_github.how_to_guide.md#filing-process)
  or in the contribution guide of the repo

## Resources

- Issue, project, and task:
  [`all.issue_workflow.explanation.md`](../work_organization/all.issue_workflow.explanation.md)
- Issues, PRs, labels, and review:
  [`all.use_github.how_to_guide.md`](../work_organization/all.use_github.how_to_guide.md)
- Git branches and commit messages:
  [`all.git.how_to_guide.md`](../tools/git/all.git.how_to_guide.md)
- Small PRs and first reviews:
  [`all.submit_code_for_review.how_to_guide.md`](../coding/all.submit_code_for_review.how_to_guide.md)
- Code review:
  [`all.code_review.how_to_guide.md`](../coding/all.code_review.how_to_guide.md)
- Doing a task with Claude Code, from task to PR:
  [`all.create_pr_with_claude_code.how_to_guide.md`](../tools/ai/all.create_pr_with_claude_code.how_to_guide.md)
- Delegating tasks to AI agents:
  [`all.auto_task.how_to_guide.md`](../tools/ai/all.auto_task.how_to_guide.md)
- Claude skills and rules:
  [`all.ai_workflows.how_to_guide.md`](../tools/ai/all.ai_workflows.how_to_guide.md)
- Organizing your work (roles, blockers, communication):
  [`all.organize_your_work.how_to_guide.md`](../work_organization/all.organize_your_work.how_to_guide.md)
- Writing docs:
  [`all.writing_docs.how_to_guide.md`](../documentation_meta/all.writing_docs.how_to_guide.md)
- Templates: `.claude/templates/auto_task.template.md`,
  `.claude/templates/specs.template.md`,
  `.claude/templates/github_PR_plan.template.md`
