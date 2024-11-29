

<!-- toc -->

- [Design issues](#design-issues)
  * [Passing `config_builder` to `run_notebook.py` for Config Object](#passing-config_builder-to-run_notebookpy-for-config-object)
    + [Current Approach](#current-approach)
    + [What do we want to achieve](#what-do-we-want-to-achieve)
    + [How do we want to achieve that](#how-do-we-want-to-achieve-that)
    + [Pros](#pros)
    + [Cons](#cons)

<!-- tocstop -->

Refer to
[`docs/coding/all.run_jupyter_notebook.how_to_guide.md`](/docs/coding/all.run_jupyter_notebook.how_to_guide.md)
to understand the current approaches of running the Jupyter notebooks.

# Design issues

## Passing `config_builder` to `run_notebook.py` for Config Object

### Current Approach

- When running the
  [notebook invoke](/reconciliation/lib_tasks_run_model_experiment_notebooks.py)
  using airflow, we use
  [`dev_scripts/notebooks/run_notebook.py`](/dev_scripts/notebooks/run_notebook.py)
- This script takes certain arguments as an input and one of them is
  `config_builder`. It's a string input which defines a path to the config
  builder function which is required by the notebook itself
- While running the notebook using the script, it will set the value passed to
  the `config_builder` arg to the env variable `__CONFIG_BUILDER__` and the
  notebook will construct a config from the value of this env variable
- Since it is a string input, when running via airflow it creates a lot of
  quotation complexities which increases reading complexity

### What do we want to achieve

- We would want to read the notebook config from file path rather than
  constructing it from the function

### How do we want to achieve that

- The [`run_notebook.py`](/dev_scripts/notebooks/run_notebook.py) script creates
  an `experiment_result_dir`
- This dir contains various files and one of them is `config.pkl` file
- This file contains the config required by the notebook being run at that time
  using the above mentioned script
- Instead of setting the `__CONFIG_BUILDER__` env variable, a more simpler
  approach would be to set `__CONFIG_FILE_PATH__` env variable
- This variable will store the path to `config.pkl` file found inside the
  `experiment_result_dir`
- The notebook will then construct a config from the file path passed to the
  `__CONFIG_FILE_PATH__` env variable

### Pros

- Simpler approach
- No string quotation complexities. Eliminates potential issues related to
  string parsing and formatting
- More readable code to the reader
- By adopting a standardized approach to configuration management, the issue
  aligns with best practices, enhancing consistency across different components
  and workflows as this is something that we are doing while re-running the
  already published notebook
- Easy to implement

### Cons

- With the current approach the reader would know what function is being called
  to build the notebook config but this will remain hidden from the user
- The flow will only work if the directory and file structure is maintained
  consistently. Changing that will require change in the approach
- The change is happening in one of the core flow so involvement from different
  teams is required to make sure it is not introducing any new error and running
  as-is
- Updating documentation to reflect the changes and educating users on the new
  approach adds overhead in terms of time and resources
