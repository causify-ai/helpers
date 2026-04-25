---
description: Review Python files for bugs, suggest fixes, and provide test cases
---

- You are a senior Python engineer

# Goal
- I will pass you reference to Python files `<input_file>`

- You will read the input file `<input_file>` and look and find the file with the
  unit tests for each file `<test_files>`, in the format
  `tests/test_<input_file>`
  - E.g., for a file `foo.py` the corresponding file with the unit tests is
    called `tests/test_foo.py`

- You will find mistakes/bugs in the code and fix them with the smallest possible
  changes
- You must keep the same input/output behavior and overall structure unless
  necessary

# Output
- What I want back:
  - A short list of the issues you found with line references
  - A corrected version of the code
  - A short one line description of why each fix works
  - A few test cases (including edge cases) and expected outputs
    ```
    - Observed behavior / error message: ...
    - Expected behavior: ...
    ```
