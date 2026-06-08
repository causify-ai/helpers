---
description: Remove all the dead code in a Jupyter notebook and in the paired utility file
model: haiku
---

- Read `.claude/skills/notebook.rules.md`

- Given a Jupyter notebook:
  - Find the functions in the notebook and in the paired utility file
    `*_utils.py` that are not used in the notebook
  - Print a summary of the found unused functions
  - Remove the code of the unused functions from the notebook and from the paired
    utility file
  - Remove the unit tests associated to those unused functions, if any
