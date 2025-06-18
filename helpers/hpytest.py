"""
Import as:

import helpers.hpytest as hpytest
"""

import logging
import os
import shutil
import sys
from typing import List, Optional

from junitparser import JUnitXml, TestCase, TestSuite

import helpers.hdbg as hdbg
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


def _pytest_show_artifacts(dir_name: str, tag: Optional[str] = None) -> List[str]:
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
    file_names = hprint.remove_empty_lines_from_string_list(file_names)
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
# Colors
# #############################################################################


class Colors:
    """
    ANSI color codes for terminal output.
    """

    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    @classmethod
    def disable(cls):
        """
        Disable colors for non-terminal output.
        """
        cls.RED = cls.GREEN = cls.YELLOW = cls.BLUE = ""
        cls.MAGENTA = cls.CYAN = cls.WHITE = cls.BOLD = cls.RESET = ""


# #############################################################################
# JUnitReporter
# #############################################################################


class JUnitReporter:

    def __init__(self, xml_file: str, use_colors: bool = True):
        self.xml_file = xml_file
        self.use_colors = use_colors
        self.xml_data = None
        self.overall_stats = {
            "passed": 0,
            "failed": 0,
            "error": 0,
            "skipped": 0,
            "total_time": 0.0,
            "total_tests": 0,
        }
        if not use_colors or not sys.stdout.isatty():
            Colors.disable()

    def parse(self):
        """
        Parse the JUnit XML file.
        """
        try:
            self.xml_data = JUnitXml.fromfile(self.xml_file)
            # Calculate overall statistics.
            for suite in self.xml_data:
                if isinstance(suite, TestSuite):
                    self.overall_stats["total_time"] += suite.time or 0
                    self.overall_stats["total_tests"] += suite.tests or 0
                    self.overall_stats["passed"] += (
                        (suite.tests or 0)
                        - (suite.failures or 0)
                        - (suite.errors or 0)
                        - (suite.skipped or 0)
                    )
                    self.overall_stats["failed"] += suite.failures or 0
                    self.overall_stats["error"] += suite.errors or 0
                    self.overall_stats["skipped"] += suite.skipped or 0
        except Exception as e:
            print(f"{Colors.RED}Error parsing XML file: {e}{Colors.RESET}")
            sys.exit(1)

    def print_summary(self):
        self.print_detailed_results()
        self.print_final_summary()

    def print_detailed_results(self):
        print(f"{Colors.BOLD}{'=' * 70}")
        print(f"test session starts")
        print(
            f"collected {self.overall_stats['total_tests']} items{Colors.RESET}"
        )
        print()
        for i, suite in enumerate(self.xml_data):
            if not isinstance(suite, TestSuite):
                continue
            # Add divider between test suites.
            if i > 0:
                print(f"\n{Colors.BLUE}{'=' * 70}{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.BLUE}Test: {suite.name}{Colors.RESET}")
            print(
                f"{Colors.BLUE}Timestamp: {getattr(suite, 'timestamp', 'Unknown')}{Colors.RESET}"
            )
            print(f"{Colors.BLUE}{'-' * 70}{Colors.RESET}")
            # Print each test case.
            for case in suite:
                if isinstance(case, TestCase):
                    status_display = self.get_colored_status(case)
                    test_time = getattr(case, "time", 0) or 0
                    print(
                        f"  {case.classname}::{case.name} {status_display} ({test_time:.3f}s)"
                    )
            # Print suite summary.
            suite_passed = (
                (suite.tests or 0)
                - (suite.failures or 0)
                - (suite.errors or 0)
                - (suite.skipped or 0)
            )
            summary_parts = []
            if suite_passed > 0:
                summary_parts.append(
                    f"{Colors.GREEN}{suite_passed} passed{Colors.RESET}"
                )
            if suite.failures and suite.failures > 0:
                summary_parts.append(
                    f"{Colors.RED}{suite.failures} failed{Colors.RESET}"
                )
            if suite.errors and suite.errors > 0:
                summary_parts.append(
                    f"{Colors.MAGENTA}{suite.errors} error{Colors.RESET}"
                )
            if suite.skipped and suite.skipped > 0:
                summary_parts.append(
                    f"{Colors.YELLOW}{suite.skipped} skipped{Colors.RESET}"
                )
            suite_summary = (
                ", ".join(summary_parts) if summary_parts else "no tests"
            )
            suite_time = getattr(suite, "time", 0) or 0
            print(
                f"{Colors.BOLD}Summary: {suite_summary} in {suite_time:.3f}s{Colors.RESET}"
            )

    def print_final_summary(self):
        summary_parts = []
        if self.overall_stats["passed"] > 0:
            summary_parts.append(
                f"{Colors.GREEN}{self.overall_stats['passed']} passed{Colors.RESET}"
            )
        if self.overall_stats["failed"] > 0:
            summary_parts.append(
                f"{Colors.RED}{self.overall_stats['failed']} failed{Colors.RESET}"
            )
        if self.overall_stats["error"] > 0:
            summary_parts.append(
                f"{Colors.MAGENTA}{self.overall_stats['error']} error{Colors.RESET}"
            )
        if self.overall_stats["skipped"] > 0:
            summary_parts.append(
                f"{Colors.YELLOW}{self.overall_stats['skipped']} skipped{Colors.RESET}"
            )
        summary_text = ", ".join(summary_parts) if summary_parts else "no tests"
        time_text = f"in {Colors.BOLD}{self.overall_stats['total_time']:.2f}s{Colors.RESET}"
        # Determine overall status
        if self.overall_stats["failed"] > 0 or self.overall_stats["error"] > 0:
            status_indicator = f"{Colors.RED}{Colors.BOLD}FAILED{Colors.RESET}"
        elif (
            self.overall_stats["skipped"] > 0
            and self.overall_stats["passed"] == 0
        ):
            status_indicator = (
                f"{Colors.YELLOW}{Colors.BOLD}SKIPPED{Colors.RESET}"
            )
        else:
            status_indicator = f"{Colors.GREEN}{Colors.BOLD}PASSED{Colors.RESET}"
        print(f"\n{Colors.BOLD}{'=' * 70}")
        print("Summary:")
        print(f"{summary_text} {time_text}")
        print(f"Result: {status_indicator}{Colors.RESET}")

    def get_colored_status(self, case: TestCase) -> str:
        """
        Get the colored status representation of test case.
        """
        if not case.result or len(case.result) == 0:
            return f"{Colors.GREEN}PASSED{Colors.RESET}"
        result_type = case.result[0].__class__.__name__
        if result_type == "Failure":
            return f"{Colors.RED}FAILED{Colors.RESET}"
        elif result_type == "Error":
            return f"{Colors.MAGENTA}ERROR{Colors.RESET}"
        elif result_type == "Skipped":
            return f"{Colors.YELLOW}SKIPPED{Colors.RESET}"
        else:
            return f"{Colors.GREEN}PASSED{Colors.RESET}"
