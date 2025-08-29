- Assume the script needs to run only on Linux

- Use hdbg.dassert functions in helpers/hdbg.py to check for invariants
  - Pass parameters using lazing formatting
    - Good
    ```
    hdbg.dassert(
          os.path.isdir(target_dir),
          "Target directory does not exist:", target_dir
      )
    ```
    - Bad
    ```
    hdbg.dassert(
          os.path.isdir(target_dir),
          f"Target directory does not exist: {target_dir}",
      )
    ```
- Use code in helpers/hsystem.py to call commands

- When creating scripts use the template
  dev_scripts_helpers/coding_tools/script_template.py
  - Create a parser function def _parse() -> argparse.ArgumentParser: def
    _main(parser: argparse.ArgumentParser) -> None:

- Use the coding style in code_template.py

- Use REST comments in docstrings

- Do not use empty lines within functions but use comments to separate chunks of
  code

- Use _LOG.debug to add debugging info that can help a programmer to track the
  issues
- Use _LOG.info instead of print
- Always use lazy % formatting in logging functions

- Do not use too many try except but let statements raise their own errors

- Use periods at the end of comments

- Use * for default parameters in functions

- If you create a new function and this is used only in this file make it
  private by starting the name with `_`

- Do not try to catching error, but let the exception propagate
  - Bad
  ```
  try:
      hsystem.system("which llm", suppress_output=True)
      _LOG.debug("llm command found")
  except Exception as e:
      hdbg.dfatal(f"llm command not found: {e}")
  ```
  - Good hsystem.system("which llm", suppress_output=True)
