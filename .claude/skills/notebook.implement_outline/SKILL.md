---
description: Implement a Jupyter notebook from an outline description (including interactive notebooks with widgets)
model: opus
---

## Description

- **Input**: A `notebook_outline.<tag>.md` outline file describing each notebook
  cell (created via `.claude/skills/notebook.create_outline/SKILL.md`)
- **Outputs**:
  1. `.ipynb` file: Fully functional Jupyter notebook with working code,
     visualizations, and interactive widgets
  2. `.py` file: A Python file paired using `jupytext` to the `.ipynb` using
     py:percent 
  2. `*_utils.py` file: Reusable helper functions for the notebook code
- **Purpose**: Implement the pedagogical design as a fully executable,
  interactive notebook

# Core Workflow

- **Understand the outline**: Review each cell's Purpose, Display, and (if
  present) Widgets and Key Insights
- **Implement utility functions**: Write reusable widget and visualization code
  in `*_utils.py`
- **Create notebook cells**: Add markdown cells (context) and code cells (widget
  calls) to the notebook
- **Follow the separation principle**: Utilities contain implementation; notebook
  contains only function calls

# Key Conventions

- Follow `.claude/skills/notebook.rules.md`: General notebook conventions and
  structure
- Follow outline cell format from `.claude/skills/notebook.create_outline/SKILL.md`
- Follow `.claude/skills/coding.rules.md` for Python code in `*_utils.py` and in
  the Python cells in `.ipynb` file

- Follow `.claude/skills/notebook.rules.md`
  `# Utilities vs. Notebook Responsibilities` for organizing utility files and
  notebooks

# Implementation Approach

## Code Organization
- Follow the section `Utilities vs. Notebook Responsibilities` from the file
  `.claude/skills/notebook.rules.md` for organizing utility files and notebook
  cells

# Sync with Jupytext
- After all modifications are complete, sync the paired `.py` file with Jupytext
  following the conventions in `# Setup and Initialization` → `## Utilities vs.
  Notebook Responsibilities` in `.claude/skills/notebook.rules.md`

# Reference Templates

- Study these before implementing; they establish the quality bar and idioms
  - `.claude/templates/notebook.template.py`
    - End-to-end notebook covering both static and interactive cell types
  - `.claude/templates/notebook_utils_template.py`
    - Paired utilities file with widget creation, state management, and
      visualization functions

- Examples of notebooks
  - `msml610/tutorials/Lesson94_Information_Theory_utils.py`
  - Production example with complex interactive patterns (especially
    `plot_joint_entropy_interactive()`)

# Implementation Patterns

## Cell Structure in Notebook

- Each cell in the outline becomes three notebook cells
- Make sure to follow the section `Cell Triplet Structure` from the file
  `.claude/skills/notebook.rules.md`

## Simple Interactive Widgets

- Follow the conventions in `.claude/skills/notebook.rules.md`
  `## Simple Interactive Widgets`

## Complex Interactive Widgets

- Follow the conventions in `.claude/skills/notebook.rules.md`
  `## Complex Interactive Widgets`
