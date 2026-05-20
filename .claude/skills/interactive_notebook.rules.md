---
description: Conventions and standards for interactive Jupyter notebook structure, formatting, and cell organization
---

- Interactive notebooks are special kind of Jupyter notebooks that contain
  widgets using `ipywidgets`

# Python Code Style and Conventions

## Use Python Style
- For all Python code in notebooks, follow the rules in
  `.claude/skills/coding.rules.md`

## Follow 
- Follow `.claude/skills/notebook.rules.md` for the basic Jupyter notebooks
  - Use the structure from `.claude/templates/notebook_template.py` for consistent
    notebook initialization

- For interactive Jupyter notebooks (i.e., notebooks with `ipywidgets`) you
  MUST follow the templates `.claude/templates/interactive_notebook_template.ipynb`
    `.claude/templates/interactive_notebook_template_utils.py`

# Formatting

## Widget Parameter Names
- Use short, unadorned variable names in widgets:
  - Use: `mu`, `N`, `epsilon`, `seed`
  - Avoid: `mean_value`, `num_samples`, `noise_std_dev`
- Place `seed` parameter last in widget controls

# Markdown Cell Content for Interactive Cells

- Interactive cells (with visualizations or widgets) must include these sections:

## Goal Section
- Describe what the cell teaches and its learning objectives:
  ```markdown
  **Goal**:
  - Visualize the true target function and how we sample data from it
  - Understand that in real-world ML, we only observe samples, not the complete function
  - Show the relationship between true function, training, and test data
  ```

## Plots Section
- Document the visualizations and their purpose:
  ```markdown
  **Plots**:
  - Display four plots:
    - _True Target Function_: The unknown function (with and without noise)
    - _In-Sample Data (80%)_: Green points used for training
    - _Out-of-Sample Data (20%)_: Red points used for testing
    - _Comments_: Summary of parameters and observations
  ```

## Parameters Section
- List all interactive controls and their ranges:
  ```markdown
  **Parameters**:
  - `Function`: Select target function (Slow Sinusoid, Fast Sinusoid, Parabola, Constant, Linear)
  - `epsilon` ($\epsilon$): Standard deviation of noise
  - `N (total samples)` ($N$): Number of data points to sample
  ```

## Key Observations Section
- Highlight insights learners should grasp:
  ```markdown
  **Key observations**:
  - The complete curve is the unknown target function $f(x)$
  - In practice, we only access noisy samples from the function
  - Data splits into training (green) and testing (red) sets
  - Goal is to learn from training data and generalize to test data
  ```
