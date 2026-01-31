You are an expert Python developer.

I will pass you a Python file paired with Jupyter notebook with jupytext using a
py:percent format (e.g., msml610/tutorials/Lesson94-Information_Theory.py)

## Modify only the Python file
- You will modify the Python file
- If there is no Python file, but only the ipynb you will run a command to pair
  the notebook and the Python file
  ```bash
  > uvx jupytext --set-formats ipynb,py:percent  <ipynb file>
  ```

## Use Python style
- For all the code follow the rules from `docs/ai_prompts/coding.format_code.md`

## Each notebook as the following format
- The first cell is:
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

- The second cell
  ```python
  import msml610_utils as ut
  import utils_Lesson94_Information_Theory as utils

  ut.config_notebook()

  # Initialize logger.
  logging.basicConfig(level=logging.INFO)
  _LOG = logging.getLogger(__name__)
  ```

## Do not use emoji or non-ascii characters
- Do not use emoji or non-ascii characters, but only ascii ones
- You can use Latex notation for formulas, like $...$ even if they are not
  rendered

## Final step
- After you have modified the Python file you will run a command to pair the
  notebook and the Python file

  ```
  > uvx jupytext --sync <python file>
  ```
