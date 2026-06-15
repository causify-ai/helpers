---
description: Format the markdown cells corresponding to interactive cells in a Jupyter Notebook
model: haiku
---

# Goal
- Given a Jupyter notebook, format the markdown cells corresponding to
  interactive / visualization cells
- Each visualization uses the triplet structure:
  - Pre-visualization markdown (goal + plot descriptions)
  - Code cell (visualization / interactive widget)
  - Post-visualization markdown (key observations + experiments)

# Workflow

## Step 1
- Update all markdown cells around interactive cells to follow the triplet
  structure:
  - **Before the visualization**: A markdown cell with the goal, plot
    descriptions (under each title), and widget descriptions (close to each
    widget)
  - **After the visualization**: A key observations markdown cell explaining
    what experiments can be done and what was learned
- Follow the conventions from `## Visualization Cell Triplet Details`
  in `.claude/skills/notebook.rules.md`

## Step 2
- At the end, sync the paired `.py` file with Jupytext following the conventions
  in `# Setup and Initialization` → `## Utilities vs. Notebook Responsibilities`
  in `.claude/skills/notebook.rules.md`

## Conventions
- Follow the rules in `.claude/skills/notebook.rules.md`, especially:
  - `## Visualization Cell Triplet Details` for the structure of pre- and
    post-visualization markdown cells
  - `## Interactive Cells` for the interactive widget patterns
  - `## Cell Triplet Structure` for the overall three-cell organization
- Do not change the intent of the notebook
