---
description: Update the plan, the log, and the decisions after a PR is merged
model: sonnet
---

# Goal

- Given the plan ids of the merged PR(s), bring the docs of the project in sync:
  tick the plan, add the log entry, record the decisions
- Log facts only: never invent a result

## Input

- `<PR_IDS>`: one or more plan ids, e.g., `PR_M10`
- `<PR_NUM>`: the GitHub PR number, optional
  - If missing, find the merged PR with `gh pr list --state merged --search
    "<PR_ID>"`
- `<DOCS_DIR>`: the `docs/` dir of the project, optional
  - If missing, use `docs/` in the current dir

# Workflow

## Check the PR Is Merged

- Read the PR with `gh pr view <PR_NUM>`
- If the PR is not merged, stop and tell the user: a PR is checked only when merged

## Update the Plan

- Tick `[x]` the PR in the roadmap and in its entry in `<DOCS_DIR>/04-plan.md`
- For a partly done PR, write the status in its entry and do not tick it
- If the scope or the order changed, edit the plan and log why in the progress log

## Update the Log

- Add the entry to `<DOCS_DIR>/07-progress.md`, after the older ones
  - Use a History row, or one section per PR when a row is too short
  - Follow `.claude/skills/project.rules.md` section "Write the Log" and the template
    `.claude/templates/project_progress.template.md`
- Take from the PR: the issue, the author, the dates in UTC, the testing evidence,
  the failing checks that the PR did not cause
- Update "Status", "Built", and "Next"
- Ask the user for any finding or number that is not in the PR: do not invent it

## Record the Decisions

- For each decision in the "Decisions" section of the PR description, add an entry
  to `<DOCS_DIR>/03-decisions.md`
  - Follow the template `.claude/templates/project_decisions.template.md`
- Add a one-line pointer to the decision in the log entry
  - Make the pointer a link to the `### D<N>. <Decision title>` header in
    `03-decisions.md`, per `.claude/skills/project.rules.md` section "Link
    Requirements and Decisions"

## Sync the Other Docs

- Apply the event map in `.claude/skills/project.rules.md` section "Map Each Event
  to the Doc to Update"
- Update the design doc of each module the PR changed
- Update `<DOCS_DIR>/README.md` if a doc was added, renamed, or removed
- Add new terms to `<DOCS_DIR>/10-glossary.md`, if the file exists

# Conventions

- Follow `.claude/skills/project.rules.md` for the docs of a project
- Follow `.claude/skills/markdown.rules.md` and `.claude/skills/text.rules.md`

# Constraints

- Append to the history: do not rewrite the past rows
- Log facts, not plans
- Do not commit any change: the user commits the doc update in the PR that finishes
  the task

# Verification

- [ ] Only merged PRs are ticked
- [ ] The log entry has the PR link, the dates in UTC, and the testing evidence
- [ ] Every decision of the PR is in `03-decisions.md`
- [ ] `<DOCS_DIR>/README.md` lists every doc in the dir
- [ ] No past row of the history was changed
