---
description: Workflow for editing Jupyter notebooks using paired Python files
---

# Purpose

- Maintain synchronization between Jupyter notebook files (.ipynb) and their
  paired Python files (.py) using Jupytext
- Edit notebooks through their Python source files, ensuring consistency between
  formats

# When to Use

- User asks to modify a Jupyter notebook (.ipynb file)
- User asks to create a notebook from existing .ipynb file without a paired .py file
- User asks to add cells, modify cells, or change notebook structure

# When NOT to Use

- User is asking questions about notebook content
- User wants to work with a Python file directly (not a notebook)

# Workflow

## Step 1: Sync Before Editing

- Check if a paired Python file exists
  - If yes: Sync the files to ensure they are in sync
    ```bash
    > uvx jupytext --sync <path/to/notebook_name.py>
    ```
  - If no: Create the pairing in `py:percent` format
    ```bash
    > uvx jupytext --set-formats ipynb,py:percent <path/to/notebook_name.ipynb>
    ```

## Step 2: Edit Only the Python File

- Modify only the .py file, never the .ipynb file directly
- Follow all notebook formatting rules from `@.claude/skills/notebook.format/SKILL.md`
- Make changes to cell content, structure, and metadata through the .py file
- Use the NotebookEdit tool on the paired .py file if needed

## Step 3: Sync After Editing

- After completing all modifications to the .py file, sync to update the .ipynb file
  ```bash
  > uvx jupytext --sync <path/to/notebook_name.py>
  ```
- This propagates your changes to the Jupyter notebook format

# Example Workflow

- User request: "Add a new cell to my tutorial notebook"
  ```bash
  > uvx jupytext --sync notebooks/my_tutorial.py
  # (edit notebooks/my_tutorial.py using NotebookEdit tool)
  > uvx jupytext --sync notebooks/my_tutorial.py
  ```

- User request: "Create a Python file for this notebook"
  ```bash
  > uvx jupytext --set-formats ipynb,py:percent notebooks/my_tutorial.ipynb
  ```

# Key Points

- Always use `py:percent` format for jupytext pairing
- Sync before editing to catch any upstream changes
- Sync after editing to generate the updated .ipynb file
- Never edit .ipynb files directly when a .py file exists
- The NotebookEdit tool and Edit tool work on the .py file
