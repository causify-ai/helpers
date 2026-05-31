---
description: Implement a Jupyter notebook from an outline description (including interactive notebooks with widgets)
model: opus
---

## Description

- **Input**: A `notebook_outline.<tag>.md` outline file describing each notebook
  cell (created via `.claude/skills/notebook.create_outline/SKILL.md`)
- **Outputs**:
  1. `.ipynb` file: Fully functional Jupyter notebook with working code,
     visualizations, and interactive widgets
  2. `.py` file: A Python file paired using `jupytext` to the `.ipynb` using
     py:percent 
  2. `*_utils.py` file: Reusable helper functions for the notebook code
- **Purpose**: Implement the pedagogical design as a fully executable,
  interactive notebook

# Core Workflow

- **Understand the outline**: Review each cell's Purpose, Display, and (if
  present) Widgets and Key Insights
- **Implement utility functions**: Write reusable widget and visualization code
  in `*_utils.py`
- **Create notebook cells**: Add markdown cells (context) and code cells (widget
  calls) to the notebook
- **Follow the separation principle**: Utilities contain implementation; notebook
  contains only function calls

# Key Conventions

- Follow `.claude/skills/notebook.rules.md`: General notebook conventions and
  structure
- Follow outline cell format from `.claude/skills/notebook.create_outline/SKILL.md`
- Follow `.claude/skills/coding.rules.md` for Python code in `*_utils.py` and in
  the Python cells in `.ipynb` file

- Follow `.claude/skills/notebook.rules.md`
  `# Utilities vs. Notebook Responsibilities` for organizing utility files and
  notebooks

# Implementation Approach

## Code Organization
- **In notebook**: Small, focused code cells that demonstrate concepts
  interactively
- **In utils**: Reusable helper functions, plotting utilities, data processing
  functions
  - Keep notebook cells readable and pedagogically clear
  - Move complexity and infrastructure code to utils
  - Import and use utils functions to keep cells focused on concepts

# Reference Templates

- Study these before implementing; they establish the quality bar and idioms
  - `.claude/templates/notebook.template.py`
    - End-to-end notebook covering both static and interactive cell types
  - `.claude/templates/notebook_utils_template.py`
    - Paired utilities file with widget creation, state management, and
      visualization functions

- Examples of notebooks
  - `msml610/tutorials/Lesson94_Information_Theory_utils.py`
  - Production example with complex interactive patterns (especially
    `plot_joint_entropy_interactive()`)

# Implementation Patterns

## Cell Structure in Notebook

- Each cell in the outline becomes three notebook cells
- Make sure to follow the section `Cell Triplet Structure` from the file
  `.claude/skills/notebook.rules.md`

## Simple Interactive Widgets

- For cells with a single visualization and a few sliders:
  - Create the widgets, visualization, and update logic in a single utility
    function
  - Return the widget container (not bare prints or displays)
  - Accept all widget parameters explicitly (don't rely on global state)

- Example:
  ```python
  def gaussian_interactive(mu_range=(0, 1), sigma_range=(0.1, 1)):
      """
      Interactive Gaussian visualization with sliders for mu and sigma.
      """
      # Create widgets
      # Create figure and initial plot
      # Create update callback
      # Return interactive container
  ```

## Complex Interactive Widgets

- Multiple coordinated visualizations (3-4 side-by-side plots, not a 2×2 grid)
- Shared parameter controls (sliders and numeric inputs for parameters)
- Explanatory subplot with text explanation of what other plots show

### Layout and Organization

```python
def complex_entropy_interactive():
    """
    Four-plot interactive widget for joint entropy exploration.
    """
    # 1. Controls at top: sliders for each parameter + numeric input fields
    # 2. Four plots in a single row:
    #    - Joint distribution heatmap
    #    - Entropy metrics / statistics
    #    - Sampled realizations / examples
    #    - Comments: text explanation of what's happening
    
    # As sliders move, update all plots and the Comments text
    # Return the full widget container (controls + plots)
```

### Best Practices for Complex Widgets

1. **Add controls first**: Both sliders (coarse adjustment) and numeric inputs
   (precise entry)
2. **Use a single row layout**: Not 2×2 grids; arrange subplots horizontally
3. **Information in Comments subplot**: Do NOT use `print()` statements
   - Create a text matplotlib axis or HTML widget
   - Dynamically generate explanation text based on current parameter values
   - Update it in the same callback as other plots
4. **Legend per plot**: Add informative legends to each subplot, not just one
   global legend
5. **Reference implementation**: study
   - `plot_joint_entropy_interactive()` in
     `msml610/tutorials/Lesson94_Information_Theory_utils.py`
   - `cell3_interactive_sample_generator()` in `notebook_utils_template.py`
