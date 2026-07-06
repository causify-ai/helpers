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
    # TODO(ai_gp): Instantiate the dict here and fill it as events are detected
    # instead of the end.
    github_tag = None
    timestamps: List[str] = []
    lines = []
    # Match a per-line GitHub Actions step tag, e.g.,
    # `run_fast_tests / run_tests\tUNKNOWN STEP\t2026-07-06T17:59:35.1181332Z `,
    # and capture the job tag, the timestamp, and the rest of the line.
    # TODO(ai_gp): Use the verbose approach to regex.
    _GITHUB_CI_LOG_TAG_REGEX = re.compile(
        r"^([^\t]+)\tUNKNOWN STEP\t\ufeff?(\S+)\s?(.*)$"
    )
    for line in txt.split("\n"):
        m = _GITHUB_CI_LOG_TAG_REGEX.match(line)
        if not m:
            lines.append(line)
            continue
        tag, timestamp, content = m.groups()
        if github_tag is None:
            github_tag = tag.split("/")[0].strip()
        timestamps.append(timestamp)
        lines.append(content)
    log = "\n".join(lines)
    info: Dict[str, Any] = {
        "github_tag": github_tag,
        "github_start_timestamp": timestamps[0],
        "github_end_timestamp": timestamps[-1],
        "github_completed": "Post job cleanup" in log,
    }
    return info, log


def parse_failed_tests(
    txt: str, only_file: bool, only_class: bool
) -> Tuple[List[str], int, int]:
    """
    Parse the failed tests from the pytest output.

    :param only_file: return only the file name
    :param only_class: return only the class name
    :return:
        - failed_tests: list of failed tests
        - num_failed: number of failed tests
        - num_passed: number of passed tests
    """
    hdbg.dassert_lte(only_file + only_class, 1)
    failed_tests = []
    num_failed = num_passed = 0
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
        # ============ 11 failed, 917 passed, 113 skipped in 64.57s (0:01:04) ============
        # ======================== 4 failed, 43 passed in 40.48s =========================
        m = re.search(r"=+\s+(\d+)\s+failed,\s+(\d+)\s+passed.*", line)
        if m:
            num_failed = int(m.group(1))
            num_passed = int(m.group(2))
    failed_tests = sorted(list(set(failed_tests)))
    #
    if num_failed and num_passed and num_failed != len(failed_tests):
        _LOG.warning(
            "n_failed=%s len(failed_tests)=%s", num_failed, len(failed_tests)
        )
    print(f"Failed tests: {num_failed}/{num_passed}")
    # Filter, if needed.
    if only_file or only_class:
        failed_tests_tmp = []
        for test in failed_tests:
            # oms/broker/ccxt/test/test_ccxt_execution_quality.py::Test_compute_adj_fill_ecdfs::test3
            m = re.match(r"(\S+)::(\S+)::\S+$", test)
            hdbg.dassert(m, f"Can't parse '{test}'")
            if only_file:
                failed_tests_tmp.append(m.group(1))
            elif only_class:
                failed_tests_tmp.append(m.group(1) + "::" + m.group(2))
            else:
                raise RuntimeError("Unexpected")
        failed_tests = sorted(list(set(failed_tests_tmp)))
    return failed_tests, num_failed, num_passed
