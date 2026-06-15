---
description: Format the markdown cells corresponding to interactive cells in a Jupyter Notebook
model: haiku
---

# Goal
- Given a Jupyter notebook, format the markdown cells corresponding to
  interactive cells

# Workflow

## Step 1
- Update all the markdown cells before an interactive cell to:
  - Be in sync with the interactive cell
  - Follow the conventions from `## Markdown Cell Content for Interactive Cells`
    in `.claude/skills/notebook.rules.md` (under `# Interactive Cells`)

## Step 2
- At the end, sync the paired `.py` file with Jupytext following the conventions
  in `# Setup and Initialization` → `## Utilities vs. Notebook Responsibilities`
  in `.claude/skills/notebook.rules.md`

## Conventions
- Follow the rules in `.claude/skills/notebook.rules.md`
- Do not change the intent of the notebook
