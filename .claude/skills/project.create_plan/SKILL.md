---
description: Write the end-to-end plan of a project from its design docs
model: opus
---

# Goal

- Given the PRD and the design docs, write `docs/plan.md`: what to build, in which
  order, as versions and PRs
- Do not implement code and do not create GitHub issues

## Input

- `<DESIGN>`: the design overview, e.g., `docs/design.architecture.md`
- `<DOCS_DIR>`: the `docs/` dir of the project, optional
  - If missing, use the dir of `<DESIGN>`

# Workflow

## Read the Inputs

- Read `<DESIGN>`, the other `design.*.md` files, and `<DOCS_DIR>/prd.md`
- Read the existing `<DOCS_DIR>/plan.md`, if any, and extend it instead of replacing
  it

## Ask If the Design Is Unclear

- If the scope or the order of the work is not perfectly clear:
  - Do not write the plan
  - Ask the user for clarification
  - Wait for the answers

## Split Into Versions

- Split the work into versions, where each version can be run and demoed
- Order the versions so that a version only needs the versions before it
- Put the components and their open questions in "Component Specs"

## Write the PR Entries

- Write the PR entries of the next version in detail
- Keep the later versions as a few bullets
- Name the PRs `PR_<component letter><number>` and never reuse an id, per
  `.claude/skills/project.rules.md` section "Name the PRs"
- Mark each PR that needs a spec: it gets one later with
  `.claude/skills/auto_task.create_plan_for_feature/SKILL.md`
- Order the PRs by dependency first, then by increasing complexity

## Write the Plan File

- Create `<DOCS_DIR>/plan.md`
- Follow the rules in `.claude/skills/project.rules.md` section "Plan File"
- Follow the template `.claude/templates/project_plan.template.md`
- Follow `.claude/skills/markdown.rules.md` and `.claude/skills/text.rules.md`
- Add the execution part only if the user says that several people work in parallel
- If `<DOCS_DIR>/progress.md` does not exist, create it from the template
  `.claude/templates/project_progress.template.md`

## Update the Index

- Add a row for each new doc to `<DOCS_DIR>/README.md`, if the file exists

# Conventions

- Follow `.claude/skills/project.rules.md` for the docs of a project
- Follow `.claude/skills/markdown.rules.md` and `.claude/skills/text.rules.md`

# Constraints

- Do not implement any code
- Do not create GitHub issues: they are filed only for the next version, when the
  work starts
- Do not copy content from the PRD or the design docs: point to it
- Do not commit any change

# Verification

- [ ] Every version is a deliverable that a person can run or demo
- [ ] Every PR has a stable id and a checkbox
- [ ] Every requirement of the PRD is covered by at least one PR
- [ ] Every requirement id in the plan is a link to its H3 in the PRD
- [ ] No PR appears before a PR it depends on
- [ ] Every open question is numbered
- [ ] The next version has detailed PR entries
