"""
Unit tests for pytest_failed.py module.

Tests free-standing functions and end-to-end behavior of the pytest log parser.
"""

import os
from typing import Any

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import dev_scripts_helpers.testing.pytest_failed as dshtpyfa


# #############################################################################
# Test_get_output_filename
# #############################################################################


class Test_get_output_filename(hunitest.TestCase):
    """
    Test _get_output_filename function for output file naming.
    """

    def helper(self, base: str, build_name: str) -> str:
        """
        Test helper for _get_output_filename.

        :param base: Base filename
        :param build_name: Build configuration name
        :return: Generated output filename
        """
        actual = dshtpyfa._get_output_filename(base, build_name=build_name)
        return actual

    def test1(self) -> None:
        """
        Test basic filename without build_name.
        """
        # Prepare inputs.
        base = "tmp.pytest_failed.repro.sh"
        build_name = ""
        # Prepare outputs.
        expected = base
        # Run test.
        actual = self.helper(base, build_name)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test filename with build_name encoding.
        """
        # Prepare inputs.
        base = "tmp.pytest_failed.repro.sh"
        build_name = "apple"
        # Prepare outputs.
        expected = "tmp.pytest_failed.apple.repro.sh"
        # Run test.
        actual = self.helper(base, build_name)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Test with different build names.
        """
        # Prepare inputs.
        base = "tmp.pytest_failed.failed_tests.txt"
        build_names = ["docker", "dev_container"]
        # Run test and check outputs.
        for build_name in build_names:
            actual = self.helper(base, build_name)
            self.assertTrue(actual.endswith(".txt"))
            self.assertIn(build_name, actual)

    def test4(self) -> None:
        """
        Test filename with non-standard base.
        """
        # Prepare inputs.
        base = "custom.output"
        build_name = "docker"
        # Prepare outputs.
        expected = f"{base}.{build_name}"
        # Run test.
        actual = self.helper(base, build_name)
        # Check outputs.
        self.assert_equal(actual, expected)


# #############################################################################
# Test_process_single_file
# #############################################################################


class Test_process_single_file(hunitest.TestCase):
    """
    Test _process_single_file end-to-end parsing of pytest logs.
    """

    def _get_log_content(self) -> str:
        """
        Get pytest log content from file or create minimal one.

        :return: Log file content string
        """
        if os.path.exists("tmp.pytest_multi_build.apple.txt"):
            log_content = hio.from_file("tmp.pytest_multi_build.apple.txt")
        else:
            log_content = """
                ============================= test session starts ==============================
                platform darwin -- Python 3.11.11, pytest-8.3.2, pluggy-1.5.0
                collected 1 item

                test_module.py::TestClass::test_method1 PASSED
                ========================= 1 passed in 0.50s =========================
                """
            log_content = hprint.dedent(log_content)
        return log_content

    def _run_test_in_scratch(
        self,
        log_content: str,
        build_name: str = "",
    ) -> Any:
        """
        Helper to create log file and run process test.

        :param log_content: Content to write to log file
        :param build_name: Optional build name
        :return: Result from _process_single_file
        """
        scratch_dir = self.get_scratch_space()
        log_file = os.path.join(scratch_dir, "test.log.txt")
        hio.to_file(log_file, log_content)
        original_dir = os.getcwd()
        try:
            os.chdir(scratch_dir)
            if build_name:
                result = dshtpyfa._process_single_file(
                    log_file, build_name=build_name
                )
            else:
                result = dshtpyfa._process_single_file(log_file)
            return result
        finally:
            os.chdir(original_dir)

    def test1(self) -> None:
        """
        Test with real pytest log file produces output files.
        """
        # Prepare inputs.
        log_content = self._get_log_content()
        # Run test.
        result = self._run_test_in_scratch(log_content)
        # Check outputs.
        self.assertGreaterEqual(result["num_total"], 0)
        scratch_dir = self.get_scratch_space()
        repro_file = os.path.join(scratch_dir, "tmp.pytest_failed.repro.sh")
        self.assertTrue(os.path.exists(repro_file))
        failed_file = os.path.join(
            scratch_dir, "tmp.pytest_failed.failed_tests.txt"
        )
        self.assertTrue(os.path.exists(failed_file))

    def test2(self) -> None:
        """
        Test with build_name creates properly named output files.
        """
        # Prepare inputs.
        log_content = self._get_log_content()
        build_name = "docker"
        # Run test.
        self._run_test_in_scratch(log_content, build_name=build_name)
        # Check outputs.
        scratch_dir = self.get_scratch_space()
        repro_file = os.path.join(
            scratch_dir, f"tmp.pytest_failed.{build_name}.repro.sh"
        )
        self.assertTrue(os.path.exists(repro_file))
        failed_file = os.path.join(
            scratch_dir, f"tmp.pytest_failed.{build_name}.failed_tests.txt"
        )
        self.assertTrue(os.path.exists(failed_file))

    def test3(self) -> None:
        """
        Test output files are created for all report types.
        """
        # Prepare inputs.
        log_content = self._get_log_content()
        expected_files = [
            "tmp.pytest_failed.repro.sh",
            "tmp.pytest_failed.repro_classes.sh",
            "tmp.pytest_failed.repro_files.sh",
            "tmp.pytest_failed.passed_tests.txt",
            "tmp.pytest_failed.failed_tests.txt",
            "tmp.pytest_failed.skipped_tests.txt",
            "tmp.pytest_failed.updated_tests.txt",
            "tmp.pytest_failed.tests_by_duration.txt",
            "tmp.pytest_failed.duration_stats.txt",
            "tmp.pytest_failed.stacktraces.txt",
        ]
        # Run test.
        self._run_test_in_scratch(log_content)
        # Check outputs: verify all expected files created.
        scratch_dir = self.get_scratch_space()
        for expected_file in expected_files:
            file_path = os.path.join(scratch_dir, expected_file)
            self.assertTrue(os.path.exists(file_path))

    def test4(self) -> None:
        """
        Test dict returned has expected keys.
        """
        # Prepare inputs.
        log_content = self._get_log_content()
        expected_keys = [
            "build",
            "passed",
            "num_passed",
            "num_failed",
            "num_skipped",
            "num_total",
        ]
        # Run test.
        result = self._run_test_in_scratch(log_content)
        # Check outputs.
        for key in expected_keys:
            self.assertIn(key, result)
