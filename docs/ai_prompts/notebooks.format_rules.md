You are an expert Python developer.

I will pass you a Python file paired with Jupyter notebook with jupytext using a
py:percent format (e.g., msml610/tutorials/Lesson94-Information_Theory.py)

# Modify Only the Python File Paired to a Jupyter Notebook

- When changing a notebook, you must only modify the Python file paired with the
  given Jupyter notebook
- If there is no Python file, but only the ipynb Jupyter notebook, you will run
  a command to pair the notebook and the Python file:
  ```bash
  > uvx jupytext --set-formats ipynb,py:percent  <ipynb file>
  ```

# Use Python Style

- For all the Python code you must follow the rules from
  `docs/ai_prompts/coding.format_code.md`

# Format of a Jupyter Notebook

- Each notebook has the following format

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
  import Lesson94_Information_Theory_utils as utils

  ut.config_notebook()

  # Initialize logger.
  logging.basicConfig(level=logging.INFO)
  _LOG = logging.getLogger(__name__)
  ```

# Do Not Use Emoji or Non-Ascii Characters

- Do not use emoji or non-ascii characters, but only ascii ones
- You can use Latex notation for formulas, like $...$ even if they are not
  rendered

# Notebook Pairing to Python File and Utility File

- Each notebook is paired with Jupytext to a Python file and has a corresponding
  `*_utils.py` file containing the code corresponding to that notebook
  - E.g., for the Jupyter notebook
    `msml610/tutorials/Lesson94-Information_Theory.ipynb` is paired with
    Jupytext to the file `msml610/tutorials/Lesson94-Information_Theory.py` and
    the corresponding `*_utils.py` file is
    `./msml610/tutorials/Lesson94_Information_Theory_utils.py`
- Given the notebook, find and print the corresponding paired file and the
  `*_utils.py` file

# Final Step

- After you have modified the Python file corresponding to the Jupyter notebook,
  you will run a command to pair the notebook and the Python file
  ```
  > uvx jupytext --sync <python file>
  ```
