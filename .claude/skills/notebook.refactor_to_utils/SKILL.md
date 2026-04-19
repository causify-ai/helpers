---
description: Move or add notebook code to a *_utils.py library file
---

You are an expert Python developer.

I will pass you a Python file paired with a Jupyter notebook using jupytext in `py:percent` format.

For all the code follow the rules from @.claude/skills/coding.format_rules/SKILL.md

# Scenarios

This skill handles two complementary scenarios:

## Scenario 1: Moving Existing Functions to Utils

When you need to extract functions from an existing notebook and move them to utils.

## Scenario 2: Adding New Code to Utils

When you need to add new functions or code to an existing utils file corresponding to the notebook.

# Workflow

## Step 1: Identify or Create the Utils File

- Find or create the library/utility file that corresponds to the notebook
  - Naming convention: Notebook name with underscores
  - E.g., `Lesson94-Information_Theory.ipynb` -> `Lesson94_Information_Theory_utils.py`
  - E.g., `tutorial_advanced.ipynb` -> `tutorial_advanced_utils.py`

## Step 2: Organize Code Structure in Utils File

- The utils file should have a structure that mirrors the flow of the notebook
- Use section separators to organize code by notebook sections
  - Example:
    ```python
    # #############################################################################
    # Cell 1: Visual Bin - Population of Marbles
    # #############################################################################

    def cell1_draw_bin_with_marbles_interactive(...):
        ...

    def _cell1_helper_function(...):
        ...

    # #############################################################################
    # Cell 2: Entropy Calculations
    # #############################################################################

    def cell2_calculate_entropy(...):
        ...
    ```

- Add the functions in the part of the utility file that corresponds to the notebook
- Group related functions together
- Use private functions (prefix with `_`) for helpers not called from the notebook

## Step 3: Move or Add Functions

### For Moving Functions (Scenario 1):

1. Copy all functions from the notebook to the utils file (without changing code)
2. Remove the functions from the notebook
3. Update notebook cells to call the utils functions

### For Adding Functions (Scenario 2):

1. Implement new code directly in the utils file
2. Create caller code in the notebook that imports and uses the functions
3. Add the code in the appropriate section following the utils file structure

## Step 4: Update Notebook to Call Utils

- Replace function implementations with imports and function calls
- Pattern:
  ```python
  import notebook_name_utils as utils

  # In code cells:
  utils.function_name(...)
  ```

- Each code cell should be minimal:
  ```python
  # Display results of Cell 2 analysis.
  utils.cell2_calculate_entropy()
  ```

## Step 5: Code Reuse

- Reuse code already existing in the `*_utils.py` file
- Reuse code already existing in the `helpers` directory
- Avoid duplication across utils functions
- Extract common patterns into helper functions

## Step 6: Sync with Jupytext

- After all modifications are complete, sync to update both files:
  ```bash
  > uvx jupytext --sync <path/to/notebook.py>
  ```

- This ensures:
  - The paired .py file matches the .ipynb file
  - All changes are propagated correctly

# Important Notes

- Always sync before editing: `uvx jupytext --sync notebook.py`
- Always sync after editing: `uvx jupytext --sync notebook.py`
- Never edit .ipynb files directly when a paired .py file exists
- See @.claude/skills/notebook.working_with_jupyter/SKILL.md for detailed Jupytext workflow
- See @.claude/skills/notebook.lint_numbered_cells/SKILL.md for function naming conventions that match cell numbers
