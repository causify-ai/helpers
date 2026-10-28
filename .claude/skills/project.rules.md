- This file contains the conventions for the docs that plan and track a project: the
  doc set, the PRD, the design docs, the plan, the progress log, and the decisions
  log
- The conventions are the same for any project in any repo
  - Rules specific to one repo (e.g., fork flow, naming) live in the docs of that
    repo

# Project Docs

## Keep All the Docs in One Dir

- Put all the docs of a project in the `docs/` dir of the project
  - E.g., `research/Noesis/docs/`
- Name a file after its role, not after its project: the dir already names the
  project
  - **Bad**: `plan.noesis.md`
  - **Good**: `plan.md`
- Keep all the files at the top level of `docs/`: no `plans/` or `specs/` subdirs
- Put only raw data in a subdir, e.g., `findings/`

## Use One Doc per Question

- A project uses a few documents, each one answering one question:

  | Document                | Question it answers                                 | Cluster    |
  | :---------------------- | :-------------------------------------------------- | :--------- |
  | `prd.md`                | What the product must do and must not do            | Specs      |
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
- Point to another doc instead of repeating it

## Group the Docs in Clusters

- Use these clusters, in this order:
  - **Onboarding**: what a newcomer reads first
    - E.g., `how_we_work.md`, `onboarding.md`, `glossary.md`
  - **Design**: how the code is built
    - E.g., `design.*.md`
  - **Plans**: what to build and what is done
    - E.g., `plan.md`, `progress.md`, other plans, e.g., a marketing plan
  - **Specs**: what each piece must do and why
    - E.g., `prd.md`, `decisions.md`, `spec.<PR_ID>.md`
  - **Notes**: working notes and open TODOs

## Write an Index in docs/README.md

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
- Use this skeleton for the table of files:
  ```markdown
  ## Description of Files

  | File                    | Description            | Cluster    |
  | :---------------------- | :--------------------- | :--------- |
  | `design.<component>.md` | <One-line description> | Design     |
  | `onboarding.md`         | <One-line description> | Onboarding |
  ```
- Add a row when a doc is added and remove it when the doc is deleted, in the same PR
- Write each doc with a title and a short goal

## Write the Onboarding Doc

- Goal of `onboarding.md`: from zero to running the code and its tests, then a
  first task
- Use numbered sections:
  - What the project is (5 minutes)
  - Access you need
  - Setup
  - Run the tests
  - Run the code
  - Read the code in this order
  - Pick a first task
  - Common problems

## Write the Glossary

- Use one table in `glossary.md` with the columns `Term` and `Meaning`
- Define the terms used in the code and docs in plain language

## Write a PRD (Product Requirements Document)

- Follow the template `.claude/templates/project_prd.template.md`
- Number the requirements `R1`, `R2`, ...
- State each requirement so that a test can check it
- List the non-goals: what the product does not do
- Describe what the product does, not how it is built: the design doc says how
- Number the open questions and tag with `-> Project` those that need their own
  project

## Write a Design Doc

- Name the doc `design.<component>.md`
  - E.g., `design.gateway.md`, `design.checker.md`
- Name the overview of the whole code `design.architecture.md`
- Follow the template `.claude/templates/project_design.template.md`
- Follow the layering and interface rules in `.claude/skills/architecture.rules.md`
- Put the README of a component next to its code and point it to the design doc
- Use `.claude/templates/architecture_doc.template.md` instead to document a Python
  file that already exists

## Write a Spec for a Complex PR

- Write a spec `spec.<PR_ID>.md` for a complex PR instead of growing its plan entry
- Follow the template `.claude/templates/specs.template.md`

## Write the Meta-Doc

- Name the doc `how_we_work.md`: a new student or RA reads one file and knows how
  the team works on the project
  - Test: after reading it, the newcomer can deliver work of the same quality as
    the current contributors
- Keep it short: point to the existing docs instead of repeating them
  - Add only what is specific to the project
  - Point to an example PR or issue that follows the process well
- Follow the template `.claude/templates/project_how_we_work.template.md`
- Update the meta-doc when the process changes

# Plan File

## Keep One Plan

- Use `plan.md` as both the roadmap and the execution plan
  - The roadmap says what to build and in which order
  - The execution part splits the PRs of the next version into smaller tasks with
    owners, dates, and acceptance criteria
- Add the execution part only when several people work in parallel
- Do not keep a separate execution-plan file: two plans drift apart

## Structure the Plan File

- Follow the template `.claude/templates/project_plan.template.md`
- Sections, in order:
  - `# <Project> Implementation Plan`
  - `## Goal`: what we build, with pointers to the background, not a copy of it
  - `## Plan Hierarchy`: how the file relates to the progress log and to the
    decisions log, and what a checked and an unchecked PR mean
  - `## Roadmap`: one bullet per version with its deliverable, and under it a
    checkbox list of the PR ids it needs
  - `# Component Specs`: one `## <Component>` section per component, with
    `### Goal` and `### Open Questions`
  - `# PRs`: one `## <version>: <Title>` section per version in roadmap order, then
    one `## Unscheduled: <Component>` section per component
  - `## Conventions`: pointers to the coding and testing rules, not a copy
  - `# <Version> Execution Plan`: optional, see "Keep One Plan"
- State in the roadmap that releases are cumulative: a version also needs the PRs
  of the versions before it
- Number the open questions and tag with `-> Project` those that need their own
  project
- Write the PR entries of the next version in detail
  - Later versions can stay as a few bullets until they are close
  - File GitHub issues only for the next version: issues for later versions go
    stale
- In the execution plan, give:
  - Milestones with dates, owners, and exit tests
  - One task table per milestone: task id, owner, acceptance criteria, and the plan
    PR it closes
  - The critical path

## Name the PRs

- Name each PR `PR_<component letter><number>`
  - E.g., `PR_M10`
- The id is stable: never reuse it and never renumber it
- List the PRs in roadmap order, not in id order
- Use the plan id in the files derived from the plan
  - **Spec**: `spec.PR_M10.md`
  - **Task list**: label the PR block `PR_M10`, not `PR1`, when the task list comes
    from `plan.md`

## Format a PR Entry

- Use one H3 per PR, with the PR id and a checkbox, following the template
  `.claude/templates/project_plan.template.md`
- Fill the entry like this:
  - **Background**: the current state and the problem, with file and function names
  - **Changes**: concrete and testable, one bullet per change
  - **Unit tests**: the behavior to check, not only "add tests"
  - **Result**: the capability that exists after the PR
  - **Owner and due date**, **Acceptance**: write them only when several people
    work in parallel, and only for the PRs of the next version

## Keep the Plan Correct

- Check `[x]` a PR only when it is merged
  - For a partly done PR, state the status in its entry
- Make each version a deliverable that a person can run or demo
- Do not copy content that lives elsewhere (papers, PRD, architecture): point to it
- Change the plan in a PR, like code
  - Log why it changed in the progress log

# Progress Log

## Structure the Log File

- Name the file `progress.md` and keep it next to the plan
- Follow the template `.claude/templates/project_progress.template.md`
- Sections, in order:
  - `## Status`: one row per milestone with target date and status, linking the PR
    that closed it
  - `## Built`: one bullet per component that exists, pointing to its design doc
    instead of describing it
  - `## Findings`: numbered facts learned, each with the measured number, linking
    the raw data (e.g., a `findings/` dir)
  - `## Next`: the next tasks in order, taken from the plan
  - `## History`: one row per date, with what was done and the PRs merged

## Write the Log

- Append to the history: do not rewrite the past rows
  - The newest row is the last one
- Log all the work:
  - Merged PRs
  - Findings, including negative results
  - Decisions
  - Work that was cancelled, and why
- Log facts, not plans: plans live in `plan.md`
- Give each finding its evidence: what was measured, where, and the number with
  its unit
- Record each experiment so that others can reproduce it:
  - The configuration and the commands
  - The model or provider identity, when relevant
  - The observed results and the limitations
  - The links to the evidence
- Write dates in UTC, as GitHub reports them
- Link the record from its issue and PR
- Do not commit secrets, private data, or large raw artifacts without an agreed
  storage approach

## Write One Entry per PR

- When a History row is too short for a PR, replace the table with one section per
  merged PR, following the template `.claude/templates/project_progress.template.md`
- Add each new section after the older ones, so the newest is the last
- Keep an `## Open Work` section above the entries
  - List the open issues and PRs, with one line on each

# Decisions Log

## Record Every Non-Obvious Choice

- Record the choice in `decisions.md`, following the template
  `.claude/templates/project_decisions.template.md`
- Write one `### D-<N>. <Decision title>` per decision
- Keep the newest decision at the bottom of its section
- Give each decision a status: `proposed`, `accepted`, or `superseded`
- Add a one-line pointer to the decision in the history row of the log

# Keep Docs in Sync

## Map Each Event to the Doc to Update

- Change a module: update its design doc, or the README of its component
- Make a decision: add it to `decisions.md`
- Finish a task: tick it in `plan.md` and add a row to the history of `progress.md`
- Change the scope or the order of the work: edit the plan and log why
- Change the way the team works: edit `how_we_work.md`
- Add, rename, or remove a doc: update the table in `docs/README.md` and the docs
  that point to it
- Add a term used in the code or docs: add it to `glossary.md`
- Change the setup or the way to run the code: edit `onboarding.md`

# PR Description

## Use the Standard Description

- Write the description of every PR following the template
  `.claude/templates/github_PR_description.template.md`
- Link each non-obvious choice to its entry in `decisions.md`
- Link the plan or spec section that the PR closes
