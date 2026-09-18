# Fix Plan for TODOs

- 24 issues below, one per `TODO(ai_gp)` line below

./dev_scripts_helpers/documentation/preprocess_notes.py:104:            # TODO(ai_gp): Convert this into a loop and shorter comments.
./dev_scripts_helpers/documentation/preprocess_notes.py:387:    # TODO(ai_gp): Use r""" and dedent
./dev_scripts_helpers/documentation/test/test_md_to_speech.py:756:        # TODO(ai_gp): Use hunteuti.capture_sys_calls() instead of mocking
./dev_scripts_helpers/documentation/test/test_md_to_speech.py:789:        # TODO(ai_gp): Use hunteuti.capture_sys_calls() instead of mocking
./dev_scripts_helpers/documentation/test/test_md_to_speech.py:851:        # TODO(ai_gp): Use hunteuti.capture_sys_calls() instead of mocking
./dev_scripts_helpers/documentation/test/test_compress_pdf.py:14:# TODO(ai_gp): Improve test to follow rules
./dev_scripts_helpers/system_tools/docker_cleanup.py:141:# TODO(ai_gp): move the comments inlined in the regex below
./dev_scripts_helpers/system_tools/test/test_docker_cleanup.py:509:    # TODO(ai_gp): Factor out common code.
./dev_scripts_helpers/system_tools/test/test_docker_cleanup.py:560:    # TODO(ai_gp): Factor out common code and use mock_sys_call.
./dev_scripts_helpers/system_tools/test/test_docker_cleanup.py:637:    # TODO(ai_gp): Factor out common code and use mock_sys_call.
./dev_scripts_helpers/system_tools/test/test_docker_cleanup.py:714:    # TODO(ai_gp): Factor out common code and use mock_sys_call.
./dev_scripts_helpers/system_tools/test/test_docker_cleanup.py:765:    # TODO(ai_gp): Factor out common code and use mock_sys_call.
./dev_scripts_helpers/download/download_utils.py:132:    # TODO(ai_gp): Move this to after *
./dev_scripts_helpers/typst/test/test_run_typst.py:160:    # TODO(ai_gp): Factor out more code.
./dev_scripts_helpers/download/test/test_process_gsheet_links.py:113:        # TODO(ai_gp): Move the assert_equal in the helper
./dev_scripts_helpers/download/test/test_process_gsheet_links.py:252:        # TODO(ai_gp): Move the assert_equal in the helper
./dev_scripts_helpers/download/test/test_update_gsheet_links_from_raindrop.py:146:        # TODO(ai_gp): Move the assert_equal in the helper
./dev_scripts_helpers/download/test/test_update_gsheet_links_from_raindrop.py:320:        # TODO(ai_gp): Move the assert_equal in the helper
./helpers/lib_tasks/test/test_lib_tasks_docker_release.py:69:        # TODO(ai_gp): Use hunteuti.capture_sys_calls() instead of mocking
./dev_scripts_helpers/documentation/test/test_notes_to_pdf.py:2536:        # TODO(ai_gp): Move check_string in the helper
./linters2/test/test_cc_lint.py:1634:        # TODO(ai_gp): Use hunteuti.capture_sys_calls() instead of mocking
./dev_scripts_helpers/documentation/test/test_lint_text.py:3566:# TODO(ai_gp): Use a helpers
./helpers/test/test_hparser.py:74:    # TODO(ai_gp): Move all the dedent in the helper
./helpers/test/test_hparser.py:539:    # TODO(ai_gp): Factor common code and assert_equal in an helper.

- All 24 TODOs live under `helpers_root/`, so every issue is filed against the
  `helpers` repo only
- Ordered by increasing fix complexity, highest-confidence fixes first within
  each complexity tier
---

### [x] Move `model` parameter after `*` in `summarize_text_with_llm()`

* Repo:
- [x] helpers (https://github.com/causify-ai/helpers)
- [ ] umd_classes (https://github.com/gpsaggese/gpsaggese.github.io)

* Problem
- Location: `dev_scripts_helpers/download/download_utils.py:132`
- `summarize_text_with_llm()` declares `model: str = _SUMMARY_MODEL` before
  the bare `*`, so `model` is not forced keyword-only like `dry_run`
- Violates `coding.rules.md`'s "Use Default Values Rarely and Force
  Keyword-Only Via `*`": every parameter with a default must be keyword-only

* Info
- **Type**: cosmetic
- **Reason of the problem**: `model` was added before the keyword-only
  marker `*` instead of after it
- **Confidence in the fix**: high
- **Fix complexity**: low
- **Verification plan**:
  - Confirm no call site passes `model` positionally (checked: all 4
    call sites in `download_hn_article_to_md.py`, `download_html_to_md.py`,
    and `download_academic_paper_to_md.py` omit `model` entirely)
  - Run `helpers/test/` and `dev_scripts_helpers/download/test/` fast tests

* Solution

- [x] PR1: Force `model` to be keyword-only
  - Move `model: str = _SUMMARY_MODEL` to after the `*` in the signature,
    next to `dry_run`

---

### [x] Convert `version_line` to a raw triple-quote string in `preprocess_notes.py`

* Repo:
- [x] helpers (https://github.com/causify-ai/helpers)
- [ ] umd_classes (https://github.com/gpsaggese/gpsaggese.github.io)

* Problem
- Location: `dev_scripts_helpers/documentation/preprocess_notes.py:389`
- `version_line` is built with escaped `\n` and escaped `\"` inside a
  single-line f-string, instead of a raw triple-quoted string
- Violates `coding.rules.md`'s "Use Triple-Quote Assignment with
  `hprint.dedent`" and "Use Raw Strings Instead of Escaping"

* Info
- **Type**: cosmetic
- **Reason of the problem**: written as a quick one-liner instead of
  following the multi-line string convention used a few lines below for
  `txt`
- **Confidence in the fix**: high
- **Fix complexity**: low
- **Verification plan**:
  - Existing golden-file tests for `_generate_title_slide_typst()` (if any)
    still pass with identical output
  - Manually diff old vs. new `version_line` value for a sample `version`

* Solution

- [x] PR1: Rewrite `version_line` as a dedented raw string
  - Replace the escaped-newline f-string with an `r"""..."""` block matching
    the indentation of `txt` below it, then `hprint.dedent()` it
  - Keep the conditional: empty string when `version` is falsy

---

### [x] Move `hprint.dedent()` calls into `helper()` in `Test_CustomHelpFormatter_split_lines`

* Repo:
- [x] helpers (https://github.com/causify-ai/helpers)
- [ ] umd_classes (https://github.com/gpsaggese/gpsaggese.github.io)

* Problem
- Location: `helpers/test/test_hparser.py:74`
- `test1` and `test2` each call `text = hprint.dedent(text)` before invoking
  `self.helper(text, width, expected)`, even though `helper()` already
  dedents `expected` internally via `assert_equal(..., dedent=True)`
- Violates `testing.rules.md`'s "Move Dedent and Checking into the Helper
  Method"

* Info
- **Type**: cosmetic
- **Reason of the problem**: `expected` was moved into the helper's
  dedent-on-compare, but `text` was left dedented at the call site
- **Confidence in the fix**: high
- **Fix complexity**: low
- **Verification plan**:
  - `pytest helpers/test/test_hparser.py::Test_CustomHelpFormatter_split_lines`
    still passes

* Solution

- [x] PR1: Dedent `text` inside `helper()`
  - Add `text = hprint.dedent(text)` at the top of `helper()`
  - Remove the now-redundant `hprint.dedent(text)` calls from `test1` and
    `test2`

---

### [x] Move `self.check_string()` call into `helper()` in `Test_notes_to_pdf_latex_cancel`

* Repo:
- [x] helpers (https://github.com/causify-ai/helpers)
- [ ] umd_classes (https://github.com/gpsaggese/gpsaggese.github.io)

* Problem
- Location: `dev_scripts_helpers/documentation/test/test_notes_to_pdf.py:2536`
- `test1` through `test4` all call the identical
  `self.check_string(output_txt, fuzzy_match=True)` right after
  `self.helper(markdown_content)`, then add test-specific `assertIn` checks
- Violates `testing.rules.md`'s "Move Dedent and Checking into the Helper
  Method": the identical, repeated check belongs in the helper
- Out of scope: this class (like ~225 other call sites repo-wide) uses the
  golden-file `self.check_string()` API that `testing.rules.md` marks as
  banned in favor of `self.assert_equal()`; fixing that repo-wide convention
  gap is a separate, much larger issue and not part of this TODO

* Info
- **Type**: cosmetic
- **Reason of the problem**: the shared golden-file check was left at each
  call site instead of being factored into `helper()`
- **Confidence in the fix**: high
- **Fix complexity**: low
- **Verification plan**:
  - `pytest dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_latex_cancel`
    still passes with unchanged golden files

* Solution

- [x] PR1: Fold the shared `check_string()` call into `helper()`
  - Add `self.check_string(output_txt, fuzzy_match=True)` at the end of
    `helper()`
  - Remove the duplicated call from `test1`, `test2`, `test3`, `test4`,
    keeping each test's own `assertIn` checks in place

---

### [x] Move `assert_equal` into `helper_mock_hn_api()` in `Test__update_article_urls`

* Repo:
- [x] helpers (https://github.com/causify-ai/helpers)
- [ ] umd_classes (https://github.com/gpsaggese/gpsaggese.github.io)

* Problem
- Location:
  `dev_scripts_helpers/download/test/test_process_gsheet_links.py:113`
- `test2` calls `self.helper_mock_hn_api(rows, expected)` then separately
  `self.assert_equal(actual_rows[0]["Article_url"], expected)`
- Violates `testing.rules.md`'s "Move Dedent and Checking into the Helper
  Method"; `test1` and `test3` use the sibling `helper()` and have the same
  pattern but are not flagged by this TODO

* Info
- **Type**: cosmetic
- **Reason of the problem**: `helper_mock_hn_api()` returns raw rows instead
  of also checking the expected `Article_url`
- **Confidence in the fix**: high
- **Fix complexity**: low
- **Verification plan**:
  - `pytest dev_scripts_helpers/download/test/test_process_gsheet_links.py::Test__update_article_urls`
    still passes

* Solution

- [x] PR1: Add `expected` param to `helper_mock_hn_api()` and assert inside
  - Change signature to
    `helper_mock_hn_api(self, rows, extracted_url, expected)`
  - Move `self.assert_equal(actual_rows[0]["Article_url"], expected)` inside
    it, then update `test2` to pass `expected` and drop the standalone
    assertion
  - `test5` calls `helper_mock_hn_api()` too but compares a different value
    (`str(actual)` over all rows), so leave it calling the helper without
    the new single-value assertion, or pass a sentinel indicating "skip"

---

### [x] Move `assert_equal` into `helper()` in `Test__update_article_clusters`

* Repo:
- [x] helpers (https://github.com/causify-ai/helpers)
- [ ] umd_classes (https://github.com/gpsaggese/gpsaggese.github.io)

* Problem
- Location:
  `dev_scripts_helpers/download/test/test_process_gsheet_links.py:252`
- `test1` calls `self.helper(rows)` then separately
  `self.assert_equal(str(actual_rows[0]), str(expected))`
- Same pattern as the sibling class above; violates `testing.rules.md`'s
  "Move Dedent and Checking into the Helper Method"

* Info
- **Type**: cosmetic
- **Reason of the problem**: `helper()` returns raw rows instead of also
  checking them against `expected`
- **Confidence in the fix**: high
- **Fix complexity**: low
- **Verification plan**:
  - `pytest dev_scripts_helpers/download/test/test_process_gsheet_links.py::Test__update_article_clusters`
    still passes

* Solution

- [x] PR1: Add `expected` param to `helper()` and assert inside
  - Change signature to `helper(self, rows, expected)`
  - Move `self.assert_equal(str(actual_rows[0]), str(expected))` inside it
  - Update `test1` to pass `expected` and drop the standalone assertion
  - Check `test2` (and any other test in the class) for the same pattern and
    migrate it too, so the class has one consistent helper contract

---

### [x] Move `assert_equal` into `helper()` in `Test__combine_raindrop_with_gsheet_links`

* Repo:
- [x] helpers (https://github.com/causify-ai/helpers)
- [ ] umd_classes (https://github.com/gpsaggese/gpsaggese.github.io)

* Problem
- Location:
  `dev_scripts_helpers/download/test/test_update_gsheet_links_from_raindrop.py:146`
- `test2` calls `self.helper(gsheet_columns, gsheet_rows, raindrop_rows)`
  then separately `self.assert_equal(str(actual_rows), str(expected_rows))`
- `test1` and `test3` use the same `helper()` with the identical assertion
  pattern; violates `testing.rules.md`'s "Move Dedent and Checking into the
  Helper Method"

* Info
- **Type**: cosmetic
- **Reason of the problem**: `helper()` returns raw rows instead of also
  checking them against `expected_rows`
- **Confidence in the fix**: high
- **Fix complexity**: low
- **Verification plan**:
  - `pytest dev_scripts_helpers/download/test/test_update_gsheet_links_from_raindrop.py::Test__combine_raindrop_with_gsheet_links`
    still passes

* Solution

- [x] PR1: Add `expected` param to `helper()` and assert inside
  - Change signature to
    `helper(self, gsheet_columns, gsheet_rows, raindrop_rows, expected)`
  - Move `self.assert_equal(str(actual_rows), str(expected))` inside it
  - Update `test1`, `test2`, `test3` (and `test4` if it follows the same
    shape) to pass `expected` and drop the standalone assertions

---

### [x] Move `assert_equal` into `helper()` in `Test__download_raindrop_data`

* Repo:
- [x] helpers (https://github.com/causify-ai/helpers)
- [ ] umd_classes (https://github.com/gpsaggese/gpsaggese.github.io)

* Problem
- Location:
  `dev_scripts_helpers/download/test/test_update_gsheet_links_from_raindrop.py:320`
- `test2` calls
  `self.helper(gsheet_timestamp, get_return_value=response)` then
  separately `self.assert_equal(str(actual_rows), str(expected_rows))`
- Same repeated pattern as the sibling class above (`test1`, `test3` use the
  identical shape)

* Info
- **Type**: cosmetic
- **Reason of the problem**: `helper()` returns raw rows instead of also
  checking them against `expected_rows`
- **Confidence in the fix**: high
- **Fix complexity**: low
- **Verification plan**:
  - `pytest dev_scripts_helpers/download/test/test_update_gsheet_links_from_raindrop.py::Test__download_raindrop_data`
    still passes

* Solution

- [x] PR1: Add `expected` param to `helper()` and assert inside
  - Change signature to
    `helper(self, gsheet_timestamp, expected, *, get_return_value)`
    (required positional before the keyword-only mock arg)
  - Move `self.assert_equal(str(actual_rows), str(expected))` inside it
  - Update `test1`, `test2`, `test3` (and pagination tests further down the
    class, if they share the shape) to pass `expected` and drop the
    standalone assertions

---

### [x] Factor out common mocking code in `Test__is_engine_available`

* Repo:
- [x] helpers (https://github.com/causify-ai/helpers)
- [ ] umd_classes (https://github.com/gpsaggese/gpsaggese.github.io)

* Problem
- Location:
  `dev_scripts_helpers/system_tools/test/test_docker_cleanup.py:509`
- `test1`, `test2`, `test3` each repeat the same
  `with (mock.patch("helpers.hsystem.check_exec", return_value=...),
  mock.patch("helpers.hdocker.is_docker_running", return_value=...)):`
  block, varying only the two booleans and the expected result
- Violates `testing.rules.md`'s "Use Helper Methods When You Have Repetitive
  Tests"

* Info
- **Type**: cosmetic
- **Reason of the problem**: no shared helper was written when the 3 tests
  were added
- **Confidence in the fix**: high
- **Fix complexity**: low
- **Verification plan**:
  - `pytest dev_scripts_helpers/system_tools/test/test_docker_cleanup.py::Test__is_engine_available`
    still passes

* Solution

- [x] PR1: Add a `helper()` taking the two booleans and the expected result
  - `helper(self, check_exec_available, docker_running, expected)` mocks
    both dependencies, calls `_is_engine_available("docker")`, and asserts
    with `self.assertEqual`
  - Rewrite `test1`, `test2`, `test3` to call `helper()` with their 3 values

---

### [x] Factor common code and move `assert_equal` into a helper in `Test_CustomHelpFormatter_format_help`

* Repo:
- [x] helpers (https://github.com/causify-ai/helpers)
- [ ] umd_classes (https://github.com/gpsaggese/gpsaggese.github.io)

* Problem
- Location: `helpers/test/test_hparser.py:539`
- `test2` and `test3` both: build a parser via
  `self._build_parser(_ForceNoColorFormatter)`, call `parser.format_help()`,
  and compare it to a byte-identical `expected` string with
  `self.assert_equal(actual, expected, dedent=True)`
- `test1` (checks `formatter._width`) and `test4` (compares colored vs.
  plain output) do not share this shape and should stay as-is

* Info
- **Type**: cosmetic
- **Reason of the problem**: no shared helper was written for the
  build-parser-and-compare-help-text pattern
- **Confidence in the fix**: high
- **Fix complexity**: low
- **Verification plan**:
  - `pytest helpers/test/test_hparser.py::Test_CustomHelpFormatter_format_help`
    still passes

* Solution

- [x] PR1: Add a `helper()` for the shared build-and-compare pattern
  - `helper(self, formatter_class, expected)` builds the parser, calls
    `format_help()`, and does
    `self.assert_equal(actual, expected, dedent=True)`
  - Rewrite `test2` and `test3` to call it; leave `test1` and `test4`
    unchanged

---

### [x] Add a helper method in `Test_perform_actions_typ_type`

* Repo:
- [x] helpers (https://github.com/causify-ai/helpers)
- [ ] umd_classes (https://github.com/gpsaggese/gpsaggese.github.io)

* Problem
- Location: `dev_scripts_helpers/documentation/test/test_lint_text.py:3566`
- `test1`, `test2`, `test3` each call
  `dshdllite._perform_actions(lines, file_name, ...)` then
  `self.assertEqual(actual, expected)`, varying only the inputs, the
  `file_type_override`/`actions` kwargs, and `expected`
- Violates `testing.rules.md`'s "Use Helper Methods When You Have Repetitive
  Tests"

* Info
- **Type**: cosmetic
- **Reason of the problem**: no shared helper was written when the 3 tests
  were added
- **Confidence in the fix**: high
- **Fix complexity**: low
- **Verification plan**:
  - `pytest dev_scripts_helpers/documentation/test/test_lint_text.py::Test_perform_actions_typ_type`
    still passes, including `test3`'s `typstyle`-installed skip condition

* Solution

- [x] PR1: Add a `helper()` for the shared call-and-compare pattern
  - `helper(self, lines, file_name, expected, *, file_type_override="",
    actions=None)` calls `_perform_actions()` and asserts equality
  - Rewrite `test1`, `test2`, `test3` to call it; keep `test3`'s
    `@pytest.mark.skipif(shutil.which("typstyle") is None, ...)` decorator

---

### [x] Use `hunteuti.capture_sys_calls()` in `Test_process_file_one_shot_with_cc`

* Repo:
- [x] helpers (https://github.com/causify-ai/helpers)
- [ ] umd_classes (https://github.com/gpsaggese/gpsaggese.github.io)

* Problem
- Location: `linters2/test/test_cc_lint.py:1634`
- `helper()` mocks `lcclint.hsystem.system` directly with
  `umock.patch.object(...)` and only checks
  `mock_system.assert_called_once()`
- `capture_sys_calls()` (`helpers/hunit_test_utils.py`) already wraps
  `helpers.hsystem.system` (and `subprocess.run`,
  `helpers.hsystem.system_to_string`), so it is a drop-in replacement here

* Info
- **Type**: cosmetic
- **Reason of the problem**: written before, or without awareness of, the
  shared `capture_sys_calls()` utility
- **Confidence in the fix**: high
- **Fix complexity**: low
- **Verification plan**:
  - `pytest linters2/test/test_cc_lint.py::Test_process_file_one_shot_with_cc`
    still passes (`test1` through `test5`, which all share `helper()`)

* Solution

- [x] PR1: Swap the direct `hsystem.system` mock for `capture_sys_calls()`
  - Replace `umock.patch.object(lcclint.hsystem, "system") as mock_system`
    with `with hunteuti.capture_sys_calls() as sys_calls:` around the same
    call
  - Replace `mock_system.assert_called_once()` with
    `self.assertEqual(len(sys_calls), 1)`
  - Import `helpers.hunit_test_utils as hunteuti` if not already imported

---

### [x] Use `hunteuti.capture_sys_calls()` in `_DockerFlowTestHelper.set_up_test()`

* Repo:
- [x] helpers (https://github.com/causify-ai/helpers)
- [ ] umd_classes (https://github.com/gpsaggese/gpsaggese.github.io)

* Problem
- Location: `helpers/lib_tasks/test/test_lib_tasks_docker_release.py:69`
- `set_up_test()` mocks `helpers.hsystem.system` with a plain
  `umock.patch(...)` `.start()`/`.stop()` patcher, only to suppress real
  system calls; `self.mock_system` is never asserted on anywhere in the file
- `_DockerFlowTestHelper` is the shared base class for every Docker-release
  test in this file, so this fixture runs for all of them
  (`@pytest.mark.need_dev_container`, so verification needs a dev container)

* Info
- **Type**: cosmetic
- **Reason of the problem**: written before, or without awareness of, the
  shared `capture_sys_calls()` utility
- **Confidence in the fix**: high
- **Fix complexity**: medium (touches shared setup for every subclass in
  the file, so it needs a full run of this file's tests, not just one class)
- **Verification plan**:
  - Run this file's tests inside the dev container:
    `invoke docker_cmd --cmd "pytest helpers/lib_tasks/test/test_lib_tasks_docker_release.py -v"`

* Solution

- [x] PR1: Replace the `hsystem.system` patcher with `capture_sys_calls()`
  - In `set_up_test()`, replace
    `self.system_patcher = umock.patch("helpers.hsystem.system")` /
    `self.mock_system = self.system_patcher.start()` with manually entering
    `hunteuti.capture_sys_calls()` (e.g., via `contextlib.ExitStack`, the
    same way the other `.start()`-based patchers in this method work) and
    storing the yielded list as `self.sys_calls`
  - In `tear_down_test()`, exit the context manager instead of calling
    `self.system_patcher.stop()`
  - Import `helpers.hunit_test_utils as hunteuti` if not already imported

---

### [x] Factor common code and use `capture_sys_calls()` in `Test__cleanup_dangling_volumes`

* Repo:
- [x] helpers (https://github.com/causify-ai/helpers)
- [ ] umd_classes (https://github.com/gpsaggese/gpsaggese.github.io)

* Problem
- Location:
  `dev_scripts_helpers/system_tools/test/test_docker_cleanup.py:560`
- `test1`, `test2`, `test3` each repeat
  `with (mock.patch("helpers.hsystem.system_to_string", return_value=...),
  mock.patch("helpers.hsystem.system") as system_mock): ...` and then assert
  on `system_mock` (`assert_not_called()` / `assert_called_once_with(...)`)
- Same root cause and fix shape as the following 3 issues
  (`Test__cleanup_dangling_images`, `Test__cleanup_unused_networks`,
  `Test__cleanup_build_cache`); see this block for the detailed rationale

* Info
- **Type**: cosmetic
- **Reason of the problem**: no shared helper was written, and the two
  separate mocks predate the `capture_sys_calls()` utility
- **Confidence in the fix**: high
- **Fix complexity**: medium
- **Verification plan**:
  - `pytest dev_scripts_helpers/system_tools/test/test_docker_cleanup.py::Test__cleanup_dangling_volumes`
    still passes

* Solution

- [x] PR1: Add a `helper()` using `capture_sys_calls()`
  - `helper(self, list_output, dry_run, expected_cmds)` mocks
    `hsystem.system_to_string` to return `list_output`, wraps the call to
    `_cleanup_dangling_volumes("docker", dry_run=dry_run)` in
    `hunteuti.capture_sys_calls()`, and asserts the captured `system` calls
    (a list of command strings, empty when no removal is expected) match
    `expected_cmds`
  - Rewrite `test1`, `test2`, `test3` to call it

---

### [x] Factor common code and use `capture_sys_calls()` in `Test__cleanup_dangling_images`

* Repo:
- [x] helpers (https://github.com/causify-ai/helpers)
- [ ] umd_classes (https://github.com/gpsaggese/gpsaggese.github.io)

* Problem
- Location:
  `dev_scripts_helpers/system_tools/test/test_docker_cleanup.py:637`
- Same root cause as `Factor common code and use capture_sys_calls() in
  Test__cleanup_dangling_volumes`: `test1`, `test2`, `test3` repeat the same
  two-mock block and assert on `system_mock`

* Info
- **Type**: cosmetic
- **Reason of the problem**: same as the sibling `dangling_volumes` issue
- **Confidence in the fix**: high
- **Fix complexity**: medium
- **Verification plan**:
  - `pytest dev_scripts_helpers/system_tools/test/test_docker_cleanup.py::Test__cleanup_dangling_images`
    still passes

* Solution

- [x] PR1: Add a `helper()` using `capture_sys_calls()`
  - Mirror the `Test__cleanup_dangling_volumes` helper shape for
    `_cleanup_dangling_images()`
  - Rewrite `test1`, `test2`, `test3` to call it

---

### [x] Factor common code and use `capture_sys_calls()` in `Test__cleanup_build_cache`

* Repo:
- [x] helpers (https://github.com/causify-ai/helpers)
- [ ] umd_classes (https://github.com/gpsaggese/gpsaggese.github.io)

* Problem
- Location:
  `dev_scripts_helpers/system_tools/test/test_docker_cleanup.py:765`
- Same root cause as the `dangling_volumes`/`dangling_images` issues above,
  with 3 tests repeating the two-mock block; the `system_to_string` mock
  here is asserted with specific args (e.g.,
  `"container builder status", abort_on_error=False`), which
  `capture_sys_calls()`'s captured `kwargs` dict supports directly

* Info
- **Type**: cosmetic
- **Reason of the problem**: same as the sibling `dangling_volumes` issue
- **Confidence in the fix**: high
- **Fix complexity**: medium
- **Verification plan**:
  - `pytest dev_scripts_helpers/system_tools/test/test_docker_cleanup.py::Test__cleanup_build_cache`
    still passes

* Solution

- [x] PR1: Add a `helper()` using `capture_sys_calls()`
  - Wrap the call to `_cleanup_build_cache()` in `capture_sys_calls()` and
    assert on the captured `system_to_string`/`system` entries (function
    name, args, kwargs) instead of two separate mocks
  - Rewrite `test1`, `test2`, `test3` to call it

---

### [x] Factor common code and use `capture_sys_calls()` in `Test__cleanup_unused_networks`

* Repo:
- [x] helpers (https://github.com/causify-ai/helpers)
- [ ] umd_classes (https://github.com/gpsaggese/gpsaggese.github.io)

* Problem
- Location:
  `dev_scripts_helpers/system_tools/test/test_docker_cleanup.py:714`
- Same root cause as the 3 issues above; `test1` additionally has a comment
  explaining it checks the *most recent* `system_to_string` call
  (`assert_called_with`, not `assert_called_once_with`), since the function
  lists dangling networks before pruning them
- Slightly higher complexity than the sibling classes: the helper must
  preserve the "list then act" call-order distinction using the captured
  calls list (e.g., asserting on `sys_calls[-1]`) instead of losing it

* Info
- **Type**: cosmetic
- **Reason of the problem**: same as the sibling `dangling_volumes` issue
- **Confidence in the fix**: medium (the call-order nuance needs care so the
  rewritten assertion keeps checking the prune call specifically, not just
  "some call happened")
- **Fix complexity**: medium
- **Verification plan**:
  - `pytest dev_scripts_helpers/system_tools/test/test_docker_cleanup.py::Test__cleanup_unused_networks`
    still passes, including the "most recent call" distinction in `test1`

* Solution

- [x] PR1: Add a `helper()` using `capture_sys_calls()`
  - Wrap the call to `_cleanup_unused_networks()` in `capture_sys_calls()`
  - Assert the last captured `system_to_string` call (or none, per test)
    matches the expected command, and that no `system` call was captured
  - Rewrite `test1`, `test2` to call it

---

### [x] Factor out repeated input-file setup in `Test_run_typst_py`

* Repo:
- [x] helpers (https://github.com/causify-ai/helpers)
- [ ] umd_classes (https://github.com/gpsaggese/gpsaggese.github.io)

* Problem
- Location: `dev_scripts_helpers/typst/test/test_run_typst.py:160`
- `test1`, `test2`, `test3`, `test4` (and likely more test methods further
  down the class) each repeat
  `in_file_path = os.path.join(self.get_scratch_space(), "book.typ")` /
  `hio.to_file(in_file_path, "= Test")`, then build a slightly different
  `argv` and mock a different subset of `dshtruty` functions
- Violates `testing.rules.md`'s "Use Helper Methods When You Have Repetitive
  Tests", though the varying mocks per test make a single shared helper
  less clean than in the other TODOs

* Info
- **Type**: cosmetic
- **Reason of the problem**: `_run_main()` was factored out already, but
  the input-file creation was left duplicated in each test method
- **Confidence in the fix**: high
- **Fix complexity**: medium (more test methods to touch than the other
  "factor out" issues, and the mocked functions differ per test, so only
  the input-file setup, not the whole test body, can be shared)
- **Verification plan**:
  - `pytest dev_scripts_helpers/typst/test/test_run_typst.py::Test_run_typst_py`
    still passes for all test methods in the class

* Solution

- [x] PR1: Add a small helper for the repeated input-file setup
  - Add `_write_input_file(self) -> str` (or extend `_run_main()`'s
    docstring-adjacent helper) that creates `book.typ` in the scratch space
    with `"= Test"` and returns its path
  - Update every test method in the class to call it instead of repeating
    the two lines inline

---

### [x] Move regex group comments inline via `re.VERBOSE` in `docker_cleanup.py`

* Repo:
- [x] helpers (https://github.com/causify-ai/helpers)
- [ ] umd_classes (https://github.com/gpsaggese/gpsaggese.github.io)

* Problem
- Location: `dev_scripts_helpers/system_tools/docker_cleanup.py:141`
- `_SYSTEM_DF_ROW_RE` is preceded by a bullet-list comment explaining each
  named group, instead of using `re.VERBOSE` with the comments inline in the
  pattern, per `coding.rules.md`'s "Explain Complex Regex"

* Info
- **Type**: cosmetic
- **Reason of the problem**: the regex was documented above the pattern
  instead of inline with `re.VERBOSE`
- **Confidence in the fix**: medium (mechanical, but a regex behavior change
  must be verified to be a true no-op)
- **Fix complexity**: medium
- **Verification plan**:
  - Add or confirm a unit test for `_parse_docker_system_df()` /
    `_SYSTEM_DF_ROW_RE` covering a normal row and a row with the optional
    `(NN%)` suffix, both before and after the change, to confirm identical
    matches
  - `pytest dev_scripts_helpers/system_tools/test/test_docker_cleanup.py`

* Solution

- [x] PR1: Convert `_SYSTEM_DF_ROW_RE` to a `re.VERBOSE` pattern
  - Move each group's explanation into an inline comment next to that part
    of the pattern, following the `coding.rules.md` example
  - Compile with `re.compile(..., re.VERBOSE)`
  - Remove the now-redundant bullet-list comment above the pattern

---

### [x] Convert Typst character-escaping to a loop with shorter comments

* Repo:
- [x] helpers (https://github.com/causify-ai/helpers)
- [ ] umd_classes (https://github.com/gpsaggese/gpsaggese.github.io)

* Problem
- Location:
  `dev_scripts_helpers/documentation/preprocess_notes.py:104`
  (inside `_replace_backtick_with_color()`'s `typst` branch)
- 7 sequential `escaped_text = escaped_text.replace(a, b)` calls, each
  preceded by its own explanatory comment (one, for `_`, spans 9 lines),
  instead of a `for (in, out) in [...]:` loop like the sibling
  `_process_abbreviations()` function a few lines below
- Each escape has a distinct, load-bearing rationale (e.g., why `_` must be
  escaped unconditionally), so "shorter comments" must not drop the
  reasoning, only compress it

* Info
- **Type**: cosmetic
- **Reason of the problem**: each escape was added incrementally with its
  own long comment instead of being consolidated into a table-like loop
- **Confidence in the fix**: medium (needs care to keep exact escaping
  order and behavior, since Typst escape sequences are order-sensitive,
  e.g. `\` must not itself be re-escaped by a later rule)
- **Fix complexity**: medium
- **Verification plan**:
  - Add a unit test (if missing) for
    `_replace_backtick_with_color(..., output_format="typst")` covering a
    string with `~`, `_`, `<`, `*`, `//`, `#`, `@` all present, asserting
    identical output before and after the refactor
  - `pytest dev_scripts_helpers/documentation/test/`

* Solution

- [x] PR1: Replace the 7 `.replace()` calls with a loop
  - Build a list of `(char, escaped)` pairs in the same order as today
  - Loop `for char, escaped in _TYPST_ESCAPE_CHARS: escaped_text =
    escaped_text.replace(char, escaped)`
  - Keep one short comment per pair (or a single comment block above the
    list) preserving the key "why", condensed from the current multi-line
    explanations

---

### [x] Clarify and apply "Improve test to follow testing.rules.md" in `test_compress_pdf.py`

* Repo:
- [x] helpers (https://github.com/causify-ai/helpers)
- [ ] umd_classes (https://github.com/gpsaggese/gpsaggese.github.io)

* Problem
- Location:
  `dev_scripts_helpers/documentation/test/test_compress_pdf.py:14`
  (file-level TODO, also references a `testing.rules.txt` file that no
  longer exists; the current file is `.claude/skills/testing.rules.md`)
- The TODO is a generic pointer at the whole file, not a specific line, so
  the concrete violations to fix are not fully specified
- Concrete violations found on review:
  - `Test_compress_pdf_py.test1`/`test2` compare string content with
    `self.assertEqual(actual_content, expected_content)` instead of
    `self.assert_equal()`, per "Always Use `self.assert_equal()` when the
    arguments are strings"
  - `test1` and `test2` each define a local `_fake_*` side-effect function
    and an inline `argv`/mock block with no shared helper, though the
    bodies differ enough (different backends) that full factoring may not
    be worthwhile

* Info
- **Type**: cosmetic
- **Reason of the problem**: file was written before, or without full
  adherence to, `testing.rules.md`
- **Confidence in the fix**: low (the TODO's scope is ambiguous: it is
  unclear whether it means only the concrete `assertEqual`-on-strings fix
  above, or a full pass over every class in the file)
- **Fix complexity**: medium
- **Verification plan**:
  - Get clarification (see below) on the intended scope before starting
  - Whatever scope is chosen: `pytest
    dev_scripts_helpers/documentation/test/test_compress_pdf.py`

* Solution
- **Decision (human, 2026-09-18)**: full `testing.rules.md` compliance pass
  over the whole file, not the minimal scope

- [x] PR1 (full scope): Full `testing.rules.md` compliance pass
  - Replaced `self.assertEqual(actual_content, expected_content)` (and all
    other string-vs-string `assertEqual`) with `self.assert_equal(...)` in
    all 4 classes
  - Checked for `self.check_string()` (none found), piecewise `assertIn()`
    (none found), naming conventions (already compliant), and the
    three-section comment structure (already present)
  - Factored the identical trailing check in `Test_compress_pdf_py.test1`/
    `test2` into a new `_check_output()` helper; left `Test__find_gs_binary`
    and the `_fake_*`/argv-mock bodies unfactored since their setups
    genuinely differ (different candidate-path logic / different backends)
  - Verified: `pytest
    dev_scripts_helpers/documentation/test/test_compress_pdf.py` — all 8
    tests pass across all 4 classes

---

### [ ] Extend `capture_sys_calls()` to mock `subprocess.Popen`, or drop the TODO (`Test__generate_audio_piper.test2`)

* Repo:
- [x] helpers (https://github.com/causify-ai/helpers)
- [ ] umd_classes (https://github.com/gpsaggese/gpsaggese.github.io)

* Problem
- Location:
  `dev_scripts_helpers/documentation/test/test_md_to_speech.py:756`
  (`Test__generate_audio_piper.test2`)
- Mocks `subprocess.Popen` directly, returning a `MagicMock` configured
  with `.communicate()` and `.returncode`, and the TODO itself says to
  switch to `hunteuti.capture_sys_calls()` "once it supports Popen"
- `capture_sys_calls()` (`helpers/hunit_test_utils.py:652`) currently only
  mocks `subprocess.run`, `helpers.hsystem.system`, and
  `helpers.hsystem.system_to_string`; it has no `Popen` support today, so
  this TODO cannot be applied as written without first extending the
  shared test infrastructure
- Same root cause as `Extend capture_sys_calls() to mock subprocess.Popen,
  or drop the TODO (Test__apply_speed_with_ffmpeg.test1)` and
  `... (Test__apply_speed_with_ffmpeg.test3)`; see that pair for the
  detailed rationale and the shared `Popen`-support proposal

* Info
- **Type**: improvement (blocked on shared infra, not a same-file fix)
- **Reason of the problem**: `capture_sys_calls()` was designed around
  fire-and-forget calls (`run`/`system`/`system_to_string`), not the
  stateful `Popen` object protocol (`.communicate()`, `.returncode`,
  per-test configurable output), so it cannot be swapped in without a
  design change to the shared helper
- **Confidence in the fix**: low (depends on a design decision, not just a
  mechanical change)
- **Fix complexity**: high (requires designing and testing a new
  `Popen`-mocking mode in `helpers/hunit_test_utils.py` that is reused by
  all 3 `Popen` call sites, plus regression risk since `capture_sys_calls()`
  is shared infra used elsewhere)
- **Verification plan**:
  - Add a unit test for the new `Popen` support in
    `helpers/test/test_hunit_test_utils.py` (or equivalent), covering
    configurable `communicate()` output and `returncode`
  - `pytest dev_scripts_helpers/documentation/test/test_md_to_speech.py::Test__generate_audio_piper`

* Solution
- **Decision (human, 2026-09-18)**: leave deferred. Do not extend
  `capture_sys_calls()` for `Popen`; this TODO and its 2 siblings below stay
  as documented, deferred debt, not touched in this pass

- [ ] PR1 (if approved): Add `Popen` support to `capture_sys_calls()`
  - Extend the context manager to also patch `subprocess.Popen`, returning
    a configurable fake process object (`communicate()` return value,
    `returncode`) supplied via a new parameter
  - Add a unit test for the new behavior
  - Shared with the other 2 `Popen` TODOs below: do this once, not 3 times

- [ ] PR2 (if approved): Migrate this call site
  - Update `Test__generate_audio_piper.test2` to use
    `hunteuti.capture_sys_calls()` instead of
    `mock.patch("subprocess.Popen", ...)`

---

### [ ] Extend `capture_sys_calls()` to mock `subprocess.Popen`, or drop the TODO (`Test__apply_speed_with_ffmpeg.test1`)

* Repo:
- [x] helpers (https://github.com/causify-ai/helpers)
- [ ] umd_classes (https://github.com/gpsaggese/gpsaggese.github.io)

* Problem
- Location:
  `dev_scripts_helpers/documentation/test/test_md_to_speech.py:789`
  (`Test__apply_speed_with_ffmpeg.test1`)
- Mocks `subprocess.Popen` directly (here just `mock.patch("subprocess.Popen")
  as mock_popen`, asserting `mock_popen.assert_not_called()`), and the TODO
  says to switch to `hunteuti.capture_sys_calls()` "once it supports Popen"
- Same root cause as `Extend capture_sys_calls() to mock subprocess.Popen,
  or drop the TODO (Test__generate_audio_piper.test2)`: `capture_sys_calls()`
  has no `Popen` support today

* Info
- **Type**: improvement (blocked on shared infra, not a same-file fix)
- **Reason of the problem**: same as the sibling `test2` issue above
- **Confidence in the fix**: low (depends on a design decision, not just a
  mechanical change)
- **Fix complexity**: high (shares the same `Popen`-support prerequisite in
  `helpers/hunit_test_utils.py` as the other 2 `Popen` TODOs)
- **Verification plan**:
  - Same shared `Popen`-support unit test as the sibling issues
  - `pytest dev_scripts_helpers/documentation/test/test_md_to_speech.py::Test__apply_speed_with_ffmpeg`

* Solution
- **Decision (human, 2026-09-18)**: leave deferred, same as the sibling
  `Popen` issue above

- [ ] PR1 (if approved): shared with the sibling `Popen` issues, see
  `Extend capture_sys_calls() to mock subprocess.Popen, or drop the TODO
  (Test__generate_audio_piper.test2)`'s PR1; do not duplicate that work

- [ ] PR2 (if approved): Migrate this call site
  - Update `Test__apply_speed_with_ffmpeg.test1` to assert
    `len(sys_calls) == 0` (or equivalent) inside `capture_sys_calls()`
    instead of `mock_popen.assert_not_called()`

---

### [ ] Extend `capture_sys_calls()` to mock `subprocess.Popen`, or drop the TODO (`Test__apply_speed_with_ffmpeg.test3`)

* Repo:
- [x] helpers (https://github.com/causify-ai/helpers)
- [ ] umd_classes (https://github.com/gpsaggese/gpsaggese.github.io)

* Problem
- Location:
  `dev_scripts_helpers/documentation/test/test_md_to_speech.py:851`
  (`Test__apply_speed_with_ffmpeg.test3`)
- Mocks `subprocess.Popen` directly, returning a `MagicMock` configured
  with `.communicate()` and `.returncode`, to test the nonzero-exit-code
  path, and the TODO says to switch to `hunteuti.capture_sys_calls()`
  "once it supports Popen"
- Same root cause as the other 2 `Popen` TODOs above: `capture_sys_calls()`
  has no `Popen` support today

* Info
- **Type**: improvement (blocked on shared infra, not a same-file fix)
- **Reason of the problem**: same as the sibling `test2`/`test1` issues
  above
- **Confidence in the fix**: low (depends on a design decision, not just a
  mechanical change)
- **Fix complexity**: high (shares the same `Popen`-support prerequisite in
  `helpers/hunit_test_utils.py` as the other 2 `Popen` TODOs)
- **Verification plan**:
  - Same shared `Popen`-support unit test as the sibling issues
  - `pytest dev_scripts_helpers/documentation/test/test_md_to_speech.py::Test__apply_speed_with_ffmpeg`

* Solution
- **Decision (human, 2026-09-18)**: leave deferred, same as the sibling
  `Popen` issue above

- [ ] PR1 (if approved): shared with the sibling `Popen` issues, see
  `Extend capture_sys_calls() to mock subprocess.Popen, or drop the TODO
  (Test__generate_audio_piper.test2)`'s PR1; do not duplicate that work

- [ ] PR2 (if approved): Migrate this call site
  - Update `Test__apply_speed_with_ffmpeg.test3` to configure the
    `side_effect`/return value for a nonzero-exit-code `Popen` (once
    `capture_sys_calls()` supports it) and assert `AssertionError` is
    still raised

---

## Result

- Done: 21 of 24 TODOs fixed, in `dev_scripts_helpers/documentation/preprocess_notes.py`,
  `dev_scripts_helpers/documentation/test/test_compress_pdf.py`,
  `dev_scripts_helpers/documentation/test/test_lint_text.py`,
  `dev_scripts_helpers/documentation/test/test_notes_to_pdf.py`,
  `dev_scripts_helpers/download/download_utils.py`,
  `dev_scripts_helpers/download/test/test_process_gsheet_links.py`,
  `dev_scripts_helpers/download/test/test_update_gsheet_links_from_raindrop.py`,
  `dev_scripts_helpers/system_tools/docker_cleanup.py`,
  `dev_scripts_helpers/system_tools/test/test_docker_cleanup.py`,
  `dev_scripts_helpers/typst/test/test_run_typst.py`,
  `helpers/lib_tasks/test/test_lib_tasks_docker_release.py`,
  `helpers/test/test_hparser.py`, `linters2/test/test_cc_lint.py`
  - Fixed via 13 parallel sub-agents, one per non-overlapping file group,
    each following the Problem/Solution write-up above
  - Verified every touched test file with `pytest`: all pass. The
    `helpers/lib_tasks/test/test_lib_tasks_docker_release.py` fix got real
    verification inside the dev container too (`invoke docker_cmd`): 21
    passed, 4 skipped (pre-existing, unrelated skips)
  - `test_compress_pdf.py` got the full `testing.rules.md` compliance pass
    (human decision), not the minimal `assertEqual`-swap scope
  - One sub-agent (`test_process_gsheet_links.py`) initially introduced
    `Optional[...] = None` default parameters on two shared test helpers,
    which conflicts with `coding.rules.md`'s "Minimize Default Values of
    None"; fixed in the verification pass by making `expected` a required
    parameter and passing `None` explicitly at the one call site that needs
    the "skip check" sentinel
  - One sub-agent (`test_lib_tasks_docker_release.py`) accidentally deleted
    4 pre-existing untracked `.log` debug files outside its assigned scope
    while cleaning up after a container run; flagged to the user, not
    restored (they are regenerated debug logs, not source)
- Not done: 3 TODOs deferred, all in
  `dev_scripts_helpers/documentation/test/test_md_to_speech.py`
  (`Test__generate_audio_piper.test2`, `Test__apply_speed_with_ffmpeg.test1`,
  `Test__apply_speed_with_ffmpeg.test3`)
  - Human decision (2026-09-18): do not extend `capture_sys_calls()` with
    `subprocess.Popen` support to unblock these; left as documented,
    deferred debt, per the "Decision" notes on each heading above
- Not committed: all changes are in the working tree only, per instructions
  to never commit without explicit permission
