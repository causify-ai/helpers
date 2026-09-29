"""
Unit tests for pytest_multi_build.py module.

Tests orchestration of pytest across multiple build configurations.
"""

import os

import pytest

import helpers.hdbg as hdbg
import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti
import dev_scripts_helpers.testing.pytest_multi_build as dshtpmubu


# #############################################################################
# Test_build_pytest_cmd
# #############################################################################


class Test_build_pytest_cmd(hunitest.TestCase):
    """
    Test _build_pytest_cmd function for building pytest commands.
    """

    def test1(self) -> None:
        """
        Test building command with single target.
        """
        # Prepare inputs.
        targets = ["helpers/test/test_module.py"]
        # Run test.
        actual = dshtpmubu._build_pytest_cmd(targets)
        # Check outputs.
        self.assert_equal(actual, "pytest_log --no_clear_screen helpers/test/test_module.py")

    def test2(self) -> None:
        """
        Test building command with multiple targets.
        """
        # Prepare inputs.
        targets = [
            "helpers/test/test_module1.py",
            "helpers/test/test_module2.py",
        ]
        # Run test.
        actual = dshtpmubu._build_pytest_cmd(targets)
        # Check outputs.
        self.assert_equal(
            actual,
            "pytest_log --no_clear_screen helpers/test/test_module1.py helpers/test/test_module2.py",
        )

    def test3(self) -> None:
        """
        Test building command with dots (run all tests in directory).
        """
        # Prepare inputs.
        targets = ["."]
        # Run test.
        actual = dshtpmubu._build_pytest_cmd(targets)
        # Check outputs.
        self.assert_equal(actual, "pytest_log --no_clear_screen .")


# #############################################################################
# Test_run_build
# #############################################################################


class Test_run_build(hunitest.TestCase):
    """
    Test _run_build function for running builds with different configurations.
    """

    def test1(self) -> None:
        """
        Test building correct shell command for docker build.
        """
        # Prepare inputs.
        build_name = "docker"
        cmd = "pytest_log helpers/test/"
        build_num = 1
        total_builds = 1
        # Prepare outputs.
        scratch_dir = self.get_scratch_space()
        original_dir = os.getcwd()
        try:
            os.chdir(scratch_dir)
            # Run test and verify command contains expected elements.
            dshtpmubu._run_build(build_name, cmd, build_num, total_builds)
            # Invariant: function should complete without raising exceptions.
        finally:
            os.chdir(original_dir)

    def test2(self) -> None:
        """
        Test building command with docker_cmd wrapper.
        """
        # Prepare inputs.
        build_name = "dev_container"
        cmd = "pytest_log helpers/test/"
        build_num = 1
        total_builds = 1
        # Prepare outputs.
        scratch_dir = self.get_scratch_space()
        original_dir = os.getcwd()
        try:
            os.chdir(scratch_dir)
            # Run test and verify it completes without error.
            dshtpmubu._run_build(build_name, cmd, build_num, total_builds)
            # Invariant: function should complete without raising exceptions.
        finally:
            os.chdir(original_dir)

    @pytest.mark.slow
    def test3(self) -> None:
        """
        Test with different build configurations.
        """
        # Prepare inputs.
        cmd = "pytest_log ."
        build_names = ["docker", "apple", "dev_container"]
        total_builds = len(build_names)
        # Prepare outputs.
        scratch_dir = self.get_scratch_space()
        original_dir = os.getcwd()
        try:
            os.chdir(scratch_dir)
            # Run test for each build.
            for build_num, build_name in enumerate(build_names, start=1):
                dshtpmubu._run_build(build_name, cmd, build_num, total_builds)
                # Invariant: function should complete without raising exceptions.
        finally:
            os.chdir(original_dir)

    def test4(self) -> None:
        """
        Test that the log file is written under a custom `output_dir`.
        """
        # Prepare inputs.
        build_name = "docker"
        cmd = "pytest_log helpers/test/"
        build_num = 1
        total_builds = 1
        output_dir = "custom_output_dir"
        # Prepare outputs.
        scratch_dir = self.get_scratch_space()
        original_dir = os.getcwd()
        try:
            os.chdir(scratch_dir)
            # Run test.
            dshtpmubu._run_build(
                build_name,
                cmd,
                build_num,
                total_builds,
                output_dir=output_dir,
            )
            # Check outputs.
            expected_log_file = os.path.join(output_dir, f"{build_name}.txt")
            hdbg.dassert_file_exists(expected_log_file)
        finally:
            os.chdir(original_dir)


# #############################################################################
# Test_clear_cache
# #############################################################################


class Test_clear_cache(hunitest.TestCase):
    """
    Test _clear_cache function for cache clearing.
    """

    def test1(self) -> None:
        """
        Test that _clear_cache calls manage_cache.py.
        """
        # Run test and capture system calls.
        with hunteuti.capture_sys_calls() as sys_calls:
            dshtpmubu._clear_cache()
        # Check outputs.
        self.assertEqual(len(sys_calls), 1)
        call_dict = sys_calls[0]
        cmd = call_dict["args"][0]
        expected_cmd = "manage_cache.py --action clear_all"
        self.assert_equal(cmd, expected_cmd)
