---
description: Implement Jupyter notebook from an outline description
---

- Given the passed description for a Jupyter notebook in the format described in
  `.claude/skills/notebook.create_outline/SKILL.md` implement the cells
  requested by the user

# Conventions
- You must always follow the rules and conventions in
  `.claude/skills/notebook.rules.md`

# Save Code to the Corresponding Library `*_utils.py`
- Each notebook is paired with Jupytext to a Python file and has a corresponding
  `*_utils.py` file containing the code corresponding to that notebook
  - E.g., for the Jupyter notebook
    `msml610/tutorials/Lesson94-Information_Theory.ipynb` is paired with
    Jupytext to the file `msml610/tutorials/Lesson94-Information_Theory.py` and
    the corresponding `*_utils.py` file is
    `./msml610/tutorials/Lesson94_Information_Theory_utils.py`

# Reference Templates
- See `.claude/templates/notebook.template.py` for a complete
  end-to-end example of implementing a notebook
