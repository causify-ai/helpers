"""
Import as:

import helpers.hpytest as hpytest
"""

import logging
import os
import re
import shutil
from typing import Any, Dict, List, Optional, Tuple

import helpers.hdbg as hdbg
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
        re.VERBOSE
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


def _set_info_field(info: Dict[str, Any], key: str, value: Any) -> Dict[str, Any]:
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
            old_value, value,
            "info['%s'] was already set to '%s', can't overwrite with '%s'",
            key,
            old_value,
            value,
        )
    info[key] = value
    return info


def parse_failed_tests(
    lines: List[str]
) -> Dict[str, Any]:
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
    failed_tests = []
    skipped_tests = []
    info: Dict[str, Any] = {
        # List of passed tests, parsed from the log.
        "log_passed_tests": None,
        # List of failed tests, parsed from the log.
        "log_failed_tests": None,
        # List of skipped tests, parsed from the log.
        "log_skipped_tests": None,
        # Number of failed tests from the log.
        "log_num_failed": None,
        # Number of passed tests from the log.
        "log_num_passed": None,
        # Number of skipped tests.
        "log_num_skipped": None,
        # Number of files with failed tests.
        "log_num_failed_files": None,
        # Number of test classes with failed tests.
        "log_num_failed_classes": None,
        # True if pytest reached the "test session starts" banner.
        "pytest_started": None,
        # The platform line, like "... -- Python ..., pytest-..., ...".
        "pytest_tag": None,
        # True if the "collected N items" line was printed.
        "pytest_collection_completed": None,
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
        # Job tag from GitHub or `None` if input is not a GitHub Actions log.
        "github_tag": None,
        # See `_parse_github_ci_log()`.
        "github_start_timestamp": None,
        "github_end_timestamp": None,
        "github_completed": None,
    }
    info.update(github_info)
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
            re.VERBOSE
        )
        line = ansi_color_pattern.sub("", line)
        # Remove other non-printable characters (keep only printable ASCII).
        nonprintable_pattern = re.compile(
            r"""
            [^            # negated character class
            \x20-\x7E     # printable ASCII range
            ]
            """,
            re.VERBOSE
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
        collected_pattern = re.compile(r"^collected \d+ items")
        if collected_pattern.search(line):
            _set_info_field(info, "pytest_collection_completed", True)
        # Parse:
        # ```
        # helpers_root/helpers/test/test_hserver.py::Test_hserver1::test_gp1 (0.00 s) PASSED [ 36%]
        # ```

        # Parse:
        # ```
        # FAILED oms/broker/ccxt/test/test_ccxt_execution_quality.py::Test_compute_adj_fill_ecdfs::test3 - RuntimeError:
        # ```
        failed_prefix_pattern = re.compile(
            r"""
            ^(FAILED|ERROR)  # status at line start
            \s
            (\S+)            # test path
            \s-              # dash separator
            """,
            re.VERBOSE
        )
        m = failed_prefix_pattern.search(line)
        if m:
            test_name = m.group(2)
            _LOG.debug("line=%s ->\n\ttest_name='%s'", line, test_name)
            failed_tests.append(test_name)
        # Parse:
        # ```
        # helpers_root/helpers/test/test_hserver.py::Test_hserver1::test_skipped (2.07 s) FAILED [ 2%]
        # ```
        failed_suffix_pattern = re.compile(
            r"""
            (\S+)           # test path
            \s\(            # space and opening paren
            \S+\s s         # duration with "s" suffix
            \)\s            # closing paren and space
            (FAILED|ERROR)  # status
            """,
            re.VERBOSE
        )
        m = failed_suffix_pattern.search(line)
        if m:
            test_name = m.group(1)
            _LOG.debug("line=%s ->\n\ttest_name='%s'", line, test_name)
            failed_tests.append(test_name)
        # Parse:
        # ```
        # helpers_root/helpers/test/test_hserver.py::Test_hserver1::test_skipped (0.00 s) SKIPPED [ 10%]
        # ```
        skipped_pattern = re.compile(
            r"""
            (\S+)         # test path
            \s\(          # space and opening paren
            \S+\s s       # duration with "s" suffix
            \)\s          # closing paren and space
            SKIPPED       # SKIPPED status
            """,
            re.VERBOSE
        )
        m = skipped_pattern.search(line)
        if m:
            test_name = m.group(1)
            _LOG.debug("line=%s ->\n\ttest_name='%s'", line, test_name)
            skipped_tests.append(test_name)
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
            re.VERBOSE
        )
        m = summary_pattern.search(line)
        if m:
            _set_info_field(info, "pytest_ended", True)
            #
            pytest_num_failed = int(m.group(1))
            _set_info_field(info, "pytest_num_failed", pytest_num_failed)
            #
            pytest_num_passed = int(m.group(2))
            _set_info_field(info, "pytest_num_passed", pytest_num_passed)
            if m.group(3) is not None:
                _set_info_field(
                    info, "pytest_num_skipped", int(m.group(3))
                )
            _set_info_field(info, "pytest_duration_in_secs", float(m.group(4)))
    # Normalize the tri-state flags (unset `None` -> `False`) now that the
    # loop is done setting each of them at most once.
    for key in ("pytest_started", "pytest_collection_completed", "pytest_ended"):
        if info[key] is None:
            info[key] = False
    #
    _set_info_field(info, "log_passed_tests", [])
    _set_info_field(info, "log_num_passed", 0)
    #
    failed_tests = sorted(list(set(failed_tests)))
    _set_info_field(info, "log_failed_tests", failed_tests)
    _set_info_field(info, "log_num_failed", len(failed_tests))
    #
    # Compute log_num_failed_classes from the failed test list.
    log_num_failed_files = (
        len(filter_failed_tests(failed_tests, only_file=True, only_class=False))
        if failed_tests
        else 0
    )
    _set_info_field(info, "log_num_failed_files", log_num_failed_files)
    #
    log_num_failed_classes = (
        len(filter_failed_tests(failed_tests, only_file=False, only_class=True))
        if failed_tests
        else 0
    )
    _set_info_field(info, "log_num_failed_classes", log_num_failed_classes)
    #
    skipped_tests = sorted(list(set(skipped_tests)))
    _set_info_field(info, "log_skipped_tests", skipped_tests)
    _set_info_field(info, "log_num_skipped", len(skipped_tests))
    # Sanity check
    # All required fields are set and not None.
    for key in info.keys():
        hdbg.dassert_is_not(info[key], None, "info[%s] was not set", key)
    # Verify consistency between log-level and pytest summary counts.
    if info["log_num_failed"] != len(failed_tests):
        _LOG.warning(
            "log_num_failed=%s len(failed_tests)=%s",
            info["log_num_failed"],
            len(failed_tests),
        )
    if info["pytest_num_failed"] is not None and info["log_num_failed"] != info["pytest_num_failed"]:
        _LOG.warning(
            "pytest_num_failed=%s log_num_failed=%s",
            info["pytest_num_failed"],
            info["log_num_failed"],
        )
    if info["pytest_num_passed"] is not None and info["log_num_passed"] != info["pytest_num_passed"]:
        _LOG.warning(
            "pytest_num_passed=%s log_num_passed=%s",
            info["pytest_num_passed"],
            info["log_num_passed"],
        )
    if info["pytest_num_skipped"] is not None and info["log_num_skipped"] != info["pytest_num_skipped"]:
        _LOG.warning(
            "pytest_num_skipped=%s log_num_skipped=%s",
            info["pytest_num_skipped"],
            info["log_num_skipped"],
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
    num_failed = info.get("pytest_num_failed") or info.get("log_num_failed") or 0
    num_passed = info.get("pytest_num_passed") or info.get("log_num_passed") or 0
    num_skipped = info.get("pytest_num_skipped")
    if num_skipped is None:
        num_skipped = len(info.get("log_skipped_tests") or [])
    num_total = num_failed + num_passed + num_skipped
    comments.append(f"Failed: {num_failed}/{num_total}")
    comments.append(f"Skipped: {num_skipped}/{num_total}")
    return "\n".join(comments)
