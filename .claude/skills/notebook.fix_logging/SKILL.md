---
description: Use this idiom for controlling logging in Jupyter notebooks
---

- For a Jupyter notebook always use the following idiom for logging
  ```python
  import logging
  # Local utility.
  import utils

  _LOG = logging.getLogger(__name__)
  utils.init_logger(_LOG)
  ```

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
