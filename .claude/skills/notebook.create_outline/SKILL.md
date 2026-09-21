---
description: Outline a Jupyter notebook that teaches concepts through example and discovery
model: sonnet
---

# Goal

- Create a comprehensive outline for an interactive Jupyter notebook that teaches a
  concept (passed from the user) through visualization and hands-on exploration
- The outline is a markdown file that:
  - Describes what each cell in the the notebook will contain without
  - Writing any code, serving as a blueprint for implementation

# Key Principles

- Make sure to follow the section `# Design Principles and Setup` from the file
  `.claude/skills/notebook.rules.md`
- The output is a `notebook_outline.<TAG>.md` markdown file that describes the
  notebook units
- Save markdown file in the current dir
- Do not write any code

# Outline Unit Structure

- Each unit in the outline corresponds to a triplet of cells in the final notebook:
  - **Markdown cell**: Section header, goal, and description of the panels and
    controls (before viz)
  - **Code cell**: Visualization, widgets, and interactive controls
  - **Markdown cell**: Guided usage, actions plus observations, then the
    implementation (after viz)

## Numbering and Naming

- Number units incrementally:
  - E.g., `Cell 1`, `Cell 2`, etc
- Use descriptive titles that signal the learning objective
  - Not just "Plot" or "Widget"
- Keep titles concise (5-7 words)

## Outline Unit Description Template

- Each outline unit describes the full visualization triplet
  - 3 notebook cells: pre-visualization markdown, code, and post-visualization
    markdown
- Use this structure for each unit:

  ```markdown
  ## Cell i: <Concise Learning Objective>

  **Goal**
  - <Learning objective 1>
  - <Learning objective 2>

  **Plots and their descriptions**
  - `<Plot 1 name>`: <Description of what it shows>
  - `<Plot 2 name>`: <Description of what it shows>
  - `Comments`: Current parameter values and state observations

  **Widgets** (if applicable)
  - `<widget name>`: <description, range, effect on display>
  - Each widget description is close to the widget itself

  **Guided usage** (post-visualization)
  - <Action on a widget, plus the observation it produces>
  - <Action on a widget, plus the observation it produces>

  **Implementation** Libraries and functions used
  ```

- Section labels take no trailing colon, and item names are plain backtick, not bold
  plus backtick
- In the final notebook, **Plots and their descriptions** plus **Widgets** become the
  `**Description**` markdown cell (split into `- Inputs` and `- Panels`), placed
  right after **Goal**
- **Implementation** becomes its own `**Implementation**` markdown cell, expanded
  into one bullet per algorithmic step, placed after **Guided usage**: see
  `.claude/skills/notebook.rules.md` `## Visualization Cell Triplet Details`

### Goal (Required)

- 1-2 bullet points stating the learning objectives
- If this is not the first outline unit, reference how it builds on prior concepts
  - Answers the question "Why is this outline unit important?"

### Plots and Their Descriptions (Required)

- Describe each plot using the pattern `` `<Plot name>`: <DESCRIPTION> ``
- Each plot's description is placed together with the plot title, not in a separate
  section
- Be specific about what the visualization shows (not implementation details)
- Include: axes labels, color scheme, what each panel displays
- Example:

  ```
  `Population bin`: Shows full population as colored marbles
  ```

### Widgets (If Applicable)

- List each control with its name and range
  - E.g., `Slider for mu in [0.0, 1.0]`
- Each widget description is placed close to the widget itself (in its `description`
  parameter or as an adjacent label)
- Explain the effect of changing each parameter on the display
- Keep widgets focused on pedagogically important parameters
- Avoid: redundant controls, parameters students won't care about

### Guided Usage (Required, Post-Visualization)

- List 2-3 bullets, each an action on a control plus the observation it produces,
  e.g., `Drag mu from 0.2 to 0.8` /
  `Observe the sample bin's color mix shift to match`
- These appear in a markdown cell **after** the visualization cell
- Focus on what to do and what it reveals, not general facts about the topic
- Include what experiments can be done with the widgets and what students will learn
  from doing them
- Do NOT repeat the Goal: go deeper

### Comments Panel (Required)

- Contains only variable state and observations associated to the current state
- Remove general commentary like "key insight" or "key idea"
- Include current parameter values, sample statistics, and state observations
  - E.g., current mu value, number of samples, sample mean/std

### Implementation (Required)

- Name specific libraries
  - E.g., `matplotlib`, `plotly`, `ipywidgets`, etc
- List key functions or classes
  - E.g., `ipywidgets.FloatSlider`, `matplotlib.animation`

# Example Outline

- Here's a well-structured unit outline to emulate:
- Description (pre-visualization) cell

  ```markdown
  ## Cell 1: Visualizing Population Distribution

  **Goal**
  - Give students a concrete visual representation of the unknown population
    distribution they're trying to infer from samples
  - Understand that we can only observe samples, not the full population
  ```

- Visualization cell

  ```markdown
  **Plots and their descriptions**
  - `Population bin`: Animated bin visualization with colored marbles
    (red vs blue) showing the true population
  - `Sample bin`: Shows a random sample drawn from the population
  - `Comments`: Current parameter values (mu, sample count)

  **Widgets**
  - `mu`: slider for true proportion of red marbles (0.0-1.0)
  - `seed`: random seed for reproducibility
  ```

- Commentary

  ```markdown
  **Guided usage**
  - Drag `mu` from 0.2 to 0.8, leaving `sample_size` fixed
    - Observe the sample bin's color mix shift to track the hidden
      population, even though the population itself stays unseen
  - Repeat with a different `seed`
    - Observe the sample bin change while the population bin does not:
      only the sample is one random draw

  **Implementation** Matplotlib animation for marbles, ipywidgets FloatSlider
    for control, matplotlib patches for marble visualization
  ```

# Lint

- After generating the file `notebook_outline.<TAG>.md`

  ```
  > lint_text.py -i `notebook_outline.<TAG>.md`
  ```

# Conventions

- Follow `.claude/skills/notebook.rules.md` for general notebook formatting
  conventions, including the `## Utilities vs. Notebook Responsibilities` section for
  organizing utility files and notebooks
- When writing markdown text follow
  - `.claude/skills/markdown.rules.md`: Markdown formatting rules
  - `.claude/skills/text.rules.md`: Bullet point conventions