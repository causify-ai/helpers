# Testing Tools

Pytest utilities for analyzing test results, collecting test metadata, and
automating test reporting. Provides quick access to test statistics and failure
analysis.

## Structure of the Dir

This directory has no subdirectories.

## Description of Files

- `pytest_count_files.sh`
  - Count test classes and functions in repository with skip statistics
- `pytest_failed.py`
  - Parse failed tests from pytest logs and generate repro scripts
- `pytest_log`
  - Run pytest with output teed to logfile for later analysis
- `pytest_marks.py`
  - Collect test marks and statistics across test suite
- `rename_test_names.sh`
  - Rename test files with pattern substitution

# Description of Executables

## `pytest_failed.py`

### What It Does

- Parses failed tests from pytest log (default: `tmp.pytest_log.txt`)
- Generates repro scripts for failed tests, test classes, and files
- Creates reports on passed, skipped, slow, and updated tests
- Copies failed test names to clipboard for quick rerunning

### Examples

- Parse default pytest log:
  ```bash
  > pytest_failed.py
  ```

- Parse custom log file:
  ```bash
  > pytest_failed.py --input custom.log
  ```

- Run with verbose output:
  ```bash
  > pytest_failed.py --input tmp.log -v DEBUG
  ```

## `pytest_marks.py`

### What It Does

- Collects all pytest tests with their marks without executing
- Reports test categorization (slow, superslow, skipped, etc.)
- Generates CSV report with comprehensive test metadata

### Examples

- Scan entire repository:
  ```bash
  > pytest_marks.py
  ```

- Scan specific directory only:
  ```bash
  > pytest_marks.py --dir helpers
  ```

## `pytest_count_files.sh`

### What It Does

- Counts test classes and functions using pytest collection
- Reports skipped and fast test statistics
- Must be run from repository root

### Examples

- Count all tests in repository:
  ```bash
  > ./pytest_count_files.sh
  ```

## `pytest_log`

### What It Does

- Runs pytest with arguments while tees output to `tmp.pytest_log.txt`
- Preserves pytest exit code for CI/CD integration
- Enables later analysis with `pytest_failed.py`

### Examples

- Run test file and save log:
  ```bash
  > ./pytest_log helpers/test/test_hpytest.py -v
  ```

## `rename_test_names.sh`

### What It Does

- Renames test files using glob patterns with substring replacement
- Prints mapping of old to new filenames
- Useful for bulk test file reorganization

### Examples

- Rename test files with pattern:
  ```bash
  > ./rename_test_names.sh OldName NewName test_files/*
  ```
