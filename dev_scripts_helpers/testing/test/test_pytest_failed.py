"""
Unit tests for pytest_failed.py module.

Tests free-standing functions and end-to-end behavior of the pytest log parser.
"""

import os

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import dev_scripts_helpers.testing.pytest_failed as dshtpyfa


# #############################################################################
# Test_get_output_filename
# #############################################################################


# TODO(ai_gp): /coding.factor_common_code
class Test_get_output_filename(hunitest.TestCase):
    """
    Test _get_output_filename function for output file naming.
    """

    def test1(self) -> None:
        """
        Test basic filename without build_name.
        """
        # Prepare inputs.
        base = "tmp.pytest_failed.repro.sh"
        build_name = ""
        # Run test.
        actual = dshtpyfa._get_output_filename(base, build_name=build_name)
        # Check outputs.
        expected = "tmp.pytest_failed.repro.sh"
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Test filename with build_name encoding.
        """
        # Prepare inputs.
        base = "tmp.pytest_failed.repro.sh"
        build_name = "apple"
        # Run test.
        actual = dshtpyfa._get_output_filename(base, build_name=build_name)
        # Check outputs.
        expected = "tmp.pytest_failed.apple.repro.sh"
        self.assertEqual(actual, expected)

    def test3(self) -> None:
        """
        Test with different build names.
        """
        # Prepare inputs.
        base = "tmp.pytest_failed.failed_tests.txt"
        # Run test and check outputs.
        for build_name in ["docker", "dev_container"]:
            actual = dshtpyfa._get_output_filename(base, build_name=build_name)
            self.assertTrue(actual.endswith(".txt"))
            self.assertIn(build_name, actual)

    def test4(self) -> None:
        """
        Test filename with non-standard base.
        """
        # Prepare inputs.
        base = "custom.output"
        build_name = "docker"
        # Run test.
        actual = dshtpyfa._get_output_filename(base, build_name=build_name)
        # Check outputs.
        expected = "custom.output.docker"
        self.assertEqual(actual, expected)


# #############################################################################
# Test_process_single_file
# #############################################################################


class Test_process_single_file(hunitest.TestCase):
    """
    Test _process_single_file end-to-end parsing of pytest logs.
    """

    def test1(self) -> None:
        """
        Test with real pytest log file produces output files.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        # Use a real pytest log if available, otherwise create minimal one.
        log_file = os.path.join(scratch_dir, "test.log.txt")
        # Read from an existing pytest log if available.
        if os.path.exists("tmp.pytest_multi_build.apple.txt"):
            log_content = hio.from_file("tmp.pytest_multi_build.apple.txt")
        else:
            # Minimal pytest log for testing.
            log_content = """
            ============================= test session starts ==============================
            platform darwin -- Python 3.11.11, pytest-8.3.2, pluggy-1.5.0
            collected 2 items

            test_module.py::TestClass::test_method1 PASSED
            test_module.py::TestClass::test_method2 PASSED
            ========================= 2 passed in 0.50s =========================
            """
            log_content = hprint.dedent(log_content)
        hio.to_file(log_file, log_content)
        # Run test.
        original_dir = os.getcwd()
        try:
            os.chdir(scratch_dir)
            result = dshtpyfa._process_single_file(log_file)
            # Check outputs.
            self.assertGreaterEqual(result["num_total"], 0)
            # Verify output files created.
            self.assertTrue(os.path.exists("tmp.pytest_failed.repro.sh"))
            self.assertTrue(os.path.exists("tmp.pytest_failed.failed_tests.txt"))
        finally:
            os.chdir(original_dir)

    def test2(self) -> None:
        """
        Test with build_name creates properly named output files.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        log_file = os.path.join(scratch_dir, "test.log.txt")
        if os.path.exists("tmp.pytest_multi_build.apple.txt"):
            log_content = hio.from_file("tmp.pytest_multi_build.apple.txt")
        else:
            log_content = """
            ============================= test session starts ==============================
            collected 1 item

            test_module.py::TestClass::test_method1 PASSED
            ========================= 1 passed in 0.50s =========================
            """
            log_content = hprint.dedent(log_content)
        hio.to_file(log_file, log_content)
        # Run test.
        original_dir = os.getcwd()
        try:
            os.chdir(scratch_dir)
            dshtpyfa._process_single_file(log_file, build_name="docker")
            # Check outputs.
            repro_file = "tmp.pytest_failed.docker.repro.sh"
            self.assertTrue(os.path.exists(repro_file))
            failed_file = "tmp.pytest_failed.docker.failed_tests.txt"
            self.assertTrue(os.path.exists(failed_file))
        finally:
            os.chdir(original_dir)

    def test3(self) -> None:
        """
        Test output files are created for all report types.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        log_file = os.path.join(scratch_dir, "test.log.txt")
        if os.path.exists("tmp.pytest_multi_build.apple.txt"):
            log_content = hio.from_file("tmp.pytest_multi_build.apple.txt")
        else:
            log_content = """
            ============================= test session starts ==============================
            collected 1 item

            test_module.py::TestClass::test_method1 PASSED
            ========================= 1 passed in 0.50s =========================
            """
            log_content = hprint.dedent(log_content)
        hio.to_file(log_file, log_content)
        # Run test.
        original_dir = os.getcwd()
        try:
            os.chdir(scratch_dir)
            dshtpyfa._process_single_file(log_file)
            # Check outputs - verify all expected files created.
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
            for expected_file in expected_files:
                self.assertTrue(os.path.exists(expected_file))
        finally:
            os.chdir(original_dir)

    def test4(self) -> None:
        """
        Test dict returned has expected keys.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        log_file = os.path.join(scratch_dir, "test.log.txt")
        if os.path.exists("tmp.pytest_multi_build.apple.txt"):
            log_content = hio.from_file("tmp.pytest_multi_build.apple.txt")
        else:
            log_content = """
            ============================= test session starts ==============================
            collected 1 item

            test_module.py::TestClass::test_method1 PASSED
            ========================= 1 passed in 0.50s =========================
            """
            log_content = hprint.dedent(log_content)
        hio.to_file(log_file, log_content)
        # Run test.
        original_dir = os.getcwd()
        try:
            os.chdir(scratch_dir)
            result = dshtpyfa._process_single_file(log_file)
            # Check outputs.
            expected_keys = [
                "build",
                "passed",
                "num_passed",
                "num_failed",
                "num_skipped",
                "num_total",
            ]
            for key in expected_keys:
                self.assertIn(key, result)
        finally:
            os.chdir(original_dir)
