"""
Import as:

import helpers.hpytest as hpytest
"""

import csv
import logging
import os
import pprint
import re
import shlex
import shutil
from typing import Any, Dict, List, Optional, Tuple

import pytest

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.htable as htable

_LOG = logging.getLogger(__name__)


# #############################################################################
# pytest_clean
# #############################################################################


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


# Remove ANSI color codes (ESC-based, caret notation, and bare bracket
# notation).
_ANSI_COLOR_PATTERN = re.compile(
    r"""
    (?:\x1b|\^\[) # ESC byte, or caret notation for ESC (some logs render the
                  # ESC byte as visible "^[" text, e.g., "^[[32mPASSED^[[0m"),
                  # followed in both cases by the literal CSI bracket below
    \[            # CSI sequence start
    [0-9;]*       # color codes
    m             # end marker
    |
    \[            # alternative bracket notation (ESC already stripped, only
                  # the bracket remains)
    [0-9;]*       # color codes
    m             # end marker
    """,
    re.VERBOSE,
)
# Remove other non-printable characters (keep only printable ASCII).
_NONPRINTABLE_PATTERN = re.compile(
    r"""
    [^            # negated character class
    \x20-\x7E     # printable ASCII range
    ]
    """,
    re.VERBOSE,
)


def _clean_log_line(line: str) -> str:
    """
    Strip ANSI color codes and other non-printable characters from a raw
    pytest log line.
    """
    line = _ANSI_COLOR_PATTERN.sub("", line)
    line = _NONPRINTABLE_PATTERN.sub("", line)
    return line


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


def parse_test_errors(
    lines: List[str], failed_tests: List[str]
) -> Dict[str, str]:
    """
    Parse the failure reason of each failed test from the pytest log.

    This re-parses the log in a second pass, after `parse_failed_tests()`
    has determined which tests failed, to extract each failed test's
    failure reason.
    The failure reason is the text of its "FAILED <test> - <Error>:" (or "ERROR
    ...") tag, up to, but not including:
    - the next such tag
    - the final summary banner, or
    - the "short test summary info" section (none of which are part of a
      test's own failure reason).

    E.g., given
    ```
    FAILED helpers/test/test_foo.py::Test1::test1 - RuntimeError:
    --------------------------------------------------------------------------------
    ACTUAL vs EXPECTED: Test1.test1
    --------------------------------------------------------------------------------
    ...
    Diff with:
    > ./tmp.diff.sh
    FAILED helpers/test/test_foo.py::Test2::test2 - AssertionError: boom
    ```
    the reason for `Test1.test1` is everything from "RuntimeError:" through
    "> ./tmp.diff.sh", and the reason for `Test2.test2` is just
    "AssertionError: boom".

    :param lines: pytest output lines, same input as `parse_failed_tests()`
    :param failed_tests: failed test names to extract a failure reason for,
        e.g., `info["log_failed_tests"]`
    :return: mapping from failed test name to its parsed failure reason; a
        failed test with no matching tag in the log is omitted
    """
    hdbg.dassert_isinstance(lines, list)
    hdbg.dassert_isinstance(failed_tests, list)
    failed_tests_set = set(failed_tests)
    failed_tag_pattern = re.compile(r"^(?:FAILED|ERROR)\s+(\S+)\s-\s(.*)$")
    summary_banner_pattern = re.compile(r"^=+\s.*\bin\s+([\d.]+)s")
    skipped_summary_pattern = re.compile(r"^SKIPPED\s+\[\d+\]\s+\S")
    test_errors: Dict[str, str] = {}
    current_test: Optional[str] = None
    current_lines: List[str] = []
    for raw_line in lines:
        line = _clean_log_line(raw_line)
        m_failed_tag = failed_tag_pattern.match(line)
        if m_failed_tag is not None:
            # Any well-formed tag line ends whatever reason is currently
            # being accumulated, whether or not it belongs to a tracked
            # failed test, so an untracked tag never gets swallowed into a
            # preceding test's reason.
            if current_test is not None:
                test_errors[current_test] = "\n".join(current_lines).strip("\n")
                current_test = None
                current_lines = []
            if (
                "::" in m_failed_tag.group(1)
                and m_failed_tag.group(1) in failed_tests_set
            ):
                current_test = m_failed_tag.group(1)
                current_lines = [m_failed_tag.group(2)]
        elif current_test is not None and (
            summary_banner_pattern.search(line)
            or skipped_summary_pattern.match(line)
            or "short test summary info" in line
        ):
            test_errors[current_test] = "\n".join(current_lines).strip("\n")
            current_test = None
            current_lines = []
        elif current_test is not None:
            current_lines.append(line)
    if current_test is not None:
        test_errors[current_test] = "\n".join(current_lines).strip("\n")
    return test_errors


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
    updated_tests = []
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
        # synthetic `path[:line]:reason#i` keys (not real pytest node
        # ids), since that section reports a repeat count and a
        # file[:line] plus a reason but not the node id. It is used
        # because it is the only place that reports *every* skipped test:
        # tests skipped via `@pytest.mark.skip`/`skipif` are never run, so
        # pytest prints no per-test verbose line (and thus no node id) for
        # them.
        "log_skipped_tests": None,
        # List of failed tests, parsed from the log.
        "log_failed_tests": None,
        # List of tests whose golden outcome file was updated during the
        # run, parsed from the "(WARNING: Test was updated)" annotation.
        "log_updated_tests": None,
        # Number of tests collected by pytest.
        "pytest_num_collected": None,
        # Number of deselected tests from the collection line (optional).
        "pytest_num_deselected": None,
        # Number of skipped tests at collection (optional).
        "pytest_num_skipped_at_collection": None,
        # Number of selected tests from the collection line (optional).
        "pytest_num_selected": None,
        # Dict mapping test names to their durations in seconds.
        "log_test_durations": None,
        # Dict mapping failed test names to their parsed failure reason,
        # i.e., the text from a "FAILED <test> - <Error>:" tag up to, but
        # not including, the next such tag (or the end of the log).
        "log_test_errors": None,
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
        # Number of tests whose golden outcome file was updated during the
        # run.
        "log_num_updated": None,
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
        line = _clean_log_line(line)
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
        collected_pattern = re.compile(
            r"collected\s+(\d+)\s+items"
            r"(?:\s+/\s+(\d+)\s+deselected)?"
            r"(?:\s+/\s+(\d+)\s+skipped)?"
            r"(?:\s+/\s+(\d+)\s+selected)?"
        )
        m_collected = collected_pattern.search(line)
        if m_collected:
            _set_info_field(info, "pytest_collection_completed", True)
            _set_info_field(
                info, "pytest_num_collected", int(m_collected.group(1))
            )
            if m_collected.group(2) is not None:
                _set_info_field(
                    info,
                    "pytest_num_deselected",
                    int(m_collected.group(2)),
                )
            if m_collected.group(3) is not None:
                _set_info_field(
                    info,
                    "pytest_num_skipped_at_collection",
                    int(m_collected.group(3)),
                )
            if m_collected.group(4) is not None:
                _set_info_field(
                    info,
                    "pytest_num_selected",
                    int(m_collected.group(4)),
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
        # Parse the golden-file update annotation on a per-test result line,
        # e.g., `... (0.13 s) (WARNING: Test was updated) PASSED [ 82%]`; it
        # can appear regardless of which pattern below ends up resolving the
        # test name and status, so it is checked independently on the raw
        # line rather than being tied to `suffix_pattern`.
        updated_annotation_pattern = re.compile(
            r"\(WARNING:\s*Test was updated\)"
        )
        is_updated = bool(updated_annotation_pattern.search(line))
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
        # Parse the pytest "short test summary info" aggregate skip lines
        # (see `skipped_summary_pattern` above); this is the only source
        # that accounts for every `@pytest.mark.skip`/`skipif` test, since
        # those never print a per-test verbose line. Computed upfront so it
        # can also be used below to tell apart a legitimately-handled
        # aggregate line from a genuinely unparseable one.
        m5 = skipped_summary_pattern.match(line)
        # Resolve `(test_name, status)` from whichever pattern matched,
        # preferring the well-formed ones and falling back to `pending_test_id`
        # only when the line's own leading token isn't a real node id.
        test_name = None
        status = None
        duration = None
        if m and "::" in m.group(1):
            test_name, duration, status = m.group(1), m.group(2), m.group(3)
        elif m2 and "::" in m2.group(2):
            # A bare file path (e.g., a collection error like "ERROR
            # test_bar.py - ModuleNotFoundError: ...", with no "::") isn't
            # a per-test node id, so it's deliberately not accepted here
            # (unlike the other statuses, `filter_failed_tests()` requires
            # every failed test to have a `path::class::test` shape, and
            # would raise on a bare file path).
            status, test_name = m2.group(1), m2.group(2)
        elif m3:
            test_name, status = m3.group(1), m3.group(2)
        elif pending_test_id is not None:
            m4 = status_at_end_pattern.search(line)
            if m4:
                test_name, status = pending_test_id, m4.group(1)
        if (
            test_name is None
            and not m5
            and any(
                tag in line for tag in ("PASSED", "FAILED", "SKIPPED", "ERROR")
            )
        ):
            # The line contains a status tag but none of the patterns above
            # matched it, e.g., because the test's own stdout got
            # byte-interleaved with the tag in the captured log (a race
            # between concurrent writers to the same stream), corrupting it
            # beyond reliable parsing (e.g., "test_foo SKIPPEDt) [ 26%]").
            # Flag it instead of silently dropping the test from the count.
            _LOG.warning("Could not parse test status from line='%s'", line)
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
            if is_updated:
                updated_tests.append(test_name)
        # Handle the pytest "short test summary info" aggregate skip lines
        # (`m5` was matched above, alongside the other status patterns).
        if m5:
            count = int(m5.group(1))
            path = m5.group(2)
            lineno = m5.group(3)
            reason = m5.group(4)
            # Always include the reason in the key, even when a line number
            # is present: two distinct skip groups can share the same
            # file:line (e.g., two different `skipif` conditions on nearby
            # lines that pytest attributes to the same line) but have
            # different reasons. Dropping the reason would collide their
            # synthetic keys and undercount the total after dedup via
            # `set()` below.
            location = f"{path}:{lineno}" if lineno is not None else path
            for i in range(count):
                skipped_summary_tests.append(f"{location}:{reason}#{i}")
        # Parse the pytest final summary line, e.g.:
        # ```
        # ============ 11 failed, 917 passed, 113 skipped in 64.57s (0:01:04) ============
        # ======================== 4 failed, 43 passed in 40.48s =========================
        # ============================== 3 passed in 0.05s ===============================
        # ============================== 3 failed in 0.05s ===============================
        # ```
        # Pytest only prints categories with a nonzero count: a clean run's
        # summary is just "N passed" (no "0 failed," prefix) and an
        # all-failing run's is just "N failed" (no "passed" at all). So
        # "failed" and "passed" are each matched independently rather than
        # with one rigid "X failed, Y passed" pattern, and default to 0 (not
        # left unset) when the summary line is present but the category
        # isn't mentioned.
        summary_banner_pattern = re.compile(r"^=+\s.*\bin\s+([\d.]+)s")
        m = summary_banner_pattern.search(line)
        if m:
            m_failed = re.search(r"(\d+)\s+failed\b", line)
            m_passed = re.search(r"(\d+)\s+passed\b", line)
            m_skipped = re.search(r"(\d+)\s+skipped\b", line)
            _set_info_field(info, "pytest_ended", True)
            #
            _set_info_field(
                info,
                "pytest_num_failed",
                int(m_failed.group(1)) if m_failed else 0,
            )
            #
            _set_info_field(
                info,
                "pytest_num_passed",
                int(m_passed.group(1)) if m_passed else 0,
            )
            if m_skipped is not None:
                _set_info_field(
                    info, "pytest_num_skipped", int(m_skipped.group(1))
                )
            _set_info_field(info, "pytest_duration_in_secs", float(m.group(1)))
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
    # Now that the failed tests are known, re-parse the log a second time to
    # extract each one's failure reason.
    test_errors = parse_test_errors(lines, val)
    _set_info_field(info, "log_test_errors", test_errors)
    #
    val = sorted(list(set(updated_tests)))
    _set_info_field(info, "log_updated_tests", val)
    _set_info_field(info, "log_num_updated", len(val))
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
        "log_updated_tests",
        "log_num_passed",
        "log_num_skipped",
        "log_num_failed",
        "log_num_failed_files",
        "log_num_failed_classes",
        "log_num_updated",
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
    # Calculate total duration, preferring the final summary line's duration.
    # Fall back to summing per-test durations when the run didn't complete.
    total_duration = info.get("pytest_duration_in_secs") or 0.0
    if total_duration == 0.0:
        total_duration = sum(
            (info.get("log_test_durations") or {}).values(), 0.0
        )
    info["total_duration"] = total_duration
    return info


def info_to_comments(info: Dict[str, Any]) -> str:
    """
    Build a short human-readable commentary from a `parse_failed_tests()` dict.

    :param info: dict as returned by `parse_failed_tests()`
    :return: multi-line string with one comment per line, e.g.,
        ```
        Run: GitHub CI (run_fast_tests)
        Pytest completed: True
        Duration: 40.48 s
        Failed: 4/47
        Skipped: 0/47
        Updated: 0/47
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
    # Total duration.
    # Prefer the final summary line's duration; fall back to summing the
    # per-test durations so the report always has a total even when the run
    # was killed or crashed before printing the final summary.
    duration_in_secs = info.get("pytest_duration_in_secs")
    if duration_in_secs is None:
        duration_in_secs = sum((info.get("log_test_durations") or {}).values())
    comments.append(f"Duration: {duration_in_secs:.2f} s")
    # Failed / tot tests and skipped / tot tests.
    # Prefer pytest values (from final summary) over log values (from parsed lines).
    num_passed = info.get("pytest_num_passed") or info.get("log_num_passed") or 0
    num_skipped = (
        info.get("pytest_num_skipped") or info.get("log_num_skipped") or 0
    )
    num_failed = info.get("pytest_num_failed") or info.get("log_num_failed") or 0
    num_updated = info.get("log_num_updated") or 0
    _LOG.debug(hprint.to_str("num_passed num_skipped num_failed num_updated"))
    #
    num_total = num_failed + num_passed + num_skipped
    # Align the labels and numerators so that the numbers line up across
    # lines (e.g., "Passed:  43/47" / "Skipped:  0/47").
    labels_and_values = [
        ("Passed", num_passed),
        ("Skipped", num_skipped),
        ("Failed", num_failed),
        ("Updated", num_updated),
    ]
    table_data = [
        [label, f"{value}/{num_total}"] for label, value in labels_and_values
    ]
    table_obj = htable.Table(table_data, ["Label", "Count"])
    # Extract just the data rows (skip header and separator).
    for line in str(table_obj).split("\n")[2:]:
        if line.strip():
            comments.append(line)
    return "\n".join(comments)


def info_to_str(info: Dict[str, Any]) -> str:
    """
    Print the parsed test results and summary.

    :param info: dict returned by `parse_failed_tests()`
    """
    txt = []
    txt.append(hprint.frame("Results"))
    # Omit the per-test lists, durations, and errors: they are too verbose
    # for a summary report and are available separately via
    # `log_test_durations` / `log_test_errors`.
    keys_to_remove = [
        "log_passed_tests",
        "log_skipped_tests",
        "log_failed_tests",
        "log_updated_tests",
        "log_test_durations",
        "log_test_errors",
        "total_duration",
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


def write_failed_tests(info: Dict[str, Any], file_name: str) -> None:
    """
    Write the list of failed tests, one per line, to a file.

    :param info: dict as returned by `parse_failed_tests()`
    :param file_name: file to write the failed tests to
    """
    hdbg.dassert_isinstance(info, dict)
    hdbg.dassert_ne(file_name, "")
    hio.to_file(file_name, "\n".join(info["log_failed_tests"]))


def write_updated_tests(info: Dict[str, Any], file_name: str) -> None:
    """
    Write the list of updated tests, one per line, to a file.

    :param info: dict as returned by `parse_failed_tests()`
    :param file_name: file to write the updated tests to
    """
    hdbg.dassert_isinstance(info, dict)
    hdbg.dassert_ne(file_name, "")
    hio.to_file(file_name, "\n".join(info["log_updated_tests"]))


def write_test_stacktraces(info: Dict[str, Any], file_name: str) -> None:
    """
    Write the failure reason of each failed test, sorted alphabetically, to
    a file.

    Each test is printed in an `hprint.frame()`, followed by its parsed failure
    reason (see `log_test_errors` in `parse_failed_tests()`).

    Failed tests with no parsed failure reason (e.g., the log didn't contain a
    "FAILED <test> - <Error>:" tag for them) are skipped.

    :param info: dict as returned by `parse_failed_tests()`
    :param file_name: file to write the test errors to
    """
    hdbg.dassert_isinstance(info, dict)
    hdbg.dassert_ne(file_name, "")
    test_errors = info["log_test_errors"]
    txt = []
    for test_name in sorted(test_errors.keys()):
        txt.append("\n" + hprint.frame(test_name, char1="/"))
        txt.append(test_errors[test_name])
    hio.to_file(file_name, "\n".join(txt))
    _LOG.debug("Created '%s'", file_name)


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
    # Compute count / total / mean / max for each key.
    stats = {
        key: {
            "count": len(durations_),
            "total_secs": sum(durations_),
            "mean_secs": sum(durations_) / len(durations_),
            "max_secs": max(durations_),
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
    # Build table for file stats.
    file_data = [
        [
            key,
            str(stat["count"]),
            f"{stat['total_secs']:.2f}",
            f"{stat['mean_secs']:.2f}",
            f"{stat['max_secs']:.2f}",
        ]
        for key, stat in compute_duration_stats_by_file(info).items()
    ]
    file_table = htable.Table(
        file_data, ["File", "Count", "Total (secs)", "Mean (secs)", "Max (secs)"]
    )
    txt.extend(str(file_table).split("\n"))
    txt.append(hprint.frame("Duration by class"))
    # Build table for class stats.
    class_data = [
        [
            key,
            str(stat["count"]),
            f"{stat['total_secs']:.2f}",
            f"{stat['mean_secs']:.2f}",
            f"{stat['max_secs']:.2f}",
        ]
        for key, stat in compute_duration_stats_by_class(info).items()
    ]
    class_table = htable.Table(
        class_data,
        ["Class", "Count", "Total (secs)", "Mean (secs)", "Max (secs)"],
    )
    txt.extend(str(class_table).split("\n"))
    hio.to_file(file_name, "\n".join(txt))
    _LOG.debug("Created '%s'", file_name)


def write_repro_script(
    tests: List[str],
    description: str,
    file_name: str,
) -> None:
    """
    Write an executable script that reruns `tests` via `pytest_log`.

    :param tests: tests, classes, or files to pass to `pytest_log`
    :param description: comment describing what `tests` contains (e.g.,
        "failed tests", "failed classes", "failed files")
    :param file_name: name of the script to create
    """
    lines = ["#!/bin/bash -xe"]
    lines.append(f"# {description}")
    if not tests:
        lines.append("# No tests")
    else:
        lines.append("pytest_log " + " ".join(tests) + " $*")
    repro_txt = "\n".join(lines)
    hio.create_executable_script(file_name, repro_txt)
    _LOG.info("Created '%s'", file_name)


# #############################################################################
# Live repro script
# #############################################################################

# TODO(ai_gp): Add explanation of who calls it and when.

# Name of the script incrementally built during a pytest run.
LIVE_REPRO_SCRIPT_FILE_NAME = "tmp.pytest_repro.sh"


def reset_live_repro_script(file_name: str = LIVE_REPRO_SCRIPT_FILE_NAME) -> None:
    """
    Delete and recreate an empty repro script at the start of a pytest session.

    :param file_name: path to the repro script
    """
    hio.delete_file(file_name)
    lines = [
        "#!/bin/bash -xe",
        "# Repro script for failed tests (auto-generated during the pytest run).",
    ]
    hio.create_executable_script(file_name, "\n".join(lines) + "\n")


def append_failed_test_to_live_repro_script(
    nodeid: str, *, file_name: str = LIVE_REPRO_SCRIPT_FILE_NAME
) -> None:
    """
    Append a `pytest_log` command for one failed test to the repro script.

    Avoids duplicates via content checking, as pytest-xdist's master
    may relay a worker's report twice.

    :param nodeid: pytest node ID of the failing test (e.g.,
        'path/to/test.py::TestClass::test_method')
    :param file_name: path to the repro script
    """
    line = f"pytest_log {shlex.quote(nodeid)} $*\n"
    # Skip if already present: pytest-xdist relays each worker's report to
    # the master too, which would otherwise call this a second time for the
    # same test.
    if os.path.exists(file_name):
        content = hio.from_file(file_name)
        if line in content:
            return
    # mode="a" maps to POSIX O_APPEND, so concurrent xdist workers writing
    # different lines to the same file won't interleave/corrupt each other.
    hio.to_file(file_name, line, mode="a")


# #############################################################################
# Multi build
# #############################################################################


# Build configurations: name -> (docker_engine, use_docker_cmd).
BUILD_CONFIG: Dict[str, Tuple[str, bool]] = {
    # Use "docker" as docker_engine, but run outside the container.
    "docker": ("docker", False),
    # Use "apple" as docker_engine, but run outside the container.
    "apple": ("apple", False),
    # Use "docker" and run inside the container.
    "dev_container": ("docker", True),
}


def get_output_file_path(basename: str, *, build_name: str = "") -> str:
    """
    Get output file path with optional build_name encoding in directory structure.

    Creates directory `tmp.pytest_failed.{build_name}/` and stores file inside.
    For example:
    - basename='duration_stats.txt', build_name='apple'
    - Returns: 'tmp.pytest_failed.apple/duration_stats.txt'

    :param basename: Filename (e.g., 'duration_stats.txt')
    :param build_name: Optional build name to create directory
    :return: Full file path
    """
    if build_name:
        dir_name = f"tmp.pytest_failed.{build_name}"
        hio.create_dir(dir_name, incremental=True)
        return os.path.join(dir_name, basename)
    return basename


def get_build_command(tests: List[str], build_name: str) -> str:
    """
    Generate pytest command for a given build and test list.

    :param tests: List of test names to run
    :param build_name: Build name (e.g., 'docker', 'apple', 'dev_container')
    :return: Complete shell command to run tests
    """
    hdbg.dassert_in(build_name, BUILD_CONFIG, "Unknown build name")
    tests_str = " ".join(tests)
    docker_engine, use_docker_cmd = BUILD_CONFIG[build_name]
    if use_docker_cmd:
        cmd = f"export CSFY_DOCKER_ENGINE='docker'; invoke docker_cmd --stage=local -v 1.6.0 --cmd \"pytest_log {tests_str} $*\""
    else:
        cmd = f"export CSFY_DOCKER_ENGINE='{docker_engine}'; pytest_log {tests_str} $*"
    return cmd


# #############################################################################
# _MarkCollectorPlugin
# #############################################################################


class _MarkCollectorPlugin:
    """
    Pytest plugin recording the marks attached to each collected test item.
    """

    def __init__(self) -> None:
        self.collected: List[Dict[str, Any]] = []

    def pytest_collection_modifyitems(self, items: List[Any]) -> None:
        # Mark names that indicate a test is statically skipped, i.e., without
        # evaluating any `skipif` condition.
        skip_mark_names = ("skip", "skipif")
        for item in items:
            mark_names = [marker.name for marker in item.iter_markers()]
            skipped = any(name in skip_mark_names for name in mark_names)
            self.collected.append(
                {
                    "nodeid": item.nodeid,
                    "marks": mark_names,
                    "skipped": skipped,
                }
            )


def collect_test_marks(target_path: str) -> List[Dict[str, Any]]:
    """
    Collect the pytest marks and static skip status of every test under
    `target_path`.

    Runs `pytest --collect-only` with `_MarkCollectorPlugin` so that
    collection happens without any test code actually running.

    :param target_path: file or directory to collect tests from
    :return: one dict per collected test, e.g.
        ```
        [{"nodeid": "helpers/test/test_hio.py::Test1::test1",
          "marks": ["slow"], "skipped": False}]
        ```
    """
    hdbg.dassert_path_exists(target_path)
    collector = _MarkCollectorPlugin()
    exit_code = pytest.main(
        ["--collect-only", "-q", target_path], plugins=[collector]
    )
    hdbg.dassert_in(
        exit_code,
        (pytest.ExitCode.OK, pytest.ExitCode.NO_TESTS_COLLECTED),
        "Pytest collection under '%s' failed with exit code %s",
        target_path,
        exit_code,
    )
    return collector.collected


def marks_to_str(marks_info: List[Dict[str, Any]]) -> str:
    """
    Build a human-readable table of test nodeids, marks, and skip status.

    :param marks_info: list of dicts as returned by `collect_test_marks()`
    :return: table with one row per test, e.g.
        ```
        Test | Marks | Skipped
        helpers/test/test_hio.py::Test1::test1 | slow | False
        ```
    """
    # Build table for marks info.
    table_data = [
        [
            entry["nodeid"],
            ",".join(entry["marks"]) if entry["marks"] else "-",
            str(entry["skipped"]),
        ]
        for entry in marks_info
    ]
    table_obj = htable.Table(table_data, ["Test", "Marks", "Skipped"])
    return str(table_obj)


def write_marks_csv(marks_info: List[Dict[str, Any]], file_name: str) -> None:
    """
    Write `marks_info` to a CSV file with columns `nodeid,marks,skipped`.

    :param marks_info: list of dicts as returned by `collect_test_marks()`
    :param file_name: file to write the CSV report to
    """
    hdbg.dassert_ne(file_name, "")
    with open(file_name, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["nodeid", "marks", "skipped"])
        for entry in marks_info:
            writer.writerow(
                [entry["nodeid"], ";".join(entry["marks"]), entry["skipped"]]
            )
    _LOG.info("Created '%s'", file_name)
