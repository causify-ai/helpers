---
description: Use this idiom for controlling logging in Jupyter notebooks
model: haiku
---

# Important: Follow Conventions
- Always follow the conventions and guidelines in
  `.claude/skills/notebook.rules.md`

- Implement the instructions in 
  `.claude/skills/notebook.rules.md` under
  `## Use Standard Template Structure`

- Use the structure from `.claude/templates/notebook.template.py` for consistent
  notebook initialization

- Use `display`

- In the local utility `*_utils.py` there should be a function like
  ```
  import helpers.hnotebook as hnotebo

  def init_logger(notebook_log: logging.Logger) -> None:
      hnotebo.config_notebook()
      hdbg.init_logger(verbosity=logging.INFO, use_exec_path=False)
      # Init notebook logging.
      hnotebo.set_logger_to_print(notebook_log)
      # Init utils logging.
      global _LOG
      _LOG = hnotebo.set_logger_to_print(_LOG)
      # Init module logging.
      causalml_logger: logging.Logger = logging.getLogger("causalml")
      hnotebo.set_logger_to_print(causalml_logger)
  ```

