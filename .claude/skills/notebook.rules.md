---
description: Conventions and standards for interactive Jupyter notebook structure, formatting, and cell organization
---

# Setup and Initialization

## Use Python Style
- For all Python code in notebooks, follow the rules in
  `.claude/skills/coding.rules.md`

## Use Standard Template Structure
- Use the structure from `.claude/templates/notebook.template.py` for consistent
  notebook initialization

- First Cell: Include autoreload, logging, and core dependencies
- Second Cell: Optionally install packages on-the-fly
- Third Cell: Notebook-specific imports and logger

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

# Code Cell Design and Content

## Single Responsibility Per Cell
- Each code cell performs exactly one logical task:
  - **Bad**: One cell that loads data, cleans it, trains a model, and plots
    results
  - **Good**: Import libraries, Load data, Clean data, Plot data, Train model,
    Evaluate model

## Split Cells That Perform Distinct Steps
- Cells that contain more than one concept / example should be split so that each
  cell has only one example

- Example1
  - **Bad** (this cell has 3 examples and should be split in 3 cells, as below)
    ```python
    # Test with fair coin.
    fair_coin = [0.5, 0.5]
    print(f"Fair coin entropy: {utils.calculate_entropy(fair_coin):.4f} bits")

    # Test with biased coin.
    biased_coin = [0.9, 0.1]
    print(f"Biased coin (90-10) entropy: {utils.calculate_entropy(biased_coin):.4f} bits")

    # Test with certain outcome.
    certain = [1.0, 0.0]
    print(f"Certain outcome entropy: {utils.calculate_entropy(certain):.4f} bits")
    ```
  - **Good**: each cell has one example
    - First cell
      ```python
      # Test with fair coin.
      # Two equally likely outcomes → maximum uncertainty, $H = 1$ bit
      fair_coin = [0.5, 0.5]
      print(f"Fair coin entropy: {utils.calculate_entropy(fair_coin):.4f} bits")
      ```
    - Second cell
      ```python
      # Test with biased coin.
      # If heads occurs 90% of the time → less uncertainty, $H < 1$ bit
      biased_coin = [0.9, 0.1]
      print(f"Biased coin (90-10) entropy: {utils.calculate_entropy(biased_coin):.4f} bits")
      ```
    - Third cell
      ```python
      # Test with certain outcome.
      # Certain results have no entropy, $H = 0$ bit.
      certain = [1.0, 0.0]
      print(f"Certain outcome entropy: {utils.calculate_entropy(certain):.4f} bits")
      ```

- Example2
  - **Bad**
    ```python
    # Use the weather-activity example.
    print("Example: Weather and Activity Correlation")
    print("=" * 50)
    utils.visualize_information_decomposition(joint_prob)

    # Calculate and display mutual information.
    mi = utils.calculate_mutual_information(joint_prob)
    print(f"\nMutual Information I(Weather; Activity) = {mi:.4f} bits")
    print(f"This means knowing the weather reduces uncertainty about activity by {mi:.4f} bits")
    ```
  - **Good**: two different cells
    ```python
    # Use the weather-activity example.
    print("Example: Weather and Activity Correlation")
    print("=" * 50)
    utils.visualize_information_decomposition(joint_prob)
    ```
    ```
    # Calculate and display mutual information.
    mi = utils.calculate_mutual_information(joint_prob)
    print(f"\nMutual Information I(Weather; Activity) = {mi:.4f} bits")
    print(f"This means knowing the weather reduces uncertainty about activity by {mi:.4f} bits")
    ```

## Code Cell Structure
- Use this standard structure in every code cell:
  ```python
  # Comment explaining the goal.
  operation
  
  print(result)
  # Comment on the outcome.
  ```
- Keep cells short and focused
- End with a visible result (via `print()`, `display()`, or a plot)

## Showing Results
- Use `display()` to show a dataframe
- Use `print()` for everything else

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

# Notebook Organization

## Markdown Header Structure and Naming

- Use level 1 headers (`#`) for Parts:
  - Format: `# Part XYZ: Description`
  - Parts group multiple related cells together

- Use level 2 headers (`##`) for Cells within Parts:
  - Format: `## Cell <part>.<id>: Description`
  - Each cell is a sub-section of its Part
  - Configuration cells (Imports, Logging) do not need `Cell <number>:` prefix

- Numbering convention: `<part>.<id>` where:
  - `<part>`: Part number (1, 2, 3, etc.)
  - `<id>`: Cell ID within that Part (1, 2, 3, etc.)
  - Example: `Cell 1.1`, `Cell 1.2`, `Cell 2.1`, `Cell 2.2`

- Example
  - **Good** structure:
    ```markdown
    # Part 1: Data Exploration and Loading

    ## Cell 1.1: Import libraries and load data

    ## Cell 1.2: Display data summary

    # Part 2: Data Preprocessing

    ## Cell 2.1: Handle missing values

    ## Cell 2.2: Normalize features
    ```

## Sequential Cell Numbering

- Cell numbers must be sequential with no gaps within each Part:
  - **Bad**: Cell 1.1 -> Cell 1.5 (skips 1.2, 1.3, 1.4)
  - **Good**: Cell 1.1 -> Cell 1.2 -> Cell 1.3

# Utility File Organization

## Sync Function Names with Cell Numbers

- Function names in `*_utils.py` must match the cell number in notebook headers:
  - **Bad**: Cell 1.2 header calls `utils.cell15_create_widget()`
  - **Good**: Cell 2 header calls `utils.cell2_create_widget()`
  - **Good**: Cell 1.2 header calls `utils.cell1_2_create_widget()`
- The cell number in the header is authoritative; update function names to match
- When cells are renumbered, update all matching function names

## Organize Code by Cell Order

- In `*_utils.py`, organize functions in the same order as notebook cells:
  - Group all functions for Cell 1.1, then Cell 1.2, etc.
  - Use section dividers to separate each cell's code:
    ```python
    # #############################################################################
    # Cell 1.1: Visual Bin: Population of Marbles
    # #############################################################################

    def cell1_1_calculate_entropy(...):
        ...

    # #############################################################################
    # Cell 1.2: Entropy vs Variance
    # #############################################################################

    def cell1_2_plot_distribution_with_stats(...):
        ...
    ```
  - `cell1_1_*()` functions first
  - `cell1_2_*()` functions next
  - Continue in ascending order by Part and Cell ID
  - Group related cell functions together

# Text and Markdown Formatting

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
- Never hard-code figure dimensions, but let callers customize size

## Use plot_causal_dag() for Causal DAGs

- Use `plot_causal_dag()` from `helpers_root/helpers/hgraphviz.py` when plotting
  causal DAGs in notebooks
- This function provides consistent styling and formatting for causal graphs
  across all notebooks

# Code Cleanup

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

# Interactive Cells

- Jupyter notebooks can contain `ipywidgets` widgets for interactive cells

## Interactive Idiom for Notebooks
- Each `cellN_*()` function must follow this exact pattern:

  1. Create parameter controls using functions in `helpers/htutorials.py`, such
     as
     - `htutori.build_widget_control()` for linear-scale sliders (alpha, beta, epsilon, etc.)
     - `htutori.build_log_widget_control()` for logarithmic-scale parameters (N, sample count)
     - `ipywidgets.Dropdown()` for categorical choices (plot type, model selector)

  2. Create `ipywidgets.Output()` to capture live updates

  3. Define `update_plot(change=None)` closure that:
     - Begins with: `with output: clear_output(wait=True)`
     - Reads current widget values
     - Creates figure
     - Fills content panels with plots/data
     - Fills last panel with comments via `htutori.add_fitted_text_box(ax4, text_content, ...)`
     - Ends with: `plt.tight_layout()` then `plt.show()`

  4. Attach observers to all widgets
     ```python
     slider.observe(update_plot, names="value")
     ```

  5. Call initial update: `update_plot()`

  6. Display via `ipywidgets.VBox()`:
     ```python
     display(ipywidgets.VBox([
         ipywidgets.Label("Description:"),
         slider1_box,
         slider2_box,
         output
     ]))
     ```

## The Multiple-Panel Layout Pattern

- All interactive cells must use a 1xn horizontal subplot layout
  - Panels 1-3: Data visualization (plots, histograms, heatmaps, etc.)
  - Panel 4: Comments panel with `ax.axis("off")`, a title, and text added
    via `htutori.add_fitted_text_box()`
    - The comment panel uses a wheat-colored rounded box (via `add_fitted_text_box`
      defaults) to highlight key observations, parameters, and insights

## Widgets

- Interactive widgets must always have:
  - The name of the variable (e.g., n, mu, nu)
  - Value cell and "-" and "+" buttons

- The widget to select the seed must always be the first widget

- `htutori.build_widget_control()` for linear-scale sliders (alpha, beta, epsilon, etc.)
- `htutori.build_log_widget_control()` for logarithmic-scale parameters (N, sample count)

- Each returns `(slider, HBox)` where the `HBox` includes the slider, +/-
  buttons, and text display

- A linear scale widget looks like
  ```python
  slider, box = htutori.build_widget_control(
      name="alpha",
      description="Shape parameter",
      min_val=0.5,
      max_val=10,
      step=0.5,
      initial_value=2,
      is_float=True,
  )
  ```

- Use a logarithmic Scale for parameters spanning orders of magnitude
  ```python
  # Create N widget with logarithmic slider and +/- buttons.
  # Uses exponents 2-10 for base 2: gives values 4, 8, 16, 32, 64, 128, 256, 512, 1024
  # Initial exponent 4 gives initial value of 16
  N_exp_slider, N_box = htutori.build_log_widget_control(
      name="log(N)",
      description="N (total samples)",
      min_exp=2,
      max_exp=10,
      initial_exp=4,
      base=2,
  )
  ```

- Use short, unadorned variable names in widgets:
  - Use: `mu`, `N`, `epsilon`, `seed`, `alpha`, `beta`
  - Avoid: `mean_value`, `num_samples`, `noise_std_dev`, `shape_param`
- Place `seed` parameter last in widget controls

## Markdown Cell Content for Interactive Cells
- Interactive cells (with visualizations or widgets) must include a markdown cell
  with the following sections:

  1. Goal Section: Describe what the cell teaches and its learning objectives:
    ```markdown
    **Goal**:
    - Visualize the true target function and how we sample data from it
    - Understand that in real-world ML, we only observe samples, not the complete function
    - Show the relationship between true function, training, and test data
    ```

  2. Plots Section: Document the visualizations and their purpose:
    ```markdown
    **Plots**:
    - Display four plots:
      - _True Target Function_: The unknown function (with and without noise)
      - _In-Sample Data (80%)_: Green points used for training
      - _Out-of-Sample Data (20%)_: Red points used for testing
      - _Comments_: Summary of parameters and observations
    ```

  3. Parameters Section: List all interactive controls and their ranges:
    ```markdown
    **Parameters**:
    - `Function`: Select target function (Slow Sinusoid, Fast Sinusoid, Parabola, Constant, Linear)
    - `epsilon` ($\epsilon$): Standard deviation of noise
    - `N (total samples)` ($N$): Number of data points to sample
    ```

  4. Key Observations Section: Highlight insights learners should grasp:
    ```markdown
    **Key observations**:
    - The complete curve is the unknown target function $f(x)$
    - In practice, we only access noisy samples from the function
    - Data splits into training (green) and testing (red) sets
    - Goal is to learn from training data and generalize to test data
    ```

- Each section should be:
  - formatted using bullet points using `.claude/skills/text.rules.md`
  - short with no more than 3-5 bullet points
