TODO(Grisha): consider merging the current doc with
[`/docs/work_organization/all.use_github.how_to_guide.md`](/docs/work_organization/all.use_github.how_to_guide.md)
into something like "ck.planning.how_to_guide.md".

# Issue workflow
```
Idea -> Project -> Task (Issue)
```

## Idea

An idea is often the starting point for new initiatives and can be abstract and
unstructured.

Examples:

- "What if we expand our current trading universe?"
- "It would be nice to get historical bid/ask data"

We use Google Docs (Gdocs) to keep track of ideas.

Example flow:

- You have an idea and you do not have time to think it through/execute at the
  moment
- However, you would like to keep track of what could be done in the future
- You put a note in a Gdoc for your future self
- Use suggestion mode so that other people can track that (once in a while we
  accept all the changes)

This is helpful because:

- We keep track of work that could be done
- Simplifies the planning
  - E.g., if someone is blocked, he/she can go to a Gdoc and choose a project
- People are notified of that change and see the text in suggestion mode
- It is quick to edit a Gdoc and has low friction
- Since an idea is abstract and unstructured it is easier to edit it later in a
  Gdoc rather than in a GitHub issue

Alternatives to a Gdoc:

- A shared planning note in the repo
- A clearly marked exploratory issue
- Link the idea from the relevant work so that the team can find it

## Project

Unlike ideas, projects have clear goals, defined scope, tangible outcomes and
time constraints.

We use GitHub Projects to track projects
[`/docs/work_organization/all.use_github.how_to_guide.md#projects`](/docs/work_organization/all.use_github.how_to_guide.md#projects).

To go from "idea" to "project" one needs to perform a through analysis:

- Identify a problem
- Suggest solutions for the problem
- Split the work into actionable tasks
- Identify the dependencies between the tasks
- Estimate the complexity
- Record the decisions that change the scope or the interfaces

A project does not need a new board for each milestone or feature.

Team leaders are responsible for converting "ideas" into "projects". The outcome
of the analysis is a GitHub Project with clear objectives, start/end dates,
assignees and filed GitHub issues.

## Task (Issue)

A task is a specific, actionable item that needs to be completed, often as part
of a project. Tasks are usually smaller in scope and more focused on single
activities or steps within a project.

We use GitHub Issues to track tasks. Every issue should belong to a GH Project
[`/docs/work_organization/all.use_github.how_to_guide.md#issue`](/docs/work_organization/all.use_github.how_to_guide.md#issue).

A task has one accountable owner and a testable result. A task includes:

- Problem and why it matters
- Scope and explicit exclusions
- Acceptance criteria: the evidence that shows the task is complete
- Dependencies, owner, and an effort estimate
- Relevant design notes, PRs, and findings

A task is complete when its evidence exists and has been reviewed, not when the
code runs.

- E.g., "Run the model benchmark" is complete when the selected configuration,
  the results, the costs, and the question set are documented and reviewed

Last review: GP on 2024-05-25
