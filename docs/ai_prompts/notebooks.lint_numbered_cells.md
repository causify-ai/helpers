Given a Jupyter notebook passed on the command line, you must improve its
appearance without changing its behavior using the rules from 
`docs/ai_prompts/notebooks.format_rules.md`

# Modify only the Python file paired to a Jupyter notebook
- Remember to modify only the Python file paired with Jupytext to the notebook
  and then sync them with Jupytext

# Rename markdown cells 
- Each markdown cell should be named, depending on the markdown header level,
  with a format like "Cell 1:" or "Cell 1.1:" as in the following
  - For header of level 1
    ```
    # Cell 1: Visual Bin: Population of Marbles.
    ```
  - For header of level 2
    ```
    ## Cell 1.1: Visual Bin: Population of Marbles.
    ```
- Cells around importing packages and configuring the notebook don't need the
  prefix "Cell:"
  ```
  # Imports
  ```

# Content of code cells
- The interactive code in the cells should have a reference to the cell

- E.g., for a cell
  ```
  ## Cell 1: Visual Bin: Population of Marbles.
  ```
  the name of the function should be
  ```
  utils.cell1_draw_bin_with_marbles_interactive()
  ```

# Reorganize code in the `utils_*.py` code
- When the code implementing the cells is in a `utils_*.py` Python file, make sure
  that:
  - The code is in the right order according to the cells
    - E.g., the code for `cell1_draw_bin_with_marbles_interactive` comes before
      the code for `cell2_...`
  - There are framed dividers between cells matching the cells
    ```
    # ####################...
    # Cell 1: Visual Bin: Population of Marbles.
    # ####################...
    ```
