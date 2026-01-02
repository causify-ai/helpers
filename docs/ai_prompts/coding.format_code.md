- Assume the script needs to run only on Linux

## Use Assertions From `helpers/hdbg.py`

- Use one of the `hdbg.dassert` functions in `helpers/hdbg.py` to check for
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

## Coding Style

- Use the coding style in `docs/ai_coding/code_template.py`
- Use REST comments in docstrings
- Do not use empty lines within functions but use comments to separate chunks of
  code
- Use periods at the end of all comments

- Use `_LOG.info` instead of print
- Use `_LOG.debug` to add debugging info that can help a programmer to track the
  issues
  - Always use lazy % formatting in logging functions

- Do not use try except to recover errors but let statements raise their own
  errors
- Use `hdbg.dassert_*` functions to check that invariants are verified

- Use `*` for default parameters in functions

- If you create a new function which it is used only in this file make it
  private by starting the name with `_`

## Use Script Template

- When creating scripts use the template
  `dev_scripts_helpers/coding_tools/script_template.py`
  - Create a parser function
    ```
    def _parse() -> argparse.ArgumentParser:

    def _main(parser: argparse.ArgumentParser) -> None:
    ```

- When using `--action`

  ```python
  actions = hparser.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
  hparser.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
  ```

- If directory doesn't exist create it using `hio.create_dir`
  - If a `--from_scratch` option is requested, create the directory from scratch

- When using temporary files use files named
  `tmp.${name_of_script}.{function}.txt` to increase debuggability by inspecting
  files
  - No need to clean up files

- When there are expensive for loop, use a progress bar using `tqdm` to track
  the progress
