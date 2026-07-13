"""
Unit tests for pytest_failed_multi_build.py module.

Tests consolidation of failed tests across multiple build configurations.
"""

import os
from typing import Any, Dict, Set

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import dev_scripts_helpers.testing.pytest_failed_multi_build as dshtpfmbu


# #############################################################################
# Test_read_failed_tests
# #############################################################################


class Test_read_failed_tests(hunitest.TestCase):
    """
    Test `_read_failed_tests` function for reading failed test files.
    """

    def _run_test_in_scratch(self, build_name: str, content: str) -> Any:
        """
        Helper method to run test in scratch directory.

        :param build_name: Build configuration name
        :param content: Content to write to failed tests file
        :return: Result from _read_failed_tests
        """
        scratch_dir = self.get_scratch_space()
        build_dir = os.path.join(scratch_dir, f"tmp.pytest_failed.{build_name}")
        hio.create_dir(build_dir, incremental=True)
        failed_file = os.path.join(build_dir, "failed_tests.txt")
        hio.to_file(failed_file, content)
        original_dir = os.getcwd()
        try:
            os.chdir(scratch_dir)
            result = dshtpfmbu._read_failed_tests(build_name)
            return result
        finally:
            os.chdir(original_dir)

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
        result = self._run_test_in_scratch(build_name, "\n".join(tests))
        # Check outputs.
        expected = tests
        self.assert_equal(str(result), str(expected))

    def test2(self) -> None:
        """
        Test reading empty failed tests file.
        """
        # Prepare inputs.
        build_name = "apple"
        # Run test.
        result = self._run_test_in_scratch(build_name, "")
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
        result = self._run_test_in_scratch(build_name, content)
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

    def _run_test_in_scratch(self, build_name: str, content: str) -> str:
        """
        Helper method to run test in scratch directory.

        :param build_name: Build configuration name
        :param content: Content to write to repro file
        :return: Result from _read_repro_script
        """
        scratch_dir = self.get_scratch_space()
        build_dir = os.path.join(scratch_dir, f"tmp.pytest_failed.{build_name}")
        hio.create_dir(build_dir, incremental=True)
        repro_file = os.path.join(build_dir, "repro.sh")
        hio.to_file(repro_file, content)
        original_dir = os.getcwd()
        try:
            os.chdir(scratch_dir)
            result = dshtpfmbu._read_repro_script(build_name)
            return result
        finally:
            os.chdir(original_dir)

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
        result = self._run_test_in_scratch(build_name, content)
        # Check outputs.
        expected = content
        self.assertEqual(result, expected)


# #############################################################################
# Test_extract_tests_from_repro
# #############################################################################


class Test_extract_tests_from_repro(hunitest.TestCase):
    """
    Test _extract_tests_from_repro function for extracting test names.
    """

    def helper(self, repro_content: str, expected_count: int) -> Any:
        """
        Test helper for _extract_tests_from_repro.

        :param repro_content: Repro script content
        :param expected_count: Expected number of tests extracted
        :return: Actual extracted tests
        """
        actual = dshtpfmbu._extract_tests_from_repro(repro_content)
        self.assertEqual(len(actual), expected_count)
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
        expected_test1 = "helpers/test/test_module.py::TestClass::test_method1"
        expected_test2 = "helpers/test/test_module.py::TestClass::test_method2"
        # Run test.
        actual = self.helper(repro_content, 2)
        # Check outputs.
        self.assertEqual(actual[0], expected_test1)
        self.assertEqual(actual[1], expected_test2)

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
        expected = "helpers/test/test_module.py::TestClass::test_method1"
        # Run test.
        actual = self.helper(repro_content, 1)
        # Check outputs.
        self.assertEqual(actual[0], expected)

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

    def _run_test_in_scratch(
        self,
        build_names: list,
        build_tests: Dict[str, list],
    ) -> Dict[str, Set[str]]:
        """
        Helper to create files and run consolidation test.

        :param build_names: List of build names
        :param build_tests: Dict mapping build name to test list
        :return: Result from _consolidate_failed_tests
        """
        scratch_dir = self.get_scratch_space()
        self._create_failed_test_files(scratch_dir, build_tests)
        original_dir = os.getcwd()
        try:
            os.chdir(scratch_dir)
            result = dshtpfmbu._consolidate_failed_tests(build_names)
            return result
        finally:
            os.chdir(original_dir)

    def test1(self) -> None:
        """
        Test consolidating failed tests from single build.
        """
        # Prepare inputs.
        build_names = ["docker"]
        build_tests = {
            "docker": ["test_method1", "test_method2"],
        }
        # Run test.
        result = self._run_test_in_scratch(build_names, build_tests)
        # Check outputs.
        self.assertEqual(len(result), 2)
        self.assertEqual(result["test_method1"], {"docker"})
        self.assertEqual(result["test_method2"], {"docker"})

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
        result = self._run_test_in_scratch(build_names, build_tests)
        # Check outputs.
        self.assertEqual(len(result), 3)
        self.assertEqual(result["test_method1"], {"docker"})
        self.assertEqual(result["test_method2"], {"docker", "apple"})
        self.assertEqual(result["test_method3"], {"apple"})


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
            content = f"#!/bin/bash -xe\n# Repro script\npytest_log {tests} $*"
            hio.to_file(repro_file, content)

    def _run_test_in_scratch(
        self,
        build_names: list,
    ) -> str:
        """
        Helper to create repro files and run consolidation test.

        :param build_names: List of build names
        :return: Result from _create_consolidated_repro
        """
        scratch_dir = self.get_scratch_space()
        self._create_repro_files(scratch_dir, build_names)
        original_dir = os.getcwd()
        try:
            os.chdir(scratch_dir)
            result = dshtpfmbu._create_consolidated_repro(build_names)
            return result
        finally:
            os.chdir(original_dir)

    def test1(self) -> None:
        """
        Test creating consolidated repro script for docker and apple builds.
        """
        # Prepare inputs.
        build_names = ["docker", "apple"]
        # Run test.
        result = self._run_test_in_scratch(build_names)
        # Check outputs.
        self.assertIn("#!/bin/bash", result)
        self.assertIn("Consolidated repro script for multiple builds.", result)
        self.assertIn("# Build: docker", result)
        self.assertIn("# Build: apple", result)
        self.assertIn("export CSFY_DOCKER_ENGINE='docker'", result)
        self.assertIn("export CSFY_DOCKER_ENGINE='apple'", result)
        self.assertIn("pytest_log", result)

    def test2(self) -> None:
        """
        Test creating consolidated repro script with dev_container build.
        """
        # Prepare inputs.
        build_names = ["dev_container"]
        # Run test.
        result = self._run_test_in_scratch(build_names)
        # Check outputs.
        self.assertIn("#!/bin/bash", result)
        self.assertIn("# Build: dev_container", result)
        self.assertIn("invoke docker_cmd --stage=local -v 1.6.0 --cmd", result)
        self.assertIn("pytest_log", result)


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
    ) -> str:
        """
        Test helper for _summary_to_str.

        :param build_names: List of build names
        :param test_to_builds: Dict mapping test names to sets of build names
        :return: Summary string result
        """
        actual = dshtpfmbu._summary_to_str(build_names, test_to_builds)
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
        # Run test.
        actual = self.helper(build_names, test_to_builds)
        # Check outputs.
        self.assertIn("Failed Tests Summary", actual)
        self.assertIn("test_method1", actual)
        self.assertIn("test_method2", actual)
        self.assertIn("Total failing tests: 2", actual)

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
        # Run test.
        actual = self.helper(build_names, test_to_builds)
        # Check outputs.
        self.assertIn("Total failing tests: 3", actual)
        self.assertIn("Tests failing in multiple builds: 2", actual)

    def test3(self) -> None:
        """
        Test summary with empty failures.
        """
        # Prepare inputs.
        build_names = ["docker", "apple"]
        test_to_builds = {}
        # Run test.
        actual = self.helper(build_names, test_to_builds)
        # Check outputs.
        self.assertIn("Total failing tests: 0", actual)
        self.assertIn("Tests failing in multiple builds: 0", actual)
