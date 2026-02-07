You are an expert Python developer.

I will pass you a Python file paired with Jupyter notebook with jupytext using a
py:percent format (e.g., msml610/tutorials/Lesson94-Information_Theory.py)

For all the code follow the rules from `docs/ai_prompts/coding.format_code.md`

# Step 1.
- Given the input, you will create a `utils_*.py` Python file called with
  a name derived from the file:
  ```
  Lesson94-Information_Theory.ipynb
  ->
  utils_Lesson94_Information_Theory.py
  ```

# Step 2.
- Then you will move all the functions from the notebook to the `utils_*.py` file
  without changing the code

# Step 3.
- You will change the Python code to call the functions in the utils file
  ```python
  import ... as utils

  utils.function(...)
  ```

## Add code to a library / utilities
- Find or create the library / utility file that correspond to the notebook
  - E.g., 
    ```
    Lesson94-Information_Theory.ipynb
    ->
    utils_Lesson94-Information_Theory.py
    ```
- Implement the code and then:
  - Save the functions and the bulk of the code in the `utils_*.py` files
  - Leave only the caller code in Jupyter notebook
- Reuse code already existing in the `utils_*.py` file and in the `helpers`
  directory

## Add code to the right place in the library
- The library / utility file should have a structure that follows the flow of the
  notebook
- Add the functions in the part of the utility file that corresponds to the
  Jupyter notebook
- There should be some separators to organize the code in the library to follow
  the structure of the notebook
  - E.g.,
    ```
    # ############################...
    # Code for ...
    # ############################...
    ```

## Functions with name ending with _inline
- Functions with name ending with _inline needs to be left in the Jupyter
  notebook and not moved to the `utils_*.py` file


# Step 4
- After you have modified the Python file you will run a command to pair the
  notebook and the Python file
  ```
  > uvx jupytext --sync <python file>
  ```
