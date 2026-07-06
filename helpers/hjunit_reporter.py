"""
Import as:

import helpers.hjunit_reporter as hjunrepo
"""

import sys

import junitparser

import helpers.hprint as hprint

# #############################################################################
# JUnitReporter
# #############################################################################


class JUnitReporter:
    def __init__(self, xml_file: str):
        self.xml_file = xml_file
        self.xml_data = None
        self.overall_stats = {
            "passed": 0,
            "failed": 0,
            "error": 0,
            "skipped": 0,
            "total_time": 0.0,
            "total_tests": 0,
        }

    def _load(self) -> None:
        """
        Load the JUnit XML file.
        """
        self.xml_data = junitparser.JUnitXml.fromfile(self.xml_file)

    def parse(self):
        """
        Parse the JUnit XML file.
        """
        try:
            self._load()
            # Calculate overall statistics.
            for suite in self.xml_data:
                if isinstance(suite, junitparser.TestSuite):
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
            print(hprint.color_highlight(f"Error parsing XML file: {e}", "red"))
            sys.exit(1)

    def _get_colored_status(self, case: junitparser.TestCase) -> str:
        """
        Get the colored status representation of test case.
        """
        if not case.result or len(case.result) == 0:
            return hprint.color_highlight("PASSED", "green")
        result_type = case.result[0].__class__.__name__
        if result_type == "Failure":
            return hprint.color_highlight("FAILED", "red")
        elif result_type == "Error":
            return hprint.color_highlight("ERROR", "red")
        elif result_type == "Skipped":
            return hprint.color_highlight("SKIPPED", "yellow")
        else:
            return hprint.color_highlight("PASSED", "green")

    def _print_detailed_results(self):
        print(hprint.color_highlight("=" * 70, "bold"))
        print(
            hprint.color_highlight(
                f"collected {self.overall_stats['total_tests']} items", "bold"
            )
        )
        for _, suite in enumerate(self.xml_data):
            if not isinstance(suite, junitparser.TestSuite):
                continue
            # Print suite header.
            print(f"\n{hprint.color_highlight('=' * 70, 'blue')}")
            print(hprint.color_highlight(f"Test: {suite.name}", "bold"))
            print(
                hprint.color_highlight(
                    f"Timestamp: {getattr(suite, 'timestamp', 'Unknown')}",
                    "bold",
                )
            )
            print(hprint.color_highlight("-" * 70, "blue"))
            # Print each test case.
            for case in suite:
                if isinstance(case, junitparser.TestCase):
                    status_display = self._get_colored_status(case)
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
                    hprint.color_highlight(f"{suite_passed} passed", "green")
                )
            if suite.failures and suite.failures > 0:
                summary_parts.append(
                    hprint.color_highlight(f"{suite.failures} failed", "red")
                )
            if suite.errors and suite.errors > 0:
                summary_parts.append(
                    hprint.color_highlight(f"{suite.errors} error", "red")
                )
            if suite.skipped and suite.skipped > 0:
                summary_parts.append(
                    hprint.color_highlight(f"{suite.skipped} skipped", "WARNING")
                )
            suite_summary = (
                ", ".join(summary_parts) if summary_parts else "no tests"
            )
            suite_time = getattr(suite, "time", 0) or 0
            print(
                hprint.color_highlight(
                    f"Summary: {suite_summary} in {suite_time:.3f}s", "INFO"
                )
            )

    def _print_final_summary(self):
        summary_parts = []
        if self.overall_stats["passed"] > 0:
            summary_parts.append(
                hprint.color_highlight(
                    f"{self.overall_stats['passed']} passed", "green"
                )
            )
        if self.overall_stats["failed"] > 0:
            summary_parts.append(
                hprint.color_highlight(
                    f"{self.overall_stats['failed']} failed", "red"
                )
            )
        if self.overall_stats["error"] > 0:
            summary_parts.append(
                hprint.color_highlight(
                    f"{self.overall_stats['error']} error", "red"
                )
            )
        if self.overall_stats["skipped"] > 0:
            summary_parts.append(
                hprint.color_highlight(
                    f"{self.overall_stats['skipped']} skipped", "yellow"
                )
            )
        summary_text = ", ".join(summary_parts) if summary_parts else "no tests"
        time_text = "in " + hprint.color_highlight(
            f"{self.overall_stats['total_time']:.2f}s", "bold"
        )
        # Determine overall status
        if self.overall_stats["failed"] > 0 or self.overall_stats["error"] > 0:
            status_indicator = hprint.color_highlight("FAILED", "red")
        elif (
            self.overall_stats["skipped"] > 0
            and self.overall_stats["passed"] == 0
        ):
            status_indicator = hprint.color_highlight("SKIPPED", "yellow")
        else:
            status_indicator = hprint.color_highlight("PASSED", "green")
        # Print summary.
        print(f"\n{hprint.color_highlight('=' * 70, 'bold')}")
        print(
            hprint.color_highlight(
                f"Summary: {summary_text} {time_text}", "INFO"
            )
        )
        print(hprint.color_highlight(f"Result: {status_indicator}", "INFO"))

    def print_summary(self):
        self._print_detailed_results()
        self._print_final_summary()
