---
description: Run pyright on Python files and fix the reported lints
model: haiku
---

# Goal
Given a list of files `<FILES>`, run `pyright` on them and fix the reported
lints without changing behavior.

# Workflow

## Run `pyright`
- Run `pyright` on the `<FILES>` generating a file `tmp.pyright_before.txt`
- Summarize the types of issues and how many of them are present

## Fix Lints From `pyright`
- Read `tmp.pyright_before.txt`
- Fix the lints without changing the behavior of the code
- If there are tests in `test/test_<FILE>.py`, run the tests to make sure they
  are still passing
  - E.g., for `helpers/haws.py` run `helpers/test/test_haws.py`

## Run `pyright` After the Fixes
- Run `pyright` on the `<FILES>` generating a file `tmp.pyright_after.txt`
- Summarize the types of issues and how many of them are present

# Verification
- [ ] Confirm `tmp.pyright_after.txt` shows fewer or no issues compared to `tmp.pyright_before.txt`
- [ ] Confirm the corresponding unit tests still pass
