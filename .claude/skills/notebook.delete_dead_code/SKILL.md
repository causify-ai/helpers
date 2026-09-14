---
description: Remove all the dead code in a Jupyter notebook and in the paired utility file
model: haiku
---

# Goal
- Given a Jupyter notebook, remove the dead code from the notebook and the
  paired utility file

# Workflow

## Follow Notebook Conventions
- Read and follow `.claude/skills/notebook.rules.md`

## Find Unused Functions
- Find the functions in the notebook and in the paired utility file
  `*_utils.py` that are not used in the notebook
- Print a summary of the found unused functions

## Remove Unused Code
- Remove the code of the unused functions from the notebook and from the paired
  utility file
- Remove the unit tests associated to those unused functions, if any

## Sync with Jupytext
- At the end, sync the paired `.py` file with Jupytext following the conventions
  in `# Code Architecture and Responsibility` -> `## Utilities vs. Notebook
  Responsibilities` in `.claude/skills/notebook.rules.md`

# Verification
- [ ] Confirm no remaining code references the removed functions
- [ ] Run the notebook top to bottom following `## Testing Notebook` in
  `.claude/skills/notebook.rules.md` and confirm it completes without errors
