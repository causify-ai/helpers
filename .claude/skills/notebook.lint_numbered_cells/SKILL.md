---
description: Ensure cells in a notebook are numbered consecutively with matching function names
---

This skill renumbers cells in a Jupyter notebook consecutively and ensures all
function names are synchronized with cell headers.

## Rules Reference

- Make sure to follow the sections on notebook cell numbering, content structure,
  and function naming from `@.claude/skills/notebook.rules.md`:
  - "Notebook Cell Numbering and Structure"
  - "Content of Markdown Cells with `Cell XYZ` Header"
  - "Code Cell Content and Function Naming"
  - "Utility File Organization"

## Workflow

1. Read all existing cell headers and identify the current numbering
2. Identify gaps, duplicates, or out-of-order cell numbers
3. Renumber headers consecutively (1, 2, 3, ... and 1.1, 1.2, ... for sub-cells)
4. Rename all functions in code cells and the `*_utils.py` file to match the new
   headers
5. Sync the paired `.py` file with Jupytext
