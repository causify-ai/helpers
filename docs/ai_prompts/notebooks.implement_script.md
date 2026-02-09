- Given the passed description for a Jupyter notebook in the format described in
  `docs/ai_prompts/notebooks.create_visual_script.md` implement the cells
  requested by the user

# Conventions

- Always use the conventions in `docs/ai_prompts/notebooks.format_rules.md`

# Save code to the `*_utils.py`

- Each notebook is paired with Jupytext to a Python file and has a corresponding
  `*_utils.py` file containing the code corresponding to that notebook
  - E.g., for the Jupyter notebook
    `msml610/tutorials/Lesson94-Information_Theory.ipynb` is paired with
    Jupytext to the file `msml610/tutorials/Lesson94-Information_Theory.py` and
    the corresponding `*_utils.py` file is
    `./msml610/tutorials/Lesson94_Information_Theory_utils.py`

- All the code implementing the widget must go in the utility
- Only the caller to the function must be in the notebook
  ```python
  # Display PDF, empirical mean nu, and compare with theoretical statistics.
  utils.sample_bernoulli3()
  # Changing the seed generates new realizations with different empirical values.
  ```

# Interactive Widgets Conventions

- Interactive widgets must always have:
  - The name of the variable (e.g., n, mu, nu)
  - Value cell and "-" and "+" buttons
- The widget to select the seed must always be the first widget

- Use code in `msml610_utils.py` like `_create_slider_widget()`,
  `build_widget_control()` to create the widgets

# Format of Cells

- Each cell description of the Jupyter notebook has the format
  ```markdown
  ## Cell i: Visual Bin.
  - Purpose: Give a concrete visual of the "unknown" population
  - Visualization:
    - Draw a 2D bin filled with red and green marbles
    - Show bin with marbles colored proportionally to mu
    - ...
  - Interactive widget:
    - Slider for mu (true proportion of red marbles, 0-1)
    - ...
  - Comment box: ...
  ```
- Each cell description corresponds to a markdown cell and an interactive cell
  - The markdown cell contains the Header and the Purpose
  - The interactive cell contains the Visualization, Interactive widget, Comment
    box

# Format of Markdown Cell
- The markdown cell has a title from the header, like:
  ```
  ## Cell i: Visual Bin.
  ```
- It describes:
  - The purpose of the cell
  - The meaning of the variables in the following interactive widget
  - What can be learned from the interactive cell

- E.g.,
  ```markdown
  ## Cell 1.2: Samples Over Time and Empirical PDF

  - Visualize $N$ samples from a Bernoulli distribution:
    - As a sequence over time
    - As an empirical probability distribution function (PDF)

  **Parameters**:
  - `mu` ($\mu$): True probability of success (between 0 and 1)
  - `N` ($N$): Number of samples to draw
  - `seed`: Random seed for reproducibility

  **Key observation**:
  - The empirical probability (blue line) is always at or below the theoretical bound (red line)
  - This confirms the Hoeffding inequality
  - The gap between them shows how conservative the bound is
  ```

# Complex Interactive Widgets

- When the user asks for a "complex interactive widget", it means that there
  must be multiple graphs (like 3 or 4 on the same row) in the same cell
- Add the controls first with both sliders and a cell to enter the values

- Use a single row of 3 or 4 graphs (not in a 2 by 2 grid)
  - E.g., joint distribution, entropy metrics, sampled realizations, explanation
  - One graph must be "Comments" containing an explanation of what's happening
    in the remaining graphs, based on the values selected in the widget
  - Add information in each graph as a legend
- Do not print any information as `print()` statement, but write all the
  information in the "Comments" graph
- You can use `plot_joint_entropy_interactive()` in
  `msml610/tutorials/Lesson94_Information_Theory_utils.py` as a reference

# Plotting Graphs

- When a plot changes a little bit because of the interactive widget controls,
  it must not abruptly change the values on the y-axis and x-axis
- The xlim and ylim of the graphs must be fixed until the graph is too big to
  fit in which case it must change so that the xlim or ylim doubles or it's
  reduced in half, so that the xlim / ylim can be stable when changing the
  widget controls
