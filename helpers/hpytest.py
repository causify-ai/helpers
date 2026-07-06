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


# TODO(ai_gp): use lines: List[str] and return a List[str]
def _parse_github_ci_log(txt: str) -> Tuple[Dict[str, Any], str]:
    """
    Parse a GitHub Actions CI log and strip the per-line step tag.

    Each line of a raw GitHub Actions log is prefixed with a tag like:
    ```
    run_fast_tests / run_tests    UNKNOWN STEP    2026-07-06T17:59:35.1181332Z
    ```
    This function removes the tag from each line, extracting the job tag and
    the timestamps of the first and last line, and detects whether the job
    ran to completion.

    :param txt: raw GitHub Actions log text with tab-separated tags
    :return:
        - info: dict with:
          - `github_tag`: job tag, e.g., "run_fast_tests"
          - `github_start_timestamp`: timestamp of the first tagged line
          - `github_end_timestamp`: timestamp of the last tagged line
          - `github_completed`: True if the log contains "Post job cleanup"
        - log: the log content with the tags removed
    """
    info: Dict[str, Any] = {
        "github_tag": None,
        "github_start_timestamp": None,
        "github_end_timestamp": None,
        "github_completed": False,
    }
    lines = []
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
    for line in txt.split("\n"):
        m = github_ci_log_tag_regex.match(line)
        if not m:
            lines.append(line)
            continue
        tag, timestamp, content = m.groups()
        if info["github_tag"] is None:
            info["github_tag"] = tag.split("/")[0].strip()
        if info["github_start_timestamp"] is None:
            info["github_start_timestamp"] = timestamp
        info["github_end_timestamp"] = timestamp
        if "Post job cleanup" in content:
            info["github_completed"] = True
        lines.append(content)
    log = "\n".join(lines)
    return info, log


# TODO(ai_gp): use lines: List[str] instead of txt
def parse_failed_tests(
    txt: str, only_file: bool, only_class: bool
) -> Dict[str, Any]:
    """
    Parse the failed tests from the pytest output.

    :param only_file: return only the file name
    :param only_class: return only the class name
    :return: dict with:
        - `failed_tests`: list of failed tests
        - `skipped_tests`: list of skipped tests
        - `num_failed`: number of failed tests
        - `num_passed`: number of passed tests
        - `num_skipped_tests`: number of skipped tests
        - `num_failed_files`: number of files with failed tests
        - `num_failed_classes`: number of test classes with failed tests
        - `pytest_started`: True if pytest reached the "test session
          starts" banner
        - `pytest_tag`: the `platform ... -- Python ..., pytest-..., ...`
          line, or `None` if not found
        - `pytest_collection_completed`: True if the "collected N items"
          line was printed
        - `pytest_ended`: True if the final summary line (e.g., "4 failed,
          43 passed in 40.48s") was printed
        - `pytest_reported_failed`: number of failed tests from the final
          summary line, or `None` if not found
        - `pytest_reported_passed`: number of passed tests from the final
          summary line, or `None` if not found
        - `pytest_reported_skipped`: number of skipped tests from the final
          summary line, or `None` if not found
        - `pytest_duration_in_secs`: run duration in seconds from the final
          summary line, or `None` if not found
        - `github_tag`: job tag from `_parse_github_ci_log()`, or `None` if
          `txt` is not a GitHub Actions log
        - `github_start_timestamp`: see `_parse_github_ci_log()`
        - `github_end_timestamp`: see `_parse_github_ci_log()`
        - `github_completed`: see `_parse_github_ci_log()`
    """
    hdbg.dassert_lte(only_file + only_class, 1)
    # Strip the GitHub Actions per-line tags, if any, and merge the extracted
    # job info into the result.
    github_info, txt = _parse_github_ci_log(txt)
    failed_tests = []
    skipped_tests = []
    num_failed = num_passed = num_skipped = 0
    # Initialize the dict with only what needs to have an initial value,
    # otherwise assign it directly.
    info: Dict[str, Any] = {
        "failed_tests": None,
        "skipped_tests": None,
        "num_failed": None,
        "num_passed": None,
        "num_skipped_tests": None,
        "pytest_started": False,
        "pytest_tag": None,
        "pytest_collection_completed": False,
        "pytest_ended": False,
        "pytest_reported_failed": None,
        "pytest_reported_passed": None,
        "pytest_reported_skipped": None,
        "pytest_duration_in_secs": None,
    }
    info.update(github_info)
    for line in txt.split("\n"):
        _LOG.debug("line=%s", line)
        # Remove ANSI color codes (both ESC-based and bracket notation).
        line = re.sub(r"\x1b\[[0-9;]*m|\[[0-9;]*m", "", line)
        # Remove other non-printable characters.
        line = re.sub(r"[^\x20-\x7E]", "", line)
        # FAILED oms/broker/ccxt/test/test_ccxt_execution_quality.py::Test_compute_adj_fill_ecdfs::test3 - RuntimeError:
        m = re.search(r"^(FAILED|ERROR) (\S+) -", line)
        if m:
            test_name = m.group(2)
            _LOG.debug("line=%s ->\n\ttest_name='%s'", line, test_name)
            failed_tests.append(test_name)
        # helpers_root/helpers/test/test_hserver.py::Test_hserver1::test_gp1 (0.00 s) PASSED [ 36%]
        m = re.search(r"(\S+) \(\S+ s\) (FAILED|ERROR)", line)
        if m:
            test_name = m.group(1)
            _LOG.debug("line=%s ->\n\ttest_name='%s'", line, test_name)
            failed_tests.append(test_name)
        # helpers_root/helpers/test/test_hserver.py::Test_hserver1::test_skipped (0.00 s) SKIPPED [ 10%]
        m = re.search(r"(\S+) \(\S+ s\) SKIPPED", line)
        if m:
            test_name = m.group(1)
            _LOG.debug("line=%s ->\n\ttest_name='%s'", line, test_name)
            skipped_tests.append(test_name)
        # ============================= test session starts ==============================
        if "test session starts" in line:
            info["pytest_started"] = True
        # platform linux -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0 -- /venv/bin/python
        m = re.search(r"^platform \S+ --.*", line)
        if m:
            info["pytest_tag"] = m.group(0)
        # collected 3361 items / 156 deselected / 7 skipped / 3205 selected
        # collected 3421 items / 5 skipped
        if re.search(r"^collected \d+ items", line):
            info["pytest_collection_completed"] = True
        # ============ 11 failed, 917 passed, 113 skipped in 64.57s (0:01:04) ============
        # ======================== 4 failed, 43 passed in 40.48s =========================
        m = re.search(
            r"=+\s+(\d+)\s+failed,\s+(\d+)\s+passed"
            r"(?:,\s+(\d+)\s+skipped)?.*?in\s+([\d.]+)s",
            line,
        )
        if m:
            num_failed = int(m.group(1))
            num_passed = int(m.group(2))
            info["pytest_ended"] = True
            info["pytest_reported_failed"] = num_failed
            info["pytest_reported_passed"] = num_passed
            if m.group(3) is not None:
                info["pytest_reported_skipped"] = int(m.group(3))
            info["pytest_duration_in_secs"] = float(m.group(4))
    failed_tests = sorted(list(set(failed_tests)))
    skipped_tests = sorted(list(set(skipped_tests)))
    #
    if num_failed and num_passed and num_failed != len(failed_tests):
        _LOG.warning(
            "n_failed=%s len(failed_tests)=%s", num_failed, len(failed_tests)
        )
    # Compute num_failed_classes and num_failed_files from the unfiltered list.
    # TODO(ai_gp): Assign the values to the dict directly instead of using temp
    # vars.
    num_failed_files = len(filter_failed_tests(
        failed_tests, only_file=True, only_class=False
    )) if failed_tests else 0
    num_failed_classes = len(filter_failed_tests(
        failed_tests, only_file=False, only_class=True
    )) if failed_tests else 0
    # Filter, if needed.
    # TODO(ai_gp): Do not filter here, but have the callers to filter.
    if only_file or only_class:
        failed_tests = filter_failed_tests(failed_tests, only_file, only_class)
    info["failed_tests"] = failed_tests
    info["skipped_tests"] = skipped_tests
    info["num_failed"] = num_failed
    info["num_passed"] = num_passed
    info["num_skipped_tests"] = num_skipped
    info["num_failed_files"] = num_failed_files
    info["num_failed_classes"] = num_failed_classes
    return info


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
    hdbg.dassert_lte(only_file + only_class, 1)
    failed_tests_tmp = []
    for test in failed_tests:
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
