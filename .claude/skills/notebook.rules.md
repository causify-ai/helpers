---
description: Conventions and standards for interative Jupyter notebook structure, formatting, and cell organization
---

# Python Code Style and Conventions

## Use Python Style
- For all Python code in notebooks, follow the rules in
  `.claude/skills/coding.rules.md`

# Notebook Structure and Initialization

## Use Standard Template Structure
- Use the structure from `.claude/templates/notebook.template.py` for consistent
  notebook initialization

## First Cell: Standard Imports and Configuration
- Include autoreload, logging, and core dependencies:
  ```python
  %load_ext autoreload
  %autoreload 2

  # System libraries.
  import logging

  # Third-party libraries.
  # import numpy as np
  # import pandas as pd
  # import seaborn as sns
  # import matplotlib.pyplot as plt
  ```

## Second Cell: Optionally Install Packages on-the-fly
- Install packages on the fly during development (all packages should be in the
  Docker container)
  ```
  # import helpers.hmodule as hmodule
  # hmodule.install_module_if_not_present(
  #     [""],
  #     use_activate=True,
  #     use_sudo=False,
  #     venv_path="/opt/venv",
  # )
  ```

## Third Cell: Notebook-Specific Imports and Logger
- Define `init_logger()` in the paired `*_utils.py` file and call it
  from the notebook, as described in `helpers_root/helpers/hnotebook.py`

- Add imports unique to this notebook after the standard cell:
  ```python
  # Helpers packages.
  import helpers.hdbg as hdbg
  import helpers.hnotebook as hnotebo

  # Tutorial-specific packages.
  import <tutorial>_utils as tutils

  # Configure the logger for this tutorial.
  _LOG = logging.getLogger(__name__)
  tutils.init_logger(_LOG)
  ```

## Notebook-to-File Pairing
- Each notebook is paired with Jupytext to a Python file
- Each notebook has a corresponding `*_utils.py` file containing the code
  corresponding to that notebook
- Use hyphens in notebook filenames and underscores in Python filenames and
  utility files

- Example
  - Notebook: `msml610/tutorials/Lesson94-Information_Theory.ipynb`
  - Paired Python file: `msml610/tutorials/Lesson94-Information_Theory.py`
  - Paired utility file: `msml610/tutorials/Lesson94_Information_Theory_utils.py`

# Code Cell Organization and Content

## Single Responsibility Per Cell
- Each code cell performs exactly one logical task:
  - **Bad**: One cell that loads data, cleans it, trains a model, and plots
    results
  - **Good**: Import libraries, Load data, Clean data, Plot data, Train model,
    Evaluate model
- Split cells if they perform multiple distinct steps

## Code Cell Structure
- Use this standard structure in every code cell:
  ```python
  # Comment explaining the goal.
  operation
  
  print(result)
  # Comment on the outcome.
  ```
- Keep cells short and focused
- End with a visible result (via `print()`, `display()`, or plot)

## Suppress Unwanted Output
- Assign output to underscore `_` to prevent display:
  - **Bad**: `statement;`
  - **Good**: `_ = statement`

## Comment Complex Code
- Add comments for non-trivial code blocks:
  - Aim for 1 comment per 2–3 lines of code
  - Focus on high-level intent, not obvious operations
  - End each comment with a period
- Example:
  ```python
  # Create an agent configured with tools and system behavior instructions.
  contract_agent = langchain.agents.create_agent(
      model=llm,
      tools=[ut.utc_now],
      # The system prompt instructs the agent to call utc_now when time is
      # requested.
      system_prompt=(
          "When time is requested, call utc_now. "
          "In your final answer, include the exact tool call used."
      ),
  )
  
  # Invoke the agent with a request for the current UTC time.
  contract_out = contract_agent.invoke(
      {
          "messages": [
              langchain_core.messages.HumanMessage(
                  content="What is the current UTC time? Use your tool."
              )
          ]
      }
  )
  
  # Extract and display the agent's final response.
  print(getattr(contract_out["messages"][-1], "content", ""))
  ```

# Cell Numbering and Naming

## Name Markdown Cells with Cell Numbers
- Use format `Cell <number>:` for markdown headers based on nesting level
- For level 1 headers, use single `#` and format like:
  `# Cell 1: Visual Bin: Population of Marbles`
- For level 2 headers, use double `##` and format like:
  `## Cell 1.1: Samples Over Time and Empirical PDF`
- Configuration cells (Imports, Logging) do not need `Cell <number>:` prefix

## Number Cells Consecutively and in Order
- Cell numbers must be sequential with no gaps:
  - **Bad**: Cell 2 -> Cell 5 (skips 3 and 4)
  - **Good**: Cell 2 -> Cell 3 -> Cell 4

## Sync Function Names with Cell Numbers
- Function names in `*_utils.py` must match the cell number in notebook headers:
  - **Bad**: Cell 2 header calls `utils.cell5_create_widget()`
  - **Good**: Cell 2 header calls `utils.cell2_create_widget()`
- The cell number in the header is authoritative; update function names to match
- When cells are renumbered, update all matching function names

# Utility File Organization

## Order Code by Cell Number
- In `*_utils.py`, organize functions in the same order as notebook cells:
  - `cell1_*()` functions first
  - `cell2_*()` functions next
  - Continue in ascending order
  - Group related cell functions together

## Use Section Dividers
- Separate each cell's code with a framed divider matching the cell title:
  ```python
  # ######################
  # Cell 1: Visual Bin: Population of Marbles
  # ######################

  def cell1_calculate_entropy(...):
      ...

  # ######################
  # Cell 2: Entropy vs Variance
  # ######################

  def cell2_plot_distribution_with_stats(...):
      ...
  ```

# Markdown Formatting Standards

## Use Nested Bullet Lists
- Organize markdown text with nested bullets for clarity:
  - **Bad**: Single paragraph with multiple ideas
    `    Examine what happens when we repeatedly sample N points. Each trial produces an empirical mean nu. This cell shows the distribution of nu and compares it with predictions from the Law of Large Numbers.    `
  - **Good**: Nested structure with related ideas grouped ` - Examine what
    happens when we repeatedly sample N points many times
    - Each trial produces an empirical mean nu
    - This cell:
      - Shows the distribution of nu over many trials
      - Compares it with the expected distribution from the Law of Large Numbers
        and Central Limit Theorem `

## Use LaTeX Notation
- Express variables and formulas with LaTeX:
  - Inline: `$\mu$ (mean), $\sigma^2$ (variance)`
  - Display: `$$E[X] = \sum x_i P(x_i)$$`
- **Bad**: `The mean is mu and variance is sigma^2`
- **Good**: `The mean is $\mu$ and variance is $\sigma^2$`

## Avoid Capitalization, Emojis, and HTML
- Do not use: ALL CAPS for emphasis, emoji, non-ASCII characters, or HTML anchor
  tags
- Use **bold** or _italic_ for emphasis instead
- Remove horizontal separators (`---`) from markdown cells

## Text Case Standards
- Use sentence case, not title case, for labels and descriptions
- Exception: LaTeX formulas may use any case
- **Bad**: `This Shows The Distribution`
- **Good**: `This shows the distribution`

# Cell Cleanup and Security

## Remove Development Environment Cells
- Remove cells for JupyterLab extensions or environment setup:
  ```python
  !sudo /bin/bash -c "(source /venv/bin/activate; pip install --quiet jupyterlab-vim)"
  !jupyter labextension enable
  ```

## Remove Package Installation Cells
- Do not install packages in notebooks; use `requirements.txt` and Docker
  instead:
  - **Remove**: `!pip install --quiet PyGithub`
  - **Instead**: Add `PyGithub` to `requirements.txt` and rebuild Docker image

## Remove Secret and Token Assignments
- Remove all cells that hardcode secrets, tokens, or credentials:
  - **Remove**: `os.environ["GITHUB_ACCESS_TOKEN"] = "..."`
  - **Instead**: Pass secrets as read-only environment variables at container
    startup

# Data Processing and Visualization

## Prefer Pandas and Seaborn
- Use `pandas` instead of `numpy` for data manipulation
- Use `seaborn` instead of `matplotlib` for plots
- Goal: Reduce code verbosity and improve readability

## Add Information to Plots, Not Output
- Embed results and information directly on plots using `ax.text()`:
  - **Bad**: Create plot, then `print(result)` below it
  - **Good**: Add result text to plot with `ax.text()` or `ax.set_title()`

## Visual Distinction Between Theoretical and Empirical Data
- When plotting both theoretical (expected) and empirical (observed) data:
  - **Theoretical**: Light, transparent colors; dotted lines
  - **Empirical**: Darker, solid colors; solid lines

## Comment Box Titles
- When using helper function `add_fitted_text_box()`, add a bold title:
  ```python
  ax.set_title("Comments", fontsize=14, fontweight="bold", pad=20)
  ```

## Configurable Figure Sizes
- All plotting functions must accept optional `figsize` parameter:
  ```python
  def plot_something(
      *,
      figsize: Optional[Tuple[int, int]] = None,
  ) -> None:
      if figsize is None:
          figsize = plt.rcParams["figure.figsize"]
      fig, ax = plt.subplots(figsize=figsize)
  ```
- Never hardcode figure dimensions; let callers customize size
