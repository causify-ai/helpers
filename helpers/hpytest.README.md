# `hpytest.py`

- Parses raw pytest / GitHub Actions logs into a structured `info` dict of
  counts (passed, failed, skipped, collected, deselected, ...) and per-test
  data (test names, durations, failure reasons)
- Used by `pytest_failed.py`, `pytest_failed_multi_build.py`, and other
  `dev_scripts_helpers/testing/` tools to summarize a test run and generate
  repro scripts for failing tests

## Anatomy of a Pytest Log

- A pytest run (in verbose mode, `-v`) produces four distinct sections, each parsed
  differently:

- **Collection line** (once, near the top):
  ```
  collected 3865 items / 155 deselected / 12 skipped / 3710 selected
  ```
  - `items`: every test pytest discovered on disk
  - `deselected`: excluded by a marker filter (e.g. `-m "not slow"`) before
    running anything
  - `skipped` (at collection): tests with an unconditional
    `@pytest.mark.skip`, recognized before running, so they never get a
    live per-test line later
  - `selected`: `items` - `deselected`, what pytest will actually process

- **Live per-test lines** (one per test, as it runs):
  ```
  test_foo.py::Test1::test1 (0.04 s) PASSED [ 36%]
  test_foo.py::Test1::test2 (2.07 s) FAILED [ 40%]
  test_bar.py::Test2::test3 SKIPPED [ 44%]
  ```
  Printed for every test pytest actually executes.
  - A test skipped dynamically at runtime (`skipif`, `pytest.skip()` inside the test
    body) still gets one of these
  - A test skipped via an unconditional decorator does not, since it is never started

- **"short test summary info" section** (once, near the end): the only
  place that lists _every_ skip, including the collection-time ones that
  never got a live line. Skips are grouped by file/line/reason, with a
  repeat count:
  ```
  SKIPPED [1] test_foo.py:15: could not import 'openai': No module named 'openai'
  SKIPPED [4] test_hserver.py:24: Config not matching
  ```
  `[4]` here means 4 distinct tests hit that same skip site

- **Final summary line** (last line):
  ```
  3534 passed, 188 skipped, 155 deselected, 1 rerun in 259.08s (0:04:19)
  ```
  Pytest only prints categories with a nonzero count, so a clean run reads
  just `3 passed in 0.05s`

## Fields Reference

- This table is the authoritative description of every field in the `info`
  dict returned by `parse_failed_tests()` in `helpers/hpytest.py`

- `github_tag`
  - _Parsed from_: GitHub Actions per-line tags
  - _Meaning_: Job tag from GitHub, `None` if input isn't a GitHub Actions log
- `github_start_timestamp`
  - _Parsed from_: GitHub Actions per-line tags
  - _Meaning_: See `_parse_github_ci_log()`
- `github_end_timestamp`
  - _Parsed from_: GitHub Actions per-line tags
  - _Meaning_: See `_parse_github_ci_log()`
- `github_completed`
  - _Parsed from_: GitHub Actions per-line tags
  - _Meaning_: See `_parse_github_ci_log()`
- `pytest_started`
  - _Parsed from_: `"test session starts"` banner
  - _Meaning_: `True` if pytest reached the banner
- `pytest_tag`
  - _Parsed from_: platform line
  - _Meaning_: The platform line, e.g. `"... -- Python ..., pytest-..., ..."`
- `pytest_collection_completed`
  - _Parsed from_: collection line
  - _Meaning_: `True` if the `"collected N items"` line was printed
- `pytest_num_collected`
  - _Parsed from_: collection line
  - _Meaning_: Number of tests collected by pytest
- `pytest_num_deselected`
  - _Parsed from_: collection line
  - _Meaning_: Number of deselected tests (optional)
- `pytest_num_skipped_at_collection`
  - _Parsed from_: collection line
  - _Meaning_: Number of tests skipped at collection (optional)
- `pytest_num_selected`
  - _Parsed from_: collection line
  - _Meaning_: Number of selected tests (optional)
- `log_passed_tests`
  - _Parsed from_: live per-test `PASSED` lines
  - _Meaning_: List of passed tests, parsed from the log
- `log_skipped_tests`
  - _Parsed from_: short-summary `SKIPPED [N]` lines (falls back to live
    lines if absent)
  - _Meaning_: List of skipped tests. When the short-summary section is
    present, entries are synthetic `path[:line]:reason#i` keys (not real
    pytest node ids), since that section reports a repeat count and a
    file[:line] plus a reason but not the node id. Used because it's the
    only place that reports *every* skipped test: tests skipped via
    `@pytest.mark.skip`/`skipif` are never run, so pytest prints no
    per-test verbose line (and thus no node id) for them
- `log_failed_tests`
  - _Parsed from_: live per-test `FAILED`/`ERROR` lines
  - _Meaning_: List of failed tests, parsed from the log
- `log_updated_tests`
  - _Parsed from_: `(WARNING: Test was updated)` annotation
  - _Meaning_: List of tests whose golden outcome file was updated during
    the run
- `log_test_durations`
  - _Parsed from_: `(N.NN s)` per line
  - _Meaning_: Dict mapping test names to their durations in seconds
- `log_test_errors`
  - _Parsed from_: `FAILED <test> - <Error>:` tags
  - _Meaning_: Dict mapping failed test names to their parsed failure
    reason, i.e., the text from a `"FAILED <test> - <Error>:"` tag up to,
    but not including, the next such tag (or the end of the log)
- `log_num_passed`
  - _Parsed from_: derived from `log_passed_tests`
  - _Meaning_: Number of passed tests from the log
- `log_num_skipped`
  - _Parsed from_: derived from `log_skipped_tests`
  - _Meaning_: Number of skipped tests
- `log_num_failed`
  - _Parsed from_: derived from `log_failed_tests`
  - _Meaning_: Number of failed tests from the log
- `log_num_failed_files`
  - _Parsed from_: derived from `log_failed_tests`
  - _Meaning_: Number of files with failed tests
- `log_num_failed_classes`
  - _Parsed from_: derived from `log_failed_tests`
  - _Meaning_: Number of test classes with failed tests
- `log_num_updated`
  - _Parsed from_: derived from `log_updated_tests`
  - _Meaning_: Number of tests whose golden outcome file was updated
- `pytest_ended`
  - _Parsed from_: final summary line
  - _Meaning_: `True` if pytest reached the final summary line, e.g.
    `"4 failed, 43 passed in 40.48s"`
- `pytest_num_failed`
  - _Parsed from_: final summary line
  - _Meaning_: Number of failed tests from the final summary line
- `pytest_num_passed`
  - _Parsed from_: final summary line
  - _Meaning_: Number of passed tests from the final summary line
- `pytest_num_skipped`
  - _Parsed from_: final summary line
  - _Meaning_: Number of skipped tests from the final summary line
- `pytest_duration_in_secs`
  - _Parsed from_: final summary line
  - _Meaning_: Run duration in seconds from the final summary line

## How the Metrics Relate to Each Other

- The equation:
  ```
  pytest_num_collected = pytest_num_deselected + pytest_num_selected
  ```
  deselected tests are excluded from "selected", but a further subset of "selected"
  (`pytest_num_skipped_at_collection`) is already known-skip and produces no live
  line
- The equation:
  ```
  log_num_passed`, `log_num_failed`, `log_num_skipped
  ```
  should each equal their `pytest_num_*` counterpart from the final summary line
  - A mismatch triggers a warning: it usually means a line's format didn't match any
    parsing pattern
- The sanity check:
  ```
  log_num_passed + log_num_failed + log_num_skipped == pytest_num_collected
  ```
  does **not** subtract `pytest_num_deselected`. It fires a benign warning any time
  markers exclude tests (e.g. `run_fast_tests` deselecting `slow`/`superslow`-marked
  tests)
- `RERUN` lines (from the `pytest-rerunfailures` plugin) match none of the
  status patterns and are silently ignored: the retried test's later
  `PASSED`/`FAILED` line is what gets counted, so it's counted once, not
  twice

## Relationship with Grepping the Raw Log

- Grepping the raw log directly for a status keyword double-counts or under-counts
  relative to the `info` dict, because pytest reports a test result in more than one
  place:
- `grep -c PASSED` matches the parsed `log_num_passed` exactly: pytest
  prints exactly one `PASSED` line per pass, nowhere else
- `grep -c SKIPPED` over-counts: it matches both the live per-test lines
  *and* the short-summary aggregate lines for the same tests. E.g. a run
  with `log_num_skipped = 188` can show `grep -c SKIPPED = 288`, split as
  176 live lines (runtime skips) + 112 aggregate lines (each an `[N]`
  group, summing to 188 tests, 12 of which never had a live line)
- `grep -c FAILED` over-counts similarly if any test failed, since failures
  get a live line, a `short test summary info` entry, and a full traceback
  block that may itself contain the word `FAILED`

- Prefer `parse_failed_tests()` over ad hoc grepping whenever an exact count is
  needed; grep is fine for eyeballing but not for totals.

## Example

```
collected 3865 items / 155 deselected / 12 skipped / 3710 selected
...
test_hmarkdown_formatting.py::Test_format::test1 (0.04 s) PASSED [ 12%]
test_piper_markdown_reader.py::Test1::test1 (10.04 s) RERUN            [ 16%]
test_piper_markdown_reader.py::Test1::test1 (2.37 s) PASSED            [ 16%]
test_hserver.py::Test2::test3 SKIPPED [ 44%]
...
=========================== short test summary info ============================
SKIPPED [1] test_hopen.py: See cryptomtc/cmamp#321
SKIPPED [4] test_hserver.py:24: Config not matching
============ 3534 passed, 188 skipped, 155 deselected, 1 rerun in 259.08s ============
```

yields:

```python
{
    "pytest_num_collected": 3865,
    "pytest_num_deselected": 155,
    "pytest_num_skipped_at_collection": 12,
    "pytest_num_selected": 3710,
    "log_num_passed": 3534,
    "log_num_skipped": 188,
    "log_num_failed": 0,
    "pytest_num_passed": 3534,
    "pytest_num_skipped": 188,
    "pytest_num_failed": 0,
    "pytest_duration_in_secs": 259.08,
}
```
