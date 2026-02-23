# Add Code to a Library / Utilities

- Find or create the library / utility file that correspond to the notebook
  - E.g., `Lesson94-Information_Theory.ipynb` ->
    Lesson94-Information_Theory_utils.py`
- Implement the code and then:
  - Save the functions and the bulk of the code in the `*_utils.py` files
  - Leave only the caller code in Jupyter notebook
- Reuse code already existing in the `*_utils.py` file and in the `helpers`
  directory

# Add Code to the Right Place in the Library

- The library / utility file should have a structure that follows the flow of
  the notebook
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
