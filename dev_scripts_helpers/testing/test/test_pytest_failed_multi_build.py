"""
Unit tests for pytest_failed_multi_build.py module.

Tests consolidation of failed tests across multiple build configurations.
"""

import contextlib
import os
from typing import Any, Dict, Set

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import dev_scripts_helpers.testing.pytest_failed_multi_build as dshtpfmbu


@contextlib.contextmanager
def _chdir_context(directory: str):
    """
    Context manager to temporarily change working directory.

    :param directory: Directory to change to
    """
    original_dir = os.getcwd()
    try:
        os.chdir(directory)
        yield
    finally:
        os.chdir(original_dir)


# #############################################################################
# Test_read_failed_tests
# #############################################################################


class Test_read_failed_tests(hunitest.TestCase):
    """
    Test `_read_failed_tests` function for reading failed test files.
    """

    def helper(self, build_name: str, content: str) -> Any:
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
        with _chdir_context(scratch_dir):
            result = dshtpfmbu._read_failed_tests(build_name)
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
        result = self.helper(build_name, "\n".join(tests))
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

    def helper(self, build_name: str, content: str) -> str:
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
        with _chdir_context(scratch_dir):
            result = dshtpfmbu._read_repro_script(build_name)
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
        result = self.helper(build_name, content)
        # Check outputs.
        expected = content
        self.assert_equal(result, expected)


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
        # Prepare outputs.
        expected = [
            "helpers/test/test_module.py::TestClass::test_method1",
            "helpers/test/test_module.py::TestClass::test_method2",
        ]
        # Run test.
        actual = self.helper(repro_content, 2)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

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
    ) -> Dict[str, Set[str]]:
        """
        Helper to create files and run consolidation test.

        :param build_names: List of build names
        :param build_tests: Dict mapping build name to test list
        :return: Result from _consolidate_failed_tests
        """
        scratch_dir = self.get_scratch_space()
        self._create_failed_test_files(scratch_dir, build_tests)
        with _chdir_context(scratch_dir):
            result = dshtpfmbu._consolidate_failed_tests(build_names)
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
        # Run test.
        result = self.helper(build_names, build_tests)
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
        result = self.helper(build_names, build_tests)
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

    def helper(
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
        with _chdir_context(scratch_dir):
            result = dshtpfmbu._create_consolidated_repro(build_names)
            return result

    def test1(self) -> None:
        """
        Test creating consolidated repro script for docker and apple builds.
        """
        # TODO(ai_gp): Apply "Replace Checking Invariants with `assert_equal` - Do not use multiple `assertIn()` calls to check individual pieces of a string output; instead compare the entire output with `assert_equal()`"
        # Prepare inputs.
        build_names = ["docker", "apple"]
        # Run test.
        actual = self.helper(build_names)
        # Check outputs.
        # Expected: Bash script with consolidated repro commands for both builds.
        # Invariant: Contains shebang, comment, build markers, engine exports, and
        # pytest_log commands.
        self.assertIn("#!/bin/bash", actual)
        self.assertIn("Consolidated repro script for multiple builds.", actual)
        self.assertIn("# Build: docker", actual)
        self.assertIn("# Build: apple", actual)
        self.assertIn("export CSFY_DOCKER_ENGINE='docker'", actual)
        self.assertIn("export CSFY_DOCKER_ENGINE='apple'", actual)
        self.assertIn("pytest_log", actual)

    def test2(self) -> None:
        """
        Test creating consolidated repro script with dev_container build.
        """
        # TODO(ai_gp): Apply "Replace Checking Invariants with `assert_equal` - Do not use multiple `assertIn()` calls to check individual pieces of a string output; instead compare the entire output with `assert_equal()`"
        # Prepare inputs.
        build_names = ["dev_container"]
        # Run test.
        actual = self.helper(build_names)
        # Check outputs.
        # Expected: Bash script with dev_container-specific repro command.
        # Invariant: Contains shebang, build marker, invoke docker_cmd, and
        # pytest_log commands.
        self.assertIn("#!/bin/bash", actual)
        self.assertIn("# Build: dev_container", actual)
        self.assertIn("invoke docker_cmd --stage=local -v 1.6.0 --cmd", actual)
        self.assertIn("pytest_log", actual)


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
        # TODO(ai_gp): Apply "Replace Checking Invariants with `assert_equal` - Do not use multiple `assertIn()` calls to check individual pieces of a string output; instead compare the entire output with `assert_equal()`"
        # Prepare inputs.
        build_names = ["docker"]
        test_to_builds = {
            "test_method1": {"docker"},
            "test_method2": {"docker"},
        }
        # Run test.
        actual = self.helper(build_names, test_to_builds)
        # Check outputs.
        # Expected: Summary report with test names and counts.
        # Invariant: Contains header, individual test names, and total count.
        self.assertIn("Failed Tests Summary", actual)
        self.assertIn("test_method1", actual)
        self.assertIn("test_method2", actual)
        self.assertIn("Total failing tests: 2", actual)

    def test2(self) -> None:
        """
        Test summary with cross-build failures.
        """
        # TODO(ai_gp): Apply "Replace Checking Invariants with `assert_equal` - Do not use multiple `assertIn()` calls to check individual pieces of a string output; instead compare the entire output with `assert_equal()`"
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
        # Expected: Summary with aggregated counts across builds.
        # Invariant: Correct total and cross-build failure counts.
        self.assertIn("Total failing tests: 3", actual)
        self.assertIn("Tests failing in multiple builds: 2", actual)

    def test3(self) -> None:
        """
        Test summary with empty failures.
        """
        # TODO(ai_gp): Apply "Replace Checking Invariants with `assert_equal` - Do not use multiple `assertIn()` calls to check individual pieces of a string output; instead compare the entire output with `assert_equal()`"
        # Prepare inputs.
        build_names = ["docker", "apple"]
        test_to_builds = {}
        # Run test.
        actual = self.helper(build_names, test_to_builds)
        # Check outputs.
        # Expected: Summary with zero counts.
        # Invariant: All counts report zero.
        self.assertIn("Total failing tests: 0", actual)
        self.assertIn("Tests failing in multiple builds: 0", actual)


# #############################################################################
# Test_extract_build_stats_missing_pytest_ended
# #############################################################################


class Test_extract_build_stats_missing_pytest_ended(hunitest.TestCase):
    """
    Test _extract_build_stats marks INCOMPLETE when pytest_ended token missing.
    """

    def test_missing_pytest_ended_token(self) -> None:
        """
        Test that missing pytest_ended token marks build as INCOMPLETE.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        build_dir = os.path.join(scratch_dir, "tmp.pytest_failed.dev_container")
        hio.create_dir(build_dir, incremental=True)
        # Create info.json without pytest_ended token.
        info_data = {
            "pytest_started": "2024-01-01T00:00:00",
            "log_num_passed": 100,
            "log_num_failed": 5,
            "log_num_skipped": 2,
            "pytest_duration_in_secs": 45.2,
        }
        info_file = os.path.join(build_dir, "info.json")
        hio.to_json(info_file, info_data)
        with _chdir_context(scratch_dir):
            # Call extract_build_stats.
            result = dshtpfmbu._extract_build_stats("dev_container")
            # Check outputs - should be marked incomplete.
            self.assertEqual(result["build"], "dev_container")
            self.assertTrue(result["incomplete"])
            self.assertEqual(result["passed"], 100)
            self.assertEqual(result["failed"], 5)

    def test_with_pytest_ended_token_completes(self) -> None:
        """
        Test that presence of pytest_ended token marks build as COMPLETE.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        build_dir = os.path.join(scratch_dir, "tmp.pytest_failed.docker")
        hio.create_dir(build_dir, incremental=True)
        # Create info.json WITH pytest_ended token.
        info_data = {
            "pytest_started": "2024-01-01T00:00:00",
            "pytest_ended": "2024-01-01T00:00:45",
            "log_num_passed": 100,
            "log_num_failed": 0,
            "log_num_skipped": 2,
            "pytest_duration_in_secs": 45.2,
        }
        info_file = os.path.join(build_dir, "info.json")
        hio.to_json(info_file, info_data)
        with _chdir_context(scratch_dir):
            # Call extract_build_stats.
            result = dshtpfmbu._extract_build_stats("docker")
            # Check outputs - should NOT be marked incomplete.
            self.assertEqual(result["build"], "docker")
            self.assertFalse(result["incomplete"])
            self.assertEqual(result["passed"], 100)
            self.assertEqual(result["failed"], 0)


# #############################################################################
# Test_build_stats_to_str_incomplete_status
# #############################################################################


class Test_build_stats_to_str_incomplete_status(hunitest.TestCase):
    """
    Test _build_stats_to_str displays INCOMPLETE status correctly.
    """

    def test_incomplete_status_display(self) -> None:
        """
        Test that INCOMPLETE status is displayed in stats table.
        """
        # TODO(ai_gp): Apply "Replace Checking Invariants with `assert_equal` - Do not use multiple `assertIn()` calls to check individual pieces of a string output; instead compare the entire output with `assert_equal()`"
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
        # Check outputs.
        # Expected: Build statistics table with status indicators.
        # Invariant: Contains all build names with correct status (PASS/FAIL/INCOMPLETE).
        self.assertIn("Build Statistics", actual)
        self.assertIn("docker", actual)
        self.assertIn("FAIL", actual)  # docker has failures
        self.assertIn("apple", actual)
        self.assertIn("INCOMPLETE", actual)  # apple is incomplete
        self.assertIn("dev_container", actual)
        self.assertIn("PASS", actual)  # dev_container passed


# #############################################################################
# Test_create_consolidated_repro_with_missing_files
# #############################################################################


class Test_create_consolidated_repro_with_missing_files(hunitest.TestCase):
    """
    Test _create_consolidated_repro skips builds with missing repro files.
    """

    def test_skips_missing_repro_files(self) -> None:
        """
        Test that missing repro scripts are skipped without crashing.
        """
        # TODO(ai_gp): Apply "Replace Checking Invariants with `assert_equal` - Do not use multiple `assertIn()` calls to check individual pieces of a string output; instead compare the entire output with `assert_equal()`"
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        # Create repro file only for docker build.
        docker_dir = os.path.join(scratch_dir, "tmp.pytest_failed.docker")
        hio.create_dir(docker_dir, incremental=True)
        docker_repro = os.path.join(docker_dir, "repro.sh")
        hio.to_file(docker_repro, "#!/bin/bash\npytest_log test_docker.py $*")
        # apple and dev_container directories don't have repro.sh.
        with _chdir_context(scratch_dir):
            # Call with all three builds.
            actual = dshtpfmbu._create_consolidated_repro(
                ["docker", "apple", "dev_container"]
            )
            # Check outputs.
            # Expected: Consolidated script includes only available builds.
            # Invariant: Only includes docker section, skips missing apple and
            # dev_container sections.
            self.assertIn("#!/bin/bash", actual)
            self.assertIn("# Build: docker", actual)
            self.assertNotIn("# Build: apple", actual)  # Should be skipped.
            self.assertNotIn("# Build: dev_container", actual)  # Should be skipped.

    def test_consolidates_only_available_builds(self) -> None:
        """
        Test that only builds with repro scripts are consolidated.
        """
        # TODO(ai_gp): Apply "Replace Checking Invariants with `assert_equal` - Do not use multiple `assertIn()` calls to check individual pieces of a string output; instead compare the entire output with `assert_equal()`"
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        # Create repro files for docker and apple.
        for build_name in ["docker", "apple"]:
            build_dir = os.path.join(scratch_dir, f"tmp.pytest_failed.{build_name}")
            hio.create_dir(build_dir, incremental=True)
            repro_file = os.path.join(build_dir, "repro.sh")
            content = f"#!/bin/bash\npytest_log test_{build_name}.py $*"
            hio.to_file(repro_file, content)
        with _chdir_context(scratch_dir):
            # Call with all three builds (only docker and apple have files).
            actual = dshtpfmbu._create_consolidated_repro(
                ["docker", "apple", "dev_container"]
            )
            # Check outputs.
            # Expected: Consolidated script includes only builds with repro files.
            # Invariant: Contains docker and apple sections, skips dev_container.
            self.assertIn("# Build: docker", actual)
            self.assertIn("# Build: apple", actual)
            self.assertNotIn("# Build: dev_container", actual)
            self.assertIn("pytest_log", actual)
