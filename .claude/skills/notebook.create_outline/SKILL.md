---
description: Create a detailed markdown outline (notebook_outline file) for a Jupyter notebook, specifying each cell's content, purpose, visuals, and interactivity to teach concepts through example and discovery
---

# Purpose

- Create a comprehensive outline for an interactive Jupyter notebook that teaches
  a concept through visualization and hands-on exploration
- The outline describes what each cell will contain without writing any code,
  serving as a blueprint for implementation
- **Output**: A `notebook_outline.<tag>.md` markdown file that describes each
  notebook cell

# Core Goals

- An effective interactive notebook outline should enable:
  - **Strong intuition**: Help students build mental models through discovery
  - **Visual explanation**: Use plots, diagrams, and animations to make concepts
    concrete
  - **Incremental building**: Start simple, add complexity layer by layer
  - **Interactive exploration**: Let students manipulate parameters and see
    immediate results

# Key Principles

- **Outline format**: Describe cells in markdown structure
  (`notebook_outline.<tag>.md`), not in code
- **Focus on examples**: Concentrate on practical examples, not theory repetition
  from slides
- **Discovery over exposition**: Emphasize "what if I change this?" over "here's
  the explanation"
- **Build on context**: Each cell should reference and extend what came before

# Cell Outline Structure

- Each cell in the outline corresponds to a pair of cells in the final notebook:
  - **Markdown cell**: Section header and pedagogical context
  - **Code cell**: Visualization, widgets, and explanatory text

## Numbering and Naming

- Number cells incrementally: `Cell 1`, `Cell 2`, etc.
- Use descriptive titles that signal the learning objective (not just "Plot" or
  "Widget")
- Keep titles concise (5-7 words)

## Cell Description Template

- Use this structure for each cell:
  ```markdown
  ## Cell i: <Concise Learning Objective>

  - **Purpose**: Explain the learning goal of this cell
  - **Display**: Describe what the visualization/output will show
  - **Interactive widget**:
    - List each control (e.g., Slider for X: 0-1)
    - Explain what each widget controls
  - **Key insights**: What should students notice or learn from this cell?
  - **Comment box**: Text or annotations that explain key findings
  - **Implementation**: Which libraries and functions will be used
  ```

### Purpose (Required)

- 1-2 sentences stating the learning objective
- If this is not the first cell, reference how it builds on prior concepts
- Answer: "Why is this cell important?"

### Display (Required)

- Describe visual elements using bullet points
- Be specific about student observations (not implementation details)
- Include: axes labels, color scheme, animation behavior
- Example: "Red line shows current sample mean, gray envelope shows ±1 std dev range"

### Interactive Widget (If Applicable)

- List each control with its name and range (e.g., "Slider for mu: 0.0-1.0")
- Explain the immediate effect of changing each parameter on the display
- Keep widgets focused on pedagogically important parameters
- Avoid: redundant controls, parameters students won't care about

### Key Insights (Required)

- List 2-3 bullet points of discoveries students should make
- Focus on learning outcomes, not mechanics
- Include "aha moments" and counterintuitive observations
- Do NOT repeat the Purpose: go deeper

### Comment Box (Required)

- Describe text annotations overlaid on the visualization (callouts, arrows)
- Or a summary text cell explaining important takeaways
- Use emphasis sparingly
- Answer: "What should students take away from this cell?"

### Implementation (Required)

- Name specific libraries (matplotlib, plotly, ipywidgets, etc.)
- List key functions or classes (e.g., "ipywidgets.FloatSlider, matplotlib.animation")
- Note performance considerations if relevant to the student experience

# Example Outline

- Here's a well-structured cell outline to emulate:
  ```markdown
  ## Cell 1: Visualizing Population Distribution

  - **Purpose**: Give students a concrete visual representation of the unknown
    population distribution they're trying to infer from samples
  - **Display**:
    - Animated bin visualization with colored marbles (red vs blue)
    - Marble colors and proportions update in real-time as slider changes
    - Count of each color displayed above the bin
    - Title emphasizes "True Population (Unknown)"
  - **Interactive widget**:
    - Slider for mu: true proportion of red marbles (0.0-1.0)
    - Description: "Drag to change the unknown true proportion. Notice how the
      bin looks different but you can only ever see samples from it in practice"
  - **Key insights**:
    - Population parameters are fixed but hidden: we only see samples
    - Small parameter changes produce visually distinct distributions
    - Intuition: different populations look different when fully observed (which
      we can't do)
  - **Comment box**: "In practice, we never see the full population: only random
    samples from it. This visualization shows what we're trying to infer from
    those samples."
  - **Implementation**: Matplotlib animation for marbles, ipywidgets FloatSlider
    for control, matplotlib patches for marble visualization
  ```

# Important Conventions

- Always follow these guidelines:
  - `.claude/skills/notebook.rules.md`: General notebook formatting conventions, including the `Utilities vs. Notebook Responsibilities` section for organizing utility files and notebooks
  - `.claude/skills/markdown.rules.md`: Markdown formatting rules
  - `.claude/skills/text.rules.md`: Bullet point conventions
