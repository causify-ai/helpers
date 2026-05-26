---
description: Implement a Jupyter notebook from an outline description (including interactive notebooks with widgets)
---

## Description

- **Input**: A `notebook_outline.<tag>.md` outline file describing each notebook
  cell (created via `.claude/skills/notebook.create_outline/SKILL.md`)
- **Outputs**:
  1. `.ipynb` file: Fully functional Jupyter notebook with working code,
  visualizations, and interactive widgets
  2. `*_utils.py` file: Reusable helper functions extracted from the notebook
  code
- **Purpose**: Implement the pedagogical design as a fully executable,
  interactive notebook
- **Scope**: Covers both standard notebooks and interactive notebooks with
  widgets (outline includes Widgets and Key Insights sections)

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
- Follow outline cell format from
  `.claude/skills/notebook.create_outline/SKILL.md`
- Follow all project-level Python conventions (see project CLAUDE.md)

# Architecture: Utilities vs. Notebook

## Organization Pattern

- Each notebook follows a paired utility model
  - **Notebook**: `msml610/tutorials/Lesson94-Information_Theory.ipynb`
  - **Jupytext paired file**: `msml610/tutorials/Lesson94-Information_Theory.py`
  - **Associated utility file**: `msml610/tutorials/Lesson94_Information_Theory_utils.py`

## Responsibility Division

- **In `*_utils.py`**: All complexity goes here
  - Widget creation and state management
  - Visualization and plotting functions
  - Data computation and transformations
  - Helper functions for interactive updates
  - Documentation and parameter descriptions

- In notebook cells (Minimal, clear calls only):
  ```python
  # Display PDF, empirical mean, and compare with theoretical statistics.
  utils.sample_bernoulli3()

  # Changing the seed generates new realizations with different empirical values.
  ```

- **Rationale**: Utilities are testable, reusable, and decoupled from notebook structure

# Implementation Approach

## Code Organization
- **In notebook**: Small, focused code cells that demonstrate concepts
  interactively
- **In utils**: Reusable helper functions, plotting utilities, data processing
  functions
  - Keep notebook cells readable and pedagogically clear
  - Move complexity and infrastructure code to utils
  - Import and use utils functions to keep cells focused on concepts

## File Structure Example Naming Pattern
- Notebook: `msml610/tutorials/Lesson94-Information_Theory.ipynb`
- Jupytext paired file: `msml610/tutorials/Lesson94-Information_Theory.py`
- Utilities file: `msml610/tutorials/Lesson94_Information_Theory_utils.py`

# Reference Templates

- Study these before implementing; they establish the quality bar and idioms
  - `.claude/templates/notebook.template.py`
    - End-to-end notebook covering both static and interactive cell types
  - `.claude/templates/interactive_notebook_utils_template.py`
    - Paired utilities file with widget creation, state management, and
      visualization functions
  - `msml610/tutorials/Lesson94_Information_Theory_utils.py`
    - Production example with complex interactive patterns (especially
      `plot_joint_entropy_interactive()`)

# Implementation Patterns

## Cell Structure in Notebook

Each cell in the outline becomes two notebook cells:

1. **Markdown cell**: Pedagogical context
   ```markdown
   ## Cell 1: Visualizing Population Distribution
   
   Understanding the true population distribution is the foundation of statistical inference.
   You can't observe the full population, only samples from it. Let's see what that looks like.
   ```

2. **Code cell**: Widget invocation
   ```python
   # Display the population as a bin of colored marbles.
   utils.visualize_population_distribution()
   ```

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
    """Four-plot interactive widget for joint entropy exploration."""
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

1. **Add controls first**: Both sliders (coarse adjustment) and numeric inputs (precise entry)
2. **Use a single row layout**: Not 2×2 grids; arrange subplots horizontally
3. **Information in Comments subplot**: Do NOT use `print()` statements
   - Create a text matplotlib axis or HTML widget
   - Dynamically generate explanation text based on current parameter values
   - Update it in the same callback as other plots
4. **Legend per plot**: Add informative legends to each subplot, not just one global legend
5. **Reference implementation**: Study `plot_joint_entropy_interactive()` in 
   `msml610/tutorials/Lesson94_Information_Theory_utils.py` and 
   `cell3_interactive_sample_generator()` in `interactive_notebook_utils_template.py`

### Example Structure

```python
def plot_entropy_interactive(p_range=(0, 1), q_range=(0, 1)):
    """Interactive joint entropy visualization.
    
    Parameters:
      p_range, q_range: Tuples (min, max) for probability ranges
      
    Returns:
      Widget container with controls and 4-plot layout
    """
    # Create sliders and numeric inputs
    slider_p = FloatSlider(min=p_range[0], max=p_range[1], step=0.01, value=0.5)
    input_p = FloatText(value=0.5)
    # ... similar for q
    
    # Create figure with 4 subplots in one row
    fig, (ax_joint, ax_entropy, ax_samples, ax_comments) = plt.subplots(
        1, 4, figsize=(16, 4)
    )
    
    # Initialize plots
    update_plots(slider_p.value, slider_q.value, ax_joint, ax_entropy, ax_samples, ax_comments)
    
    # Create callback for interactivity
    def on_change(change):
        update_plots(slider_p.value, slider_q.value, ax_joint, ax_entropy, ax_samples, ax_comments)
        fig.canvas.draw()
    
    # Wire up all controls
    slider_p.observe(on_change, 'value')
    slider_q.observe(on_change, 'value')
    input_p.observe(on_change, 'value')
    input_q.observe(on_change, 'value')
    
    # Create controls and return container
    controls = VBox([HBox([slider_p, input_p]), HBox([slider_q, input_q])])
    return VBox([controls, fig.canvas])
```

# Conventions
- You must always follow the rules and conventions in
  `.claude/skills/notebook.rules.md`
- See `.claude/templates/notebook.template.py` for a complete end-to-end example
  of implementing a notebook
