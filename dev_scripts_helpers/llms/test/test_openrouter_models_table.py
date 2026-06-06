import os

import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest


# #############################################################################
# Test_openrouter_models_table_py
# #############################################################################


# TODO(ai_gp): Run /factor_common_code
class Test_openrouter_models_table_py(hunitest.TestCase):
    """
    End-to-end tests for openrouter_models_table.py executable.
    """

    def test1(self) -> None:
        """
        Test with single model, cache disabled, and no external API calls.
        """
        # Prepare inputs.
        scratch_space = self.get_scratch_space()
        models_file = os.path.join(scratch_space, "test_models.txt")
        model_ids_content = """
        google/gemini-3.1-pro-preview
        """
        hio.to_file(models_file, hprint.dedent(model_ids_content))
        executable = hgit.find_file_in_git_tree("openrouter_models_table.py")
        # Run test.
        # Use DISABLE_CACHE to bypass caching entirely (no cache reads or writes).
        cmd = (
            f"{executable} "
            f"--models_from_file={models_file} "
            f"--cache_mode=DISABLE_CACHE"
        )
        exit_code, result = hsystem.system_to_string(cmd, abort_on_error=True)
        # Check outputs.
        # Expected from command: script attempts to run and fetch data
        # This test validates the script structure and argument parsing
        # If APIs are available, output should contain expected columns
        self.assertIn("Name", result)
        self.assertIn("Model_ID", result)

    def test2(self) -> None:
        """
        Test with single action: openrouter_pricing.
        """
        scratch_space = self.get_scratch_space()
        models_file = os.path.join(scratch_space, "test_models.txt")
        model_ids_content = """
        google/gemini-3.1-pro-preview
        """
        hio.to_file(models_file, hprint.dedent(model_ids_content))
        executable = hgit.find_file_in_git_tree("openrouter_models_table.py")
        cmd = (
            f"{executable} "
            f"--models_from_file={models_file} "
            f"-a openrouter_pricing "
            f"--cache_mode=DISABLE_CACHE"
        )
        _, result = hsystem.system_to_string(cmd, abort_on_error=True)
        # Should have Model_ID and pricing columns
        self.assertIn("Model_ID", result)
        self.assertIn("Input_Cost", result)
        self.assertIn("Output_Cost", result)
        self.assertIn("Context", result)

    def test3(self) -> None:
        """
        Test with single action: openrouter_throughput.
        """
        scratch_space = self.get_scratch_space()
        models_file = os.path.join(scratch_space, "test_models.txt")
        model_ids_content = """
        google/gemini-3.1-pro-preview
        """
        hio.to_file(models_file, hprint.dedent(model_ids_content))
        executable = hgit.find_file_in_git_tree("openrouter_models_table.py")
        cmd = (
            f"{executable} "
            f"--models_from_file={models_file} "
            f"-a openrouter_throughput "
            f"--cache_mode=DISABLE_CACHE"
        )
        _, result = hsystem.system_to_string(cmd, abort_on_error=True)
        # Should have Model_ID and Speed columns
        self.assertIn("Model_ID", result)
        self.assertIn("Speed_(tok/s)", result)

    def test4(self) -> None:
        """
        Test with single action: aa_benchmarks.
        """
        scratch_space = self.get_scratch_space()
        models_file = os.path.join(scratch_space, "test_models.txt")
        model_ids_content = """
        google/gemini-3.1-pro-preview
        """
        hio.to_file(models_file, hprint.dedent(model_ids_content))
        executable = hgit.find_file_in_git_tree("openrouter_models_table.py")
        cmd = (
            f"{executable} "
            f"--models_from_file={models_file} "
            f"-a aa_benchmarks "
            f"--cache_mode=DISABLE_CACHE"
        )
        _, result = hsystem.system_to_string(cmd, abort_on_error=True)
        # Should have Model_ID and benchmark columns
        self.assertIn("Model_ID", result)
        self.assertIn("Coding_IQ", result)
        self.assertIn("General_IQ", result)

    def test5(self) -> None:
        """
        Test with single action: openrouter_per_model_usage.
        """
        scratch_space = self.get_scratch_space()
        models_file = os.path.join(scratch_space, "test_models.txt")
        model_ids_content = """
        google/gemini-3.1-pro-preview
        """
        hio.to_file(models_file, hprint.dedent(model_ids_content))
        executable = hgit.find_file_in_git_tree("openrouter_models_table.py")
        cmd = (
            f"{executable} "
            f"--models_from_file={models_file} "
            f"-a openrouter_per_model_usage "
            f"--cache_mode=DISABLE_CACHE"
        )
        _, result = hsystem.system_to_string(cmd, abort_on_error=True)
        # Should have Model_ID and usage columns
        self.assertIn("Model_ID", result)
        self.assertIn("Week_Tokens", result)
        self.assertIn("Month_Tokens", result)

    def test6(self) -> None:
        """
        Test with multiple actions: pricing and benchmarks.
        """
        scratch_space = self.get_scratch_space()
        models_file = os.path.join(scratch_space, "test_models.txt")
        model_ids_content = """
        google/gemini-3.1-pro-preview
        """
        hio.to_file(models_file, hprint.dedent(model_ids_content))
        executable = hgit.find_file_in_git_tree("openrouter_models_table.py")
        cmd = (
            f"{executable} "
            f"--models_from_file={models_file} "
            f"-a openrouter_pricing "
            f"-a aa_benchmarks "
            f"--cache_mode=DISABLE_CACHE"
        )
        _, result = hsystem.system_to_string(cmd, abort_on_error=True)
        # Should have columns from both actions
        self.assertIn("Model_ID", result)
        self.assertIn("Input_Cost", result)
        self.assertIn("Coding_IQ", result)

    def test7(self) -> None:
        """
        Test with all actions together.
        """
        scratch_space = self.get_scratch_space()
        models_file = os.path.join(scratch_space, "test_models.txt")
        model_ids_content = """
        google/gemini-3.1-pro-preview
        """
        hio.to_file(models_file, hprint.dedent(model_ids_content))
        executable = hgit.find_file_in_git_tree("openrouter_models_table.py")
        cmd = (
            f"{executable} "
            f"--models_from_file={models_file} "
            f"--cache_mode=DISABLE_CACHE"
        )
        _, result = hsystem.system_to_string(cmd, abort_on_error=True)
        # Should have columns from all actions
        self.assertIn("Model_ID", result)
        self.assertIn("Input_Cost", result)
        self.assertIn("Speed_(tok/s)", result)
        self.assertIn("Coding_IQ", result)
        self.assertIn("Week_Tokens", result)
