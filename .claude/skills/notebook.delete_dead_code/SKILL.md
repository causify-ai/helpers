---
description: Remove all the dead code in a Jupyter notebook and in the paired utility file
model: haiku
---

# Goal
Given a Jupyter notebook, remove the dead code from the notebook and the paired
utility file

## Step 1
- Read and follow `.claude/skills/notebook.rules.md`

## Step 2
- Find the functions in the notebook and in the paired utility file
  `*_utils.py` that are not used in the notebook
- Print a summary of the found unused functions

## Step 3
- Remove the code of the unused functions from the notebook and from the paired
  utility file
- Remove the unit tests associated to those unused functions, if any

## Step 4
- At the end, sync the paired `.py` file with Jupytext following the conventions
  in `# Setup and Initialization` → `## Utilities vs. Notebook Responsibilities`
  in `.claude/skills/notebook.rules.md`
