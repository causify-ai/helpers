"""
Import as:

import helpers.hpytest as hpytest
"""

import logging
import os
import pprint
import re
import shutil
from typing import Any, Dict, List, Optional, Tuple

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


def _pytest_show_artifacts(
    dir_name: str, *, tag: Optional[str] = None
) -> List[str]:
    hdbg.dassert_ne(dir_name, "")
    hdbg.dassert_dir_exists(dir_name)
    cd_cmd = f"cd {dir_name} && "
    # There might be no pytest artifacts.
    abort_on_error = False
    file_names: List[str] = []
    # Find pytest artifacts.
    cmd = 'find . -name ".pytest_cache" -type d'
    _, output_tmp = hsystem.system_to_string(
        cd_cmd + cmd, abort_on_error=abort_on_error
    )
    file_names.extend(output_tmp.split())
    #
    cmd = 'find . -name "__pycache__" -type d'
    _, output_tmp = hsystem.system_to_string(
        cd_cmd + cmd, abort_on_error=abort_on_error
    )
    file_names.extend(output_tmp.split())
    # Find .pyc artifacts.
    cmd = 'find . -name "*.pyc" -type f'
    _, output_tmp = hsystem.system_to_string(
        cd_cmd + cmd, abort_on_error=abort_on_error
    )
    file_names.extend(output_tmp.split())
    # Remove empty lines.
    file_names = hprint.remove_empty_lines(file_names)
    #
    if tag is not None:
        num_files = len(file_names)
        _LOG.info("%s: %d", tag, num_files)
        _LOG.debug("\n%s", hprint.indent("\n".join(file_names)))
    return file_names  # type: ignore


def pytest_clean(dir_name: str, preview: bool = False) -> None:
    """
    Clean pytest artifacts.
    """
    _LOG.warning("Cleaning pytest artifacts")
    hdbg.dassert_ne(dir_name, "")
    hdbg.dassert_dir_exists(dir_name)
    if preview:
        _LOG.warning("Preview only: nothing will be deleted")
    # Show before cleaning.
    file_names = _pytest_show_artifacts(dir_name, tag="Before cleaning")
    # Clean.
    for f in file_names:
        exists = os.path.exists(f)
        _LOG.debug("%s -> exists=%s", f, exists)
        if exists:
            if not preview:
                if os.path.isdir(f):
                    shutil.rmtree(f)
                elif os.path.isfile(f):
                    os.remove(f)
                else:
                    raise ValueError(f"Can't delete {f}")
            else:
                _LOG.debug("rm %s", f)
    # Show after cleaning.
    file_names = _pytest_show_artifacts(dir_name, tag="After cleaning")
    hdbg.dassert_eq(len(file_names), 0)


# #############################################################################
# Parse failed tests.
# #############################################################################


def _parse_github_ci_log(lines: List[str]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Parse a GitHub Actions CI log and strip the per-line step tag.

    Each line of a raw GitHub Actions log is prefixed with a tag like:
    ```
    run_fast_tests / run_tests    UNKNOWN STEP    2026-07-06T17:59:35.1181332Z
    ```
    This function removes the tag from each line, extracting the job tag and
    the timestamps of the first and last line, and detects whether the job
    ran to completion.

    :param lines: raw GitHub Actions log lines with tab-separated tags
    :return:
        - info: dict with:
          - `github_tag`: job tag, e.g., "run_fast_tests"
          - `github_start_timestamp`: timestamp of the first tagged line
          - `github_end_timestamp`: timestamp of the last tagged line
          - `github_completed`: True if the log contains "Post job cleanup"
        - log_lines: the log content lines with the tags removed
    """
    hdbg.dassert_isinstance(lines, list)
    info: Dict[str, Any] = {
        "github_tag": None,
        "github_start_timestamp": None,
        "github_end_timestamp": None,
        "github_completed": False,
    }
    log_lines = []
    # Match a per-line GitHub Actions step tag, e.g.,
    # `run_fast_tests / run_tests\tUNKNOWN STEP\t2026-07-06T17:59:35.1181332Z `,
    # and capture the job tag, the timestamp, and the rest of the line.
    github_ci_log_tag_regex = re.compile(
        r"""
        ^([^\t]+)             # job tag(s)
        \tUNKNOWN\ STEP\t     # separator
        \ufeff?               # optional UTF-8 BOM
        (\S+)                 # timestamp
        \s?                   # optional whitespace
        (.*)$                 # remaining content
        """,
        re.VERBOSE,
    )
    for line in lines:
        m = github_ci_log_tag_regex.match(line)
        if not m:
            log_lines.append(line)
            continue
        tag, timestamp, content = m.groups()
        if info["github_tag"] is None:
            info["github_tag"] = tag.split("/")[0].strip()
        if info["github_start_timestamp"] is None:
            info["github_start_timestamp"] = timestamp
        info["github_end_timestamp"] = timestamp
        if "Post job cleanup" in content:
            info["github_completed"] = True
        log_lines.append(content)
    return info, log_lines


def filter_failed_tests(
    failed_tests: List[str], only_file: bool, only_class: bool
) -> List[str]:
    """
    Filter failed tests down to their file or class name.

    :param failed_tests: list of failed tests, e.g.,
        `oms/broker/ccxt/test/test_ccxt_execution_quality.py::Test_compute_adj_fill_ecdfs::test3`
    :param only_file: return only the file name
    :param only_class: return only the class name
    :return: filtered, deduped, and sorted list of failed tests
    """
    hdbg.dassert_isinstance(failed_tests, list)
    hdbg.dassert_eq(only_file + only_class, 1)
    failed_tests_tmp = []
    for test in failed_tests:
        # E.g.,
        # oms/broker/ccxt/test/test_ccxt_execution_quality.py::Test_compute_adj_fill_ecdfs::test3
        m = re.match(r"(\S+)::(\S+)::\S+$", test)
        hdbg.dassert(m, "Can't parse '%s'", test)
        if only_file:
            failed_tests_tmp.append(m.group(1))
        elif only_class:
            failed_tests_tmp.append(m.group(1) + "::" + m.group(2))
        else:
            raise RuntimeError("Unexpected")
    failed_tests = sorted(list(set(failed_tests_tmp)))
    return failed_tests


def _set_info_field(
    info: Dict[str, Any], key: str, value: Any
) -> Dict[str, Any]:
    """
    Assign `value` to `info[key]`.

    :param info: info dict to update in place
    :param key: field to assign; it must already be declared in `info` so
        that all the recognized fields are known upfront
    :param value: value to assign; if the field was already assigned, the
        new value must match the old one, so that each field is
        effectively set once
    """
    hdbg.dassert_in(key, info, "Unknown info field '%s'", key)
    old_value = info[key]
    if old_value is not None:
        hdbg.dassert_eq(
            old_value,
            value,
            "info['%s'] was already set to '%s', can't overwrite with '%s'",
            key,
            old_value,
            value,
        )
    info[key] = value
    return info


def parse_failed_tests(lines: List[str]) -> Dict[str, Any]:
    """
    Parse the failed tests from the pytest output.

    :param lines: pytest output lines (can be obtained by splitting txt by newline)
    :return: dict with info about the run, see the inline comments on each
        field below
    """
    hdbg.dassert_isinstance(lines, list)
    # Strip the GitHub Actions per-line tags, if any, and merge the extracted
    # job info into the result.
    github_info, lines = _parse_github_ci_log(lines)
    #
    passed_tests = []
    failed_tests = []
    skipped_tests = []
    # From full name of test to duration in secs.
    test_durations: Dict[str, float] = {}
    info: Dict[str, Any] = {
        # Job tag from GitHub or `None` if input is not a GitHub Actions log.
        "github_tag": None,
        # See `_parse_github_ci_log()`.
        "github_start_timestamp": None,
        "github_end_timestamp": None,
        "github_completed": None,
        # True if pytest reached the "test session starts" banner.
        "pytest_started": None,
        # The platform line, like "... -- Python ..., pytest-..., ...".
        "pytest_tag": None,
        # True if the "collected N items" line was printed.
        "pytest_collection_completed": None,
        # List of passed tests, parsed from the log.
        "log_passed_tests": None,
        # List of skipped tests, parsed from the log. When the pytest
        # "short test summary info" section is present, entries are
        # synthetic `path:line_or_reason#i` keys (not real pytest node
        # ids), since that section reports a repeat count and a
        # file[:line] but not the node id. It is used because it is the
        # only place that reports *every* skipped test: tests skipped via
        # `@pytest.mark.skip`/`skipif` are never run, so pytest prints no
        # per-test verbose line (and thus no node id) for them.
        "log_skipped_tests": None,
        # List of failed tests, parsed from the log.
        "log_failed_tests": None,
        # Number of tests collected by pytest.
        "pytest_num_collected": None,
        # Dict mapping test names to their durations in seconds.
        "log_test_durations": None,
        # Number of passed tests from the log.
        "log_num_passed": None,
        # Number of skipped tests.
        "log_num_skipped": None,
        # Number of failed tests from the log.
        "log_num_failed": None,
        # Number of files with failed tests.
        "log_num_failed_files": None,
        # Number of test classes with failed tests.
        "log_num_failed_classes": None,
        # True if pytest reached the final summary line "4 failed, 43 passed in
        # 40.48s".
        "pytest_ended": None,
        # Number of failed tests from the final summary line.
        "pytest_num_failed": None,
        # Number of passed tests from the final summary line.
        "pytest_num_passed": None,
        # Number of skipped tests from the final summary line.
        "pytest_num_skipped": None,
        # Run duration in seconds from the final summary line.
        "pytest_duration_in_secs": None,
    }
    # Test id printed alone on a line, with nothing else, e.g., when a test's
    # own logging (a golden-file "WARNING: ..." message) gets interleaved with
    # the verbose "(duration s) STATUS" tag on the *following* line, so the node
    # id and its status end up on two separate physical lines instead of one:
    # ```
    # helpers/test/test_hunit_test.py::TestCheckDataFrame1::test_check_df_missing3
    # WARNING: Update golden outcome file '.../test_df.txt'(0.11 s) (WARNING: Test was updated) PASSED [ 82%]
    # ```
    bare_test_id_pattern = re.compile(r"^(\S+::\S+)\s*$")
    # Verbose per-test line without a duration, e.g., a plain module-level
    # function test that pytest doesn't time:
    # ```
    # test_foo.py::test_function PASSED                [ 46%]
    # ```
    no_duration_pattern = re.compile(
        r"""
        (\S+::\S+)                  # test path (must contain ::)
        \s+
        (PASSED|FAILED|ERROR|SKIPPED)
        \s+\[
        """,
        re.VERBOSE,
    )
    # Status tag at the end of a line whose leading "test path" token is not a
    # real node id (e.g., a golden-file path glued to the duration with no
    # separating space, as in the interleaved case above). Used together with
    # `pending_test_id` captured from a preceding `bare_test_id_pattern` line.
    status_at_end_pattern = re.compile(
        r"\b(PASSED|FAILED|ERROR|SKIPPED)\s+\[\s*\S*%\]\s*$"
    )
    # Pytest "short test summary info" aggregate skip line, e.g.:
    # ```
    # SKIPPED [1] path/to/test.py:13: reason text
    # SKIPPED [4] path/to/test.py: reason text
    # ```
    # This is the only place that accounts for tests skipped via
    # `@pytest.mark.skip`/`skipif`, since those are never run and so never print
    # a per-test verbose line.
    skipped_summary_pattern = re.compile(
        r"""
        ^SKIPPED\s+
        \[(\d+)\]\s+      # repeat count
        (\S+?)            # file path
        (?::(\d+))?       # optional line number
        :\s               # colon-space before the reason
        (.*)$             # reason
        """,
        re.VERBOSE,
    )
    pending_test_id: Optional[str] = None
    skipped_summary_tests: List[str] = []
    for line in lines:
        _LOG.debug("line=%s", line)
        # Remove ANSI color codes (both ESC-based and bracket notation).
        ansi_color_pattern = re.compile(
            r"""
            \x1b\[        # ESC sequence start
            [0-9;]*       # color codes
            m             # end marker
            |
            \[            # alternative bracket notation
            [0-9;]*       # color codes
            m             # end marker
            """,
            re.VERBOSE,
        )
        line = ansi_color_pattern.sub("", line)
        # Remove other non-printable characters (keep only printable ASCII).
        nonprintable_pattern = re.compile(
            r"""
            [^            # negated character class
            \x20-\x7E     # printable ASCII range
            ]
            """,
            re.VERBOSE,
        )
        line = nonprintable_pattern.sub("", line)
        # Parse:
        # ```
        # ============================= test session starts ==============================
        # ```
        if "== test session starts ==" in line:
            _set_info_field(info, "pytest_started", True)
        # Parse:
        # ```
        # platform linux -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0 -- /venv/bin/python
        # ```
        platform_pattern = re.compile(r"^platform \S+ --.*")
        m = platform_pattern.search(line)
        if m:
            _set_info_field(info, "pytest_tag", m.group(0))
        # Parse:
        # ```
        # collected 3361 items / 156 deselected / 7 skipped / 3205 selected
        # collected 3421 items / 5 skipped
        # ```
        # TODO(ai_gp): Add also information about deselected, skipped, selected
        # (that are optional).
        collected_pattern = re.compile(r"^collected (\d+) items")
        m_collected = collected_pattern.search(line)
        if m_collected:
            _set_info_field(info, "pytest_collection_completed", True)
            _set_info_field(
                info, "pytest_num_collected", int(m_collected.group(1))
            )
        # A line containing only a test id (no status yet): remember it in
        # case the following line's status ends up glued to unrelated text
        # (see `pending_test_id` above).
        m_bare = bare_test_id_pattern.match(line)
        if m_bare:
            pending_test_id = m_bare.group(1)
        # Parse:
        # ```
        # helpers_root/helpers/test/test_hserver.py::Test_hserver1::test_gp1 (0.00 s) PASSED [ 36%]
        # helpers_root/helpers/test/test_hserver.py::Test_hserver1::test_skipped (2.07 s) FAILED [ 2%]
        # ... (0.13 s) (WARNING: Test was updated) PASSED [ 82%]
        # ```
        suffix_pattern = re.compile(
            r"""
            (\S+)                       # test path
            \s\(                        # space and opening paren
            (\S+)\s s                   # duration with "s" suffix
            \)\s                        # closing paren and space
            (?:\(WARNING:[^)]*\)\s)?    # optional golden-file update annotation
            (\S+)                       # status (e.g., FAILED, PASSED, ...)
            """,
            re.VERBOSE,
        )
        m = suffix_pattern.search(line)
        # Parse:
        # ```
        # FAILED oms/broker/ccxt/test/test_ccxt_execution_quality.py::Test_compute_adj_fill_ecdfs::test3 - RuntimeError:
        # ```
        prefix_pattern = re.compile(
            r"""
            ^(\S+)           # status at line start (e.g., FAILED, PASSED, ...)
            \s
            (\S+)            # test path
            \s-              # dash separator
            """,
            re.VERBOSE,
        )
        m2 = prefix_pattern.search(line)
        m3 = no_duration_pattern.search(line)
        # Resolve `(test_name, status)` from whichever pattern matched,
        # preferring the well-formed ones and falling back to `pending_test_id`
        # only when the line's own leading token isn't a real node id.
        test_name = None
        status = None
        duration = None
        if m and "::" in m.group(1):
            test_name, duration, status = m.group(1), m.group(2), m.group(3)
        elif m2:
            status, test_name = m2.group(1), m2.group(2)
        elif m3:
            test_name, status = m3.group(1), m3.group(2)
        elif pending_test_id is not None:
            m4 = status_at_end_pattern.search(line)
            if m4:
                test_name, status = pending_test_id, m4.group(1)
        if test_name is not None:
            pending_test_id = None
            _LOG.debug(
                "line=%s ->\n\ttest_name='%s', status='%s'",
                line,
                test_name,
                status,
            )
            if duration is not None:
                try:
                    test_durations[test_name] = float(duration)
                except ValueError:
                    _LOG.debug(
                        "Could not parse duration='%s' for test='%s'",
                        duration,
                        test_name,
                    )
            if status == "PASSED":
                passed_tests.append(test_name)
            elif status == "SKIPPED":
                skipped_tests.append(test_name)
            elif status in ("FAILED", "ERROR"):
                failed_tests.append(test_name)
            else:
                hdbg.dassert("Invalid status='%s' in line='%s'", status, line)
        # Parse the pytest "short test summary info" aggregate skip lines
        # (see `skipped_summary_pattern` above); this is the only source
        # that accounts for every `@pytest.mark.skip`/`skipif` test, since
        # those never print a per-test verbose line.
        m5 = skipped_summary_pattern.match(line)
        if m5:
            count = int(m5.group(1))
            path = m5.group(2)
            lineno_or_reason = (
                m5.group(3) if m5.group(3) is not None else m5.group(4)
            )
            for i in range(count):
                skipped_summary_tests.append(f"{path}:{lineno_or_reason}#{i}")
        # Parse:
        # ```
        # ============ 11 failed, 917 passed, 113 skipped in 64.57s (0:01:04) ============
        # ======================== 4 failed, 43 passed in 40.48s =========================
        # ```
        summary_pattern = re.compile(
            r"""
            =+\s+                    # leading equals
            (\d+)\s+failed,\s+       # number of failures
            (\d+)\s+passed           # number of passes
            (?:,\s+(\d+)\s+skipped)? # optional skipped count
            .*?                      # any other content
            in\s+([\d.]+)s           # duration in seconds
            """,
            re.VERBOSE,
        )
        m = summary_pattern.search(line)
        if m:
            _set_info_field(info, "pytest_ended", True)
            #
            _set_info_field(info, "pytest_num_failed", int(m.group(1)))
            #
            _set_info_field(info, "pytest_num_passed", int(m.group(2)))
            if m.group(3) is not None:
                _set_info_field(info, "pytest_num_skipped", int(m.group(3)))
            _set_info_field(info, "pytest_duration_in_secs", float(m.group(4)))
    # Set the flags from `None` to `False` now that the loop is done setting
    # each of them at most once.
    for key in ("pytest_started", "pytest_collection_completed", "pytest_ended"):
        if info[key] is None:
            info[key] = False
    #
    val = sorted(list(set(passed_tests)))
    _set_info_field(info, "log_passed_tests", val)
    _set_info_field(info, "log_num_passed", len(val))
    # Prefer the short-summary-derived skip list: it is the only source that
    # accounts for skips pytest never times (and thus never prints a per-test
    # verbose line for), so it is the only one that can match
    # `pytest_num_skipped`. Combining it with `skipped_tests` would
    # double-count, since every skip already appears in the summary too.
    val = (
        sorted(set(skipped_summary_tests))
        if skipped_summary_tests
        else sorted(set(skipped_tests))
    )
    _set_info_field(info, "log_skipped_tests", val)
    _set_info_field(info, "log_num_skipped", len(val))
    #
    val = sorted(list(set(failed_tests)))
    _set_info_field(info, "log_failed_tests", val)
    _set_info_field(info, "log_num_failed", len(val))
    #
    _set_info_field(info, "log_test_durations", test_durations)
    # Compute log_num_failed_classes from the failed test list.
    val = (
        len(filter_failed_tests(failed_tests, only_file=True, only_class=False))
        if failed_tests
        else 0
    )
    _set_info_field(info, "log_num_failed_files", val)
    #
    val = (
        len(filter_failed_tests(failed_tests, only_file=False, only_class=True))
        if failed_tests
        else 0
    )
    _set_info_field(info, "log_num_failed_classes", val)
    # Add GitHub info.
    for key, val in github_info.items():
        _set_info_field(info, key, val)
    # Sanity check.
    # Only assert non-`None` for fields that must be present:
    # - `github_*` (except `github_completed`): only present when parsing a
    #   GitHub Actions log, `None` for a local run.
    # - `pytest_tag`: only set if the "platform ..." line was printed, e.g.
    #   missing if pytest crashed before printing it.
    # - `pytest_num_failed/passed/skipped`, `pytest_duration_in_secs`: only set
    #   if the final summary line was printed, e.g. missing if the run was
    #   killed mid-way or crashed before completing.
    required_fields = (
        "github_completed",
        "pytest_started",
        "pytest_collection_completed",
        "pytest_ended",
        "log_passed_tests",
        "log_skipped_tests",
        "log_failed_tests",
        "log_num_passed",
        "log_num_skipped",
        "log_num_failed",
        "log_num_failed_files",
        "log_num_failed_classes",
    )
    for key in required_fields:
        hdbg.dassert_is_not(info[key], None, "info[%s] was not set", key)
    # Verify consistency between log-level and pytest summary counts.
    if (
        info["pytest_num_passed"] is not None
        and info["log_num_passed"] != info["pytest_num_passed"]
    ):
        _LOG.warning(
            "pytest_num_passed=%s log_num_passed=%s",
            info["pytest_num_passed"],
            info["log_num_passed"],
        )
    if (
        info["pytest_num_skipped"] is not None
        and info["log_num_skipped"] != info["pytest_num_skipped"]
    ):
        _LOG.warning(
            "pytest_num_skipped=%s log_num_skipped=%s",
            info["pytest_num_skipped"],
            info["log_num_skipped"],
        )
    if (
        info["pytest_num_failed"] is not None
        and info["log_num_failed"] != info["pytest_num_failed"]
    ):
        _LOG.warning(
            "pytest_num_failed=%s log_num_failed=%s",
            info["pytest_num_failed"],
            info["log_num_failed"],
        )
    # Check that the sum of passed, failed, and skipped is the total number collected.
    if info["pytest_num_collected"] is not None:
        total_parsed = (
            info["log_num_passed"]
            + info["log_num_failed"]
            + info["log_num_skipped"]
        )
        if total_parsed != info["pytest_num_collected"]:
            _LOG.warning(
                "Total parsed tests=%s (passed=%s + failed=%s + skipped=%s) "
                "does not match collected=%s",
                total_parsed,
                info["log_num_passed"],
                info["log_num_failed"],
                info["log_num_skipped"],
                info["pytest_num_collected"],
            )
    return info


def info_to_comments(info: Dict[str, Any]) -> str:
    """
    Build a short human-readable commentary from a `parse_failed_tests()` dict.

    :param info: dict as returned by `parse_failed_tests()`
    :return: multi-line string with one comment per line, e.g.,
        ```
        Run: GitHub CI (run_fast_tests)
        Pytest completed: True
        Failed: 4/47
        Skipped: 0/47
        ```
    """
    hdbg.dassert_isinstance(info, dict)
    comments = []
    # GitHub CI / local run.
    if info.get("github_tag"):
        comments.append(f"Run: GitHub CI ({info['github_tag']})")
    else:
        comments.append("Run: local")
    # Pytest completed.
    comments.append(f"Pytest completed: {info.get('pytest_ended', False)}")
    # Failed / tot tests and skipped / tot tests.
    # Prefer pytest values (from final summary) over log values (from parsed lines).
    num_passed = info.get("pytest_num_passed") or info.get("log_num_passed") or 0
    num_skipped = (
        info.get("pytest_num_skipped") or info.get("log_num_skipped") or 0
    )
    num_failed = info.get("pytest_num_failed") or info.get("log_num_failed") or 0
    _LOG.debug(hprint.to_str("num_passed num_skipped num_failed"))
    #
    num_total = num_failed + num_passed + num_skipped
    comments.append(f"Passed: {num_passed}/{num_total}")
    comments.append(f"Skipped: {num_skipped}/{num_total}")
    comments.append(f"Failed: {num_failed}/{num_total}")
    return "\n".join(comments)


def info_to_str(info: Dict[str, Any]) -> str:
    """
    Print the parsed test results and summary.

    :param info: dict returned by `parse_failed_tests()`
    """
    txt = []
    txt.append(hprint.frame("Results"))
    # Omit the per-test lists and durations: they are too verbose for a
    # summary report and are available separately via `log_test_durations`.
    keys_to_remove = [
        "log_passed_tests",
        "log_skipped_tests",
        "log_failed_tests",
        "log_test_durations",
    ]
    info_to_print = {k: v for k, v in info.items() if k not in keys_to_remove}
    txt.append(pprint.pformat(info_to_print))
    txt.append(hprint.frame("Summary"))
    txt.append(info_to_comments(info))
    return "\n".join(txt)


# #############################################################################
# Write test reports.
# #############################################################################


def write_passed_tests(info: Dict[str, Any], file_name: str) -> None:
    """
    Write the list of passed tests, one per line, to a file.

    :param info: dict as returned by `parse_failed_tests()`
    :param file_name: file to write the passed tests to
    """
    hdbg.dassert_isinstance(info, dict)
    hdbg.dassert_ne(file_name, "")
    hio.to_file(file_name, "\n".join(info["log_passed_tests"]))


def write_skipped_tests(info: Dict[str, Any], file_name: str) -> None:
    """
    Write the list of skipped tests, one per line, to a file.

    :param info: dict as returned by `parse_failed_tests()`
    :param file_name: file to write the skipped tests to
    """
    hdbg.dassert_isinstance(info, dict)
    hdbg.dassert_ne(file_name, "")
    hio.to_file(file_name, "\n".join(info["log_skipped_tests"]))


def write_tests_by_duration(info: Dict[str, Any], file_name: str) -> None:
    """
    Write all timed tests ordered by duration, descending, to a file.

    Passed, failed, and skipped tests are all included, since the goal is to
    find the slowest tests regardless of outcome.

    :param info: dict as returned by `parse_failed_tests()`
    :param file_name: file to write the sorted tests to
    """
    hdbg.dassert_isinstance(info, dict)
    hdbg.dassert_ne(file_name, "")
    test_durations = info["log_test_durations"]
    sorted_tests = sorted(
        test_durations.items(), key=lambda kv: kv[1], reverse=True
    )
    lines = [
        f"{duration:.2f} s  {test_name}" for test_name, duration in sorted_tests
    ]
    hio.to_file(file_name, "\n".join(lines))


def _compute_duration_stats(
    test_durations: Dict[str, float], level: str
) -> Dict[str, Dict[str, Any]]:
    """
    Aggregate test durations by file or by class.

    :param test_durations: mapping from full test name to duration in
        seconds, e.g., `{"a/b.py::TestFoo::test1": 0.12}`
    :param level: aggregation level, either "file" or "class"
    :return: mapping from the aggregation key (a file path for `level="file"`,
        or `file::class` for `level="class"`) to a dict with `count`,
        `total_secs`, `mean_secs`, sorted by `total_secs` descending, e.g.,
        ```
        {"a/b.py::TestFoo": {"count": 2, "total_secs": 0.5, "mean_secs": 0.25}}
        ```
    """
    hdbg.dassert_in(level, ("file", "class"), "Invalid aggregation level")
    # Group durations by the requested key.
    durations_by_key: Dict[str, List[float]] = {}
    for test_name, duration in test_durations.items():
        parts = test_name.split("::")
        key = parts[0] if level == "file" else "::".join(parts[:-1])
        durations_by_key.setdefault(key, []).append(duration)
    # Compute count / total / mean for each key.
    stats = {
        key: {
            "count": len(durations_),
            "total_secs": sum(durations_),
            "mean_secs": sum(durations_) / len(durations_),
        }
        for key, durations_ in durations_by_key.items()
    }
    stats = dict(
        sorted(stats.items(), key=lambda kv: kv[1]["total_secs"], reverse=True)
    )
    return stats


def compute_duration_stats_by_file(
    info: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """
    Aggregate test durations by file, sorted by total duration descending.

    :param info: dict as returned by `parse_failed_tests()`
    :return: see `_compute_duration_stats()`
    """
    hdbg.dassert_isinstance(info, dict)
    return _compute_duration_stats(info["log_test_durations"], "file")


def compute_duration_stats_by_class(
    info: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """
    Aggregate test durations by class, sorted by total duration descending.

    :param info: dict as returned by `parse_failed_tests()`
    :return: see `_compute_duration_stats()`
    """
    hdbg.dassert_isinstance(info, dict)
    return _compute_duration_stats(info["log_test_durations"], "class")


def write_duration_stats(info: Dict[str, Any], file_name: str) -> None:
    """
    Write test duration statistics, aggregated by file and by class, to a
    file.

    :param info: dict as returned by `parse_failed_tests()`
    :param file_name: file to write the duration statistics to
    """
    hdbg.dassert_isinstance(info, dict)
    hdbg.dassert_ne(file_name, "")
    txt = []
    txt.append(hprint.frame("Duration by file"))
    # TODO(ai_gp): Change the format to be like 'tests: count, total secs'
    # Ranked by decreasing total secs
    for key, stat in compute_duration_stats_by_file(info).items():
        txt.append(f"{stat['total_secs']:.2f} s  {stat['count']} tests  {key}")
    txt.append(hprint.frame("Duration by class"))
    for key, stat in compute_duration_stats_by_class(info).items():
        txt.append(f"{stat['total_secs']:.2f} s  {stat['count']} tests  {key}")
    # TODO(ai_gp): Report the created file in the format tmp.pytest_failed.sorted_class_file.txt
    hio.to_file(file_name, "\n".join(txt))
