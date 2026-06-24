---
description: Create a detailed markdown outline (notebook_outline file) for a Jupyter notebook, specifying each cell's content, purpose, visuals, and interactivity to teach concepts through example and discovery
model: opus
---

# Goal

- Create a comprehensive outline for an interactive Jupyter notebook that teaches
  a concept through visualization and hands-on exploration
- The outline describes what each cell will contain without writing any code,
  serving as a blueprint for implementation
- **Output**: A `notebook_outline.<tag>.md` markdown file that describes each
  notebook cell

# Key Principles

- Make sure to follow the section `Effective Notebook Design Principles` from the
  file `.claude/skills/notebook.rules.md`
- **Outline format**: Describe cells in markdown structure
  (`notebook_outline.<tag>.md`), not in code

# Cell Outline Structure

- Each cell in the outline corresponds to a triplet of cells in the final notebook:
  - **Markdown cell**: Section header, goal, and pedagogical content (before viz)
  - **Code cell**: Visualization, widgets, and interactive controls
  - **Markdown cell**: Key observations and what to learn (after viz)

## Numbering and Naming

- Number cells incrementally: `Cell 1`, `Cell 2`, etc.
- Use descriptive titles that signal the learning objective (not just "Plot" or
  "Widget")
- Keep titles concise (5-7 words)

## Cell Description Template

- Each cell in the outline describes the full visualization triplet (3 notebook
  cells: pre-visualization markdown, code, and post-visualization markdown).

- Use this structure for each cell:
  ```markdown
  ## Cell i: <Concise Learning Objective>

  **Goal**:
  - <Learning objective 1>
  - <Learning objective 2>

  **Plots and their descriptions**:
  - _<Plot 1 name>_: <Description of what it shows>
  - _<Plot 2 name>_: <Description of what it shows>
  - _Comments_: Current parameter values and state observations

  **Widgets** (if applicable):
  - <widget name>: <description, range, effect on display>
  - Each widget description is close to the widget itself

  **Key observations** (post-visualization):
  - <Discovery 1 students should make>
  - <Discovery 2 students should make>

  **Implementation**: Libraries and functions used
  ```

### Goal (Required)

- 1-2 bullet points stating the learning objectives
- If this is not the first cell, reference how it builds on prior concepts
- Answer: "Why is this cell important?"

### Plots and Their Descriptions (Required)

- Describe each plot using the pattern `_<Plot name>_: <description>`
- Each plot's description is placed together with the plot title, not in a
  separate section
- Be specific about what the visualization shows (not implementation details)
- Include: axes labels, color scheme, what each panel displays
- Example: "_Population bin_: Shows full population as colored marbles"

### Widgets (If Applicable)

- List each control with its name and range (e.g., "Slider for mu: 0.0-1.0")
- Each widget description is placed close to the widget itself (in its
  `description` parameter or as an adjacent label)
- Explain the immediate effect of changing each parameter on the display
- Keep widgets focused on pedagogically important parameters
- Avoid: redundant controls, parameters students won't care about

### Key Observations (Required, Post-Visualization)

- List 2-3 bullet points of discoveries students should make
- These appear in a markdown cell **after** the visualization cell
- Focus on learning outcomes, not mechanics
- Include what experiments can be done and what students will learn
- Do NOT repeat the Goal: go deeper

### Comments Panel (Required)

- Contains only variable state and observations associated to the current state
- Remove general commentary like "key insight" or "key idea"
- Include current parameter values, sample statistics, and state observations
- Example: current mu value, number of samples, sample mean/std

### Implementation (Required)

- Name specific libraries (matplotlib, plotly, ipywidgets, etc.)
- List key functions or classes (e.g., "ipywidgets.FloatSlider, matplotlib.animation")
- Note performance considerations if relevant to the student experience

# Example Outline

- Here's a well-structured cell outline to emulate:
  ```markdown
  ## Cell 1: Visualizing Population Distribution

  **Goal**:
  - Give students a concrete visual representation of the unknown population
    distribution they're trying to infer from samples
  - Understand that we can only observe samples, not the full population
  ```

- Visualization
  ```markdown
  **Implementation**: Matplotlib animation for marbles, ipywidgets FloatSlider
    for control, matplotlib patches for marble visualization

  **Plots and their descriptions**:
  - _Population bin_: Animated bin visualization with colored marbles
    (red vs blue) showing the true population
  - _Sample bin_: Shows a random sample drawn from the population
  - _Comments_: Current parameter values (mu, sample count)

  **Widgets**:
  - `mu`: slider for true proportion of red marbles (0.0-1.0)
  - `seed`: random seed for reproducibility
  ```

- Commentary
  ```markdown
  **Key observations**:
  - Population parameters are fixed but hidden: we only see samples
  - Small parameter changes produce visually distinct distributions
  - Intuition: different populations look different when fully observed
    (which we can't do)
  ```

# Important Conventions

- Always follow these guidelines:
  - `.claude/skills/notebook.rules.md`: General notebook formatting conventions,
    including the `Utilities vs. Notebook Responsibilities` section for
    organizing utility files and notebooks
  - `.claude/skills/markdown.rules.md`: Markdown formatting rules
  - `.claude/skills/text.rules.md`: Bullet point conventions
