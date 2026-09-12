---
description: Split test classes into separate files based on the functions they test
model: haiku
---

# Goal
- The user passes a file with unit tests `<TEST_FILE>`

# Workflow

## Find Tested Functions
- Find the functions that are tested in the file `<TEST_FILE>`
- Prepare a plan that shows a mapping between
  - Test classes
  - The functions tested by each class
  - The file containing the tested functions

## Propose Split Plan
- Propose a plan to split the test classes in multiple files to match the code
  they test
  - E.g., `Test_func1`, testing the function `func1` in `funcs.py` should go
    in `test_funcs.py`

## Get User Confirmation
- Ask the user to confirm the plan

## Implement the Plan
- Implement the plan moving the code without changing it

# Important
- For all the code you must follow the instructions in
  - `.claude/skills/coding.rules.md`
  - `.claude/skills/testing.rules.md`

# Verification
- [ ] Run the moved tests and confirm they still pass
- [ ] Confirm no test logic changed during the move
