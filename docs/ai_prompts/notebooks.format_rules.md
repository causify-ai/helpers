- You are an expert Python developer.

- I will pass you a Python file paired with Jupyter notebook with jupytext using
  a `py:percent` format
  - E.g., `msml610/tutorials/Lesson94-Information_Theory.py`

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
  import pandas as pd
  import seaborn as sns
  import matplotlib.pyplot as plt

  ut.config_notebook()

  # Initialize logger.
  logging.basicConfig(level=logging.INFO)
  _LOG = logging.getLogger(__name__)
  ```

- The second cell is like:

  ```python
  import msml610_utils as ut
  import Lesson94_Information_Theory_utils as utils
  ```

# Do Not Use Emoji or Non-Ascii Characters

- Do not use emoji or non-ascii characters, but only ascii ones
- You can use Latex notation for formulas, like $...$ even if they are not
  rendered

# Title for the Comment Box

- When using `add_fitted_text_box()` set the title
  ```
  ax.set_title("Comments", fontsize=14, fontweight="bold", pad=20)
  ```

# Interactive Widgets Conventions

- Interactive widgets must always have:
  - The name of the variable (e.g., n, mu, nu)
  - Value cell and "-" and "+" buttons
- The widget to select the seed must always be the first widget

- Use code in `msml610_utils.py` like `_create_slider_widget()`,
  `build_widget_control()` to create the widgets

# Logarithmic Widget Control

- When asked to build a logarithmic widget control, use the following idiom
  ```python
  # Create N widget with logarithmic slider and +/- buttons.
  # Uses exponents 2-10 for base 2: gives values 4, 8, 16, 32, 64, 128, 256, 512, 1024
  # Initial exponent 4 gives initial value of 16
  N_exp_slider, N_box = mtumsuti.build_log_widget_control(
      name="log(N)",
      description="N (total samples)",
      min_exp=2,
      max_exp=10,
      initial_exp=4,
      base=2,
  )
  ```

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
