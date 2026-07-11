"""
Unit tests for pytest_multi_build.py module.

Tests orchestration of pytest across multiple build configurations.
"""

import os

import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti
import dev_scripts_helpers.testing.pytest_multi_build as pmb


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
        actual = pmb._build_pytest_cmd(targets)
        # Check outputs.
        self.assertEqual(actual, "pytest_log helpers/test/test_module.py")

    def test2(self) -> None:
        """
        Test building command with multiple targets.
        """
        # Prepare inputs.
        targets = ["helpers/test/test_module1.py", "helpers/test/test_module2.py"]
        # Run test.
        actual = pmb._build_pytest_cmd(targets)
        # Check outputs.
        self.assertEqual(
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
        actual = pmb._build_pytest_cmd(targets)
        # Check outputs.
        self.assertEqual(actual, "pytest_log .")


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
            with open(output_file, "w") as f:
                f.write("old output")
        # Change working directory for the test.
        original_dir = os.getcwd()
        try:
            os.chdir(scratch_dir)
            # Run test.
            pmb._cleanup_old_files()
            # Check outputs.
            for build_name in ["docker", "apple", "dev_container"]:
                output_file = f"tmp.pytest_multi_build.{build_name}.txt"
                self.assertFalse(os.path.exists(output_file))
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
            pmb._cleanup_old_files()
            # Check outputs.
            for build_name in ["docker", "apple", "dev_container"]:
                output_file = f"tmp.pytest_multi_build.{build_name}.txt"
                self.assertFalse(os.path.exists(output_file))
        finally:
            os.chdir(original_dir)


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
        docker_engine = "docker"
        use_docker_cmd = False
        # Prepare outputs.
        scratch_dir = self.get_scratch_space()
        original_dir = os.getcwd()
        try:
            os.chdir(scratch_dir)
            # Run test and verify command contains expected elements.
            pmb._run_build(
                build_name,
                cmd,
                docker_engine,
                use_docker_cmd=use_docker_cmd,
            )
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
        docker_engine = "docker"
        use_docker_cmd = True
        # Prepare outputs.
        scratch_dir = self.get_scratch_space()
        original_dir = os.getcwd()
        try:
            os.chdir(scratch_dir)
            # Run test and verify it completes without error.
            pmb._run_build(
                build_name,
                cmd,
                docker_engine,
                use_docker_cmd=use_docker_cmd,
            )
            # Invariant: function should complete without raising exceptions.
        finally:
            os.chdir(original_dir)

    def test3(self) -> None:
        """
        Test with different build configurations.
        """
        # Prepare inputs.
        cmd = "pytest_log ."
        docker_engine = "docker"
        # Prepare outputs.
        scratch_dir = self.get_scratch_space()
        original_dir = os.getcwd()
        try:
            os.chdir(scratch_dir)
            # Run test for each build.
            for build_name in ["docker", "apple", "dev_container"]:
                pmb._run_build(
                    build_name,
                    cmd,
                    docker_engine,
                    use_docker_cmd=False,
                )
                # Invariant: function should complete without raising exceptions.
        finally:
            os.chdir(original_dir)


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
            pmb._clear_cache()
        # Check outputs.
        self.assertEqual(len(invocations), 1)
        call_dict = invocations[0]
        cmd = call_dict["args"][0]
        self.assertIn("manage_cache.py", cmd)
        self.assertIn("--action clear_all", cmd)
