---
description: Lint a Jupyter notebook to improve its appearance without changing behavior
---

- Given a Jupyter notebook passed on the command line, you must improve its
  appearance without changing its behavior

- Use the rules from @.claude/skills/notebook.format_rules/SKILL.md

- For interactive cells use the rules from
  @.claude/skills/notebook.interactive_cell.format_rules/SKILL.md

# Use Jupytext

- When changing a notebook, you must only modify the Python file paired with the
  given Jupyter notebook
- If there is no Python file, but only the ipynb Jupyter notebook, you will run
  a command to pair the notebook and the Python file:

  ```bash
  > uvx jupytext --set-formats ipynb,py:percent  <ipynb file>
  ```

- After you have modified the Python file corresponding to the Jupyter notebook,
  you will run a command to pair the notebook and the Python file
  ```
  > uvx jupytext --sync <python file>
  ```
