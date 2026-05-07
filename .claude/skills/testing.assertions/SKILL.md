---
description: Reference rules for DataFrame/Series assertions, repr/str testing, and QA testing patterns. Load when writing assertions for pandas objects, testing __repr__/__str__, or testing Docker/invoke behavior from the host.
---

- This file contains rules for DataFrame/Series assertions, repr/str testing,
  and QA testing

# DataFrame and Series Assertions

## Structured DataFrame Checks
- Prefer these helpers over converting a DataFrame to a string manually
- `check_df_output` validates shape, columns, and unique values before a full
  string comparison:
  ```python
  self.check_df_output(
      actual_df,
      expected_length=10,
      expected_column_names=["open", "high", "low", "close", "volume"],
      expected_column_unique_values={"exchange_id": ["binance"]},
      expected_signature=r"""
  # df=
  # index=[2024-01-01, 2024-01-10]
  # columns=open,high,low,close,volume,exchange_id
  # shape=(10, 6)
  """,
  )
  ```
  - Pass `None` for any parameter to skip that check
  - Pass `"__CHECK_STRING__"` as `expected_signature` to delegate to
    `self.check_string()` (golden file mode)

- `check_srs_output` does the same for a `pd.Series`:
  ```python
  self.check_srs_output(
      actual_srs,
      expected_length=5,
      expected_unique_values=["BTC", "ETH"],
      expected_signature=r"""
  0    BTC
  1    ETH
  dtype: object
  """,
  )
  ```

- `assert_dfs_close` asserts two DataFrames are numerically close (uses
  `numpy.allclose` to check and `np.testing.assert_allclose` to report
  failures); prefer it over `assert_equal(df_to_str(a), df_to_str(b))` when
  floating-point round-off is possible:
  ```python
  self.assert_dfs_close(actual_df, expected_df, rtol=1e-5)
  ```

- `check_dataframe` is golden file testing for DataFrames — serialises to CSV
  and compares element-wise within a tolerance; use it like `check_string()`:
  ```python
  self.check_dataframe(actual_df)
  # Multiple DFs in one test — use a tag to distinguish golden files.
  self.check_dataframe(actual_df, tag="prices_df")
  ```

# Repr / Str Testing

## Obj_to_str_TestCase Mixin
- Use `hunteuti.Obj_to_str_TestCase` to standardise tests for objects that
  implement `__repr__`, `__str__`, or `to_config_str()`
- `hunitest.TestCase` **must come first** in the MRO so that `assert_equal`
  and `check_string` resolve correctly
  ```python
  import helpers.hunit_test_utils as hunteuti

  class TestMyClass1(hunitest.TestCase, hunteuti.Obj_to_str_TestCase):
      def test_repr1(self) -> None:
          obj = MyClass(value=42)
          self.run_test_repr(obj, expected_str="MyClass(value=42)")

      def test_str1(self) -> None:
          obj = MyClass(value=42)
          self.run_test_str(obj, expected_str="value=42")
  ```

  | Method | Calls |
  | :----- | :---- |
  | `run_test_repr(obj, expected_str)` | `obj.__repr__()` |
  | `run_test_str(obj, expected_str)` | `obj.__str__()` |
  | `run_test_to_config_str(obj, expected_str)` | `obj.to_config_str()` |

- All three methods use `purify_text=True` and `fuzzy_match=True` internally

# QA Testing

## QaTestCase
- Use `hunitest.QaTestCase` for tests that validate Docker container behaviour
  from the **host machine** (not inside a container)
- It carries `@pytest.mark.qa` and auto-skips when `hserver.is_inside_docker()`
  returns `True`
  ```python
  import helpers.hunit_test as hunitest

  class TestInvokeTask1(hunitest.QaTestCase):
      def test_docker_bash1(self) -> None:
          # Only runs on the host, never inside a container.
          import helpers.hsystem as hsystem
          rc, _ = hsystem.system("invoke docker_bash --cmd 'echo hello'")
          self.assert_equal(str(rc), "0")
  ```

- Add `@pytest.mark.no_container` in `pytest.ini` if the test must be excluded
  from the default in-Docker test run
