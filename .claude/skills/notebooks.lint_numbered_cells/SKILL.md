---
description: Lint a Jupyter notebook and ensure cells are numbered consecutively with matching function names
---

- Given a Jupyter notebook passed on the command line, you must improve its
  appearance without changing its behavior using the rules from
  @.claude/skills/notebooks.format_rules/SKILL.md

## Workflow

1. Read all existing cell headers and identify the current numbering
2. Identify gaps, duplicates, or out-of-order cell numbers
3. Renumber headers consecutively (1, 2, 3, ... and 1.1, 1.2, ... for sub-cells)
4. Rename all functions in code cells and the `*_utils.py` file to match the new
   headers
5. Sync the paired `.py` file with Jupytext

# Use Jupytext

- Remember to modify only the Python file paired with Jupytext to the notebook
  and then sync them with Jupytext

# Rename Markdown Cells

- Each markdown cell must be named, depending on the markdown header level, with
  a format like "Cell 1:" or "Cell 1.1:" as in the following
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

# Cells in Increasing Order

- Cells should be increasing and consecutive order
  - Bad

    ```markdown
    # Cell 2: Entropy vs Variance

    # Cell 5: Interactive Visualization: Binary Entropy
    ```
  - Good

    ```markdown
    # Cell 2: Entropy vs Variance

    # Cell 3: Interactive Visualization: Binary Entropy
    ```

- When cells are renamed in the Python and Jupyter notebook also the names of
  the functions should be renamed
  - Bad

    ```python
    # Cell 2: Interactive Visualization: Binary Entropy

    utils.cell5_create_binary_entropy_widget()
    ```
  - Good

    ```python
    # Cell 2: Interactive Visualization: Binary Entropy

    utils.cell2_create_binary_entropy_widget()
    ```

# Header of a Markdown Cell with `Cell XYZ`

- A markdown cell can have a title starting with `Cell XYZ: ...`
  - If the header is level 1 (e.g., 1, 2, 3), it should have a single `#`, e.g.,
    ```markdown
    # Cell i: Visual Bin.
    ```
  - If the header is level 2 (e.g., 1.2, 2.3), it should be prepended `##`,
    e.g.,
    ```markdown
    ## Cell 1.2: Samples Over Time and Empirical PDF.
    ```

# Content of a Markdown Cell with `Cell XYZ` Header

- Each Markdown cell before of an interactive cell should have a description of
  the parameters

## Goal

- Describe the goal of the interactive cell
  ```markdown
  **Goal**:
  - Visualize the true target function and how we sample data from it
  - Understand that in real-world machine learning, we don't have access to the
    complete target function: we only observe sampled points
  - Show the relationship between the true function, in-sample (training) data,
    and out-of-sample (test) data
  ```

## Plots

- Describe the plots of the interactive cell
  ```markdown
  **Plots**:
  - Display four plots:
    - _True Target Function_: The complete unknown function we want to learn
      (shown with and without noise)
    - _In-Sample Data (80%)_: Green points used for training the model
    - _Out-of-Sample Data (20%)_: Red points used for testing the model
    - _Comments_: Summary of parameters and observations
  ```

## Parameters

- Describe the parameters of the interactive cell
  ```markdown
  **Parameters**:
  - `Function`: Select the true target function (Slow Sinusoid, Fast Sinusoid,
    Parabola, Constant, or Linear)
  - `epsilon` ($\epsilon$): Standard deviation of noise added to observations
  - `N (total samples)` ($N$): Number of data points to sample from the function
  ```

## Key Observations

- Describe the key points and observations of the interactive cell
  ```markdown
  **Key observations**:
  - The complete curve represents the unknown target function $f(x)$
  - In practice, we only have access to a few noisy samples from this function
  - We split data into training (green) and testing (red) sets
  - The goal is to learn from training data and generalize to test data
  ```

# Use Nested Bullets

- Each markdown cell must have text organized in nested bullet list
  - Bad
    ```
    Examine what happens when we repeatedly sample N points many times. Each trial produces an empirical mean nu. This cell shows the distribution of nu over many trials and compares it with the expected distribution predicted by the Law of Large Numbers and Central Limit Theorem.
    ```
  - Good
    ```
    - Examine what happens when we repeatedly sample N points many times
    - Each trial produces an empirical mean nu
    - This cell:
      - Shows the distribution of nu over many trials
      - Compares it with the expected distribution predicted by the Law of Large
        Numbers and Central Limit Theorem.
    ```

# Do Not Use Capitalized Text

- Do not use capitalized text, but prefer to use italic or bold text

# Use Latex Notation

- Markdown cell must use Latex notation for variables and formulas

# Content of Code Cells

- The interactive code in each cell must have a reference to the cell itself so
  that they are in sync

- E.g., for a cell with the header
  ```
  ## Cell 1: Visual Bin: Population of Marbles.
  ```
  the name of the function must be:
  ```
  utils.cell1_draw_bin_with_marbles_interactive()
  ```

# Keep Function Names in Sync with the Cells

- The name of a Python function needs to be in sync with the header of the
  corresponding cell
  - Good
    ```markdown
    # Cell 1: True Target Function and Data Sampling

    utils.cell1_plot_true_target_function()
    ```
    ```markdown
    ## Cell 2.2: Interactive Hoeffding Inequality Demonstration

    utils.cell22_hoeffding_inequality_demo()
    ```
  - Bad
    ```markdown
    ## Cell 2.2: Interactive Hoeffding Inequality Demonstration

    utils.cell4_hoeffding_inequality_demo()
    ```

- Assume that the header of the cells are correct and the function names need to
  be renamed

# Widget Variable Names

- In the widgets of an interactive cell use only the names of the variables
  without description
  - `mu`, `N`, `epsilon`, `seed`
- `seed` should be the last one

# Reorganize Code in the `*_utils.py` Python File

- When the code implementing the cells is in a `*_utils.py` Python file, make
  sure that:

1. All the code must be in the right order according to the cells
   - E.g., the code for `cell1_draw_bin_with_marbles_interactive` comes before
     the code for `cell2_...`
2. All the code for each chunk of cells is close to each other
3. In the Python file, there are framed dividers between cells matching the
   title of the cells
   - Good

     ```python
     # ####################...
     # Cell 1: Visual Bin: Population of Marbles.
     # ####################...

     def cell1_calculate_entropy(
     ...

     # ####################...
     # Cell 2: ...
     # ####################...

     def cell2_plot_distribution_with_stats(
     ```
