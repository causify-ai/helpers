---
description: Create an outline for a Jupyter notebook with visual and interactive cells for teaching concepts
---

- Given the passed content, you need to create a Jupyter notebook that helps a
  college student to understand the requested concepts

# Goals

- The goals for the Jupyter notebook are:
  - Strong intuition
  - Visual explanation
  - Build example incrementally
  - Use interactive widgets so that user can change the important variables and
    see the results immediately

- Do not write any code
  - The Jupyter notebook is described in terms of a markdown
  - Create or update the file with the script `jupyter_script.<tag>.md`

# Important

- Always follow the conventions and guidelines in `.claude/skills/notebook.rules.md`

# Format of Interactive Cells

## Numbering and Structure

- Cells should be numbered incrementally with a format `Cell i: <description>`
- Each cell description corresponds to a **pair of cells** in the final notebook:
  1. **Markdown cell**: Contains the header and purpose explanation
  2. **Code cell**: Contains visualization, interactive widgets, and comment box

## Content Focus

- Focus only on examples without repeating content from the slides
- Each cell should build incrementally on previous concepts
- Emphasize discovery through interaction rather than explanation

## Cell Description Template

- Describe each cell using the following structure with bullet points:
  ```markdown
  ## Cell i: <Concise Title>

  - **Purpose**: Explain the learning goal of this cell
  - **Display**: Describe what the visualization/output will show
  - **Interactive widget**:
    - List each widget (e.g., Slider for X: 0-1)
    - Explain what each widget controls
  - **Key insights**: What should students notice or learn from this cell?
  - **Comment box**: Text or annotations that explain key findings
  - **Implementation**: Which libraries and functions will be used
  ```

### Purpose
- 1-2 sentences explaining the learning objective
- Connect to prior cells when applicable

### Display
- Use bullet points to describe each visual element
- Be specific about what students will observe
- Include axes labels, color schemes, and layout details

### Interactive Widget
- List each control by name and range/options
- Explain the immediate effect of changing each parameter
- Widgets should update the display in real-time

### Key Insights
- 2-3 bullet points of what students should discover
- Avoid repeating the purpose; focus on learning outcomes
- Include "aha moments" or counterintuitive observations

### Comment Box
- Annotations directly in the visualization (text overlays, callouts)
- Or a text cell explaining important takeaways
- Use emphasis sparingly

### Implementation
- Name specific Python libraries (matplotlib, plotly, ipywidgets, etc.)
- List key functions or classes needed
- Include performance considerations if relevant

## Example

```markdown
## Cell 1: Visual Population Distribution

- **Purpose**: Give students a concrete visual representation of the unknown
  population distribution
- **Display**:
  - Animated visualization of a bin with marbles
  - Marbles colored proportionally to the parameter $\mu$
  - Real-time count of marble colors updated as slider changes
- **Interactive widget**:
  - Slider for $\mu$ (true proportion of red marbles, range 0-1)
  - Animation speed control (optional)
- **Key insights**:
  - Population parameters are fixed but unknown to us
  - Small changes in $\mu$ produce visually distinct distributions
- **Comment box**: "This is the true population. In practice, we can't see this
  directly—only samples from it."
- **Implementation**: Matplotlib for visualization, ipywidgets Slider for
  interactivity
```

# Formatting
- Do not use non-ascii characters
  - E.g., use mu instead of μ

- Do not use page separator

# Important

- When writing markdown you must follow the rules and conventions in
  `.claude/skills/markdown.rules.md`

- When writing bullet points you must follow the rules and conventions in
  `.claude/skills/text.rules.bullet_points.md`
