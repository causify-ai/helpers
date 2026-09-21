---
description: Use idiom for controlling logging in Jupyter notebooks
model: haiku
---

# Goal
- Implement the instructions in
  `.claude/skills/notebook.rules.md` under
  `## Use Standard Template Structure`

- Use the structure from `.claude/templates/notebook.template.py` for consistent
  notebook initialization

- Use `display`

- In the local utility `*_utils.py` there should be a function like
  ```
  import helpers.hnotebook as hnotebo

  def init_loggers(notebook_log: logging.Logger) -> None:
      """
      Wire the notebook logger into the utils logger.

      :param notebook_log: logger owned by the notebook
      """
      hnotebo.init_loggers(notebook_log, utils_log=_LOG)
  ```
  - `hnotebo.init_loggers()` already calls `config_notebook()`, initializes
    `hdbg` at INFO level, and redirects the notebook and utils loggers to
    print
  - If the notebook needs a third-party logger (e.g., `causalml`), redirect it
    inside `init_loggers()` with `hnotebo.set_logger_to_print()`:
    ```
    hnotebo.set_logger_to_print(logging.getLogger("causalml"))
    ```

- In the notebook, the last setup cell calls `utils.init_loggers(_LOG)`
  instead of `logging.basicConfig()` or `hdbg.init_logger()`

# Workflow

## Sync Notebook
- At the end, sync the paired `.py` file with Jupytext following the conventions
  in `# Code Architecture and Responsibility` -> `## Utilities vs. Notebook
  Responsibilities` in `.claude/skills/notebook.rules.md`

# Conventions
- Always follow the conventions and guidelines in
  `.claude/skills/notebook.rules.md`

# Verification
- [ ] Confirm the notebook init cell matches `.claude/templates/notebook.template.py`
- [ ] Confirm `utils.init_loggers()` is called and log messages print in the notebook
- [ ] Confirm the `.ipynb` and paired `.py` file are in sync via Jupytext
