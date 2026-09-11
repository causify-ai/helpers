---
description: Format the markdown cells of a notebook like slides
model: haiku
---

# Goal
- Given an interactive Jupyter notebook, update and format all the markdown cells
  without changing their content

# Workflow

## Sync Markdown Cells
- Update all the markdown cells to be in sync with the interactive cell

## Markdown Cells Needs to Use Bullet Lists
- The text in markdown cells need to be structured markdown bullet points with
  nested bullets for clarity and conciseness, following the rules in
  - `.claude/skills/slides.rules.md`: rules for formatting slides
  - `.claude/skills/text.rules.md`: rules for formatting bullet points
- Follow `## Use Bullet-Point Comments for Structured Explanations` from
  `.claude/skills/notebook.rules.md`

## Sync Notebook
- At the end, sync the paired `.py` file with Jupytext following the conventions
  in `# Code Architecture and Responsibility` -> `## Utilities vs. Notebook
  Responsibilities` in `.claude/skills/notebook.rules.md`

# Conventions
- Always follow the conventions and guidelines in
  `.claude/skills/notebook.rules.md`

# Constraints
- Do not change the intent of the cell

# Verification
- [ ] Confirm the meaning of every markdown cell is unchanged
- [ ] Confirm the `.ipynb` and paired `.py` file are in sync via Jupytext
