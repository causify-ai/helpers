- Given the passed content, you need to create a Jupyter notebook that helps a
  college student to understand the requested concepts
  - The Jupyter notebook is described in terms of a markdown
  - Create or update the file with the script `script.md`

- The goals are:
  - Strong intuition
  - Visual explanation
  - Build example incrementally
  - Interactivity with widgets so that user can change the important variables
    and see the results immediately

- Do not write any code

# Markdown description of each cell
- Focus only on the examples without repeating content from the content

- Describe each cell using bullet points

- Each cell is described with the following format
  ```
  ## Cell i: Visual Bin.
  - Type: Markdown or Interactive
  - Visualization:
    - Draw a 2D bin filled with red and green marbles
    - ...
  - Interactive widget:
    - Slider for mu (true proportion of red marbles, 0-1)
    - ...
  - Display:
    - Show bin with marbles colored proportionally to mu
  - Comment box: ...
  - Purpose: Give students concrete visual of the "unknown" population
  ```

- Cells should be numbered incrementally with a format
  ```
  ## Cell 1: Visual Bin: Population of Marbles.
  ```

- Example
  ```
  ## Cell i: Visual Bin.
  - Type: Markdown or Interactive
  - Visualization:
    - Draw a 2D bin filled with red and green marbles
    - ...
  - Interactive widget:
    - Slider for mu (true proportion of red marbles, 0-1)
    - ...
  - Display:
    - Show bin with marbles colored proportionally to mu
  - Comment box: ...
  - Purpose: Give students concrete visual of the "unknown" population
  ```

# Formatting
- Do not use non-ascii characters
  - E.g., use mu instead of μ

- Do not use page separator
