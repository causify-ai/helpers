---
description: Format Python code according to project coding conventions and style rules
---

## Only Linux and MacOS

- Assume the script needs to run only on Linux and MacOS

## Follow the Coding Style from the Template

- Use the coding style in @docs/ai_templates/code_template.py

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

## Use _LOG

- Use `_LOG.info` instead of print, unless there is a comment explicitly saying
  that it should be used print
- Use `_LOG.debug` to add debugging info that can help a programmer to track the
  issues
  - Always use lazy % formatting in logging functions

## Do not use try-except
- Do not use try except to recover errors but let statements raise their own
  errors

## Use * for Default Parameters
- Use `*` to mark which parameters in functions should be default parameters

## Mark Private Functions
- If you create a new function which it is used only in the file make it private
  by starting the name with `_`

## Remove Empty Lines
- Remove empty lines inside functions so that the code is compact

## Add Comments
- Use comments to separate chunks of code
- Use periods at the end of all comments

## Use Script Template

- When creating scripts use the script template
  `dev_scripts_helpers/coding_tools/script_template.py`

- Create a parser function
  ```python
  def _parse() -> argparse.ArgumentParser:

  def _main(parser: argparse.ArgumentParser) -> None:
  ```

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

## Create Dirs
- If directory doesn't exist create it using `hio.create_dir`
  - If a `--from_scratch` option is requested, create the directory from scratch

## Temporary files
- When using temporary files use files named
  `tmp.${name_of_script}.{function}.txt` to increase debuggability by inspecting
  files
  - No need to clean up files

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
