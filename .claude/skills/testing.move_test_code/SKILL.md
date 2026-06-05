---
description: Split test classes from a test file into the correct separate test files based on what function they test
model: haiku
---

- I will pass you a file with unit tests `<test/test_<filename>.py>`

# Step 1
- Find the functions that are tested in the file `<test_file.py>`
- Prepare a plan that shows a mapping between
  - Test classes 
  - The functions tested by each class
  - The file containing the tested functions

# Step 2
- Propose a plan to split the test classes in multiple files to match the code
  they test
  - E.g., `Test_func1`, testing the function `func1` in `funcs.py` should go
    in `test_funcs.py`

# Step 3
- Ask for the user to confirm the plan

# Step 4
- Implement the plan moving the code without changing it

# Important
- For all the code you must follow the instructions in
  - `.claude/skills/coding.rules.md`
  - `.claude/skills/testing.rules.md`
