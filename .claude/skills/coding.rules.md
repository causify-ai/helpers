- This file contains all the conventions for Python coding rules.

# Environment and Platform

## Only Linux and MacOS

- Assume the script needs to run only on Linux and MacOS

# Code Style and Structure

## Follow the Coding Style from the Template

- Use the coding style in `@docs/ai_templates/code_template.py`

## Use * for Default Parameters

- Use `*` to mark which parameters in functions should be default parameters

## Type Hints: Use `typing` Module Style

- Use type hints from the `typing` module instead of newer PEP 604 syntax
- Use `Tuple`, `Dict`, `Optional` instead of `tuple`, `dict`, `|` union syntax
  - **Good**: Use `typing` module
    ```python
    from typing import Dict, Tuple, Optional
    
    def process(data: Dict[str, str], item: Optional[str]) -> Tuple[str, int]:
        ...
    ```
  - **Bad**: Use newer PEP 604 syntax
    ```python
    def process(data: dict[str, str], item: str | None) -> tuple[str, int]:
        ...
    ```

## Mark Private Functions

- If you create a new function which it is used only in the file make it private
  by starting the name with `_`

## Remove Empty Lines

- Remove empty lines inside functions so that the code is compact

# Error Handling and Assertions

## Use Assertions From `helpers/hdbg.py`

- Use specialized `hdbg.dassert_*` functions instead of generic `hdbg.dassert()`
- Choose the most specific assertion function for your check

- Common specialized assertion functions:
  - `hdbg.dassert_in(value, container)` - Check membership
  - `hdbg.dassert_not_in(value, container)` - Check non-membership
  - `hdbg.dassert_eq(val1, val2)` - Check equality
  - `hdbg.dassert_ne(val1, val2)` - Check inequality
  - `hdbg.dassert_lt(val1, val2)` - Check less than
  - `hdbg.dassert_lte(val1, val2)` - Check less than or equal
  - `hdbg.dassert_isinstance(obj, type)` - Check type
  - `hdbg.dassert_file_exists(path)` - Check file existence
  - `hdbg.dassert_dir_exists(path)` - Check directory existence

- Example: Use `dassert_in()` instead of generic `dassert()`
  - Good: Check if value is in container
    ```python
    hdbg.dassert_in(
        ext,
        _FORMAT_MAP,
        "Unsupported file format; supported formats are: %s",
        ", ".join(_FORMAT_MAP.keys()),
    )
    ```
  - Bad: Generic assertion with membership check
    ```python
    hdbg.dassert(
        ext in _FORMAT_MAP,
        "Unsupported file format; supported formats are: %s",
        ", ".join(_FORMAT_MAP.keys()),
    )
    ```

- Pass parameters using lazy formatting (not f-strings)
  - Good
    ```python
    hdbg.dassert_ne(
        name,
        "",
        "Name cannot be empty:",
        name,
    )
    ```
  - Bad
    ```python
    hdbg.dassert_ne(
        name,
        "",
        f"Name cannot be empty: {name}",
    )
    ```

## Do not use try-except

- Do not use try except to recover errors but let statements raise their own
  errors

## Use `hsystem`

- Use code in `helpers/hsystem.py` to call commands
- Do not try to catching error, but let the exception propagate
  - Bad
    ```python
    try:
        hsystem.system("which llm", suppress_output=True)
        _LOG.debug("llm command found")
    except Exception as e:
        hdbg.dfatal(f"llm command not found: {e}")
    ```
  - Good
    ```python
    hsystem.system("which llm", suppress_output=True)
    ```

# Documentation and Comments

## Use REST Style for Comments

- Use REST comments in docstrings

- If the comment is only one line, still convert it to
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

- When there are multiple values for an input or an output variable
  format them as a list:
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

- An example of a good full docstring comment is
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

## Add Comments

- Override any minimalist comment defaults, but add explanatory comments liberally

- Use comments to separate logical chunks of code.
- Explain the logic and intent of code sections, especially for:
  - Complex algorithms or multi-step processes
  - Conditional branches and why they're needed
  - Non-obvious variable assignments or transformations
  - Implementation choices and workarounds
  - Algorithm steps in a sequence

- Comments should explain the WHY and the algorithm flow, not just the WHAT
  - **Bad**: (obvious from the code)
    ```
    # Iterate over lines
    for line in lines:
      ...
    ```
  - **Good**: (explains intent)
    ```
    # Process imports in two passes: first collect, then validate.
    ```

- Leave existing comments unless they are incorrect, even if they explain
  WHAT code does and they are redundant

- Prefer single-line comments over multi-line comment blocks when possible

- Use periods at the end of all comments

- In comments always use `: ` instead of ` - `
  - **Bad**
    ```
    # Check outputs.` - Result verification
    ```
  - **Good**
    ```
    # Check outputs.`: Result verification
    ```

# Logging

## Use _LOG

- Use `_LOG.info` instead of print, unless there is a comment explicitly saying
  that it should be used print
- Use `_LOG.debug` to add debugging info that can help a programmer to track the
  issues
  - Always use lazy % formatting in logging functions

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
- List all external (non-stdlib, non-helpers) packages required by the script in the `dependencies` array
- This allows scripts to be run directly without pre-installing packages: `./script.py`

## Use Standard Argument Helpers from `hparser`

- Use `hparser` helper functions to add standard arguments instead of defining them manually
- This ensures consistency across all scripts in the project

- For verbosity/logging level:
  ```python
  import helpers.hparser as hparser
  hparser.add_verbosity_arg(parser)
  # In _main(): hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
  ```

## Use Action Idiom

- When using `--action`

  ```python
  actions = hparser.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
  hparser.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
  ```

## Use Limit Range Idiom

- For limit range arguments:
  ```python
  hparser.add_limit_range_arg(parser)
  # In _main(): limit_range = hparser.parse_limit_range_args(args)
  ```

## Command Line Argument Naming

- Use only underscores as separators in command line arguments, not dashes
- Good: `--cache_reset`, `--max_iterations`, `--output_dir`
- Bad: `--cache-reset`, `--max-iterations`, `--output-dir`
- This applies to both long-form argument names and the attribute names assigned
  by argparse (which converts `_` to `_` in the namespace)

## Create Dirs

- If directory doesn't exist create it using `hio.create_dir`
  - If a `--from_scratch` option is requested, create the directory from scratch

## Temporary files

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

## Use verbatim to refer to functions and values

- When referring to variables and functions in code use verbatim
  - **Bad**
    ```python
    # Create a curated list from get_md_colors().
    ```
  - **Good**
    ```python
    # Create a curated list from `get_md_colors()`.
    ```
