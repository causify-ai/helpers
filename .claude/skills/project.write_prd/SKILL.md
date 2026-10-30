---
description: Turn an idea into a product requirements doc (PRD) for a project
model: opus
---

# Goal

- Given an idea, write `docs/prd.md`: what the product must do and must not do
- Do not design the solution and do not write code

## Input

- `<IDEA>`: an idea file (e.g., `research/ideas/<name>.md`) or a free-text
  description
- `<DOCS_DIR>`: the `docs/` dir of the project, optional
  - If missing, use `docs/` in the current dir

# Workflow

## Read the Idea

- Read `<IDEA>` and the files it links to (papers, related ideas, existing code)
- Read the existing docs in `<DOCS_DIR>`, if any, to avoid repeating them

## Ask If the Idea Is Unclear

- If the goal, the users, or the scope is not perfectly clear:
  - Do not write the PRD
  - Ask the user for clarification
  - Wait for the answers
- Do not guess a requirement to fill a section
  - Put each unresolved item in "Open Questions"

## Write the PRD

- Create `<DOCS_DIR>/prd.md`
- Follow the rules in `.claude/skills/project.rules.md` section "Write a PRD"
- Follow the template `.claude/templates/project_prd.template.md`
- Follow `.claude/skills/markdown.rules.md` and `.claude/skills/text.rules.md`
- Point to the idea file and to the background instead of copying them

## Update the Index

- If `<DOCS_DIR>/README.md` exists, add a row for `prd.md`, per
  `.claude/skills/project.rules.md` section "Write an Index in docs/README.md"

# Conventions

- Follow `.claude/skills/project.rules.md` for the docs of a project
- Follow `.claude/skills/markdown.rules.md` and `.claude/skills/text.rules.md`

# Constraints

- Do not describe the solution: that is the job of `architecture.write_design`
- Do not commit any change
- Do not create a GitHub issue

# Verification

- [ ] Every requirement is an H3 `` ### `R<N>` (<short description>) `` and a test can
      check it
- [ ] The non-goals are listed
- [ ] Every open question is numbered
- [ ] The PRD does not contain design or code
- [ ] The row for `prd.md` is in `<DOCS_DIR>/README.md`, if the file exists
