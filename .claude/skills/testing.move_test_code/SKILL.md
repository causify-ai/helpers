---
description: Moves test classes from a monolithic test file into per-module test files. Use when a test file has grown too large, tests multiple unrelated modules, or when the user wants to split or reorganize a large test file.
---

## Step 1: Build the Move Plan
- Read `test_file.py` and identify all test classes
- For each test class, find the source file containing the functions/classes it
  tests
- Produce a mapping table:

  | Test class | Target test file |
  | :--------- | :--------------- |
  | `TestFoo1` | `foo/test/test_foo.py` |
  | `TestBar1` | `bar/test/test_bar.py` |

- Present the mapping to the user before proceeding

## Step 2: Execute the Move
- For each test class in the mapping, append it to the target file using
  `split_in_files.py` (at
  `dev_scripts_helpers/coding_tools/split_in_files.py`):
  ```bash
  python dev_scripts_helpers/coding_tools/split_in_files.py \
      --input <test_file> \
      --class <TestClassName1> \
      --output <target_test_file> \
      --append
  ```
- Do not preserve the class in `test_file.py` — this is a move, not a copy
- Remove the moved class from `test_file.py` after appending
- If `<target_test_file>` does not exist yet, create it first with the standard
  imports and `_LOG` boilerplate (see `testing.rules.md#unit-test-code-structure`)

## Step 3: Verify
- Run the original file (now reduced) to confirm no remaining tests broke:
  ```bash
  pytest <test_file> -v
  ```
- Run each destination file to confirm moved tests pass:
  ```bash
  pytest <target_test_file> -v
  ```
- Fix any failures before reporting done
