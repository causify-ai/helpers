import logging
import os

import pytest

import helpers.hio as hio
import helpers.hllm_cli as hllmcli
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_apply_llm_with_files
# #############################################################################


class Test_apply_llm_with_files(hunitest.TestCase):
    """
    Test apply_llm_with_files using the library interface.

    Tests run various command-line configurations using the Python library
    interface (default mode without --use_llm_executable flag).
    """

    @pytest.mark.skip(reason="Test disabled by default - requires LLM API access")
    def test_library(self) -> None:
        """
        Test multiple command-line configurations using library interface.

        Tests various command-line argument combinations to ensure they
        execute without errors. Does not verify output correctness.
        """
        # Get scratch space for test files.
        scratch_dir = self.get_scratch_space()
        # Create input file.
        input_file = os.path.join(scratch_dir, "input.txt")
        hio.to_file(input_file, "2+2=")
        # TODO(ai_gp): Move test_cases out of the test function and share it across the testes.
        # Define test cases as list of tuples (description, kwargs).
        test_cases = [
            (
                "Basic usage with library (default mode)",
                {},
            ),
            (
                "With custom system prompt",
                {
                    "system_prompt": "You are a helpful math assistant. Solve the problem step by step."
                },
            ),
            (
                "With specific model selection",
                {"model": "gpt-4"},
            ),
            (
                "With progress bar (expected character count)",
                {"expected_num_chars": 500},
            ),
            (
                "Complete example with all options",
                {
                    "system_prompt": "You are a helpful assistant that provides concise answers",
                    "model": "claude-3-5-sonnet-20241022",
                    "expected_num_chars": 1000,
                },
            ),
        ]
        # Run each test case.
        for idx, (description, kwargs) in enumerate(test_cases, 1):
            _LOG.info("Running test case %d: %s", idx, description)
            output_file = os.path.join(scratch_dir, f"output_{idx}.txt")
            # Run test.
            hllmcli.apply_llm_with_files(
                input_file=input_file,
                output_file=output_file,
                use_llm_executable=False,
                **kwargs,
            )
            # Check that output file was created.
            self.assert_equal(os.path.exists(output_file), True)
            # Check that output file is not empty.
            output_content = hio.from_file(output_file)
            self.assert_equal(len(output_content) > 0, True)

    @pytest.mark.skip(reason="Test disabled by default - requires LLM CLI executable")
    def test_executable(self) -> None:
        """
        Test multiple command-line configurations using executable interface.

        Tests various command-line argument combinations to ensure they
        execute without errors. Does not verify output correctness.
        """
        # Get scratch space for test files.
        scratch_dir = self.get_scratch_space()
        # Create input file.
        input_file = os.path.join(scratch_dir, "input.txt")
        hio.to_file(input_file, "2+2=")
        # Define test cases as list of tuples (description, kwargs).
        test_cases = [
            (
                "Basic usage with executable",
                {},
            ),
            (
                "With custom system prompt",
                {
                    "system_prompt": "You are a helpful math assistant. Solve the problem step by step."
                },
            ),
            (
                "With specific model selection",
                {"model": "gpt-4"},
            ),
            (
                "With progress bar (expected character count)",
                {"expected_num_chars": 500},
            ),
            (
                "Complete example with all options",
                {
                    "system_prompt": "You are a helpful assistant that provides concise answers",
                    "model": "claude-3-5-sonnet-20241022",
                    "expected_num_chars": 1000,
                },
            ),
        ]
        # Run each test case.
        for idx, (description, kwargs) in enumerate(test_cases, 1):
            _LOG.info("Running test case %d: %s", idx, description)
            output_file = os.path.join(scratch_dir, f"output_{idx}.txt")
            # Run test.
            hllmcli.apply_llm_with_files(
                input_file=input_file,
                output_file=output_file,
                use_llm_executable=True,
                **kwargs,
            )
            # Check that output file was created.
            self.assert_equal(os.path.exists(output_file), True)
            # Check that output file is not empty.
            output_content = hio.from_file(output_file)
            self.assert_equal(len(output_content) > 0, True)
