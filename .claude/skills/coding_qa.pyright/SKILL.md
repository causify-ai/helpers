---
description: Run pyright on files and fix the lints
---

# Step 1
- Run pyright on the passed Python files saving the output in tmp.pyright_before.txt

# Step 2
- Read `tmp.pyright_before.txt` and fix all the lints using the mininum amount of
  changes and making sure that the behavior is not unintentionally changed

# Step 3
- Read the related unit tests
  - Start from the ones that correspond to the file
  - E.g., for `helpers/haws.py` run `helpers/test/test_haws.py`

# Step 3
- Run pyright again on the passed files saving the output in `tmp.pyright_after.txt`
