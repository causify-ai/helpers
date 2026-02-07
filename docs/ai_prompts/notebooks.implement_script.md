Given the passed script for a Jupyter notebook in the format described in
`docs/ai_prompts/notebooks.create_visual_script.md` implement one cell at the
time, unless the user explicitly says to implement all the cells

# Conventions

- Always use the conventions in `docs/ai_prompts/notebooks.format_rules.md`

# Save code to the `utils_*.py`

- Each notebook is paired with Jupytext to a Python file and has a corresponding
  `utils_*.py` file containing the code corresponding to that notebook
  - E.g., for the Jupyter notebook
    `msml610/tutorials/Lesson94-Information_Theory.ipynb` is paired with
    Jupytext to the file `msml610/tutorials/Lesson94-Information_Theory.py` and
    the corresponding `utils_*.py` file is
    `./msml610/tutorials/utils_Lesson94_Information_Theory.py`

- All the code implementing the widget must go in the utility
- Only the caller to the function must be in the notebook
  ```
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
  `msml610/tutorials/utils_Lesson94_Information_Theory.py` as a reference

# Plotting Graphs

- When a plot changes a little bit because of the interactive widget controls,
  it must not abruptly change the values on the y-axis and x-axis
- The xlim and ylim of the graphs must be fixed until the graph is too big to
  fit in which case it must change so that the xlim or ylim doubles or it's
  reduced in half, so that the xlim / ylim can be stable when changing the
  widget controls

# Format of Each Jupyter Cell

- Each cell has only one concept / group of statements and a comment on the
  result
- Each cell has:
  - A comment explaining what we want to do
  - A group of commands
  - A statement to show the result (e.g., `print()`, `display()`)
  - A comment about the outcome
  ```
  # Comment explaining what we are trying to do.
  operation

  print results
  # Comment on the result.
  ```

- Example:
  ```python
  # Test with broken coin.
  biased_coin = [1.0, 0.0]
  print(f"Biased coin (100-0) entropy: {utils.calculate_entropy(biased_coin):.4f} bits")
  # If heads occurs 100% of the time → no uncertainty, $H = 0$ bit.
  ```
