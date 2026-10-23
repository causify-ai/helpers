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
      document, see
      [Organize the Docs of a Project](#organize-the-docs-of-a-project) and
      [Write a Project Meta-Doc](#write-a-project-meta-doc)
- Example:
  - the `Noesis` project in the `umd_classes` repo
  - `research/Noesis/docs/README.md`: index of all the docs of the project
  - `research/Noesis/docs/plan.md`: end-to-end plan
  - `research/Noesis/docs/progress.md`: log of what was done
  - `research/Noesis/docs/decisions.md`: log of why it is built this way
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

- All the docs of a project live in the `docs/` dir of the project
  - Name a file after its role, not after its project: the dir already names the
    project
    - E.g., `plan.md`, not `plan.noesis.md`
  - Keep all the files at the top level of `docs/`: no `plans/` or `specs/`
    subdirs
  - Put only raw data in a subdir, e.g., `findings/`
- A project uses a few documents, each one answering one question:

  | Document                | Question it answers                                 | Cluster    |
  | :---------------------- | :-------------------------------------------------- | :--------- |
  | `plan.md`               | What to build, in which order, who does it, by when | Plans      |
  | `progress.md`           | What is done, learned, next                         | Plans      |
  | `decisions.md`          | Why it is built this way                            | Specs      |
  | `spec.<PR_ID>.md`       | How one complex PR is built                         | Specs      |
  | `design.<component>.md` | How one component, or the whole code, is built      | Design     |
  | `how_we_work.md`        | How the team works on it                            | Onboarding |
  | `onboarding.md`         | How to set up, run, and test it                     | Onboarding |
  | `glossary.md`           | What the terms used in the code and docs mean       | Onboarding |

- Start with `plan.md`, `progress.md`, and `how_we_work.md`
  - Add the others only when needed
- `how_we_work.md` is the meta-doc of the project
  - See [Write a Project Meta-Doc](#write-a-project-meta-doc)
- `design.<component>.md` describes how a component works
  - E.g., `design.gateway.md`, `design.checker.md`
  - `design.architecture.md` is the overview of the whole code
  - The README of a component lives next to its code and points to its design doc
- `plan.md` is both the roadmap and the execution plan
  - The roadmap says what to build and in which order
  - The execution part splits the PRs of the next version into smaller tasks with
    owners, dates, and acceptance criteria
  - Add the execution part only when several people work in parallel
  - Do not keep a separate execution-plan file: two plans drift apart
- `spec.<PR_ID>.md` is an implementation spec for one complex PR
  - Follow the template `.claude/templates/specs.template.md`

## Organize the Docs of a Project

- Goal: a newcomer finds the right doc without asking
- Write `docs/README.md` as the index of the docs
  - E.g., `research/Noesis/docs/README.md`
- Structure of `docs/README.md`:
  - `# Docs`
    - What the docs cover
    - Where to start, e.g., `onboarding.md`, then `design.architecture.md`
    - Where the component READMEs live
  - `## Structure of the Dir`
    - A table of the subdirs, e.g., `findings/`
    - State that all the other docs sit at the top level, grouped by cluster
  - `## Description of Files`
    - One row per file, with a one-line description and its cluster
- Use these clusters, in this order:
  - **Design**: how the code is built (`design.*.md`)
  - **Onboarding**: what a newcomer reads first (`how_we_work.md`,
    `onboarding.md`, `glossary.md`)
  - **Plans**: what to build and what is done (`plan.md`, `progress.md`, other
    plans, e.g., a marketing plan)
  - **Specs**: what each piece must do and why (the product requirements,
    `decisions.md`, `spec.<PR_ID>.md`)
  - **Notes**: working notes and open TODOs
- Use this skeleton for the table of files:
  ```markdown
  ## Description of Files

  | File                    | Description                | Cluster    |
  | :---------------------- | :------------------------- | :--------- |
  | `design.<component>.md` | <One-line description>     | Design     |
  | `onboarding.md`         | <One-line description>     | Onboarding |
  ```
- Add a row when you add a doc and remove it when you delete the doc
  - Do it in the same PR
- Write each doc with a title and a short goal, then point to the other docs
  instead of repeating them
- Structure of the onboarding doc, `onboarding.md`:
  - Goal: from zero to running the code and its tests, then a first task
  - Numbered sections: what the project is (5 minutes), access you need, setup,
    run the tests, run the code, read the code in this order, pick a first task,
    common problems
- Structure of the glossary, `glossary.md`:
  - One table with the columns `Term` and `Meaning`
  - Plain-language definitions of the terms used in the code and docs
- Structure of a design doc, `design.<component>.md`:
  - Goal and where the component fits
  - Files and import graph
  - One request (or run) end to end
  - Configuration, endpoints, and known limits
  - What is deliberately not built

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
- Create the file `plan.md` in the `docs/` dir of the project
  - E.g., `research/Noesis/docs/plan.md`
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

- Mirror the structure of `plan.md`:
  - `# <Project> Implementation Plan`
  - `## Goal`
    - What we build
    - Pointers to the background, not a copy of it
  - `## Plan Hierarchy`
    - How this file relates to the progress log and to the decisions log
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
  - `# <Version> Execution Plan` (optional, only when several people work in
    parallel)
    - Milestones with dates, owners, and exit tests
    - One task table per milestone: task id, owner, acceptance criteria, and the
      plan PR it closes
    - The critical path

### Format of a PR Entry

- Use one H3 per PR, with the PR id and a checkbox:
  ```markdown
  ### `PR_M10`: [ ] <Title>

  - Background: <what exists today, with file paths, and the gap>
  - <Change 1>
  - <Change 2>
  - Unit tests: <what the tests check>
  - Result: <what a user can do after this PR that was not possible before>
  - Owner and due date: <who, by when>
  - Acceptance: <the checks that close the PR>
  ```
- Fill the entry like this:
  - **Background**: the current state and the problem, with file and function names
  - **Changes**: concrete and testable, one bullet per change
  - **Unit tests**: the behavior to check, not only "add tests"
  - **Result**: the capability that exists after the PR
  - **Owner and due date**, **Acceptance**: needed only when several people work in
    parallel, and only for the PRs of the next version

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
- Create the file `progress.md` next to the plan
  - E.g., `research/Noesis/docs/progress.md`

### Structure of the Log File

- Mirror the structure of `progress.md`:
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
  - Plans live in `plan.md`
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

- Record every non-obvious choice in `decisions.md`
  - Keep the newest decision at the bottom of its section
  - E.g., `research/Noesis/docs/decisions.md`
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

## How to Document Research

- **Goal**: a reader sees what was run, what result came out, and what to do next,
  without asking
- Keep a Google Doc for the research of each project
  - The Google Doc holds the visual evidence (e.g., screenshots of the results)
  - `progress.md` holds the implementation, findings and the decisions made to
    implement the mechanisms, see [Keep a Progress Log](#keep-a-progress-log)

- The goal is to make the research reproducible by:
  - Adding unit tests for notebooks (like fast tests as smoke tests, small run and
    slow / superslow tests to freeze important research results)
  - Adding unit tests for the code with the same approach
  - Use a `config` (e.g., a Python dict) controlling all the parameters of an
    experiment so that the config becomes the signature of the experiment
    - Given the `config` one should be able to reproduce exactly the set up

- Write one entry for every day of work with:
  - Screenshots of the results from the notebooks
  - Pointers to the relevant sections and files
    - E.g., the notebook, the section header, the script
  - Comments on what each experiment means
  - What was learned
  - What is next

- Use this skeleton for each daily entry:
  ```text
  Date: <date>

  Screenshots:
  - <Screenshot of a result from a notebook>
    - Where: <notebook / section / file>
    - What it does: <what the code or the plot does>

  Learned:
  - <What was learned from the results>

  Next:
  - <The next step>
  ```
- Save the Google Doc in the shared
  [research dir](https://drive.google.com/drive/folders/1XQ5zrk80eScbcynOsc1loDppzAjGNy2x)
  - Create a subdir named exactly like the GH issue of the project
  - Put the Google Doc and its supporting files in that subdir
- Link the Google Doc from the GH issue, the PR, and `progress.md`

## Keep Docs in Sync

- Change a module -> update its design doc (or the README of its component)
- Make a decision -> add it to `decisions.md`
- Finish a task -> tick it in `plan.md` and add a row to the history of
  `progress.md`
- Change the scope or the order of the work -> edit the plan and log why
- Change the way the team works -> edit `how_we_work.md`
- Add, rename, or remove a doc -> update the table in `docs/README.md` and the
  docs that point to it
- Add a term used in the code or docs -> add it to `glossary.md`
- Change the setup or the way to run the code -> edit `onboarding.md`

## Write a Project Meta-Doc

- Goal: a new student or RA reads one file and knows how we work on the project
  - Test: after reading it, the newcomer can deliver work of the same quality as
    the current contributors
- Create the file `how_we_work.md` in the `docs/` dir of the project
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
  - Add it to `decisions.md` and link it here

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
