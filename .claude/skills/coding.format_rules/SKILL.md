---
description: Format Python code according to project coding conventions and style rules
---

## Only Linux and MacOS

- Assume the script needs to run only on Linux and MacOS

## Follow the Coding Style from the Template

- Use the coding style in @docs/ai_templates/code_template.py

## Use Assertions From `helpers/hdbg.py`

- Use one of the `hdbg.dassert_*` functions in `helpers/hdbg.py` to check for
  invariants

- Pass parameters using lazing formatting
  - Good
    ```python
    hdbg.dassert...(
          ...
          "Target directory does not exist:", target_dir
      )
    ```
  - Bad
    ```python
    hdbg.dassert...(
          ...
          f"Target directory does not exist: {target_dir}",
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

## Use Action Idiom
- When using `--action`

  ```python
  actions = hparser.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
  hparser.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
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
