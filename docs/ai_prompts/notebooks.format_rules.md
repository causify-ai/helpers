You are an expert Python developer.

I will pass you a Python file paired with Jupyter notebook with jupytext using a
py:percent format (e.g., msml610/tutorials/Lesson94-Information_Theory.py)

# Modify only the Python file paired to a Jupyter notebook
- When changing a notebook, you must only modify the Python file paired with the
  given Jupyter notebook
- If there is no Python file, but only the ipynb Jupyter notebook, you will run a
  command to pair the notebook and the Python file:
  ```bash
  > uvx jupytext --set-formats ipynb,py:percent  <ipynb file>
  ```

# Use Python style
- For all the Python code you must follow the rules from
  `docs/ai_prompts/coding.format_code.md`

# Each notebook as the following format
- The first cell of a notebook is:
  ```python
  %load_ext autoreload
  %autoreload 2

  import logging

  import numpy as np
  import matplotlib.pyplot as plt
  import seaborn as sns
  ...

  # Set plotting style.
  sns.set_style("whitegrid")
  plt.rcParams["figure.figsize"] = (12, 6)
  ```

- The second cell is like:
  ```python
  import msml610_utils as ut
  import utils_Lesson94_Information_Theory as utils

  ut.config_notebook()

  # Initialize logger.
  logging.basicConfig(level=logging.INFO)
  _LOG = logging.getLogger(__name__)
  ```

# Do not use emoji or non-ascii characters
- Do not use emoji or non-ascii characters, but only ascii ones
- You can use Latex notation for formulas, like $...$ even if they are not
  rendered

# Notebook pairing to Python file and utility file
- Each notebook is paired with Jupytext to a Python file and has a corresponding
  `utils_*.py` file containing the code corresponding to that notebook
  - E.g., for the Jupyter notebook
    `msml610/tutorials/Lesson94-Information_Theory.ipynb`
    is paired with Jupytext to the file
    `msml610/tutorials/Lesson94-Information_Theory.py`
    and the corresponding `utils_*.py` file is
    `./msml610/tutorials/utils_Lesson94_Information_Theory.py`
- Given the notebook, find and print the corresponding paired file and the
  `utils_*.py` file

# Final step
- After you have modified the Python file corresponding to the Jupyter notebook,
  you will run a command to pair the notebook and the Python file

  ```
  > uvx jupytext --sync <python file>
  ```
