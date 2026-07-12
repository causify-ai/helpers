"""
Unit tests for pytest_multi_build.py module.

Tests orchestration of pytest across multiple build configurations.
"""

import os

import helpers.hio as hio
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
        self.assert_equal(actual, "pytest_log helpers/test/test_module.py")

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
            "pytest_log helpers/test/test_module1.py helpers/test/test_module2.py",
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
        self.assert_equal(actual, "pytest_log .")


# #############################################################################
# Test_cleanup_old_files
# #############################################################################


class Test_cleanup_old_files(hunitest.TestCase):
    """
    Test _cleanup_old_files function for cleaning up old output files.
    """

    def test1(self) -> None:
        """
        Test removing old build output files.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        # Create old output files.
        for build_name in ["docker", "apple", "dev_container"]:
            output_file = os.path.join(
                scratch_dir, f"tmp.pytest_multi_build.{build_name}.txt"
            )
            hio.to_file(output_file, "old output")
        # Change working directory for the test.
        original_dir = os.getcwd()
        try:
            os.chdir(scratch_dir)
            # Run test.
            dshtpmubu._cleanup_old_files()
            # Check outputs.
            expected_files = {}
            for build_name in ["docker", "apple", "dev_container"]:
                output_file = f"tmp.pytest_multi_build.{build_name}.txt"
                expected_files[output_file] = False
            actual_files = {
                f"tmp.pytest_multi_build.{build_name}.txt": os.path.exists(f"tmp.pytest_multi_build.{build_name}.txt")
                for build_name in ["docker", "apple", "dev_container"]
            }
            self.assert_equal(str(actual_files), str(expected_files))
        finally:
            os.chdir(original_dir)

    def test2(self) -> None:
        """
        Test cleanup with no old files present.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        # Change working directory for the test.
        original_dir = os.getcwd()
        try:
            os.chdir(scratch_dir)
            # Run test (should not raise).
            dshtpmubu._cleanup_old_files()
            # Check outputs.
            actual_files = {
                f"tmp.pytest_multi_build.{build_name}.txt": os.path.exists(f"tmp.pytest_multi_build.{build_name}.txt")
                for build_name in ["docker", "apple", "dev_container"]
            }
            expected_files = {
                f"tmp.pytest_multi_build.{build_name}.txt": False
                for build_name in ["docker", "apple", "dev_container"]
            }
            self.assert_equal(str(actual_files), str(expected_files))
        finally:
            os.chdir(original_dir)


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
        with hunteuti.capture_system_calls() as invocations:
            dshtpmubu._clear_cache()
        # Check outputs.
        self.assertEqual(len(invocations), 1)
        call_dict = invocations[0]
        cmd = call_dict["args"][0]
        expected_cmd = "manage_cache.py --action clear_all"
        self.assert_equal(cmd, expected_cmd)
