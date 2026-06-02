---
description: Reorganize the Python testing functions in a file
model: haiku
---

# Goal
- Reorganize the Python functions in a testing file `*/test/test_*.py`
  using the following rules

## Order the Testing Classes in the same order as the Python file
- Order the testing classes in the same order as the functions that they are testing
  are declared in the Python file

- E.g., if in a Python `.../file.py`
  ```python
  def test1(...)

  def test2(...)
  ```
  the corresponding `.../test/test_file.py` 
  ```pyhthon
  class Test_test1(...)

  class Test_test2(...)
  ```

# Constraints

## Preserve Behavior Exactly

- Do not modify functionality, logic, signatures, control flow, side effects, or
  semantics
- The resulting code must behave identically to the original

## Move Code Only

- The refactor must be structural only

- Allowed changes:
  - Reordering functions
  - Adding section headers
  - Renaming internal/private functions consistently

- Disallowed changes:
  - Rewriting logic
  - Simplifying implementations
  - Changing APIs
  - Changing imports unnecessarily
  - Modifying formatting beyond what is required for reorganization
