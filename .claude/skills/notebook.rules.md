---
description: Conventions and standards for interactive Jupyter notebook structure, formatting, and cell organization
---

# Effective Notebook Design Principles

## Core Goals
- An effective interactive notebook should enable:
  - **Strong intuition**: Help students build mental models through discovery
  - **Visual explanation**: Use plots, diagrams, and animations to make concepts
    concrete
  - **Incremental building**: Start simple, add complexity layer by layer
  - **Interactive exploration**: Let students manipulate parameters and see
    immediate results

## Key Principles
- **Focus on examples**: Concentrate on practical examples, not theory repetition
  from slides
- **Discovery over exposition**: Emphasize "what if I change this?" over "here's
  the explanation"
- **Build on context**: Each cell should reference and extend what came before

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

## Utilities vs. Notebook Responsibilities

### Notebook-to-File Pairing
- Each notebook is paired with Jupytext to a Python file
- Each notebook has a corresponding `*_utils.py` file containing the code
  corresponding to that notebook
- Use hyphens in notebook filenames and underscores in Python filenames and
  utility files

- Example
  - Notebook: `msml610/tutorials/Lesson94-Information_Theory.ipynb`
  - Paired Python file: `msml610/tutorials/Lesson94-Information_Theory.py`
  - Paired utility file: `msml610/tutorials/Lesson94_Information_Theory_utils.py`

### Responsibility Division
- All complexity goes in `*_utils.py`:
  - Widget creation and state management
  - Visualization and plotting functions
  - Data computation and transformations
  - Helper functions for interactive updates
  - Documentation and parameter descriptions

- In notebook cells (minimal, clear calls only):
  - Keep notebook cells readable and pedagogically clear
  - Move complexity and infrastructure code to utils
  - Import and use utils functions to keep cells focused on concepts
  - Example pattern:
    ```python
    # Display PDF, empirical mean, and compare with theoretical statistics.
    utils.sample_bernoulli3()
    ```

- **Rationale**: Utilities are testable, reusable, and decoupled from notebook structure

### Use Existing Utils Functions During Generation

- When generating a notebook, check if a corresponding `*_utils.py` file already
  exists:
  - If it does, prefer using its existing functions instead of writing new inline
    code or proposing new functions
  - If the notebook uses new cell numbers, update the utils function names to
    match (see `## Sync Function Names with Cell Numbers`)
  - If a needed function doesn't exist in the utils file, add it following the
    existing patterns and conventions

- **Rationale**: Existing utils files contain tested, reusable code that follows
  project conventions. Using them avoids duplication, keeps cells clean, and
  maintains consistency across notebooks

## Library Calls vs. Visualization in Package Tutorials
- When writing a tutorial for a package:
  - Keep the code that executes library calls and explores the API in the notebook
    - Show how to use the library's data structures and functions
    - Demonstrate the actual library calls and their results
  - Keep all visualization and plotting code in the `*_utils.py` file
    - Move complex visualizations, widgets, and formatting to utils
    - Call visualization functions from the notebook with simple parameters
  
- When computation is too expensive or complex to run in the notebook:
  - Create a small, simple example in the notebook that demonstrates the API
    - Show the data structures and library calls clearly
    - Keep the example lightweight so it runs quickly
  - Move the full, complex computation into a function in `*_utils.py`
    - This function handles the expensive computation out of view
    - The notebook calls this function to display precomputed results
  
- **Example pattern**:
  - **Bad** (visualization code embedded in notebook):
    ```python
    # Notebook cell with complex visualization mixed with API calls.
    results = library.process_data(data)
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes[0, 0].scatter(results['x'], results['y'])
    axes[0, 1].plot(results['trend'])
    # ... more plotting code ...
    ```
  
  - **Good** (library calls in notebook, visualization in utils):
    ```python
    # In notebook: show library calls clearly.
    results = library.process_data(data)
    utils.visualize_analysis_results(results)
    
    # In utils file: complex visualization separated.
    def visualize_analysis_results(results):
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        axes[0, 0].scatter(results['x'], results['y'])
        # ... full visualization code ...
    ```

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

## Use Pandas Dataframes and not Print for Tables
- Use pandas dataframes for tables and do not create tables using `print`
  - **Bad**
    ```
    print(f"{'Property':<25} {'sachs_discrete':<20} {'galton_stature':<20}")
    print("-" * 65)
    for key in sachs_tags:
        print(f"{key:<25} {str(sachs_tags[key]):<20} {str(galton_tags[key]):<20}")
    ```
  - **Good**
    ```
    # Build a comparison DataFrame from the tags dictionaries.
    tags_df = pd.DataFrame(
        {
            "Property": list(sachs_tags.keys()),
            "sachs_discrete": [str(sachs_tags[k]) for k in sachs_tags],
            "galton_stature": [str(galton_tags[k]) for k in sachs_tags],
        }
    )
    display(tags_df)
    ```

## Print Variable Name With Value
- When using `print()` to inspect a variable, always include the variable name as a
  label alongside its value
  ```python
  print("type(env)=", type(env))
  print("env=", env)
  ```
  - **Bad**: bare output with no context
    ```python
    print(env)
    ```
  - **Good**: self-documenting print with variable name
    ```python
    print("env=", env)
    ```

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

## Use Bullet-Point Comments for Structured Explanations

- When a comment describes multiple related points (mental models, parameters,
  observations, or key takeaways), use bullet-point format with each point on
  its own line instead of a single inline paragraph:
  - **Bad**: inline paragraph style
    ```python
    # **Mental model**: a `Space` is a typed contract. It knows the shape,
    # dtype, and bounds of valid data. It can sample random valid values and
    # check membership.
    ```
  - **Good**: bullet-point style with each point on its own indented line
    ```python
    # - **Mental model**:
    #   - A `Space` is a typed contract
    #   - It knows the shape, dtype, and bounds of valid data
    #   - It can sample random valid values and check membership
    ```

- **Rationale**: Bullet-point comments are easier to scan quickly, work better
  with diff tools (each point is a separate change), and align with the nested
  bullet style used throughout notebook markdown cells

# Notebook Organization

## API Notebook Overview and Summary Sections

- Every API notebook (a notebook that introduces a library or framework) must
  include two specific markdown sections:

  1. `## Library Overview` at the very beginning, right after setup cells but
     before the first code cell:
     - Use the structure:
       ```markdown
       ## Library Overview

       - **What problem it solves**: ...
       - **Key abstraction**: ...
       - **Mental model**:
         ```
         ...
         ```
       - **Key classes**:
         - ...
       ```

  2. `## Summary: The Mental Model` as the final markdown cell:
     - Recap the 2-4 essential takeaways the reader should remember
     - Each bullet must be a complete, standalone statement

- **Rationale**: The overview gives the big picture before diving into details;
  the summary reinforces what to remember after closing the notebook

## Cell Triplet Structure

- Each visualization in a notebook is composed of three notebook cells:

  1. **Markdown cell**: Explains what we want to achieve, the goal
     ```markdown
     ## Cell 1: Visualizing Population Distribution

     **Goal**:
     - Visualize the true population distribution
     - Understand sampling from a finite population
     ```

  2. **Code cell**: Visualization / interactive widget (optionally with
     ipywidget)
     ```python
     # Display the population as a bin of colored marbles.
     utils.visualize_population_distribution()
     ```
     - Documents the plots and their diagrams with comments, e.g.,
       ```
       _Population bin_: Shows the full population as colored marbles
       _Sample bin_: Shows a random sample drawn from the population
       ```

  3. **Explanation cell**: A markdown cell explaining key observations, what
     experiments can be done, and what we will learn
     ```markdown
     **Key observations**:
     - Population parameters are fixed but hidden: we only see samples
     - Small parameter changes produce visually distinct distributions
     - Try changing the sample size to see how the estimate improves
     ```

- For all the markdown cells use bullet points with nested bullets for clarity
  and conciseness, following the rules in
  - `.claude/skills/slides.rules.md`: rules for formatting slides
  - `.claude/skills/text.rules.md`: rules for formatting bullet points

## Markdown Header Structure and Naming

- Every notebook must group its cells under at least one `# Part N:` header,
  even when there is a single logical part
- Never use a level-1 header (`#`) for an individual cell; cells always use
  `## Cell <part>.<id>:`

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

## Avoid Anti-Pattern Sections

- Do not add sections labeled "Anti-patterns" or discuss anti-patterns as a
  formal section in notebook content
- Notebooks should focus on teaching correct concepts and best practices rather
  than cataloging mistakes
- Use the **Bad** / **Good** pattern for individual examples when showing what
  to avoid, not full "Anti-patterns" sections

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

## Replace Emdashes with Colons
- Do not use emdashes, but replace them with `:`
  - **Bad**
    ```
    ## Primitive 1: `list_datasets()` — The Catalog
    ```
  - **Good**
    ```
    ## Primitive 1: `list_datasets()`: The Catalog
    ```

## Non-ASCII Characters
- Avoid non-ASCII characters in code and documentation
- Use ASCII equivalents instead:
  - Use `mu` instead of `μ`, `alpha` instead of `α`
  - Use `pi` instead of `π`, `lambda` instead of `λ`
- This applies to `print()` output, f-strings, and plot/axis labels too, not
  just prose. Use ASCII equivalents:
  - `->` and `<-` instead of arrows
  - `~=` or `approx` instead of the approx symbol
  - `R^2` instead of `R` with a superscript 2
  - `in` instead of the set-membership symbol
  - `-` instead of en-dash or em-dash
- Exception: LaTeX formulas within markdown (e.g., `$\mu$`, `$\alpha$`) are
  acceptable

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

## Keep Introspection Lines
- It is acceptable to keep a `func??` introspection line to display a function's
  source or signature

## Print Public Methods of Objects
- Use `hintrospection.print_public_methods()` from
  `helpers_root/helpers/hintrospection.py` to display the public interface of a
  class or module in a notebook cell:
  list, which renders cleanly in notebook cells
- This provides a self-documenting overview of available methods, their
  signatures, and first-line docstrings
  - **Bad** (bare `dir()` with no context):
    ```python
    dir(library_module)
    ```
  - **Bad** (manually printing method names):
    ```python
    methods = [m for m in dir(library_module) if not m.startswith("_") and callable(getattr(library_module, m))]
    print(methods)
    ```
  - **Good** (standardized introspection with signatures and documentation):
    ```python
    hintros.print_public_methods(library_module, use_markdown=True)
    ```

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

  6. Display via `ipywidgets.VBox()`, without a redundant `Label` (see
     `## Remove Redundant Labels Before Control Boxes`):
     ```python
     display(ipywidgets.VBox([
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

## Remove Redundant Labels Before Control Boxes

- The descriptions are already encoded inside each widget control (via the
  `description` parameter of `build_widget_control()` or `ipywidgets` controls,
  and the `name` parameter shown in the play button / +/- box).
  Adding a separate `ipywidgets.Label` before the VBox/HBox of controls is
  redundant and wastes vertical space

- **Bad**: Wrapping controls in a `Label` then a VBox of controls
  ```python
  display(ipywidgets.VBox([
      ipywidgets.Label("Parameters:"),
      slider1_box,
      slider2_box,
  ]))
  ```
  - Each control already shows its own name/description inline
  - The `Label` adds no new information

- **Good**: Display controls directly, relying on their embedded descriptions
  ```python
  display(ipywidgets.VBox([
      slider1_box,
      slider2_box,
  ]))
  ```

- **Bad**: Label in the 2-row Output Widget Pattern
  ```python
  display(VBox([
      HBox([Label("Controls:"), controls_box]),
      output,
  ]))
  ```
- **Good**: No redundant label
  ```python
  display(VBox([
      HBox([controls_box]),
      output,
  ]))
  ```

- The same principle applies to the interactive idiom:
  - **Bad** (from the Interactive Idiom section):
    ```python
    display(ipywidgets.VBox([
        ipywidgets.Label("Description:"),
        slider1_box,
        slider2_box,
        output
    ]))
    ```
  - **Good**:
    ```python
    display(ipywidgets.VBox([
        slider1_box,
        slider2_box,
        output
    ]))
    ```

## The Output Widget Pattern for Interactive Cells

- When creating an interactive cell with ipywidget controls, HTML info panels,
  and matplotlib plots, use the Output widget pattern that separates controls
  from rendering into a clean 2-row layout:

  ```python
  # 1. Build ipywidget controls + HTML info in the top row.
  controls = VBox([dropdowns, sliders])
  info = HTML("<description>")

  # 2. Single Output widget owns all matplotlib rendering.
  output = Output()

  def update(_):
      with output:
          clear_output(wait=True)

          # 2a. One matplotlib figure, N subplots.
          _, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(14, 5))

          # 2b. Draw into each axes.
          plot_grid(ax_left)
          comments_panel(ax_right)

          plt.tight_layout()
          plt.show()

  # 3. Arrange as 2x2 grid:
  #    [controls] [HTML info]   <- ipywidgets HBox
  #    [plot]     [comments]    <- matplotlib subplots inside one Output
  top_row = HBox([controls, info])
  display(VBox([top_row, output]))
  ```

- **Do not** mix widgets and matplotlib figures in separate `display()` calls
  arranged manually. Having a single `Output()` widget that holds all matplotlib
  rendering guarantees:
  - The figure is recreated from scratch on every update, avoiding stale state
  - `clear_output(wait=True)` prevents flicker by blocking until the new figure
    is ready
  - Subplots in one figure stay aligned (shared x-axis, consistent sizing)
  - The separation of concerns: controls / HTML / plots are three distinct zones

- **Do not** use multiple Output widgets or mix inline `plt.show()` calls with
  ipywidget displays for the same interactive cell. One `Output()` that holds
  `plt.subplots()` in a shared figure is simpler and more maintainable.

- **Rationale**: This pattern cleanly separates the interactive controls (top
  row) from the visualization output (bottom row), uses a single matplotlib
  figure with subplots for all visual content, and avoids layout flickering
  via `clear_output(wait=True)`.

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

## Visualization Cell Triplet Details

Each visualization follows a three-cell structure:

### Markdown Cell (Before the Visualization)

- Title and Goal format:
  ```markdown
  ## Cell <part>.<id>: <Short Description>

  **Goal**:
  - Build intuition for <concept>
  - <Learning objective 2>
  ```

- Each plot's description is placed underneath the plot title, not in a separate
  "Plots" section. Describe them as italicized phrases with a colon:
  ```markdown
  _Population bin_: Shows the full unknown population as colored marbles
  _Sample bin_: Shows a random sample drawn from the population
  _Comments_: Current parameter values and state observations
  ```

- Each widget has its description close to it (in the widget's `description`
  parameter or as a label above the widget), ensuring it is entirely readable.

- Parameters and their ranges can be listed as bullet points under a
  `**Parameters**` heading, but keep them concise.

### Code Cell (The Visualization)

- The visualization code, optionally with ipywidgets for interactivity.

- The "Comments" panel (subplot or text box) should contain **only variable
  state and observations associated to the current state**, not general "key
  idea" commentary:
  ```python
  comment_text = (
      f"Parameters:\n"
      f"  alpha: {alpha:.2f}\n"
      f"  beta: {beta:.2f}\n"
      f"  N: {n_samples}\n\n"
      f"Sample statistics:\n"
      f"  mean: {mean_sample:.4f}\n"
      f"  std: {std_sample:.4f}"
  )
  ```
  Remove comments like "key insight" or "observation" from the Comments panel;
  keep only the information about the current parameter state.

### Markdown Cell (After the Visualization)

- After the interactive / visualization cell, add a markdown cell with key
  observations:
  ```markdown
  **Key observations**:
  - Utility spreads backward from the terminals, one ring of cells per sweep
  - Cells near the $+1$ terminal end high
  - Cells near the $-1$ terminal end low
  - The change per sweep shrinks geometrically: convergence is guaranteed

  - Early sweeps only affect cells adjacent to the terminals
  - Later sweeps refine the interior until nothing changes
  - Higher gamma propagates value further but converges more slowly
  ```

## Simple Interactive Widgets

- For cells with a single visualization and a few sliders:
  - Create the widgets, visualization, and update logic in a single utility
    function
  - Return the widget container (not bare prints or displays)
  - Accept all widget parameters explicitly (don't rely on global state)

- Example:
  ```python
  def gaussian_interactive(mu_range=(0, 1), sigma_range=(0.1, 1)):
      """
      Interactive Gaussian visualization with sliders for mu and sigma.
      """
      # Create widgets
      # Create figure and initial plot
      # Create update callback
      # Return interactive container
  ```

## Complex Interactive Widgets

- Multiple coordinated visualizations (3-4 side-by-side plots, not a 2x2 grid)
- Shared parameter controls (sliders and numeric inputs for parameters)
- Explanatory subplot with text explanation of what other plots show

### Layout and Organization

```python
def complex_entropy_interactive():
    """
    Four-plot interactive widget for joint entropy exploration.
    """
    # 1. Controls at top: sliders for each parameter + numeric input fields
    # 2. Four plots in a single row:
    #    - Joint distribution heatmap
    #    - Entropy metrics / statistics
    #    - Sampled realizations / examples
    #    - Comments: text explanation of what's happening

    # As sliders move, update all plots and the Comments text
    # Return the full widget container (controls + plots)
```

### Best Practices for Complex Widgets

1. **Add controls first**: Both sliders (coarse adjustment) and numeric inputs
   (precise entry)
2. **Use a single row layout**: Not 2x2 grids; arrange subplots horizontally
3. **Information in Comments subplot**: Do NOT use `print()` statements
   - Create a text matplotlib axis or HTML widget
   - Dynamically generate explanation text based on current parameter values
   - Update it in the same callback as other plots
4. **Legend per plot**: Add informative legends to each subplot, not just one
   global legend
5. **Reference implementation**: study
   - `plot_joint_entropy_interactive()` in
     `msml610/tutorials/Lesson94_Information_Theory_utils.py`
   - `cell3_interactive_sample_generator()` in `notebook_utils_template.py`

# Testing Notebook

- You run a command like:
  ```
  > docker_cmd.sh "python /git_root/tutorials/<package>/<paired python file>.py
  ```
  to run a notebook top to bottom and make sure it works
