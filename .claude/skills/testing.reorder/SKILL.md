---
description: Reorganize test classes and functions to match the order of the tested code
model: haiku
---

# Goal
- Reorganize the Python test classes and functions in a testing file
  `*/test/test_*.py` to match the order of the functions they test in the
  corresponding source file

# Conventions
- For all the code you must follow the instructions in
  - `.claude/skills/coding.rules.md`
  - `.claude/skills/testing.rules.md`

# Workflow

## Find Test Code
- Find the functions in `<FILENAME>.py` that are tested in the file
  `test/test_<FILENAME>.py`

## Prepare a Plan
- Prepare a plan that shows a mapping between
  - Test classes
  - The functions tested by each class
  - The file containing the tested functions

### Order the Testing Classes in the Same Order as the Python File
- Reorganize the code in `test/test_<FILENAME>.py` to match the order of the
  functions declared in `<FILENAME>.py`

- E.g., if in a Python `.../file.py`
  ```python
  def test1(...)

  def test2(...)
  ```
  the corresponding `.../test/test_file.py`
  ```python
  class Test_test1(...)

  class Test_test2(...)
  ```

### Preserve Behavior Exactly
- Do not modify functionality, logic, signatures, control flow, side effects, or
  semantics
- The resulting code must behave identically to the original

### Move Code Only
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

## Implement the Plan
- Implement the plan moving the code without changing it
- Run the related unit tests to make sure everything works

# Verification
- [ ] Confirm test classes appear in the same order as the functions they test
- [ ] Run the related unit tests and confirm they pass
- [ ] Confirm no logic, signatures, or behavior changed
