---
description: Convert a notebook_outline outline into a fully functional Jupyter notebook with working code cells and visualizations
---

- **Input**: A `notebook_outline.<tag>.md` outline file describing each notebook
  cell (created via `.claude/skills/notebook.create_outline/SKILL.md`)
- **Outputs**:
  1. `.ipynb` file: Fully functional Jupyter notebook with working code,
  visualizations, and interactive widgets
  2. `*_utils.py` file: Reusable helper functions extracted from the notebook
  code
- **Purpose**: Implement the pedagogical design as a fully executable,
  interactive notebook

# Implementation Approach

## Code Organization
- **In notebook**: Small, focused code cells that demonstrate concepts
  interactively
- **In utils**: Reusable helper functions, plotting utilities, data processing
  functions
  - Keep notebook cells readable and pedagogically clear
  - Move complexity and infrastructure code to utils
  - Import and use utils functions to keep cells focused on concepts

## File Structure Example naming pattern:
- Notebook: `msml610/tutorials/Lesson94-Information_Theory.ipynb`
- Jupytext paired file: `msml610/tutorials/Lesson94-Information_Theory.py`
- Utilities file: `msml610/tutorials/Lesson94_Information_Theory_utils.py`

# Conventions
- You must always follow the rules and conventions in
  `.claude/skills/notebook.rules.md`
- See `.claude/templates/notebook.template.py` for a complete end-to-end example
  of implementing a notebook
