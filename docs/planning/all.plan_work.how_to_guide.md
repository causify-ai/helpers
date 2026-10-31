# Plan Work

## Summary

- This document describes how we plan and track the work of a software project:
  - Write one end-to-end plan that says what to build and in which order
  - Execute the plan one small, reviewable PR at a time
  - Keep a log of everything done, including decisions
- This document gives the order of the steps and the points where a human decides
  - The formats of the docs live in `.claude/skills/project.rules.md`
  - The skeletons to copy live in `.claude/templates/project_*.template.md`
- The process is the same for any project in any repo
  - Rules specific to one repo (e.g., fork flow, naming) live in the docs of that
    repo
  - This is "how we do things": other projects follow the same process
- This document points to the existing docs instead of repeating them
  - See [Resources](#resources)

## Planning Hierarchy

- Work flows from abstract to concrete:
  ```text
  Idea -> Project -> Task (GitHub issue) -> PR -> Review -> Commit
  ```
- **Idea**: the abstract and unstructured starting point of a new initiative
  - E.g., _"What if we expand our current trading universe?"_
  - E.g., _"Implement getting and using historical bid/ask data"_
- **Project**: an initiative with clear goals, defined scope, tangible outcomes,
  and time constraints
  - We track it as a GitHub Project, see
    [`docs/work_organization/all.use_github.how_to_guide.md`](/docs/work_organization/all.use_github.how_to_guide.md#projects)
- **Task**: a specific, actionable item that is part of a project
  - We track it as a GitHub Issue, see
    [`docs/work_organization/all.use_github.how_to_guide.md`](/docs/work_organization/all.use_github.how_to_guide.md#issue)

- This document covers what is below the idea level:
  - How to turn an idea into a plan
  - How to cut the plan into PRs
  - How to log the progress

- One task maps to one or more PRs
  - A PR is the unit of review

## Capture an Idea

- **Goal**: keep track of the work that could be done, with low friction
- Flow:
  1. You have an idea and no time to think it through or execute it now
  2. Put a note in a Google Doc (Gdoc) for your future self
     - Use suggestion mode, so that other people can track the change
     - Once in a while, accept all the changes
  3. When the idea is picked, turn it into a file `research/ideas/<name>.md`
- Why use a Gdoc:
  - We keep track of work that could be done
  - Planning is simpler: someone who is blocked can open the Gdoc and choose a
    project
  - People are notified of the change and see the text in suggestion mode
  - A Gdoc is quick to edit and has low friction
  - An idea is abstract and unstructured, so it is easier to edit in a Gdoc than
    in a GitHub issue
- Alternatives to a Gdoc:
  - A shared planning note in the repo
  - A clearly marked exploratory issue
  - A link to the idea from the relevant work, so that the team can find it

## From Idea to Merged PR

- **Goal**: the sequence of skills that takes a complex software project from an idea to
  merged code
- The flow has four phases:
  - **Define**: what to build and how
  - **Plan**: in which order
  - **Build**: one reviewed PR at a time
  - **Close**: update the docs
- Each phase ends with a human gate
  - An agent never crosses a gate alone
  - Run a skill, read its output, fix it, and only then move on

- Diagram of the flow:
  ```mermaid
  graph LR
    A["Idea"] --> B["PRD"]
    B --> C["Design"]
    C --> D["plan.md"]
    D --> E["tasks.md and specs"]
    E --> F{"Execution mode"}
    F -->|tight loop| G["Interactive"]
    F -->|batch| H["Stacked PRs"]
    F -->|remote| I["Single PR on GitHub"]
    G --> J["Make the PR mergeable"]
    H --> J
    I --> J
    J --> K["Human review and merge"]
    K --> L["Update the docs"]
    L -->|next version| E
  ```

## Plan Documents

- All the docs of a project live in the `docs/` dir of the project
- The doc set, what each doc answers, and its cluster are defined in
  `.claude/skills/project.rules.md` section _"Use One Doc per Question"_
- Start with `plan.md`, `progress.md`, and `how_we_work.md`
  - Add the others only when needed
- `plan.md` is both the roadmap and the execution plan
  - Do not keep a separate execution-plan file: two plans drift apart
- Write a spec for a complex PR instead of growing its entry
  - Follow the template `.claude/templates/specs.template.md`

## Organize the Docs of a Project

- **Goal**: a newcomer finds the right doc without asking
- Write `docs/README.md` as the index of the docs
  - E.g., `research/Noesis/docs/README.md`
  - Follow `.claude/skills/project.rules.md` section "Write an Index in
    docs/README.md"
- Add a row when you add a doc and remove it when you delete the doc
  - Do it in the same PR
- Write the onboarding doc, the glossary, and the design docs as described in
  `.claude/skills/project.rules.md` section "Project Docs"
- Create a C4 diagram of the system following `.claude/skills/C4.rules.md`
  - E.g., `research/Estimate_academic_paper_quality/docs/design.architecture.md`
- Make every reference to a file in a doc clickable
  - E.g., a path like `research/Estimate_academic_paper_quality/docs/prd.md`
  - Follow `.claude/skills/project.rules.md` section "Make File References
    Clickable"

- Write every requirement and every decision as an H3, so that other docs link it
  - Requirement in `prd.md`: `### R3. (Bibliographic source)`
  - Decision in `decisions.md`: `### D7. <Decision title>`
  - Refer to it with a link to its header, never with a bare id
    - E.g.,
      ```
      `[`R3`](/research/Estimate_academic_paper_quality/docs/prd.md#r3-bibliographic-source)
      ```
  - The ids are stable: never reuse them and never renumber them
  - Follow `.claude/skills/project.rules.md` section "Link Requirements and
    Decisions"

## The Loop

- Every change follows the same loop:
  1. Pick a task from the plan (or propose one for approval and inclusion in the
     plan)
  2. Plan before code: write a short design and get a teammate's OK
     - What changes, which files, which interfaces, which tests, which choices are
       still open
     - Put a non-trivial design in the GitHub issue
  3. Open a GitHub issue, see "Naming an Issue" in
     [`docs/work_organization/all.use_github.how_to_guide.md`](/docs/work_organization/all.use_github.how_to_guide.md#naming-an-issue)
     - Write the issue number down: it goes in the branch name, the commits, and the
       PR
     - Point to the section of the plan or of the spec in the issue, do not copy it
       (DRY)
  4. Branch, code, test, commit, open the PR, and address the review
     - Follow the rest of the document and workflows
  5. Merge, then update the plan and the log, see
     [Keep Docs in Sync](#keep-docs-in-sync)
- Keep PRs reviewable
  - One component or one milestone task per PR
  - Respect the size cap in
    [`docs/coding/all.submit_code_for_review.how_to_guide.md`](/docs/coding/all.submit_code_for_review.how_to_guide.md#stick-to-smaller-prs)
  - Use the template `.claude/templates/github_PR_plan.template.md` to split a big PR
- Delegate a task list to an AI agent with the `auto_task` flow
  - See
    [`docs/tools/ai/all.auto_task.how_to_guide.md`](/docs/tools/ai/all.auto_task.how_to_guide.md)

## Create an End-to-End Plan

- **Goal**: one canonical file that says what to build and in which order, so that
  anyone (human or agent) can pick the next PR without asking
- Create the file `plan.md` in the `docs/` dir of the project
  - E.g., `research/Noesis/docs/plan.md`
  - Draft it with `/project.create_plan`
- Steps to create it:
  1. Write the problem and the goal, and point to the background (paper, PRD,
     architecture doc)
  2. List the components, the candidate solutions, and their open questions
  3. Split the work into versions, where each version can be run and demoed
  4. Write the PR entries of the next version in detail
     - Identify the dependencies between the entries
     - Estimate the complexity of each entry
     - Later versions can stay as a few bullets until they are close
     - File GitHub issues only for the immediate work (the next version)
       - The plan often changes after the first iteration
       - Issues for later versions would go stale and need to be rewritten
  5. Review the plan before executing it
     - See `/auto_task.criticize`
- To break a complex feature into an ordered PR plan with a spec per complex PR, see
  `/auto_task.create_plan_for_feature`

### Rules for the Plan

- The structure of the file, the format of a PR entry, and the naming and checking of
  PRs are in `.claude/skills/project.rules.md` section "Plan File"
- Copy the template `.claude/templates/project_plan.template.md`
- Change the plan in a PR, like code
  - Log why it changed in the progress log

## Keep a Progress Log

- **Goal**: one file that records everything done, including decisions
  - A new person sees what happened and why without asking
- Create the file `progress.md` next to the plan
  - E.g., `research/Noesis/docs/progress.md`
  - Copy the template `.claude/templates/project_progress.template.md`
  - The structure and the rules of the log are in `.claude/skills/project.rules.md`
    section "Progress Log"
- Update the log in the PR that finishes the task
  - Draft the update with `/project.update_progress`
- Link the record from its issue and PR

### Record Decisions

- Record every non-obvious choice in `decisions.md`
  - E.g., `research/Noesis/docs/decisions.md`
  - The format is in `.claude/skills/project.rules.md` section "Decisions Log"
  - Copy the template `.claude/templates/project_decisions.template.md`
  - Write each decision as its own H3 `### D<N>. <Decision title>`, so that other
    docs can link it
- Link the decision from the design docs that follow it and from the description of
  the PR that implements it

## How to Document Research

- A research project keeps a Google Doc and a daily entry per day of work
- See
  [`docs/planning/all.document_research.how_to_guide.md`](/docs/planning/all.document_research.how_to_guide.md)

## Keep Docs in Sync

- Update the docs in the PR that finishes the task
  - Run `/project.update_progress` to draft the updates
- The map from an event (e.g., a decision, a finished task) to the doc to update is
  in `.claude/skills/project.rules.md` section "Keep Docs in Sync"

## Write a Project Meta-Doc

- Goal: a new team member reads one file and knows how we work on the project
- Test: after reading it, the newcomer can deliver work of the same quality as the
  current contributors
- Create a file `how_we_work.md` in the `docs/` dir of the project
  - E.g., `research/Noesis/docs/how_we_work.md`
  - Copy the template `.claude/templates/project_how_we_work.template.md`
  - The rules are in `.claude/skills/project.rules.md` section "Write the Meta-Doc"

// TODO(gp): Does it belong here?
- Treat a bulleted task list in an issue or in a review comment as work to do
  - Track each item in GitHub and mark it as done there
  - Tick each box with a short link to the result, e.g.,
    `- [x] Update the master plan: PR #123`
  - Create a separate issue for each large item
- Update the meta-doc when the process changes

## PR Description Template

- Copy the template `.claude/templates/github_PR_description.template.md` into every
  PR
  - `/github.find_name_for_pr` writes a draft of it in `pr_description.md`
- Link the PR to its issue as described in "Filing Process" in
  [`docs/work_organization/all.use_github.how_to_guide.md`](/docs/work_organization/all.use_github.how_to_guide.md#filing-process)
  or in the contribution guide of the repo

# Examples
- The `Noesis` project in the `umd_classes` repo follows the 
  - `research/Noesis/docs/README.md`: index of all the docs of the project
  - `research/Noesis/docs/plan.md`: end-to-end plan
  - `research/Noesis/docs/progress.md`: log of what was done
  - `research/Noesis/docs/decisions.md`: log of why it is built this way
  - `research/Noesis/docs/how_we_work.md`: what `Noesis` adds to this process

- The list of the projects following this approach is
  `docs/planning/project_list.md`

# Workflows

## Define

- **Goal**: decide what to build and how
- **Commands**:
  ```text
  claude> /research_idea.format <project>/idea.md
  claude> /project.write_prd <project>/idea.md
  claude> /text.criticize <project>/docs/prd.md
  claude> /architecture.write_design <project>/docs/prd.md
  claude> /text.criticize <project>/docs/design.architecture.md
  ```
- **Gates**:
  - Pick the idea
  - Approve the scope
  - Approve the design

## Plan

- **Goal**: decide in which order to build it
- **Commands**:
  ```text
  claude> /project.create_plan <project>/docs/design.architecture.md
  claude> /auto_task.criticize <project>/docs/plan.md
  claude> /auto_task.create_plan_for_feature <project>/docs/plan.md PR_A1
  claude> /auto_task.criticize tasks.md
  ```
- **Gates**:
  - Teammate OK on `plan.md`
  - Confirm the plan in `tasks.md` and the specs

## Build

- **Goal**: build code using PRs so that they can be reviewed one at a time
- **Commands**:
  ```text
  # Choose one execution mode.
  claude> /auto_task.execute_interactively tasks.md
  claude> /auto_task.execute_with_stacked_prs tasks.md
  claude> /auto_task.execute_remotely_with_single_pr tasks.md
  ```
- Rules for the flow:
  - Commit between two skills, so that each skill gives a separate diff to review
    - See
      [`docs/tools/ai/all.ai_workflows.how_to_guide.md`](/docs/tools/ai/all.ai_workflows.how_to_guide.md#coding-workflows)
  - Run `/auto_task.criticize` before any execution skill
  - Choose the execution mode with
    [`docs/tools/ai/all.auto_task.how_to_guide.md`](/docs/tools/ai/all.auto_task.how_to_guide.md#step-3-choose-an-execution-mode)
  - Authorize the agent to commit and push only for the automated modes
    - See
      [`docs/tools/ai/all.auto_task.how_to_guide.md`](/docs/tools/ai/all.auto_task.how_to_guide.md#prerequisite-authorize-git-commits-and-pushes)
  - Let a human merge: no skill or AI should merge a PR

- **Gates**:
  - The PR author should be able to explain every line of the code

## Test 
- **Goal**: make sure
- **Commands**:
  ```text
  # Write code and tests, as needed.
  claude> /testing.write_unit_tests <file>

  # Make the PR green and describe it.
  claude> /github.get_pr_to_pass_local_tests
  claude> /github.get_pr_to_pass_ci_tests
  claude> /github.get_pr_ready_to_merge
  claude> /github.find_name_for_pr

  # Only if the PR is too big.
  claude> /github.split_branch_in_PRs

  # After review comments.
  claude> /auto_task.restack
  ```
- **Gates**:
  - The new code is tested at least 80%
  - The interaction of the new code are properly tested (e.g., integration tests,
    end-to-end tests)
  - All the specs are tested

## Update Docs and Close GH Issue

- **Goal**:
  - Keep the docs in sync with the code
  - Make merging PRs automatically close related and connected to the GH Issue
- **Commands**:
  ```text
  claude> /project.update_progress PR_A1
  ```
- **Gates**: check the log in `plan.md`, `progress.md`, and `decisions.md`

## Review and Merge
// TODO(ai_gp): We need a workflow to review the PR

  ```text
  claude> /code-review
  ```

  // Built in
  // - /code-review [low|medium|high|xhigh|max|ultra] [target] reviews the current diff, a PR number, a branch, or a path for correctness bugs. --comment posts inline PR comments. --fix applies the fixes. ultra runs a billed cloud multi-agent review.
  // - /security-review reviews the pending branch changes for security issues.
  // - /simplify reviews changed code for reuse, simplification, and efficiency, then applies fixes. It does not hunt for bugs.

  // Repo skills
  // - coding_qa.review reviews Python files for bugs, suggests fixes, and proposes test cases.
  // - coding.improve_code_for_humans improves readability and debuggability.
  // - github.describe_pr_for_review describes PRs in a fixed format, scores complexity and quality, and suggests a review order.

- **Gates**:
  - A human reviews each PR
  - Review and merge: a human merges

# Software Project Documents

## Product

- **Vision / One-Pager**:
  - A short pitch: the problem, the opportunity and why the project should exist
  - Findings from users: pain points, needs and target user profiles
- **PRD (Product Requirements Document)**:
  - What to build and why
  - users, goals, success metrics, scope, non-goals and user stories.
- **Roadmap**: Milestones and phases over time.

## Design

- **Technical Spec / Design Doc (RFC)**: How it will be built: architecture, components, data flow, alternatives and risks.
- **ADRs (Architecture Decision Records)**: One short record per key decision: context, decision and consequences.
- **API Spec**: Endpoint contracts, request and response formats, and error codes.
- **Data Model / Schema Doc**: Entities, relationships, fields and migration notes.
- **UX/UI Designs**: Wireframes, mockups and user flows.
- **Security & Privacy Review**: Threat model, data handling, auth and compliance concerns.

## Execution

- **Implementation Plan**: Work broken into ordered, testable tasks with owners.
- **Progress Log**: A dated record of what was done, decisions made, blockers and next steps.
- **Test Plan**: Testing strategy, test cases and acceptance criteria.
- **Risk & Issue Log**: Known risks and issues, their impact, mitigations and owners.

## Shipping & Operations

- **README**: What the project is and how to install, run and contribute.
- **Changelog / Release Notes**: User-facing changes in each version.
- **Deployment Guide**: Environments, configuration, CI/CD and secrets handling.
- **Runbook**: How to operate, monitor and fix common production problems.
- **Postmortem**: Incident summary, root cause, impact and follow-up actions.

# Resources

- Projects, issues, PRs, labels, and review:
  [`docs/work_organization/all.use_github.how_to_guide.md`](/docs/work_organization/all.use_github.how_to_guide.md)
- Git branches and commit messages:
  [`docs/tools/git/all.git.how_to_guide.md`](/docs/tools/git/all.git.how_to_guide.md)
- Small PRs and first reviews:
  [`docs/coding/all.submit_code_for_review.how_to_guide.md`](/docs/coding/all.submit_code_for_review.how_to_guide.md)
- Code review:
  [`docs/coding/all.code_review.how_to_guide.md`](/docs/coding/all.code_review.how_to_guide.md)
- Doing a task with Claude Code, from task to PR:
  [`docs/tools/ai/all.create_pr_with_claude_code.how_to_guide.md`](/docs/tools/ai/all.create_pr_with_claude_code.how_to_guide.md)
- Delegating tasks to AI agents:
  [`docs/tools/ai/all.auto_task.how_to_guide.md`](/docs/tools/ai/all.auto_task.how_to_guide.md)
- Claude skills and rules:
  [`docs/tools/ai/all.ai_workflows.how_to_guide.md`](/docs/tools/ai/all.ai_workflows.how_to_guide.md)
- Organizing your work (roles, blockers, communication):
  [`docs/work_organization/all.organize_your_work.how_to_guide.md`](/docs/work_organization/all.organize_your_work.how_to_guide.md)
- Writing docs:
  [`docs/documentation_meta/all.writing_docs.how_to_guide.md`](/docs/documentation_meta/all.writing_docs.how_to_guide.md)
- Where to add new material:
  [`docs/documentation_meta/all.where_to_add_material.explanation.md`](/docs/documentation_meta/all.where_to_add_material.explanation.md)
- Documenting research:
  [`docs/planning/all.document_research.how_to_guide.md`](/docs/planning/all.document_research.how_to_guide.md)
- Rules and templates:
  - `.claude/skills/project.rules.md`
  - `.claude/templates/project_*.template.md`
  - `.claude/templates/github_PR_description.template.md`
  - `.claude/templates/auto_task.template.md`
  - `.claude/templates/specs.template.md`
  - `.claude/templates/github_PR_plan.template.md`
