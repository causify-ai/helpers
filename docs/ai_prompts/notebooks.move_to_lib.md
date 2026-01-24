You are an expert Python developer.

I will pass you a Python file paired with Jupyter notebook with jupytext using a
py:percent format (e.g., msml610/tutorials/Lesson94-Information_Theory.py)

## Step 1.
- Given the input, you will create a Python file called with the same name of the
  file:

  ```
  Lesson94-Information_Theory.ipynb
  ->
  utils_Lesson94-Information_Theory.ipynb
  ```

## Step 2.
- Then you will move all the functions from the notebook to the utils file
  without changing the code

## Step 3.
- You will change the Python code to call the functions in the utils file
  ```python
  import ... as utils

  utils.function(...)
  ```

- For all the code follow the rules from `docs/ai_prompts/coding.format_code.md`

## Step 4
- After you have modified the Python file you will run a command to pair the
  notebook and the Python file
  ```
  > uvx jupytext --sync <python file>
  ```
