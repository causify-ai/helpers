- It should work only on Linux / MacOS systems
- Use hdbg.dassert functions in helpers/hdbg.py to check for invariants
- Use code in helpers/hsystem.py to call commands

- When creating scripts use the template
  dev_scripts_helpers/coding_tools/script_template.py
  - Create a parser function 
    def _parse() -> argparse.ArgumentParser:
    def _main(parser: argparse.ArgumentParser) -> None:

- Use the coding style in code_template.py

- Use REST comments in docstrings

- Do not use empty lines within functions but use comments to separate chunks of
  code

- Use _LOG.debug to add debugging info that can help a programmer to track the
  issues
- Use _LOG.info instead of print

- Do not use too many try except but let statements raise their own errors

- Use periods at the end of comments

- Use * for default parameters in functions

- If you create a new function and this is used only in this file make it private
  by starting the name with `_`
