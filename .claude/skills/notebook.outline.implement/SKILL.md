---
description: Implement Jupyter notebook from an outline description
---

- Given the passed description for a Jupyter notebook in the format described in
  `.claude/skills/notebook.outline.create/SKILL.md` implement the cells requested
  by the user

# Conventions

- You must always follow the rules and conventions in
  `.claude/skills/notebook.rules.md`

# Save Code to the corresponding library `*_utils.py`

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

# Format of Interactive Cells

- The format is described in `.claude/skills/notebook.outline.create/SKILL.md`
  `# Format of Interactive Cell`

# Reference Templates

- See `.claude/templates/interactive_notebook.template.py` for a complete
  end-to-end example of implementing an interactive notebook with:
  - Multiple cells (static, simple interactive, complex interactive, heatmap)
  - Proper documentation structure with goals, parameters, and observations
  - Integration with utility functions in `interactive_notebook_utils_template.py`
  - Best practices for widget creation and plot updates

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
- See also the multiple-plot example in
  `interactive_notebook_utils_template.py::cell3_interactive_sample_generator()`
