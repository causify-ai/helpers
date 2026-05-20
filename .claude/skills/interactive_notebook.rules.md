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
  - Use the structure from `.claude/templates/notebook_template.py` for
    consistent notebook initialization

- For interactive Jupyter notebooks (i.e., notebooks with `ipywidgets`) you MUST
  follow the templates `.claude/templates/interactive_notebook_template.ipynb`
  and `.claude/templates/interactive_notebook_utils_template.py`

# Standard Function Structure (the Interactive Idiom)

- Each `cellN_*()` function must follow this exact pattern:

1. Create parameter controls using functions in `helpers/htutorials.py`, such
   as
   - `htutori.build_widget_control()` for linear-scale sliders (alpha, beta, epsilon, etc.)
   - `htutori.build_log_widget_control()` for logarithmic-scale parameters (N, sample count)
   - `ipywidgets.Dropdown()` for categorical choices (plot type, model selector)

2. Create `ipywidgets.Output()` to capture live updates

3. Define `update_plot(change=None)` closure that:
   - Begins with: `with output: clear_output(wait=True)`
   - Reads current widget values
   - Creates figure
   - Fills content panels with plots/data
   - Fills last panel with comments via `htutori.add_fitted_text_box(ax4, text_content, ...)`
   - Ends with: `plt.tight_layout()` then `plt.show()`

4. Attach observers to all widgets
   ```python
   slider.observe(update_plot, names="value")
   ```

5. Call initial update: `update_plot()`

6. Display via `ipywidgets.VBox()`:
   ```python
   display(ipywidgets.VBox([
       ipywidgets.Label("Description:"),
       slider1_box,
       slider2_box,
       output
   ]))
   ```

## The 4-Panel Layout Pattern

- All interactive cells must use a 1xn horizontal subplot layout `figsize=(20, 5)`:
  - Panels 1-3: Data visualization (plots, histograms, heatmaps, etc.)
  - Panel 4: Comments panel with `ax.axis("off")`, a title, and text added
    via `htutori.add_fitted_text_box()`
    - The comment panel uses a wheat-colored rounded box (via `add_fitted_text_box`
      defaults) to highlight key observations, parameters, and insights

## Widget Control Patterns

### Linear Scale (default for most parameters)
```python
slider, box = htutori.build_widget_control(
    name="alpha",
    description="Shape parameter",
    min_val=0.5,
    max_val=10,
    step=0.5,
    initial_value=2,
    is_float=True,
)
```

### Logarithmic Scale (for parameters spanning orders of magnitude)
```python
exp_slider, box = htutori.build_log_widget_control(
    name="log(N)",
    description="Sample count",
    min_exp=2,      # 2^2 = 4
    max_exp=12,     # 2^12 = 4096
    initial_exp=10, # 2^10 = 1024
    base=2,
)
```

Each returns `(slider, HBox)` where the `HBox` includes the slider, +/- buttons, and text display.

# Formatting

## Widget Parameter Names
- Use short, unadorned variable names in widgets:
  - Use: `mu`, `N`, `epsilon`, `seed`, `alpha`, `beta`
  - Avoid: `mean_value`, `num_samples`, `noise_std_dev`, `shape_param`
- Place `seed` parameter last in widget controls

## Import Statements
All utils files must import:
```python
import helpers.htutorial as htutori
from IPython.display import clear_output, display
```

# Markdown Cell Content for Interactive Cells
- Interactive cells (with visualizations or widgets) must include these
  sections:

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
