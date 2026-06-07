- This file contains all the conventions for Python coding rules.

# Environment and Platform

## Only Linux and MacOS

- Assume the script needs to run only on Linux and MacOS

# Code Style and Structure

## Follow the Coding Style From the Template

- Use the coding style in `.claude/templates/coding.template.py`

## Use `typing` Module Style for Type Hints

- Use type hints from the `typing` module instead of newer PEP 604 syntax
- Use `Tuple`, `Dict`, `Optional` instead of `tuple`, `dict`, `|` union syntax
  - **Bad**: Use newer PEP 604 syntax
    ```python
    def process(data: dict[str, str], item: str | None) -> tuple[str, int]:
        ...
    ```
  - **Good**: Use `typing` module
    ```python
    from typing import Dict, Tuple, Optional
    
    def process(data: Dict[str, str], item: Optional[str]) -> Tuple[str, int]:
        ...
    ```

## Use `os` and `os.path` for Path Operations

- Use `os` and `os.path` for path operations instead of `pathlib.Path`

- **Bad**: Using `pathlib`
  ```python
  from pathlib import Path
  
  file_path = Path("/tmp/data.txt")
  if file_path.exists():
      content = file_path.read_text()
  ```
- **Good**: Using `os` and `os.path`
  ```python
  import os
  
  file_path = "/tmp/data.txt"
  if os.path.exists(file_path):
      with open(file_path, "r") as f:
          content = f.read()
  ```

## Mark Private Functions

- Functions that are used only in one file, must be private and their name must
  start with `_`

## Remove Empty Lines

- If empty lines are used to separate chunks of code, convert empty lines into
  comments for the chunk of code
- Remove empty lines inside functions so that the code is compact

## Make Code Cohesive

- Refactor the code to improve locality, readability, and maintainability
	without changing behavior

- Transformation rules:
  - Preserve exact semantics and execution order
  - Move intermediate computations so they appear immediately before their first
    use
  - Group related logic into self-contained contiguous blocks
  - Keep temporary variables close to the operation that consumes them
  - Reduce the distance between:
    - Data preparation
    - Derived values
    - The operation that uses them
  - Preserve variable names and existing logic
  - Do not introduce helper functions, abstractions, or new control flow
  - Preserve formatting style and comments where possible
  - Do not reorder operations if doing so could change behavior
  - The refactor should only improve structural organization and locality of
    reference

- Transform code shaped like:
  ```python
  shared_value_a = ...
  shared_value_b = ...

  derived_a = ...
  derived_b = ...

  operation_a(...)
  operation_b(...)
  ```
  into
  ```python
  derived_a = ...
  operation_a(...)
  #
  derived_b = ...
  operation_b(...)
  ```

- Example
  - **Bad**
    ```python
    # Build propensity score model.
    ps_model = LogisticRegression(penalty=None)
    ps_model.fit(train[X], train[T])
    # Compute propensity scores once.
    propensity_scores = ps_model.predict_proba(train[X])
    # Split treatment groups.
    train_t0 = train.query(f"{T} == 0")
    train_t1 = train.query(f"{T} == 1")
    # Extract corresponding sample weights.
    w_t0 = 1 / propensity_scores[train[T] == 0, 0]
    w_t1 = 1 / propensity_scores[train[T] == 1, 1]
    ```
  - **Good**
    ```python
    # Build propensity score model.
    ps_model = LogisticRegression(penalty=None)
    ps_model.fit(train[X], train[T])
    # Compute propensity scores.
    propensity_scores = ps_model.predict_proba(train[X])
    # Outcome models.
    m0 = LGBMRegressor()
    # Split treatment groups.
    train_t0 = train.query(f"{T} == 0")
    # Extract corresponding sample weights.
    w_t0 = 1 / propensity_scores[train[T] == 0, 0]
    # Same for other outcome.
    m1 = LGBMRegressor()
    train_t1 = train.query(f"{T} == 1")
    w_t1 = 1 / propensity_scores[train[T] == 1, 1]
    ```

## Decompose Dense Method Chain in Assignments

- Decomposing a dense method chain (e.g., from `pandas`) into linear intermediate
  assignments to improve readability, debuggability, and explainability
  - Unrolling a method chain into explicit transformation stages
  - Making implicit dataframe transformations explicit
  - Converting a compact fluent pipeline into self-documenting procedural steps
  - Introducing narrative structure into transformations

- Example
  - **Bad**
    ```python
    test_cf = (
        test
        .drop(columns=[T])
        .assign(key=1)
        .merge(t_grid)
        .assign(**{y_hat_col: lambda d: s_learner.predict(d[X + [T]])})
    )
    ```
  - **Good**
    ```python
    # Remove original treatment values to create a clean base for counterfactuals.
    test_cf = test.drop(columns=[T])
    # Add merge key to enable cross-product with treatment grid.
    test_cf = test_cf.assign(key=1)
    # Create counterfactual dataset by merging each test row with all treatment
    # values.
    test_cf = test_cf.merge(t_grid)
    # Generate predictions for each (features, treatment) combination.
    test_cf = test_cf.assign(**{y_hat_col: lambda d: s_learner.predict(d[X + [T]])})
    ```

# Error Handling and Assertions

## Use `dassert` instead of if ... raise

- Use `dassert` instead of if ... raise

- **Bad**
	```python
	if not header_line.startswith("#"):
			raise ValueError(
					"Line %d is not a markdown header: '%s'" % (line_num, header_line)
			)
	```
- **Good**
	```
	hdbg.dassert(header_line.startswith("#"),
		"Line %d is not a markdown header: '%s'",
		str(line_num, header_line)
	)
	```

## Use `dassert` instead of `assert`

- Use the proper specialized `dassert_*` from `helpers/hdbg.py` instead of a
	Python `assert`

- **Bad**
	```
	assert end_header_str_converted is not None
	```
- **Good**
	```
	hdbg.dassert_is_not(end_header_str_converted, None)
	```

## Use Specialized `dassert_*`

- Use specialized `hdbg.dassert_*` functions from `helpers/hdbg.py`
  instead of generic `hdbg.dassert()`
  - Choose the most specific assertion function for your check

- Common specialized assertion functions:
  - `hdbg.dassert_in(value, container)`: Check membership
  - `hdbg.dassert_not_in(value, container)`: Check non-membership
  - `hdbg.dassert_eq(val1, val2)`: Check equality
  - `hdbg.dassert_ne(val1, val2)`: Check inequality
  - `hdbg.dassert_lt(val1, val2)`: Check less than
  - `hdbg.dassert_lte(val1, val2)`: Check less than or equal
  - `hdbg.dassert_isinstance(obj, type)`: Check type
  - `hdbg.dassert_file_exists(path)`: Check file existence
  - `hdbg.dassert_dir_exists(path)`: Check directory existence

- Example: Use `dassert_in()` instead of generic `dassert()`
  - **Bad**: Generic assertion with membership check
    ```python
    hdbg.dassert(
        ext in _FORMAT_MAP,
        "Unsupported file format; supported formats are: %s",
        ", ".join(_FORMAT_MAP.keys()),
    )
    ```
  - **Good**: Check if value is in container
    ```python
    hdbg.dassert_in(
        ext,
        _FORMAT_MAP,
        "Unsupported file format; supported formats are: %s",
        ", ".join(_FORMAT_MAP.keys()),
    )
    ```

- Pass parameters using lazy formatting and not f-strings
  - **Bad**
    ```python
    hdbg.dassert_ne(
        name,
        "",
        f"Name cannot be empty: {name}",
    )
    ```
  - **Good**
    ```python
    hdbg.dassert_ne(
        name,
        "",
        "Name cannot be empty:",
        name,
    )
    ```

## Add Message to `dassert`
- For each `dassert_*()` assertion make sure there is a message explaining why
  the assertion is important
  - **Bad**
    ```python
    hdbg.dassert(len(results) > 0)
    ```
  - **Good**
    ```python
    hdbg.dassert(len(results) > 0, "Query must return at least one result")
    ```
  - **Bad**
    ```python
    hdbg.dassert_eq(len(results), expected_len, "error")
    ```
  - **Good**
    ```python
    hdbg.dassert_eq(len(results), expected_len, 
                f"Expected number of results doesn't match the passed one")
    ```

- When adding a comment try to not repeat information already present in the
  assertion
  - **Bad** since `dassert_in()` will already print the valid values
    ```python
    hdbg.dassert_in(
      method,
      ["auto", "github_api", "linear_scan"],
      f"Invalid method '{method}'; must be one of: auto, github_api, linear_scan",
    )
    ```
  - **Good**
    ```python
    hdbg.dassert_in(
      method,
      ["auto", "github_api", "linear_scan"],
      "Invalid method specified"
    )
    ```

- When adding a comment do not use the f-string formatting, but use the
  printf-style string formatting
  - **Bad**
    ```python
    hdbg.dassert(
        branch.startswith(prefix),
        f"Remote branch '{branch}' must start with '{prefix}' prefix",
    )
    ```
  - **Good**
    ```python
    hdbg.dassert(
      branch.startswith(prefix),
        "Remote branch '%s' needs to start with '%s'",
        branch,
        prefix,
    )
    ```

## Use `raise` Instead of `dassert(False, ...)`

- When unconditionally raising an error, use `raise` with an appropriate exception
  instead of `hdbg.dassert(False, ...)`

- Example: Use `raise` for unconditional errors
  - **Bad**: Using `dassert(False, ...)` for unconditional errors
    ```python
    hdbg.dassert(
        False,
        "Output directory already contains chapter files: %s (use --overwrite to replace)",
        output_dir,
    )
    ```
  - **Good**: Use `raise` with appropriate exception
    ```python
    raise ValueError(
        f"Output directory already contains chapter files: {output_dir} "
        "(use --overwrite to replace)"
    )
    ```

## Do Not Use `try-except`

- Do not use try except to recover errors but let statements raise their own
  errors

# Docstrings

## Use Docstrings on Three Lines

- If the docstring is only one line, convert it to three lines
  - **Bad**
    ```python
    def reset(self) -> None:
      """Reset any internal state of the strategy."""
      pass
    ```
  - **Good**
    ```python
    def reset(self) -> None:
      """
      Reset any internal state of the strategy.
      """
      pass
    ```

## Use REST Style for Docstrings

- Always use REST style for docstrings

- When there are multiple values for an input or an output variable format them
  as a list:
  - **Bad**
    ```python
    :param interpolate_colors: If True, evenly space selected colors across
      all bold items; if False, use a predefined sequence for common counts
      (1-4 items get fixed color sets, more items cycle through all_md_colors)
    :param all_md_colors: List of available colors to cycle through (defaults
      to the curated list from get_md_colors())
    ```
  - **Good**:
    ```python
    :param use_abbreviations:
       - If True, use abbreviated color syntax (e.g., `\red{foo}`)
       - If False, use full LaTeX syntax (e.g., `\textcolor{red}{foo}`)
    :param all_md_colors: List of available colors to cycle through
        - Default: curated list from `get_md_colors()`
    ```

- An example of a good docstring comment is
  ```python
  r"""
  Colorize bold markdown items `**text**` with color commands.

  Scans the text line-by-line for bold markdown items and wraps each in a
  color command (e.g., `**\red{text}**`). Skips code blocks and tables to
  preserve their formatting. Bold items are colored sequentially using the
  provided color list.

  :param txt: Markdown text containing bold items to colorize
  :param use_abbreviations:
      - If True, use abbreviated color syntax (e.g., `\red{foo}`)
      - If False, use full LaTeX syntax (e.g., `\textcolor{red}{foo}`)
  :param interpolate_colors:
      - If True, evenly space selected colors across all bold items
      - If False, use a predefined sequence for common counts (1-4 items get
        fixed color sets, more items cycle through all_md_colors)
  :param all_md_colors: List of available colors to cycle through
      - Default: curated list from `get_md_colors()`
  :return: Markdown text with bold items wrapped in color commands
  """
  ```

## Update Docstrings If Out-of-sync

- Update the docstring to functions and file that are not in sync with the code
  - **Bad**:
    ```python
    def calculate_total(items):
        """
        Calculate something.
        """
        return sum(item.price for item in items if item.active)
    ```
  - **Good**
    ```python
    def calculate_total(items):
        """
        Calculate sum of prices for all active items.
        
        :param items: List of Item objects with price and active attributes
        :return: Total price as float
        """
        return sum(item.price for item in items if item.active)
    ```

- Make sure all the functions have a REST comments in docstrings
  - Add docstrings to functions and file that are missing

## Add Input/Output Examples to Docstrings When Non-Obvious

- Include concrete examples of inputs and outputs in function docstrings when
  the expected data types or formats are not immediately apparent from the
  signature or parameter names
- Use examples in these scenarios:
  - Complex data structures (nested dicts, custom objects, specific formats)
  - Transformations where the output differs significantly from the input
  - Edge cases or special values that need clarification
  - When parameter purposes or expected ranges are ambiguous

- **Bad**: Vague description without examples for complex transformation
  ````python
  def transform_data(raw_input):
      """
      Transform raw input into normalized format.
      
      :param raw_input: Input data to transform
      :return: Transformed data
      """
  ````
- **Good**: Clear examples showing input/output for complex transformation
  ````python
  def transform_data(raw_input):
      """
      Transform raw input into normalized format.
      
      :param raw_input: Dict with keys 'name', 'age', 'salary'
          Example:
          ```
          {'name': 'Alice', 'age': '30', 'salary': '50000.00'}
          ```
      :return: Dict with normalized values (strings to proper types)
          Example:
          ```
          {'name': 'Alice', 'age': 30, 'salary': 50000.0}
          ```
      """
  ````

- **Good**
  ````python
  def _fetch_aa_benchmarks(model_name: str) -> Dict[str, Optional[float]]:
    """
    Fetch benchmark data from Artificial Analysis API using cached models.

    :param model_name: Model name in OpenRouter or AA format
    :return: Dict with "coding_score" and "intelligence_score" (None if not found)
        ```
        {'coding_score': None, 'intelligence_score': None}
        ```
    """
  ````

- **Good**
  ````python
  def _format_table(table: pd.DataFrame) -> pd.DataFrame:
    """
    Format table columns using appropriate formatting functions.

    Applies formatting to numerical columns for display:
    - Input_Cost, Output_Cost: formatted via _format_cost()
    - Context: formatted via _format_context()
    - Speed_(tok/s): formatted via _format_benchmark()
    - Coding_IQ, General_IQ: formatted via _format_benchmark()

    :param table: DataFrame with raw numerical data
        ```
        Model_ID | Input_Cost | Output_Cost | Context | Speed_(tok/s) | Coding_IQ
        ---
        openai/... | 0.003 | 0.015 | 128000 | 25.5 | 72.3
        ```

    :return: DataFrame with formatted string columns for display
        ```
        Model_ID | Input_Cost | Output_Cost | Context | Speed_(tok/s) | Coding_IQ
        ---
        openai/... | "0.003" | "0.015" | "128K" | "25.5" | "72.3"
        ```
    """
  ````


## Use Verbatim to Refer to Python Objects

- When referring to Python objects (e.g., variables, classes, and functions) in
  comments and docstrings use verbatim included in backticks
  - For functions also include a call, e.g., `func()`

- Example (variable in comment):
  - **Bad**
    ```python
    # Increment the variable num_counter.
    ```
  - **Good**
    ```python
    # Increment the variable `num_counter`
    ```

- Example (function in comment):
  - **Bad**
    ```
    # Create a curated list from get_md_colors.
    ```
  - **Good**
    ```
    # Create a curated list from `get_md_colors()`.
    ```

- Example (variable in docstring):
  - **Bad**
    ```python
    """
    Increment the variable num_counter.
    """
    ```
  - **Good**
    ```python
    """
    Increment the variable `num_counter`.
    """
    ```

- Example (function in docstring):
  - **Bad**
    ```
    """
    Test helper for standardize_filename().
    """
    ```
  - **Good**
    ```
    """
    Test helper for `standardize_filename()`.
    """
    ```

# Comments

## Add Comments Liberally
- You must override any minimalist comment defaults add explanatory comments
  liberally
  - Leave existing comments unless they are incorrect, even if they explain
    WHAT code does and they are redundant

## Comment Chunk of Code
- Use comments to separate logical chunks of code
- Explain the logic and intent of code sections, especially for:
  - Complex algorithms or multi-step processes
  - Conditional branches and why they're needed
  - Non-obvious variable assignments or transformations
  - Implementation choices and workarounds
  - Algorithm steps in a sequence

- Comments should explain the WHY and the algorithm flow, not only the WHAT
  - **Bad**: (obvious from the code)
    ```python
    # Iterate over lines.
    for line in lines:
      ...
    ```
  - **Good**: (explains intent)
    ```python
    # Process imports in two passes: first collect, then validate.
    ```

## Commenting Style
- Prefer single-line comments over multi-line comment blocks when possible

- Use periods at the end of all comments

- In comments always use `: ` instead of ` - `
  - **Bad**
    ```
    # Check outputs - Result verification
    ```
  - **Good**
    ```
    # Check outputs: Result verification
    ```

## Convert Empty Lines and Empty Comments in Block Comments
- Do not use empty lines within functions but use comments to separate chunks of
  code

- If there are empty lines or empty comments `# ` separating chunks of code
  replace them with comments explaining the block

## Leave Existing Comments Untouched

- Leave untouched comments that represent examples of input-output relationships
  - E.g.,
    ```python
    # Transform:
    #   ('a2bfc704', ['head_hash', 'remh_hash'])
    # into
    #   'head_hash = remh_hash = a2bfc704'
    ```

- Leave comments that represent running a command and getting a result:
  - E.g.,
    ```python
    # > git config --file /Users/saggese/src/.../.gitmodules --get-regexp path
    # submodule.amp.path amp
    ```

- Do not remove TODOs or other comment code, unless you are sure they are
  redundant, wrong, or and useless
  - Example to keep:
    ```python
    # Divide by 2 since we count the number of occurrences of `**`, while we
    # want to count `**bold**` as 1.
    # hdbg.dassert_eq(tot_bold % 2, 0, "tot_bold=%s needs to be even", tot_bold)
    num_bolds = tot_bold // 2
    ```
  - Example to keep:
    ```python
    # TODO(gp): -> List[str]
    # TODO(gp): Use hmarkdown.process_lines() and test it.
    def colorize_bullet_points_in_slide(
    ```

# Function Design

## Minimize Default Values of None in Function Interfaces

- In function signatures and class constructors, avoid `None` as default values to
  minimize `Optional` types in type hints
- Use meaningful default values of the same type instead to keep interfaces
  simpler and reduce the need for `Optional`

- **Bad**: Using `None` defaults creates `Optional` type requirements
  ```python
  def process(
      data: Dict[str, str],
      *,
      timeout: Optional[int] = None,
      name: Optional[str] = None,
  ) -> str:
      if timeout is None:
          timeout = 30
      if name is None:
          name = "default"
      ...
  ```
- **Good**: Use meaningful type-matching defaults
  ```python
  def process(
      data: Dict[str, str],
      *,
      timeout: int = 30,
      name: str = "",
  ) -> str:
      ...
  ```

- This pattern applies to:
  - Function parameters and return types
  - Class constructor arguments
  - Dataclass field definitions
  - Any interface that accepts arguments with defaults

- Choose meaningful defaults based on the parameter type:
  - For strings: use `""` (empty string)
  - For integers: use `0`, `-1`, or another sentinel that makes semantic sense
  - For booleans: use `False` or `True` based on intended semantics
  - For paths: use `""` or consider making the parameter required

## Use `*` to Force Keyword Arguments for Optional Parameters

- Default values should be rare exceptions: only use them when 99.9% of all calls
  need the same value
- For optional parameters
  - always use a default value
  - use `*` to force keyword argument passing
- This makes the API more explicit and prevents silent surprises when defaults
  change

- **Bad**: Optional parameters with defaults are too convenient to ignore
  ```python
  def analyze(
      data: List[str],
      verbose: bool = False,
      timeout: int = 30,
      output_format: str = "json",
  ) -> Dict[str, Any]:
      ...
  ```
- **Good**: Force keyword arguments for optional parameters using `*`
  ```python
  def analyze(
      data: List[str],
      *,
      verbose: bool = False,
      timeout: int = 30,
      output_format: str = "json",
  ) -> Dict[str, Any]:
      ...
  ```

## Use Default Values Very Rarely in Interfaces

- Only provide defaults when the parameter is truly optional and the default
  applies to 99.9% of use cases and make them 
  ```python
  def connect(
      host: str,
      port: int,
      *,
      ssl: bool = True,  # Almost all connections use SSL
      timeout: int = 30, # timeout is required to be explicit
  ) -> Connection:
      ...
  ```

- Parameters with default must be keyword-only parameters (after a `*`)

- Benefits of using `*`:
  - Callers must explicitly state their intention via keyword arguments
  - Reduces brittleness when adding new parameters to existing functions
  - Makes APIs more discoverable and self-documenting
  - Prevents accidental reliance on defaults that may change in maintenance

## Call Functions With Position Arguments for Required, Keywords for Optional

- When calling functions, follow this convention:
  - Use positional arguments for mandatory parameters only
  - Use keyword arguments (by name) for all parameters that have default values
- This makes calls explicit and self-documenting, matching the function definition style

- **Bad**: Using positional arguments for optional parameters hides intent
  ```python
  # Define
  def analyze(data: List[str], *, verbose: bool = False, timeout: int = 30) -> Dict:
      ...
  
  # Call - implicit about which parameters have defaults
  result = analyze(data_list, False, 60)
  ```
- **Good**: Use position for required, keywords for optional
  ```python
  # Define
  def analyze(data: List[str], *, verbose: bool = False, timeout: int = 30) -> Dict:
      ...
  
  # Call - explicit about optional parameters
  result = analyze(data_list, verbose=False, timeout=60)
  ```

- Apply this pattern consistently:
  - Mandatory parameters (no default): use position
  - Optional parameters (has default): use keyword argument with name
  - If a function uses `*` to force keywords, the call naturally follows this
    pattern

# Logging

## Use _LOG

- Use `_LOG.info` instead of print, unless there is a comment explicitly saying
  that it should be used print
- Use `_LOG.debug` to add debugging info that can help a programmer to track the
  issues
  - Always use lazy % formatting in logging functions

## Enclose Variables in Single Quotes in Log Messages

- When logging messages that include variable values for user display, enclose
  variables in single quotes to make them visually distinct from surrounding text
- This improves readability and helps users identify actual values in log output

- **Bad**: Variables not visually distinct
  ```python
  _LOG.info("Downloading %s from %s", book_name, url)
  ```
- **Good**: Variables enclosed in single quotes
  ```python
  _LOG.info("Downloading '%s' from '%s'", book_name, url)
  ```

# Script Development

## Use Script Template

- When creating scripts use the script template
  `dev_scripts_helpers/coding_tools/script_template.py`

- Create a parser function
  ```python
  def _parse() -> argparse.ArgumentParser:

  def _main(parser: argparse.ArgumentParser) -> None:
  ```

## Script Shebang and Dependencies

- For scripts with external package dependencies, use the `uv run` shebang with
  inline script dependencies:
  ```python
  #!/usr/bin/env -S uv run

  # /// script
  # dependencies = ["pydeps", "networkx", "pyyaml", "graphviz"]
  # ///
  ```
- List all external (non-stdlib, non-helpers) packages required by the script in
  the `dependencies` array
- This allows scripts to be run directly without pre-installing packages: `./script.py`

## Make Scripts Executable

- When creating a Python script, run `chmod +x` on it to make it executable
- In the README and comments, always refer to scripts as `./script.py` or
  `script.py`, never as `python script.py`
  - **Bad**: Documentation refers to the script as needing Python
    ```
    # Run the script: python standardize_book_filename.py
    # Usage: python convert_epub_to_md.py input.epub output.md
    ```
  - **Good**: Documentation refers to the script as executable
    ```
    # Run the script: ./standardize_book_filename.py
    # Usage: ./convert_epub_to_md.py input.epub output.md
    ```

## Script Docstring Usage Examples

- When writing docstrings or comments to explain how to use a script, do not use
  the entire file path and do not prepend with `python`
- Refer to scripts using their simple filename or relative path with `./`

- **Bad**: Uses full path and `python` prefix
  ```python
  """
  > python dev_scripts_helpers/llms/llm_cli.py -i some.md ...
  """
  ```
- **Good**: Uses simple script name
  ```python
  """
  > extract_from_md.py -i some.md ...
  """
  ```

## Use Standard Argument Helpers From `hparser`

- Use `hparser` helper functions to add standard arguments instead of defining
  them manually
- This ensures consistency across all scripts in the project

- For verbosity/logging level:
  ```python
  import helpers.hparser as hparser
  hparser.add_verbosity_arg(parser)
  # In _main(): hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
  ```

## Use Action Idiom

- When using actions in a script use the code and idiom from
  `./helpers/hselect_action.py`

## Use Limit Range Idiom

- For limit range arguments:
  ```python
  hparser.add_limit_range_arg(parser)
  # In _main(): limit_range = hparser.parse_limit_range_args(args)
  ```

## Command Line Argument Naming

- Use only underscores as separators in command line arguments, not dashes
  - **Good**: `--cache_reset`, `--max_iterations`, `--output_dir`
  - **Bad**: `--cache-reset`, `--max-iterations`, `--output-dir`
- This applies to both long-form argument names and the attribute names assigned
  by argparse (which converts `_` to `_` in the namespace)

## Use Mutually Exclusive Groups for Conflicting Options

- When options are mutually exclusive, use `add_mutually_exclusive_group()` to
  enforce the constraint in argparse instead of validating manually in code
- This provides automatic conflict detection and generates proper help text

- **Bad**: Manual validation for mutually exclusive options
  ```python
  parser.add_argument("--input_file", type=str, default="")
  parser.add_argument("--input_text", type=str, default="")
  
  def _main(args: argparse.Namespace) -> None:
      if args.input_file and args.input_text:
          raise ValueError("Cannot specify both --input_file and --input_text")
      if not args.input_file and not args.input_text:
          raise ValueError("Must specify either --input_file or --input_text")
  ```
- **Good**: Use `add_mutually_exclusive_group()` in parser
  ```python
  input_group = parser.add_mutually_exclusive_group(required=True)
  input_group.add_argument("--input_file", type=str, default="")
  input_group.add_argument("--input_text", type=str, default="")
  # Argument validation is handled automatically by argparse
  ```

## Use Single Types With Meaningful Defaults for Parser Inputs

- When defining parser arguments, use a single consistent type (e.g., `str`, `int`)
  with a meaningful default value to represent "not set" instead of `None`
- This simplifies type hints and avoids `Optional` types throughout your code

- **Bad**: Using `None` as default creates `Optional` type requirements
  ```python
  parser.add_argument("--name", type=str, default=None)
  parser.add_argument("--count", type=int, default=None)
  
  def _main(args: argparse.Namespace) -> None:
      name: Optional[str] = args.name
      count: Optional[int] = args.count
  ```
- **Good**: Use meaningful defaults to keep single types
  ```python
  parser.add_argument("--name", type=str, default="")
  parser.add_argument("--count", type=int, default=0)
  
  def _main(args: argparse.Namespace) -> None:
      name: str = args.name
      count: int = args.count
  ```

- Choose meaningful defaults based on the argument type:
  - For strings: use `""` (empty string)
  - For integers: use `0` (or another sentinel like `-1`)
  - For paths: use `""` (empty string) or handle validation in the parser

## Create Dirs

- If directory doesn't exist create it using `hio.create_dir`
  - If a `--from_scratch` option is requested, create the directory from scratch

## Temporary Files

- When using temporary files use files named
  `tmp.${name_of_script}.{function}.txt` to increase debuggability by inspecting
  files
  - No need to clean up files

# Code Quality and Performance

## Use Progress Bar

- When there are expensive for loop, use a progress bar using `tqdm` to track
  the progress

## Explain Complex Regex

- When using complex regex, use comments and `re.VERBOSE`
  - **Bad**
    ```python
    quote_pattern = r"(`[^`]*`|(?<!\w)'[^']*'(?!\w)|\"[^\"]*\")"
    ```
  - **Good**
    ```python
    quote_pattern = r"""
    (
        `[^`]*`          # backtick quotes: `anything except backtick`

      |                 # OR

        (?<!\w)         # left side is NOT a word character
        '[^']*'         # single quoted text
        (?!\w)          # right side is NOT a word character

      |                 # OR

        "[^"]*"         # double quoted text
    )
    """

    pattern = re.compile(quote_pattern, re.VERBOSE)
    ```

# System Integration

## Use `hsystem`

- Use code in `helpers/hsystem.py` to call commands
- Do not try to catching error, but let the exception propagate
  - **Bad**
    ```python
    try:
        hsystem.system("which llm", suppress_output=True)
        _LOG.debug("llm command found")
    except Exception as e:
        hdbg.dfatal(f"llm command not found: {e}")
    ```
  - **Good**
    ```python
    hsystem.system("which llm", suppress_output=True)
    ```

## How to Build Command Lines

- When building command lines use one command line option per line
  and f-strings

  - **Bad**
    ```python
    cmd_parts = [
        "notes_to_pdf.py",
        "--input",
        input_file,
        "--output",
        output_file,
        "--type",
        "slides",
        "--toc_type",
        "navigation",
        "--skip_action",
        "cleanup_after",
        "--skip_action",
        "open",
    ]
    ```
  - **Good**
    ```python
    cmd_parts = [
        "notes_to_pdf.py",
        f"--input={input_file}",
        f"--output={output_file}",
        "--type=slides",
        "--toc_type=navigation",
        "--skip_action=cleanup_after",
        "--skip_action=open",
    ]
    ```
