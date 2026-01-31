Given the passed script, implement one cell at the time, unless the user
explicitly says to implement all the cells

## Conventions
- Use the conventions in `docs/ai_prompts/notebooks.format_rules.md`

## Save code to the utils_*.py
- Given the notebook, find, print, and read the corresponding `utils_*.py` file
  - E.g., for `./msml610/tutorials/Lesson94-Information_Theory.py`
    the corresponding utils file is
    `./msml610/tutorials/utils_Lesson94_Information_Theory.py`
- All the code implementing the widget should go in the utility

- Only the caller to the function should be in the notebook
  ```
  # Display PDF, empirical mean nu, and compare with theoretical statistics.
  utils.sample_bernoulli3()
  # Changing the seed generates new realizations with different empirical values.
  ```

## Interactive widgets conventions
- Interactive widgets must always have:
  - The name of the variable (e.g., n, mu, nu)
  - A short explanation of what they are (e.g., number of samples, prob of
    success)
  - Value cell and "-" and "+" buttons

- Use code in `msml610_utils.py` like `_create_slider_widget()`,
  `build_widget_control()` to create the widgets

## Interactive widgets
- When the user asks for an "end-to-end interactive widget", it means that there
  should be multiple graphs (like 3 or 4 on the same row)
- Add the controls first with both sliders and a cell to enter the values
  - Clearly identify the meaning of each slider
  - E.g., "n = the number of sample points used", "rho = the correlation between the two random variables"

- Use a single row of 3 or 4 graphs (not in a 2 by 2 grid)
  - E.g., joint distribution, entropy metrics, sampled realizations, explanation
  - One graph should be "Comments" containing an explanation of what's happening
    in the remaining graphs, based on the values
  - Add information in each graph as a legend
- Do not print any information as `print()` statement, but write all the
  information in the "Comments" graph

- You can use `plot_joint_entropy_interactive()` in
  `msml610/tutorials/utils_Lesson94_Information_Theory.py` as a reference

- Use code in `msml610_utils.py` like `_create_slider_widget()`,
  `build_widget_control()` to create the widgets
