---
description: Format rules for interactive cells in Jupyter notebooks
---

# Interactive Widgets Conventions

- Interactive widgets must always have:
  - The name of the variable (e.g., n, mu, nu)
  - Value cell and "-" and "+" buttons
- The widget to select the seed must always be the first widget

- Use code in `msml610_utils.py` like `_create_slider_widget()`,
  `build_widget_control()` to create the widgets

# Logarithmic Widget Control

- When asked to build a logarithmic widget control, use the following idiom
  ```python
  # Create N widget with logarithmic slider and +/- buttons.
  # Uses exponents 2-10 for base 2: gives values 4, 8, 16, 32, 64, 128, 256, 512, 1024
  # Initial exponent 4 gives initial value of 16
  N_exp_slider, N_box = mtumsuti.build_log_widget_control(
      name="log(N)",
      description="N (total samples)",
      min_exp=2,
      max_exp=10,
      initial_exp=4,
      base=2,
  )
  ```

# Format of Code Cells with Interactive Demo

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
