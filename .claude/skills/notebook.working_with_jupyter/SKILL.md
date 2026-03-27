---
description: Actions when you are asked to work on a Jupyter Notebook ipynb file
---

- Every time you are requested to work on a Jupyter Notebook ipynb file
  you always have to follow the steps

# Step 1: Make sure that the paired files *.py and *.ipynb are in sync

- Always make sure that the paired ipynb and py files are in sync
  ```bash
  > uvx jupytext --sync <Python file>
  ```

# Step 2: Work on the Python file *.py

- When changing a notebook, you must only modify the Python file *.py paired with
  the given Jupyter notebook
- If there is no Python file, but only the ipynb Jupyter notebook, you will run
  a command to pair the notebook and the Python file:
  ```bash
  > uvx jupytext --set-formats ipynb,py:percent  <ipynb file>
  ```

# Step 3: Sync the modified Python *.py file with Jupyter *.ipynb

- After you have modified the Python file *.py corresponding to the Jupyter
  notebook, you will run a command to pair the notebook and the Python file
  ```
  > uvx jupytext --sync <Python file>
  ```
