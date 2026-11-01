---
description: Write the design docs of a project from its PRD, before the code
model: opus
---

# Goal

- Given a PRD (Product Requirement Document), write `docs/design.architecture.md` and
  one `docs/design.<component>.md` per component
- Design before the code exists: do not write code

## Input

- `<PRD>`: the PRD file, e.g., `docs/prd.md`
- `<DOCS_DIR>`: the `docs/` dir of the project, optional
  - If missing, use the dir of `<PRD>`

# Workflow

## Read the Inputs

- Read `<PRD>` and the existing docs in `<DOCS_DIR>`
- Read the existing code and docs of the repo that the design must fit
- Read `.claude/skills/architecture.rules.md` and `.claude/skills/C4.rules.md`

## Ask If the PRD Is Unclear

- If a requirement is ambiguous or two requirements conflict:
  - Do not guess
  - Ask the user for clarification
  - Wait for the answers

## Split Into Components

- Propose the components, each with one responsibility
- Respect the layering rules in `.claude/skills/architecture.rules.md`
- Show the proposal to the user and wait for confirmation before writing the docs

## Write the Overview

- Create `<DOCS_DIR>/design.architecture.md`
- Follow the template `.claude/templates/project_design.template.md`
- Show the context and the containers with a PlantUML C4 diagram, per
  `.claude/skills/C4.rules.md`
- Map each requirement `R<N>` of the PRD to the component that satisfies it
  - Link each `R<N>` to its H3 in the PRD, per `.claude/skills/project.rules.md`
    section "Link Requirements and Decisions"

## Write One Doc per Component

- Create `<DOCS_DIR>/design.<component>.md` for each component
- Follow the rules in `.claude/skills/project.rules.md` section "Write a Design Doc"
- Follow the template `.claude/templates/project_design.template.md`
- Distinguish facts about existing code from decisions made in the design
- Record each non-obvious choice in `<DOCS_DIR>/decisions.md`, following the
  template `.claude/templates/project_decisions.template.md`
  - Create the file if it does not exist
- Link each decision from the design docs that follow it, per
  `.claude/skills/project.rules.md` section "Link Requirements and Decisions"

## Update the Index

- Add a row for each new doc to `<DOCS_DIR>/README.md`, if the file exists

# Conventions

- Follow `.claude/skills/project.rules.md` for the docs of a project
- Follow `.claude/skills/architecture.rules.md` for layering and interfaces
- Follow `.claude/skills/markdown.rules.md` and `.claude/skills/text.rules.md`

# Constraints

- Do not implement any code
  - Short snippets (a class interface, a schema, a function signature) are fine
- Do not use this skill to document a Python file that already exists: use
  `.claude/skills/readme.write_architecture/SKILL.md`
- Do not commit any change

# Verification

- [ ] Every requirement of the PRD maps to a component
- [ ] Every component has one responsibility and one design doc
- [ ] The overview has a PlantUML C4 diagram
- [ ] No design doc has a Mermaid C4 diagram
- [ ] Every non-obvious choice is in `decisions.md`
- [ ] Every requirement id and decision id in a design doc is a link to its H3
- [ ] No design doc contains full implementation code
