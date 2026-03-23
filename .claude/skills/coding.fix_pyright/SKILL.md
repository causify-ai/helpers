---
description: Fix the lints from pyright in Python files
---

Given a list of files $FILE

# Step 1: Run pyright

- Run `pyright` on the $FILES generating a file `tmp.pyright_before.txt`
- Summarize the types of issues and how many of them are present

# Step 2: Fix lints from pyright

- Read `tmp.pyright_before.txt`
- Fix the lints without changing the behavior of the code
- If there are tests in `test/test_$FILE.py`, run the tests to make sure they are
  still passing

# Step 3: Run pyright after the fixes

- Run `pyright` on the $FILES generating a file `tmp.pyright_after.txt`
- Summarize the types of issues and how many of them are present
