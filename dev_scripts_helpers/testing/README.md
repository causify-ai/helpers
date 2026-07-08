# Structure of the Dir

This directory has no subdirectories.

# Description of Executables

## `pytest_failed.py`

- **What It Does**:
  - Parses the failed tests out of a pytest log (default
    `tmp.pytest_log.txt`), prints a summary, and copies the test names to
    the clipboard
  - Writes repro scripts to rerun the failed tests, failed test classes, and
    failed test files
  - Writes reports listing passed tests, skipped tests, updated golden
    outcomes, tests ordered by duration, duration statistics, and failure
    stacktraces

- Parse failed tests from the default log file `tmp.pytest_log.txt`
  ```bash
  > pytest_failed.py
  ```

- Parse failed tests from a specific log file
  ```bash
  > pytest_failed.py --input tmp.log
  ```

- Run with verbose logging
  ```bash
  > pytest_failed.py --input tmp.log -v DEBUG
  ```

## `pytest_marks.py`

- **What It Does**:
  - Collects every pytest test under a file or directory (without running
    any test) together with its pytest marks (`slow`, `superslow`, etc.) and
    whether it is statically marked as skipped
  - Prints a human-readable summary and writes the full report to
    `tmp.pytest_marks.csv`

- Scan the whole repo
  ```bash
  > pytest_marks.py
  ```

- Scan only a specific directory
  ```bash
  > pytest_marks.py --dir helpers
  ```

## `pytest_count_files.sh`

- **What It Does**:
  - Runs `pytest --collect-only` and counts the number of test classes and
    test functions, as well as skipped and fast test functions
  - Must be run from inside the `amp` repo checkout (checks the parent
    directory name)

- Count test classes and functions in the current repo
  ```bash
  > ./pytest_count_files.sh
  ```

## `rename_test_names.sh`

- **What It Does**:
  - Renames files matching a glob pattern by replacing one substring with
    another, printing each `old -> new` mapping

- Rename all `TestReadDataFromDisk*` files to `TestDiskDataSource*`
  ```bash
  > ./rename_test_names.sh TestReadDataFromDisk TestDiskDataSource core/dataflow/test/TestReadDataFromDisk*
  ```

## `pytest_log`

- **What It Does**:
  - Runs `pytest` with the given arguments, tees the output to
    `tmp.pytest_log.txt`, and preserves pytest's exit code
  - Intended to be used together with `pytest_failed.py`, which parses
    `tmp.pytest_log.txt` by default

- Run a test file and save the log for later parsing
  ```bash
  > ./pytest_log helpers/test/test_hpytest.py -v
  ```
