---
description: Ensure notebook cells are numbered consecutively with matching function names
model: haiku
---

# Goal
- Renumber cells in a Jupyter notebook consecutively and ensure all function
  names are synchronized with cell headers

# Workflow

## Identify Current Numbering
- Read all existing cell headers and identify the current numbering
- Make sure to follow the sections from `.claude/skills/notebook.rules.md`:
  - `# Notebook Structure and Headers` (Markdown Header Structure and Naming,
    Sequential Cell Numbering)
  - `# Code Architecture and Responsibility` (Sync Function Names with Cell
    Numbers, Organize Code by Cell Order)
- Identify gaps, duplicates, or out-of-order cell numbers

## Renumber Headers and Functions
- Renumber headers consecutively (1, 2, 3, ... and 1.1, 1.2, ... for sub-cells)
- Rename all functions in code cells and the `*_utils.py` file to match the new
  headers

## Sync with Jupytext
- Sync the paired `.py` file with Jupytext following the conventions in
  `# Code Architecture and Responsibility` -> `## Utilities vs. Notebook
  Responsibilities` in `.claude/skills/notebook.rules.md`

# Conventions
- Follow the notebook conventions in `.claude/skills/notebook.rules.md`

# Verification
- [ ] Confirm cell numbers are sequential with no gaps within each Part
- [ ] Confirm every `cellN_*()` function name matches its cell header number
- [ ] Confirm the `.ipynb` and paired `.py` file are in sync via Jupytext
