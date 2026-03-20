---
description: Create a Jupyter notebook script description with visual and interactive cells for teaching concepts
---

- Given the passed content, you need to create a Jupyter notebook that helps a
  college student to understand the requested concepts

# Goals

- The goals for the Jupyter notebook are:
  - Strong intuition
  - Visual explanation
  - Build example incrementally
  - Interactivity with widgets so that user can change the important variables
    and see the results immediately

- Do not write any code
  - The Jupyter notebook is described in terms of a markdown
  - Create or update the file with the script `jupyter_script.md`

# Markdown Description of Each Cell

- Focus only on the examples without repeating content from the content

- Describe each cell using bullet points

- Each cell is described with the following format

  ```markdown
  ## Cell i: Visual Bin.
  - Purpose: Give a concrete visual of the "unknown" population
  - Display:
    - Show bin with marbles colored proportionally to mu
    - ...
  - Interactive widget:
    - Slider for mu (true proportion of red marbles, 0-1)
    - ...
  - Key insights: ...
  ```

- Cells should be numbered incrementally with a format

# Formatting

- Do not use non-ascii characters
  - E.g., use mu instead of μ

- Do not use page separator
