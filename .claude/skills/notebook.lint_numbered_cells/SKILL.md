---
description: Ensure cells in a notebook are numbered consecutively with matching function names
model: haiku
---

# Goal
Renumber cells in a Jupyter notebook consecutively and ensures all function names
are synchronized with cell headers

# Workflow

## Step 1
- Read all existing cell headers and identify the current numbering
- Make sure to follow the sections from `.claude/skills/notebook.rules.md`:
  - `## Notebook Organization` (Markdown Header Structure and Naming, Sequential
    Cell Numbering)
  - `## Utility File Organization` (Sync Function Names with Cell Numbers, Organize
    Code by Cell Order)
- Identify gaps, duplicates, or out-of-order cell numbers

## Step 2
- Renumber headers consecutively (1, 2, 3, ... and 1.1, 1.2, ... for sub-cells)
- Rename all functions in code cells and the `*_utils.py` file to match the new
  headers

## Step 3
- Sync the paired `.py` file with Jupytext following the conventions in 
  `# Setup and Initialization` → `## Utilities vs. Notebook Responsibilities`
  in `.claude/skills/notebook.rules.md`

## Conventions
- `.claude/skills/notebook.rules.md`

## Constraints
- Read and follow `.claude/skills/notebook.rules.md`
