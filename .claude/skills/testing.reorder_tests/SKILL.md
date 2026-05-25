---
description: Reorganize the test classes to match the order of the code they test
---

- I will pass you a file with unit tests `<test/test_<filename>.py>`

# Step 1
- Find the functions in `<filename.py>` that are tested in the file
  `<test/test_<filename>.py>`
- Prepare a plan that shows a mapping between
  - Test classes 
  - The functions tested by each class
  - The file containing the tested functions

# Step 2
- Reorganize the code in `<test/test_<filename>.py>` to match the order of the
  functions in `<filename.py>`

# Step 3
- Implement the plan moving the code without changing it

# Important
- For all the code you must follow the instructions in
  - `.claude/skills/coding.rules.md`
  - `.claude/skills/testing.rules.md`
