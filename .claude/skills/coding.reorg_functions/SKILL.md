---
description: Reorganize the functions in a file
---

# Reorganize the functions in a file

- Reorganize the functions in the passed files so that:
  - Functions are grouped together in "layers" separated by frames like
    ```
    # #############################################################################
    # <Description>.
    # #############################################################################
    ```
  - Layers are organized from simple to more complex
  - Functions inside layers are organized from simple / more basic to more complex
  - Functions that are used only in this file (i.e., private functions) are marked
    as private
    - E.g., `_foo_bar(...)`

# Important
- Code must only be moved and not changed
- The behavior of function must not be changed
