"""
Unit tests for pytest_failed_multi_build.py module.

Tests consolidation of failed tests across multiple build configurations.
"""

import os
from typing import Any, Dict, List, Optional, Set

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest
import dev_scripts_helpers.testing.pytest_failed_multi_build as dshtpfmbu


# #############################################################################
# Shared Helper Functions
# #############################################################################


def _setup_build_files(
    test_case: hunitest.TestCase,
    build_name: str,
    file_name: str,
    content: str,
) -> str:
    """
    Setup build directory and file for testing.

    :param test_case: Test case instance
    :param build_name: Build configuration name
    :param file_name: Name of file to create (e.g., "failed_tests.txt", "repro.sh")
    :param content: Content to write to file
    :return: Scratch directory path
    """
    scratch_dir = test_case.get_scratch_space()
    build_dir = os.path.join(scratch_dir, f"tmp.pytest_failed.{build_name}")
    hio.create_dir(build_dir, incremental=True)
    file_path = os.path.join(build_dir, file_name)
    hio.to_file(file_path, content)
    return scratch_dir


# #############################################################################
# Test_read_failed_tests
# #############################################################################


class Test_read_failed_tests(hunitest.TestCase):
    """
    Test `_read_failed_tests` function for reading failed test files.
    """

    def helper(self, build_name: str, content: str, expected: Any = None) -> Any:
        """
        Helper method to run test in scratch directory and check outputs.

        :param build_name: Build configuration name
        :param content: Content to write to failed tests file
        :param expected: Expected output (if provided, runs assertion)
        :return: Result from _read_failed_tests
        """
        scratch_dir = _setup_build_files(self, build_name, "failed_tests.txt", content)
        with hsystem.cd(scratch_dir):
            result = dshtpfmbu._read_failed_tests(build_name)
        if expected is not None:
            self.assert_equal(str(result), str(expected))
        return result

    def test1(self) -> None:
        """
        Test reading failed tests from a file.
        """
        # Prepare inputs.
        build_name = "docker"
        tests = [
            "helpers/test/test_module.py::TestClass::test_method1",
            "helpers/test/test_module.py::TestClass::test_method2",
        ]
        # Run test.
        expected = tests
        self.helper(build_name, "\n".join(tests), expected)

    def test2(self) -> None:
        """
        Test reading empty failed tests file.
        """
        # Prepare inputs.
        build_name = "apple"
        # Run test.
        result = self.helper(build_name, "")
        # Check outputs.
        expected = []
        self.assert_equal(str(result), str(expected))

    def test3(self) -> None:
        """
        Test reading file with whitespace and empty lines.
        """
        # Prepare inputs.
        build_name = "dev_container"
        content = """
            helpers/test/test_module.py::TestClass::test_method1

            helpers/test/test_module.py::TestClass::test_method2
        """
        content = hprint.dedent(content)
        # Run test.
        result = self.helper(build_name, content)
        # Check outputs.
        expected = [
            "helpers/test/test_module.py::TestClass::test_method1",
            "helpers/test/test_module.py::TestClass::test_method2",
        ]
        self.assert_equal(str(result), str(expected))


# #############################################################################
# Test_read_repro_script
# #############################################################################


class Test_read_repro_script(hunitest.TestCase):
    """
    Test _read_repro_script function for reading repro scripts.
    """

    def helper(self, build_name: str, content: str, expected: Optional[str] = None) -> str:
        """
        Helper method to run test in scratch directory and check outputs.

        :param build_name: Build configuration name
        :param content: Content to write to repro file
        :param expected: Expected output (if provided, runs assertion)
        :return: Result from _read_repro_script
        """
        scratch_dir = _setup_build_files(self, build_name, "repro.sh", content)
        with hsystem.cd(scratch_dir):
            result = dshtpfmbu._read_repro_script(build_name)
        if expected is not None:
            self.assert_equal(result, expected)
        return result

    def test1(self) -> None:
        """
        Test reading repro script content.
        """
        # Prepare inputs.
        build_name = "docker"
        content = """
        #!/bin/bash
        pytest helpers/test/test_module.py
        """
        content = hprint.dedent(content)
        # Run test.
        expected = content
        self.helper(build_name, content, expected)


# #############################################################################
# Test_extract_tests_from_repro
# #############################################################################


class Test_extract_tests_from_repro(hunitest.TestCase):
    """
    Test _extract_tests_from_repro function for extracting test names.
    """

    def helper(
        self,
        repro_content: str,
        expected_count: int,
        expected: Optional[Any] = None,
    ) -> Any:
        """
        Test helper for _extract_tests_from_repro.

        :param repro_content: Repro script content
        :param expected_count: Expected number of tests extracted
        :param expected: Expected output (if provided, runs assertion)
        :return: Actual extracted tests
        """
        actual = dshtpfmbu._extract_tests_from_repro(repro_content)
        self.assertEqual(len(actual), expected_count)
        if expected is not None:
            self.assert_equal(str(actual), str(expected))
        return actual

    def test1(self) -> None:
        """
        Test extracting tests from pytest_log command in repro script.
        """
        # Prepare inputs.
        repro_content = """
        #!/bin/bash -xe
        # Repro script for the failed tests
        pytest_log helpers/test/test_module.py::TestClass::test_method1 helpers/test/test_module.py::TestClass::test_method2 $*
        """
        repro_content = hprint.dedent(repro_content)
        # Prepare outputs.
        expected = [
            "helpers/test/test_module.py::TestClass::test_method1",
            "helpers/test/test_module.py::TestClass::test_method2",
        ]
        # Run test.
        self.helper(repro_content, 2, expected)

    def test2(self) -> None:
        """
        Test extracting single test from pytest_log command.
        """
        # Prepare inputs.
        repro_content = """
        #!/bin/bash -xe
        # Repro script
        pytest_log helpers/test/test_module.py::TestClass::test_method1 $*
        """
        repro_content = hprint.dedent(repro_content)
        # Prepare outputs.
        expected = [
            "helpers/test/test_module.py::TestClass::test_method1",
        ]
        # Run test.
        actual = self.helper(repro_content, 1)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test3(self) -> None:
        """
        Test with no pytest_log command.
        """
        # Prepare inputs.
        repro_content = """
        #!/bin/bash
        # Some other script
        echo "hello"
        """
        repro_content = hprint.dedent(repro_content)
        # Run test.
        actual = dshtpfmbu._extract_tests_from_repro(repro_content)
        # Check outputs.
        expected = []
        self.assertEqual(actual, expected)


# #############################################################################
# Test_consolidate_failed_tests
# #############################################################################


class Test_consolidate_failed_tests(hunitest.TestCase):
    """
    Test _consolidate_failed_tests function for consolidating failures.
    """

    def _create_failed_test_files(
        self,
        scratch_dir: str,
        build_tests: Dict[str, list],
    ) -> None:
        """
        Create failed test files for multiple builds.

        :param scratch_dir: Scratch directory path
        :param build_tests: Dict mapping build name to test list
        """
        for build_name, tests in build_tests.items():
            build_dir = os.path.join(
                scratch_dir, f"tmp.pytest_failed.{build_name}"
            )
            hio.create_dir(build_dir, incremental=True)
            failed_file = os.path.join(build_dir, "failed_tests.txt")
            hio.to_file(failed_file, "\n".join(tests))

    def helper(
        self,
        build_names: list,
        build_tests: Dict[str, list],
        expected: Optional[Dict[str, Set[str]]] = None,
    ) -> Dict[str, Set[str]]:
        """
        Helper to create files and run consolidation test.

        :param build_names: List of build names
        :param build_tests: Dict mapping build name to test list
        :param expected: Expected output (if provided, runs assertion)
        :return: Result from _consolidate_failed_tests
        """
        scratch_dir = self.get_scratch_space()
        self._create_failed_test_files(scratch_dir, build_tests)
        with hsystem.cd(scratch_dir):
            result = dshtpfmbu._consolidate_failed_tests(build_names)
        self.assert_equal(str(result), str(expected))
        return result

    def test1(self) -> None:
        """
        Test consolidating failed tests from single build.
        """
        # Prepare inputs.
        build_names = ["docker"]
        build_tests = {
            "docker": ["test_method1", "test_method2"],
        }
        # Prepare outputs.
        expected = {
            "test_method1": {"docker"},
            "test_method2": {"docker"},
        }
        # Run test.
        self.helper(build_names, build_tests, expected)

    def test2(self) -> None:
        """
        Test consolidating tests across multiple builds.
        """
        # Prepare inputs.
        build_names = ["docker", "apple"]
        build_tests = {
            "docker": ["test_method1", "test_method2"],
            "apple": ["test_method2", "test_method3"],
        }
        # Run test.
        expected = {
            "test_method1": {"docker"},
            "test_method2": {"docker", "apple"},
            "test_method3": {"apple"},
        }
        self.helper(build_names, build_tests, expected)


# #############################################################################
# Test_create_consolidated_repro
# #############################################################################


class Test_create_consolidated_repro(hunitest.TestCase):
    """
    Test _create_consolidated_repro function for consolidated scripts.
    """

    def _create_repro_files(
        self,
        scratch_dir: str,
        build_names: list,
    ) -> None:
        """
        Create repro script files for multiple builds.

        :param scratch_dir: Scratch directory path
        :param build_names: List of build names
        """
        for build_name in build_names:
            build_dir = os.path.join(
                scratch_dir, f"tmp.pytest_failed.{build_name}"
            )
            hio.create_dir(build_dir, incremental=True)
            repro_file = os.path.join(build_dir, "repro.sh")
            tests = f"test/test_{build_name}.py::TestClass::test_method"
            # TODO(ai_gp): Use """ and dedent.
            content = f"#!/bin/bash -xe\n# Repro script\npytest_log {tests} $*"
            hio.to_file(repro_file, content)

    def helper(
        self,
        build_names: List[str],
        expected: str,
    ) -> str:
        """
        Helper to create repro files and run consolidation test.

        :param build_names: List of build names
        :param expected: Expected output (if provided, runs assertion)
        :return: Result from _create_consolidated_repro
        """
        scratch_dir = self.get_scratch_space()
        self._create_repro_files(scratch_dir, build_names)
        with hsystem.cd(scratch_dir):
            result = dshtpfmbu._create_consolidated_repro(build_names)
        self.assert_equal(result, expected, dedent=True, fuzzy_match=True)
        return result

    def test1(self) -> None:
        """
        Test creating consolidated repro script for docker and apple builds.
        """
        # Prepare inputs.
        build_names = ["docker", "apple"]
        # Prepare outputs.
        expected = """
        #!/bin/bash
        # Consolidated repro script for multiple builds.

        BUILD_TAG=pytest_multi_build

        # Build: docker
        export CSFY_DOCKER_ENGINE='docker'; pytest_log test/test_docker.py::TestClass::test_method $* 2>&1 | tee tmp.$BUILD_TAG.docker.txt

        # Build: apple
        export CSFY_DOCKER_ENGINE='apple'; pytest_log test/test_apple.py::TestClass::test_method $* 2>&1 | tee tmp.$BUILD_TAG.apple.txt

        """
        # Run test.
        self.helper(build_names, expected)

    def test2(self) -> None:
        """
        Test creating consolidated repro script with dev_container build.
        """
        # Prepare inputs.
        build_names = ["dev_container"]
        # Prepare outputs.
        # Expected: Bash script with dev_container-specific repro command.
        # dev_container uses invoke docker_cmd, docker/apple use plain pytest_log.
        expected = """
        #!/bin/bash
        # Consolidated repro script for multiple builds.

        BUILD_TAG=pytest_multi_build

        # Build: dev_container
        export CSFY_DOCKER_ENGINE='docker'; invoke docker_cmd --stage=local -v 1.6.0 --cmd "pytest_log test/test_dev_container.py::TestClass::test_method $*" 2>&1 | tee tmp.$BUILD_TAG.dev_container.txt

        """
        # Run test.
        self.helper(build_names, expected)


# #############################################################################
# Test_summary_to_str
# #############################################################################


class Test_summary_to_str(hunitest.TestCase):
    """
    Test _summary_to_str function for summary generation.
    """

    def helper(
        self,
        build_names: list,
        test_to_builds: Dict[str, Set[str]],
        expected: str,
    ) -> str:
        """
        Test helper for _summary_to_str and check outputs.

        :param build_names: List of build names
        :param test_to_builds: Dict mapping test names to sets of build names
        :param expected: Expected output (if provided, runs assertion)
        :return: Summary string result
        """
        actual = dshtpfmbu._summary_to_str(build_names, test_to_builds)
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)
        return actual

    def test1(self) -> None:
        """
        Test summary string generation with single build failures.
        """
        # Prepare inputs.
        build_names = ["docker"]
        test_to_builds = {
            "test_method1": {"docker"},
            "test_method2": {"docker"},
        }
        # Prepare outputs.
        expected = """
        ################################################################################
        Failed Tests Summary
        ################################################################################
        Test Name    | Builds |
        ------------ | ------ |
        test_method1 | docker |
        test_method2 | docker |

        Total failing tests: 2
        Across builds: docker
        Tests failing in multiple builds: 0
        """
        # Run test.
        self.helper(build_names, test_to_builds, expected)

    def test2(self) -> None:
        """
        Test summary with cross-build failures.
        """
        # Prepare inputs.
        build_names = ["docker", "apple", "dev_container"]
        test_to_builds = {
            "test_method1": {"docker", "apple"},
            "test_method2": {"docker"},
            "test_method3": {"apple", "dev_container"},
        }
        # Prepare outputs.
        expected = """
        ################################################################################
        Failed Tests Summary
        ################################################################################
        Test Name | Builds |
        ------------ | -------------------- |
        test_method1 | apple, docker |
        test_method2 | docker |
        test_method3 | apple, dev_container |

        Total failing tests: 3
        Across builds: docker, apple, dev_container
        Tests failing in multiple builds: 2
        """
        # Run test.
        self.helper(build_names, test_to_builds, expected)

    def test3(self) -> None:
        """
        Test summary with empty failures.
        """
        # Prepare inputs.
        build_names = ["docker", "apple"]
        test_to_builds = {}
        # Prepare outputs.
        expected = """
        ################################################################################
        Failed Tests Summary
        ################################################################################
        Test Name | Builds |
        --------- | ------ |

        Total failing tests: 0
        Across builds: docker, apple
        Tests failing in multiple builds: 0
        """
        # Run test.
        self.helper(build_names, test_to_builds, expected)


# #############################################################################
# Test_summary_conditional_display
# #############################################################################


class Test_summary_conditional_display(hunitest.TestCase):
    """
    Test that Failed Tests Summary is not shown when there are no failures.
    """

    def test_no_summary_when_no_failures(self) -> None:
        """
        Test that summary is not generated when test_to_builds is empty.
        """
        # Prepare inputs: no failed tests.
        test_to_builds = {}
        # Verify the check works as expected.
        should_show_summary = bool(test_to_builds)
        # Check outputs.
        self.assertFalse(should_show_summary)

    def test_summary_shown_when_failures_exist(self) -> None:
        """
        Test that summary is generated when test_to_builds has failures.
        """
        # Prepare inputs: with failed tests.
        test_to_builds = {
            "test_method1": {"docker"},
        }
        # Verify the check works as expected.
        should_show_summary = bool(test_to_builds)
        # Check outputs.
        self.assertTrue(should_show_summary)


# #############################################################################
# Test_extract_build_stats_missing_pytest_ended
# #############################################################################


class Test_extract_build_stats_missing_pytest_ended(hunitest.TestCase):
    """
    Test _extract_build_stats marks INCOMPLETE when pytest_ended token missing.
    """

    def helper(self, build_name: str, info_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Helper to setup build directory with info.json and extract stats.

        :param build_name: Build configuration name
        :param info_data: Data to write to info.json
        :return: Result from _extract_build_stats
        """
        scratch_dir = self.get_scratch_space()
        build_dir = os.path.join(scratch_dir, f"tmp.pytest_failed.{build_name}")
        hio.create_dir(build_dir, incremental=True)
        info_file = os.path.join(build_dir, "info.json")
        hio.to_json(info_file, info_data)
        with hsystem.cd(scratch_dir):
            result = dshtpfmbu._extract_build_stats(build_name)
        return result

    def test1(self) -> None:
        """
        Test that missing pytest_ended token marks build as INCOMPLETE.
        """
        # Prepare inputs.
        info_data = {
            "pytest_started": "2024-01-01T00:00:00",
            "log_num_passed": 100,
            "log_num_failed": 5,
            "log_num_skipped": 2,
            "pytest_duration_in_secs": 45.2,
        }
        # Run test.
        result = self.helper("dev_container", info_data)
        # Check outputs - should be marked incomplete.
        expected = {
            "build": "dev_container",
            "passed": 100,
            "skipped": 2,
            "failed": 5,
            "total": 107,
            "duration": "45.2s",
            "incomplete": True,
        }
        # TODO(ai_gp): Move to helper.
        self.assert_equal(str(result), str(expected))

    def test2(self) -> None:
        """
        Test that presence of pytest_ended token marks build as COMPLETE.
        """
        # Prepare inputs.
        info_data = {
            "pytest_started": "2024-01-01T00:00:00",
            "pytest_ended": "2024-01-01T00:00:45",
            "log_num_passed": 100,
            "log_num_failed": 0,
            "log_num_skipped": 2,
            "pytest_duration_in_secs": 45.2,
        }
        # Run test.
        result = self.helper("docker", info_data)
        # Check outputs - should NOT be marked incomplete.
        expected = {
            "build": "docker",
            "passed": 100,
            "skipped": 2,
            "failed": 0,
            "total": 102,
            "duration": "45.2s",
            "incomplete": False,
        }
        self.assert_equal(str(result), str(expected))


# #############################################################################
# Test_build_stats_to_str_incomplete_status
# #############################################################################


class Test_build_stats_to_str_incomplete_status(hunitest.TestCase):
    """
    Test _build_stats_to_str displays status correctly with incomplete builds.
    """

    def test1(self) -> None:
        """
        Test that proper status is displayed with incomplete builds.
        Incomplete builds with total=0 show NOT STARTED status.
        """
        # Prepare inputs.
        build_stats = [
            {
                "build": "docker",
                "passed": 235,
                "skipped": 9,
                "failed": 19,
                "total": 263,
                "duration": "45.2s",
                "incomplete": False,
            },
            {
                "build": "apple",
                "passed": 0,
                "skipped": 0,
                "failed": 0,
                "total": 0,
                "duration": "N/A",
                "incomplete": True,
            },
            {
                "build": "dev_container",
                "passed": 240,
                "skipped": 8,
                "failed": 0,
                "total": 248,
                "duration": "50.1s",
                "incomplete": False,
            },
        ]
        # Run test.
        actual = dshtpfmbu._build_stats_to_str(build_stats)
        # Verify colorization is present (ANSI escape codes).
        self.assertIn("\033[", actual)
        # Remove ANSI codes and verify expected content.
        clean_actual = hprint.remove_non_printable_chars(actual)
        expected = """
        ################################################################################
        Build Statistics
        ################################################################################
        Build         | Status              | Passed | Skipped | Failed | Total | Duration |
        ------------- | ------------------- | ------ | ------- | ------ | ----- | -------- |
        docker        | FAIL       | 235    | 9       | 19     | 263   | 45.2s    |
        apple         | NOT STARTED | 0      | 0       | 0      | 0     | N/A      |
        dev_container | PASS       | 240    | 8       | 0      | 248   | 50.1s    |
        """
        self.assert_equal(clean_actual, expected, dedent=True)


# #############################################################################
# Test_build_stats_to_str_colorization
# #############################################################################


class Test_build_stats_to_str_colorization(hunitest.TestCase):
    """
    Test _build_stats_to_str status colorization behavior.
    """

    def _check_colorized_output(
        self,
        build_stats: list,
        expected_status: str,
        *,
        expected: Optional[str] = None,
        dedent: bool = False,
    ) -> None:
        """
        Helper to check that status appears in colorized output.

        :param build_stats: Build statistics list
        :param expected_status: Expected status string (e.g., "PASS", "FAIL")
        :param expected: Expected full output (if provided, uses assert_equal)
        :param dedent: Whether to dedent and strip the expected string
        """
        actual = dshtpfmbu._build_stats_to_str(build_stats)
        # Verify colorization is present (ANSI escape codes).
        self.assertIn("\033[", actual)
        clean_actual = hprint.remove_non_printable_chars(actual)
        # Check that expected status appears in output or compare full output.
        if expected is not None:
            if dedent:
                expected_str = hprint.dedent(expected).strip()
            else:
                expected_str = expected
            self.assert_equal(clean_actual, expected_str)
        else:
            self.assertIn(expected_status, clean_actual)

    def test1(self) -> None:
        """
        Test that PASS status is displayed when no failures.
        """
        # Prepare inputs: build with no failures.
        build_stats = [
            {
                "build": "docker",
                "passed": 368,
                "skipped": 20,
                "failed": 0,
                "total": 388,
                "duration": "11.87s",
                "incomplete": False,
            },
        ]
        expected = """
        ################################################################################
        Build Statistics
        ################################################################################
        Build  | Status        | Passed | Skipped | Failed | Total | Duration |
        ------ | ------------- | ------ | ------- | ------ | ----- | -------- |
        docker | PASS | 368    | 20      | 0      | 388   | 11.87s   |"""
        # Run test.
        self._check_colorized_output(build_stats, "PASS", expected=expected, dedent=True)

    def test2(self) -> None:
        """
        Test that FAIL status is displayed when there are failures.
        """
        # Prepare inputs: build with failures.
        build_stats = [
            {
                "build": "docker",
                "passed": 357,
                "skipped": 20,
                "failed": 11,
                "total": 388,
                "duration": "12.45s",
                "incomplete": False,
            },
        ]
        expected = """
        ################################################################################
        Build Statistics
        ################################################################################
        Build  | Status        | Passed | Skipped | Failed | Total | Duration |
        ------ | ------------- | ------ | ------- | ------ | ----- | -------- |
        docker | FAIL | 357    | 20      | 11     | 388   | 12.45s   |"""
        # Run test.
        self._check_colorized_output(build_stats, "FAIL", expected=expected, dedent=True)

    def test_not_started_status_colorization(self) -> None:
        """
        Test that NOT STARTED status is displayed when no info file exists.
        """
        # Prepare inputs: build with no pytest file (total=0, incomplete=True).
        build_stats = [
            {
                "build": "dev_container",
                "passed": 0,
                "skipped": 0,
                "failed": 0,
                "total": 0,
                "duration": "N/A",
                "incomplete": True,
            },
        ]
        expected = """
        ################################################################################
        Build Statistics
        ################################################################################
        Build         | Status              | Passed | Skipped | Failed | Total | Duration |
        ------------- | ------------------- | ------ | ------- | ------ | ----- | -------- |
        dev_container | NOT STARTED | 0      | 0       | 0      | 0     | N/A      |"""
        # Run test.
        self._check_colorized_output(
            build_stats, "NOT STARTED", expected=expected, dedent=True
        )

    def test_in_progress_status_colorization(self) -> None:
        """
        Test that IN PROGRESS status is displayed when pytest incomplete.
        """
        # Prepare inputs: build running but not finished (incomplete=True, total>0).
        build_stats = [
            {
                "build": "apple",
                "passed": 150,
                "skipped": 5,
                "failed": 0,
                "total": 155,
                "duration": "N/A",
                "incomplete": True,
            },
        ]
        expected = """
        ################################################################################
        Build Statistics
        ################################################################################
        Build | Status               | Passed | Skipped | Failed | Total | Duration |
        ----- | -------------------- | ------ | ------- | ------ | ----- | -------- |
        apple | IN PROGRESS | 150    | 5       | 0      | 155   | N/A      |"""
        # Run test.
        self._check_colorized_output(
            build_stats, "IN PROGRESS", expected=expected, dedent=True
        )

    def test_in_progress_no_tests_yet(self) -> None:
        """
        Test that IN PROGRESS status is displayed even with no tests output yet.
        """
        # Prepare inputs: pytest started but produced no output (incomplete=True, total=0).
        build_stats = [
            {
                "build": "docker",
                "passed": 0,
                "skipped": 0,
                "failed": 0,
                "total": 0,
                "duration": "N/A",
                "incomplete": True,
            },
        ]
        # Prepare outputs.
        expected = """
        ################################################################################
        Build Statistics
        ################################################################################
        Build  | Status              | Passed | Skipped | Failed | Total | Duration |
        ------ | ------------------- | ------ | ------- | ------ | ----- | -------- |
        docker | NOT STARTED | 0      | 0       | 0      | 0     | N/A      |"""
        # Run test.
        self._check_colorized_output(build_stats, "NOT STARTED", expected=expected, dedent=True)


# #############################################################################
# Test_build_stats_to_str_new_status_conditions
# #############################################################################


class Test_build_stats_to_str_new_status_conditions(hunitest.TestCase):
    """
    Test _build_stats_to_str with new status conditions.
    """

    # TODO(ai_gp): Factor out a helper function with a self.assert_equal so
    # that we can check the output of each test.
    def test1(self) -> None:
        """
        Test NOT STARTED status when no pytest file exists.
        Scenario: incomplete=True, total=0 (no info.json file)
        """
        # Prepare inputs.
        build_stats = [
            {
                "build": "docker",
                "passed": 0,
                "skipped": 0,
                "failed": 0,
                "total": 0,
                "duration": "N/A",
                "incomplete": True,
            },
        ]
        # Run test.
        actual = dshtpfmbu._build_stats_to_str(build_stats)
        clean_actual = hprint.remove_non_printable_chars(actual)
        # Check outputs.
        self.assertIn("NOT STARTED", clean_actual)
        self.assertNotIn("IN PROGRESS", clean_actual)

    def test2(self) -> None:
        """
        Test IN PROGRESS status when pytest running but unfinished.
        Scenario: incomplete=True, total>0 (no pytest_ended marker)
        """
        # Prepare inputs.
        build_stats = [
            {
                "build": "apple",
                "passed": 100,
                "skipped": 10,
                "failed": 5,
                "total": 115,
                "duration": "N/A",
                "incomplete": True,
            },
        ]
        # Run test.
        actual = dshtpfmbu._build_stats_to_str(build_stats)
        clean_actual = hprint.remove_non_printable_chars(actual)
        # Check outputs.
        self.assertIn("IN PROGRESS", clean_actual)
        self.assertNotIn("NOT STARTED", clean_actual)

    def test3(self) -> None:
        """
        Test IN PROGRESS status when pytest started but no output yet.
        Scenario: incomplete=True, total=0, but info.json exists (edge case)
        Should be treated as NOT STARTED since total=0.
        """
        # Prepare inputs.
        build_stats = [
            {
                "build": "dev_container",
                "passed": 0,
                "skipped": 0,
                "failed": 0,
                "total": 0,
                "duration": "N/A",
                "incomplete": True,
            },
        ]
        # Run test.
        actual = dshtpfmbu._build_stats_to_str(build_stats)
        clean_actual = hprint.remove_non_printable_chars(actual)
        # Check outputs - total=0 should be NOT STARTED.
        self.assertIn("NOT STARTED", clean_actual)

    def test4(self) -> None:
        """
        Test PASS status when pytest completed with no failures.
        Scenario: incomplete=False, failed=0
        """
        # Prepare inputs.
        build_stats = [
            {
                "build": "docker",
                "passed": 500,
                "skipped": 20,
                "failed": 0,
                "total": 520,
                "duration": "45.2s",
                "incomplete": False,
            },
        ]
        # Run test.
        actual = dshtpfmbu._build_stats_to_str(build_stats)
        clean_actual = hprint.remove_non_printable_chars(actual)
        # Check outputs.
        self.assertIn("PASS", clean_actual)
        self.assertNotIn("FAIL", clean_actual)

    def test5(self) -> None:
        """
        Test FAIL status when pytest completed with failures.
        Scenario: incomplete=False, failed>0
        """
        # Prepare inputs.
        build_stats = [
            {
                "build": "apple",
                "passed": 495,
                "skipped": 20,
                "failed": 5,
                "total": 520,
                "duration": "47.1s",
                "incomplete": False,
            },
        ]
        # Run test.
        actual = dshtpfmbu._build_stats_to_str(build_stats)
        clean_actual = hprint.remove_non_printable_chars(actual)
        # Check outputs.
        self.assertIn("FAIL", clean_actual)
        self.assertNotIn("PASS", clean_actual)

    def test6(self) -> None:
        """
        Test table with multiple builds showing all status types.
        """
        # Prepare inputs.
        build_stats = [
            {
                "build": "docker",
                "passed": 0,
                "skipped": 0,
                "failed": 0,
                "total": 0,
                "duration": "N/A",
                "incomplete": True,
            },
            {
                "build": "apple",
                "passed": 100,
                "skipped": 5,
                "failed": 0,
                "total": 105,
                "duration": "N/A",
                "incomplete": True,
            },
            {
                "build": "dev_container",
                "passed": 520,
                "skipped": 20,
                "failed": 0,
                "total": 540,
                "duration": "48.5s",
                "incomplete": False,
            },
        ]
        # Run test.
        actual = dshtpfmbu._build_stats_to_str(build_stats)
        clean_actual = hprint.remove_non_printable_chars(actual)
        # Check outputs.
        self.assertIn("NOT STARTED", clean_actual)
        self.assertIn("IN PROGRESS", clean_actual)
        self.assertIn("PASS", clean_actual)


# #############################################################################
# Test_create_consolidated_repro_with_missing_files
# #############################################################################


class Test_create_consolidated_repro_with_missing_files(hunitest.TestCase):
    # TODO(ai_gp): Factor out a helper function with a self.assert_equal so
    # that we can check the output of each test.
    def test1(self) -> None:
        """
        Test that missing repro scripts are skipped without crashing.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        # Create repro file only for docker build.
        docker_dir = os.path.join(scratch_dir, "tmp.pytest_failed.docker")
        hio.create_dir(docker_dir, incremental=True)
        docker_repro = os.path.join(docker_dir, "repro.sh")
        hio.to_file(docker_repro, "#!/bin/bash\npytest_log test_docker.py $*")
        # apple and dev_container directories don't have repro.sh.
        with hsystem.cd(scratch_dir):
            # Call with all three builds.
            actual = dshtpfmbu._create_consolidated_repro(
                ["docker", "apple", "dev_container"]
            )
        # Check outputs.
        # Expected: Consolidated script includes only available builds.
        # Only docker has a repro.sh file, so only docker section appears.
        expected = """
        #!/bin/bash
        # Consolidated repro script for multiple builds.

        BUILD_TAG=pytest_multi_build

        # Build: docker
        export CSFY_DOCKER_ENGINE='docker'; pytest_log test_docker.py $* 2>&1 | tee tmp.$BUILD_TAG.docker.txt

        """
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)

    def test2(self) -> None:
        """
        Test that only builds with repro scripts are consolidated.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        # Create repro files for docker and apple.
        for build_name in ["docker", "apple"]:
            build_dir = os.path.join(
                scratch_dir, f"tmp.pytest_failed.{build_name}"
            )
            hio.create_dir(build_dir, incremental=True)
            repro_file = os.path.join(build_dir, "repro.sh")
            content = f"#!/bin/bash\npytest_log test_{build_name}.py $*"
            hio.to_file(repro_file, content)
        with hsystem.cd(scratch_dir):
            # Call with all three builds (only docker and apple have files).
            actual = dshtpfmbu._create_consolidated_repro(
                ["docker", "apple", "dev_container"]
            )
        # Check outputs.
        # Expected: Consolidated script includes only builds with repro files.
        # Docker and apple have repro.sh files, but dev_container is skipped.
        expected = """
        #!/bin/bash
        # Consolidated repro script for multiple builds.

        BUILD_TAG=pytest_multi_build

        # Build: docker
        export CSFY_DOCKER_ENGINE='docker'; pytest_log test_docker.py $* 2>&1 | tee tmp.$BUILD_TAG.docker.txt

        # Build: apple
        export CSFY_DOCKER_ENGINE='apple'; pytest_log test_apple.py $* 2>&1 | tee tmp.$BUILD_TAG.apple.txt

        """
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)
