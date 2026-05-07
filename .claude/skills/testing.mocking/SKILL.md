---
description: Reference rules and patterns for mocking in Python unit tests. Load when writing, reviewing, or patching tests that interact with external dependencies (AWS/S3, 3rd-party APIs, databases, GitHub).
---

- This file contains rules and patterns for mocking in unit tests

# Mocking Philosophy

## Refs
- Introductory article:
  [https://realpython.com/python-mock-library/](https://realpython.com/python-mock-library/)
- Official Python docs:
  [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)

## Mock Only External Dependencies
- Mock only interactions with external components:
  - 3rd-party providers (e.g., CCXT, OpenAI)
  - Cloud infra: S3 (see [`/helpers/hmoto.py`](/helpers/hmoto.py)), AWS Secrets
  - Databases
  - GitHub
- Mock the external library, not our internal wrapper on top of it

  **Good**: mock `github.Github` (the external provider)
  ```python
  @umock.patch("github.Github")
  def test_github_labels(self, mock_github):
      mock_repo = umock.Mock()
      mock_github.return_value.get_repo.return_value = mock_repo
  ```

  **Bad**: mock `helpers.get_labels` (our internal wrapper)
  ```python
  @umock.patch("helpers.get_labels")
  def test_github_labels(self, mock_helper):
      ...
  ```

- Keep mocks minimal — include only attributes the function under test actually
  uses

  **Bad** (unused fields bloat the mock):
  ```python
  mock_label.name = "bug"
  mock_label.color = "f29513"          # unused
  mock_label.description = "..."       # unused
  mock_label.created_at = "2024-01-01" # unused
  ```

  **Good**:
  ```python
  mock_label = umock.Mock()
  mock_label.name = "bug"              # only what the function uses
  mock_repo.get_labels.return_value = [mock_label]
  ```

- Do not test external providers themselves — only verify our code handles their
  responses correctly

## Do Not Mock Internal Dependencies
- Never mock code inside our repo; test the real interaction between components
- Mocking internal code creates maintenance problems and hides integration bugs

## Test End-to-end, Not Implementation
- Test the public behavior of a class, not the internal steps used to achieve it
- Rationale: over-mocking internals means every refactor breaks tests even when
  the external behavior is unchanged
- Mock only what is needed to isolate the true external boundary

  **Bad** (mocking internal helpers alongside the external provider):
  ```python
  @umock.patch("docker.build_container")
  @umock.patch("helpers.get_labels")
  @umock.patch("github.Github")
  def test_github_labels(self, mock_get_labels, mock_build_container, mock_github):
      ...
  ```

  **Good** (mock only the external boundary):
  ```python
  @umock.patch("github.Github")
  def test_github_labels(self, mock_github):
      mock_repo = umock.Mock()
      mock_github.return_value.get_repo.return_value = mock_repo
  ```

# Mocking Rules

## Mock at the Call Site
- Mock the object at the location where it is called, not where it is defined:
  `@umock.patch.object(calling_module.dep, "method")` not
  `@umock.patch.object(defining_module, "method")`

# Patching Patterns

## Object Patch with Return Value
```python
import unittest.mock as umock
import helpers.hsftp as hsftp  # the module under test, which imports hsecret internally

@umock.patch.object(hsftp.hsecret, "get_secret")
def test_function_call1(self, mock_get_secret: umock.MagicMock):
    mock_get_secret.return_value = "dummy"
```
- Mocks `get_secret` at the call site (`hsftp`), not the definition site
  (`hsecret`) — mocks are applied after module load so patching at the
  definition site in the test file has no effect

## Path Patch with Multiple Return Values
```python
@umock.patch("helpers.hsecret.get_secret")
def test_function_call1(self, mock_get_secret: umock.MagicMock):
    mock_get_secret.side_effect = ["dummy", Exception]
```
- `side_effect` as a list: each call pops the next value; `Exception` is raised

## Three Ways to Apply `patch`
- **Decorator** (preferred for simple cases):
  ```python
  @umock.patch("helpers.hsecret.get_secret")
  def test_function_call1(self, mock_get_secret: umock.MagicMock):
      pass
  ```
- **Manual start/stop** (needed when patch spans class-level setup):
  ```python
  patch = umock.patch("helpers.hsecret.get_secret")
  mock = patch.start()   # returns the MagicMock
  patch.stop()           # must be called explicitly
  ```
- **Context manager** (useful when multiple decorators get hard to read):
  ```python
  with umock.patch("helpers.hsecret.get_secret") as mock:
      pass
  ```

## Verify Mock State After a Test
```python
@umock.patch.object(exchange._exchange, "fetch_ohlcv")
def test_function_call1(self, fetch_ohlcv_mock: umock.MagicMock):
    self.assertEqual(fetch_ohlcv_mock.call_count, 1)
    actual_args = tuple(fetch_ohlcv_mock.call_args)
    expected_args = (
        ("BTC/USDT",),
        {"limit": 2, "since": 1, "timeframe": "1m"},
    )
    self.assertEqual(actual_args, expected_args)
```
- Use `call_args_list` to check all calls when count > 1:
  ```python
  actual = str(fetch_ohlcv_mock.call_args_list)
  self.assert_equal(actual, expected, fuzzy_match=True)
  ```

## Class-level Mocks Via `set_up_test`
- Declare patches as class attributes; start/stop in `set_up_test` /
  `tear_down_test` so the same patch object is reused for every test method:
  ```python
  class TestCcxtExtractor1(hunitest.TestCase):
      get_secret_patch = umock.patch.object(ivcdexex.hsecret, "get_secret")
      ccxt_patch = umock.patch.object(ivcdexex, "ccxt", spec=ivcdexex.ccxt)

      def set_up_test(self) -> None:
          self.get_secret_mock = self.get_secret_patch.start()
          self.ccxt_mock = self.ccxt_patch.start()
          self.get_secret_mock.return_value = {"apiKey": "test", "secret": "test"}

      def tear_down_test(self) -> None:
          self.get_secret_patch.stop()
          self.ccxt_patch.stop()
  ```
- Do not move patch creation into `set_up_test`: that would create a new
  `patch` object per test, making `start/stop` track different instances

## Specs
```python
# No spec — any attribute access is allowed and returns MagicMock.
@umock.patch.object(ivcdexex, "ccxt")
# Shallow spec — only valid ccxt attributes allowed; returned values unspecced.
@umock.patch.object(ivcdexex, "ccxt", spec=ivcdexex.ccxt)
# Deep spec — everything recursively validated against the real object.
@umock.patch.object(ivcdexex, "ccxt", autospec=True)
```

## Caveats
- Python built-in methods cannot be patched directly — wrap via the module that
  imports them:
  ```python
  # Patching datetime.now directly raises AttributeError.
  # Patch the module-level reference instead:
  datetime_patch = umock.patch.object(module, "datetime", spec=module.datetime)
  ```
- To instantiate an abstract class in tests, patch `__abstractmethods__`:
  ```python
  abstract_patch = umock.patch.object(
      MyAbstractClass, "__abstractmethods__", new=set()
  )
  ```

# AWS / S3 Mocking

## `hmoto.S3Mock_TestCase`
- Use `hmoto.S3Mock_TestCase` from [`/helpers/hmoto.py`](/helpers/hmoto.py)
  for in-process S3 mocking via the `moto` library
- **`moto` must be imported before `boto3`** — `hmoto.py` enforces this
- The base class creates a fresh `mock_bucket` per test in `set_up_test()` and
  tears it down in `tear_down_test()`
  ```python
  import helpers.hmoto as hmoto

  class TestMyS3Feature1(hmoto.S3Mock_TestCase):
      def test_upload1(self) -> None:
          import boto3
          client = boto3.client("s3")
          client.put_object(Bucket=self.bucket_name, Key="data.csv", Body=b"a,b\n1,2\n")
          response = client.get_object(Bucket=self.bucket_name, Key="data.csv")
          self.assert_equal(response["Body"].read().decode(), "a,b\n1,2\n")
  ```
- Carries `@pytest.mark.requires_ck_aws` and `@pytest.mark.requires_ck_infra`
  — subclasses inherit both markers

# Capturing System Calls

## `hunteuti.capture_system_calls`
- Context manager that intercepts `subprocess.run()` and
  `helpers.hsystem._system()` without executing any real shell command
- Each intercepted call is recorded as `{"function": ..., "args": ..., "kwargs": ...}`
  ```python
  import helpers.hunit_test_utils as hunteuti

  class TestRunner1(hunitest.TestCase):
      def test_no_real_shell1(self) -> None:
          with hunteuti.capture_system_calls() as calls:
              my_function_that_runs_shell_commands()
          self.assert_equal(str(len(calls)), "1")
          self.assert_equal(calls[0]["function"], "subprocess.run")
  ```
- Pass `side_effect` to simulate failures:
  ```python
  with hunteuti.capture_system_calls(side_effect=RuntimeError) as calls:
      with self.assertRaises(RuntimeError):
          my_function()
  ```
