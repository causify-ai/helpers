---
description: Ensure cells in a notebook are numbered consecutively with matching function names
model: haiku
---

Renumber cells in a Jupyter notebook consecutively and ensures all function names
are synchronized with cell headers

## Rules Reference
- Make sure to follow the sections on notebook organization and utility file
  structure from `.claude/skills/notebook.rules.md`:
  - `## Notebook Organization` (Markdown Header Structure and Naming, Sequential
    Cell Numbering)
  - `## Utility File Organization` (Sync Function Names with Cell Numbers, Organize
    Code by Cell Order)

## Workflow
1. Read all existing cell headers and identify the current numbering
2. Identify gaps, duplicates, or out-of-order cell numbers
3. Renumber headers consecutively (1, 2, 3, ... and 1.1, 1.2, ... for sub-cells)
4. Rename all functions in code cells and the `*_utils.py` file to match the new
   headers
5. Sync the paired `.py` file with Jupytext
