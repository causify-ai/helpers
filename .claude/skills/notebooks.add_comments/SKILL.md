---
description: Add comments in the markdown cells of a Jupyter notebook
---

# Conventions

- Always use the conventions in @.claude/skills/notebooks.format_rules/SKILL.md

# Format of Code Cells

- Each code cell description of the Jupyter notebook needs to have a
  clear explanation of:
  - Purpose of what the code does
  - What is done
  - What is the key insight
- Use bullet points in markdown, using clear and direct language

- E.g., for a code cell like
  ```python
  mtl0cireout.plot_single_vs_separate_trends()
  ```
  the markdown code before it should be like:
  ```verbatim
  - **Purpose**: Demonstrates the importance of stratification in causal inference
  - **What it shows**: The difference between fitting a single regression line to
    pooled data vs. fitting separate lines for each subgroup
  - **Key insight**: The choice of regression model can lead to different
    conclusions about the relationship between price discount and amount.
    sold for different business sizes
  ```
