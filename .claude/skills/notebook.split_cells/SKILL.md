---
description: Split Jupyter notebook cells so each cell performs only one logical task
model: haiku
---

# Goal
- Make sure that each code cell in a Jupyter notebook performs only one
  logical task

## Conventions
- Implement the rules in `.claude/skills/notebook.rules.md` under
  - `## Single Responsibility Per Cell` and
  - `## Split Cells That Perform Distinct Steps`

## Sync
- At the end, sync the paired `.py` file with Jupytext following the
  conventions in `# Setup and Initialization` → `## Utilities vs. Notebook Responsibilities`
  in `.claude/skills/notebook.rules.md`
