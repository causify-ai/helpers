---
description: Project-specific test infrastructure for `hunitest.TestCase`. Load when writing tests in this repo to know which directory helpers, golden-file methods, and test-mode utilities to use.
---

- This file covers the project-specific test infrastructure every unit test in
  this repo relies on
- Source: [`/helpers/hunit_test.py`](/helpers/hunit_test.py)

# Directory Helpers

## `hunitest.TestCase` Path Methods
- All derive from `hunitest.TestCase` — paths are scoped to the running test
  class and method automatically

  | Method | Returns |
  | :----- | :------ |
  | `get_input_dir()` | Local path for static test fixtures checked into git |
  | `get_output_dir()` | Local path for golden files (managed by `check_string`) |
  | `get_scratch_space()` | Local ephemeral dir, deleted after the test |
  | `get_s3_scratch_dir()` | S3 path for large temporary data, unique per user/server/test |
  | `get_s3_input_dir()` | S3 path for input fixtures stored in the repo's S3 bucket |

- `get_s3_scratch_dir()` builds a path like:
  ```text
  s3://alphamatic-data/tmp/cache.unit_test/<user>.<server>.<project>.<TestClass.test_method>
  ```
  Use when a test writes large temporary data to S3 that must not persist
  between runs

- `get_s3_input_dir()` mirrors `get_input_dir()` but on S3, using
  `unit_test_bucket_path` from `repo_config.yaml`; useful when fixtures are too
  large to commit to git

## Directory Structure
```text
module/test/
├── outcomes/
│   └── TestFooBar1.test_method_a/
│       ├── input/              <- get_input_dir()  [static fixtures]
│       └── output/
│           └── test.txt        <- check_string() golden file
├── scratch/
│   └── TestFooBar1.test_method_a/  <- get_scratch_space() [deleted after test]
└── test_foo.py
```

# Golden File Testing

## `check_string`
- Compares actual output against a frozen reference file in
  `outcomes/<TestClass.test_method>/output/test.txt`
- On first run (no golden file), it creates the file — review and commit it
- On subsequent runs, it diffs against the frozen file and fails if different
  ```python
  import helpers.hunit_test as hunitest

  class TestMyModule1(hunitest.TestCase):
      def test_format1(self) -> None:
          actual = my_function(input_data)
          self.check_string(actual)
  ```
- Pass `purify_text=True` to strip machine-specific noise (absolute paths,
  usernames, git refs) before freezing — use it whenever output contains
  environment-specific strings:
  ```python
  self.check_string(actual, purify_text=True)
  ```
- Use `assert_equal` instead of `check_string` when the expected value is short
  enough to inline in the test:
  ```python
  self.assert_equal(actual, expected)
  # With fuzzy whitespace matching:
  self.assert_equal(actual, expected, fuzzy_match=True)
  ```

# Test-mode Utilities

## Module-level Helpers
- Use inside production code that must behave differently during tests

  | Function | Purpose |
  | :------- | :------ |
  | `hunitest.in_unit_test_mode()` | `True` when running under pytest; skip expensive side effects |
  | `hunitest.pytest_print(txt)` | Write to stdout bypassing pytest's capture |
  | `hunitest.pytest_warning(txt, prefix="")` | Like `pytest_print` with a yellow `WARNING:` label |
  ```python
  import helpers.hunit_test as hunitest

  def expensive_side_effect() -> None:
      if hunitest.in_unit_test_mode():
          return  # Skip in tests.
      ...
  ```
