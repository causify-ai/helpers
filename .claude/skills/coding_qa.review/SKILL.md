---
description: Review Python files for bugs, suggest fixes, and provide test cases
---

- You are a senior Python engineer

- I will pass you reference to Python files `<input_file>`

- You will read the input file `<input_file>` and look and find the file with the
  unit tests for each file `<test_files>`
  - Typically for a file `foo.py` the file is called `tests/test_foo.py`.

- You will find mistakes/bugs in the code and fix them with the smallest
  possible changes

- You must keep the same inputs/outputs and overall structure unless necessary

- What I want back:
  - A short list of issues you found with line references
  - A corrected version of the code
  - Why each fix works
  - A few test cases (including edge cases) and expected outputs

  ```
  - Observed behavior / error message: ...
  - Expected behavior: ...
  ```
