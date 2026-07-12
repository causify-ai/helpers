"""
Unit tests for pytest_failed_multi_build.py module.

Tests consolidation of failed tests across multiple build configurations.
"""

import os
from typing import Dict, Set

import helpers.hio as hio
import helpers.hunit_test as hunitest
import dev_scripts_helpers.testing.pytest_failed_multi_build as dshtpfmbu


# #############################################################################
# Test_read_failed_tests
# #############################################################################


class Test_read_failed_tests(hunitest.TestCase):
    """
    Test _read_failed_tests function for reading failed test files.
    """

    def test1(self) -> None:
        """
        Test reading failed tests from a file.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        build_name = "docker"
        failed_file = os.path.join(
            scratch_dir, f"tmp.pytest_failed.{build_name}.failed_tests.txt"
        )
        tests = [
            "helpers/test/test_module.py::TestClass::test_method1",
            "helpers/test/test_module.py::TestClass::test_method2",
        ]
        hio.to_file(failed_file, "\n".join(tests))
        # Change working directory for the test.
        original_dir = os.getcwd()
        try:
            os.chdir(scratch_dir)
            # Run test.
            result = dshtpfmbu._read_failed_tests(build_name)
            # Check outputs.
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0], tests[0])
            self.assertEqual(result[1], tests[1])
        finally:
            os.chdir(original_dir)

    def test2(self) -> None:
        """
        Test reading empty failed tests file.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        build_name = "apple"
        failed_file = os.path.join(
            scratch_dir, f"tmp.pytest_failed.{build_name}.failed_tests.txt"
        )
        hio.to_file(failed_file, "")
        # Change working directory for the test.
        original_dir = os.getcwd()
        try:
            os.chdir(scratch_dir)
            # Run test.
            result = dshtpfmbu._read_failed_tests(build_name)
            # Check outputs.
            self.assertEqual(len(result), 0)
        finally:
            os.chdir(original_dir)

    def test3(self) -> None:
        """
        Test reading file with whitespace and empty lines.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        build_name = "dev_container"
        failed_file = os.path.join(
            scratch_dir, f"tmp.pytest_failed.{build_name}.failed_tests.txt"
        )
        content = """
        helpers/test/test_module.py::TestClass::test_method1

        helpers/test/test_module.py::TestClass::test_method2
        """
        hio.to_file(failed_file, content)
        # Change working directory for the test.
        original_dir = os.getcwd()
        try:
            os.chdir(scratch_dir)
            # Run test.
            result = dshtpfmbu._read_failed_tests(build_name)
            # Check outputs.
            self.assertEqual(len(result), 2)
        finally:
            os.chdir(original_dir)


# #############################################################################
# Test_read_repro_script
# #############################################################################


class Test_read_repro_script(hunitest.TestCase):
    """
    Test _read_repro_script function for reading repro scripts.
    """

    def test1(self) -> None:
        """
        Test reading repro script content.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        build_name = "docker"
        repro_file = os.path.join(
            scratch_dir, f"tmp.pytest_failed.{build_name}.repro.sh"
        )
        content = "#!/bin/bash\npytest helpers/test/test_module.py"
        hio.to_file(repro_file, content)
        # Change working directory for the test.
        original_dir = os.getcwd()
        try:
            os.chdir(scratch_dir)
            # Run test.
            result = dshtpfmbu._read_repro_script(build_name)
            # Check outputs.
            self.assertEqual(result, content)
        finally:
            os.chdir(original_dir)


# #############################################################################
# Test_extract_tests_from_repro
# #############################################################################


class Test_extract_tests_from_repro(hunitest.TestCase):
    """
    Test _extract_tests_from_repro function for extracting test names.
    """

    def test1(self) -> None:
        """
        Test extracting tests from pytest_log command in repro script.
        """
        # Prepare inputs.
        repro_content = """#!/bin/bash -xe
# Repro script for the failed tests
pytest_log helpers/test/test_module.py::TestClass::test_method1 helpers/test/test_module.py::TestClass::test_method2 $*
"""
        # Run test.
        actual = dshtpfmbu._extract_tests_from_repro(repro_content)
        # Check outputs.
        self.assertEqual(len(actual), 2)
        self.assertEqual(
            actual[0], "helpers/test/test_module.py::TestClass::test_method1"
        )
        self.assertEqual(
            actual[1], "helpers/test/test_module.py::TestClass::test_method2"
        )

    def test2(self) -> None:
        """
        Test extracting single test from pytest_log command.
        """
        # Prepare inputs.
        repro_content = """#!/bin/bash -xe
# Repro script
pytest_log helpers/test/test_module.py::TestClass::test_method1 $*
"""
        # Run test.
        actual = dshtpfmbu._extract_tests_from_repro(repro_content)
        # Check outputs.
        self.assertEqual(len(actual), 1)
        self.assertEqual(
            actual[0], "helpers/test/test_module.py::TestClass::test_method1"
        )

    def test3(self) -> None:
        """
        Test with no pytest_log command.
        """
        # Prepare inputs.
        repro_content = """#!/bin/bash
# Some other script
echo "hello"
"""
        # Run test.
        actual = dshtpfmbu._extract_tests_from_repro(repro_content)
        # Check outputs.
        self.assertEqual(actual, [])


# #############################################################################
# Test_consolidate_failed_tests
# #############################################################################


class Test_consolidate_failed_tests(hunitest.TestCase):
    """
    Test _consolidate_failed_tests function for consolidating failures.
    """

    def test1(self) -> None:
        """
        Test consolidating failed tests from single build.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        build_names = ["docker"]
        # Create failed test files.
        for build_name in build_names:
            failed_file = os.path.join(
                scratch_dir, f"tmp.pytest_failed.{build_name}.failed_tests.txt"
            )
            tests = ["test_method1", "test_method2"]
            hio.to_file(failed_file, "\n".join(tests))
        # Change working directory for the test.
        original_dir = os.getcwd()
        try:
            os.chdir(scratch_dir)
            # Run test.
            result = dshtpfmbu._consolidate_failed_tests(build_names)
            # Check outputs.
            self.assertEqual(len(result), 2)
            self.assertEqual(result["test_method1"], {"docker"})
            self.assertEqual(result["test_method2"], {"docker"})
        finally:
            os.chdir(original_dir)

    def test2(self) -> None:
        """
        Test consolidating tests across multiple builds.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        build_names = ["docker", "apple"]
        # Create failed test files for different builds.
        docker_tests = ["test_method1", "test_method2"]
        apple_tests = ["test_method2", "test_method3"]
        for build_name, tests in [
            ("docker", docker_tests),
            ("apple", apple_tests),
        ]:
            failed_file = os.path.join(
                scratch_dir, f"tmp.pytest_failed.{build_name}.failed_tests.txt"
            )
            hio.to_file(failed_file, "\n".join(tests))
        # Change working directory for the test.
        original_dir = os.getcwd()
        try:
            os.chdir(scratch_dir)
            # Run test.
            result = dshtpfmbu._consolidate_failed_tests(build_names)
            # Check outputs.
            self.assertEqual(len(result), 3)
            self.assertEqual(result["test_method1"], {"docker"})
            self.assertEqual(result["test_method2"], {"docker", "apple"})
            self.assertEqual(result["test_method3"], {"apple"})
        finally:
            os.chdir(original_dir)


# #############################################################################
# Test_create_consolidated_repro
# #############################################################################


class Test_create_consolidated_repro(hunitest.TestCase):
    """
    Test _create_consolidated_repro function for consolidated scripts.
    """

    def test1(self) -> None:
        """
        Test creating consolidated repro script for docker and apple builds.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        build_names = ["docker", "apple"]
        # Create repro files with proper format.
        for build_name in build_names:
            repro_file = os.path.join(
                scratch_dir, f"tmp.pytest_failed.{build_name}.repro.sh"
            )
            tests = f"test/test_{build_name}.py::TestClass::test_method"
            content = f"#!/bin/bash -xe\n# Repro script\npytest_log {tests} $*"
            hio.to_file(repro_file, content)
        # Change working directory for the test.
        original_dir = os.getcwd()
        try:
            os.chdir(scratch_dir)
            # Run test.
            result = dshtpfmbu._create_consolidated_repro(build_names)
            # Check outputs.
            self.assertIn("#!/bin/bash", result)
            self.assertIn(
                "Consolidated repro script for multiple builds.", result
            )
            self.assertIn("# Build: docker", result)
            self.assertIn("# Build: apple", result)
            self.assertIn("export CSFY_DOCKER_ENGINE='docker'", result)
            self.assertIn("export CSFY_DOCKER_ENGINE='apple'", result)
            self.assertIn("pytest_log", result)
        finally:
            os.chdir(original_dir)

    def test2(self) -> None:
        """
        Test creating consolidated repro script with dev_container build.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        build_names = ["dev_container"]
        # Create repro file.
        repro_file = os.path.join(
            scratch_dir, "tmp.pytest_failed.dev_container.repro.sh"
        )
        tests = "test/test_dev_container.py::TestClass::test_method"
        content = f"#!/bin/bash -xe\n# Repro script\npytest_log {tests} $*"
        hio.to_file(repro_file, content)
        # Change working directory for the test.
        original_dir = os.getcwd()
        try:
            os.chdir(scratch_dir)
            # Run test.
            result = dshtpfmbu._create_consolidated_repro(build_names)
            # Check outputs.
            self.assertIn("#!/bin/bash", result)
            self.assertIn("# Build: dev_container", result)
            self.assertIn(
                "invoke docker_cmd --stage=local -v 1.6.0 --cmd", result
            )
            self.assertIn("pytest_log", result)
        finally:
            os.chdir(original_dir)


# #############################################################################
# Test_summary_to_str
# #############################################################################


class Test_summary_to_str(hunitest.TestCase):
    """
    Test _summary_to_str function for summary generation.
    """

    def test1(self) -> None:
        """
        Test summary string generation with single build failures.
        """
        # Prepare inputs.
        build_names = ["docker"]
        test_to_builds: Dict[str, Set[str]] = {
            "test_method1": {"docker"},
            "test_method2": {"docker"},
        }
        # Run test.
        actual = dshtpfmbu._summary_to_str(build_names, test_to_builds)
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
        test_to_builds: Dict[str, Set[str]] = {
            "test_method1": {"docker", "apple"},
            "test_method2": {"docker"},
            "test_method3": {"apple", "dev_container"},
        }
        # Run test.
        actual = dshtpfmbu._summary_to_str(build_names, test_to_builds)
        # Check outputs.
        self.assertIn("Total failing tests: 3", actual)
        self.assertIn("Tests failing in multiple builds: 2", actual)

    def test3(self) -> None:
        """
        Test summary with empty failures.
        """
        # Prepare inputs.
        build_names = ["docker", "apple"]
        test_to_builds: Dict[str, Set[str]] = {}
        # Run test.
        actual = dshtpfmbu._summary_to_str(build_names, test_to_builds)
        # Check outputs.
        self.assertIn("Total failing tests: 0", actual)
        self.assertIn("Tests failing in multiple builds: 0", actual)
