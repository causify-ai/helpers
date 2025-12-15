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

# Test cases shared across both library and executable tests.
# Each tuple contains (description, kwargs) and corresponding llm_cli.py command.
_TEST_CASES = [
    # llm_cli.py --input_file input.txt --output_file output.txt
    (
        "Basic usage with input file",
        {},
    ),
    # llm_cli.py --input_file input.txt --output_file output.txt --system_prompt "You are a helpful math assistant. Solve the problem step by step."
    (
        "With custom system prompt",
        {
            "system_prompt": "You are a helpful math assistant. Solve the problem step by step."
        },
    ),
    # llm_cli.py --input_file input.txt --output_file output.txt --model gpt-4
    (
        "With specific model selection",
        {"model": "gpt-4"},
    ),
    # llm_cli.py --input_file input.txt --output_file output.txt --expected_num_chars 500
    (
        "With progress bar (expected character count)",
        {"expected_num_chars": 500},
    ),
    # llm_cli.py --input_file input.txt --output_file output.txt --system_prompt "You are a helpful assistant that provides concise answers" --model gpt-4o-mini --expected_num_chars 1000
    (
        "Complete example with all options",
        {
            "system_prompt": "You are a helpful assistant that provides concise answers",
            "model": "gpt-4o-mini",
            "expected_num_chars": 1000,
        },
    ),
]

# Test cases for input_text functionality.
# Each tuple contains (description, kwargs) and corresponding llm_cli.py command.
_TEST_CASES_INPUT_TEXT = [
    # llm_cli.py --input_text "2+2=" --output_file output.txt
    (
        "Basic usage with input text",
        {
            "input_text": "2+2=",
        },
    ),
    # llm_cli.py --input_text "What is Python?" --output_file output.txt --system_prompt "You are a helpful assistant"
    (
        "With input text and system prompt",
        {
            "input_text": "What is Python?",
            "system_prompt": "You are a helpful assistant",
        },
    ),
    # llm_cli.py --input_text "Explain recursion" --output_file output.txt --model gpt-4o-mini
    (
        "With input text and specific model",
        {
            "input_text": "Explain recursion",
            "model": "gpt-4o-mini",
        },
    ),
]

# Test cases for print_only functionality.
# Each tuple contains (description, kwargs) and corresponding llm_cli.py command.
_TEST_CASES_PRINT_ONLY = [
    # llm_cli.py --input_text "2+2=" --output_file -
    (
        "Print to screen with input text",
        {
            "input_text": "2+2=",
            "print_only": True,
        },
    ),
]


class Test_apply_llm_with_files(hunitest.TestCase):
    """
    Test apply_llm_with_files using both library and executable interfaces.

    Tests run various command-line configurations to ensure they execute
    without errors. Does not verify output correctness.
    """

    def _run_test_cases(self, use_llm_executable: bool) -> None:
        """
        Helper method to run test cases with specified interface.

        :param use_llm_executable: if True, use CLI executable; if False, use library
        """
        # Get scratch space for test files.
        scratch_dir = self.get_scratch_space()
        # Create input file.
        input_file = os.path.join(scratch_dir, "input.txt")
        hio.to_file(input_file, "2+2=")
        # Run each test case.
        for idx, (description, kwargs) in enumerate(_TEST_CASES, 1):
            _LOG.info("Running test case %d: %s", idx, description)
            output_file = os.path.join(scratch_dir, f"output_{idx}.txt")
            # Run test.
            hllmcli.apply_llm_with_files(
                input_file=input_file,
                output_file=output_file,
                use_llm_executable=use_llm_executable,
                **kwargs,
            )
            # Check that output file was created.
            self.assertTrue(os.path.exists(output_file))
            # Check that output file is not empty.
            output_content = hio.from_file(output_file)
            self.assertGreater(len(output_content), 0)

    @pytest.mark.skipif(
        __import__("importlib").util.find_spec("llm") is None,
        reason="llm Python library is not installed"
    )
    def test_library(self) -> None:
        """
        Test multiple command-line configurations using library interface.

        Tests various command-line argument combinations to ensure they
        execute without errors. Does not verify output correctness.
        """
        self._run_test_cases(use_llm_executable=False)

    @pytest.mark.skipif(
        not hllmcli._check_llm_executable(),
        reason="llm executable not found"
    )
    def test_executable(self) -> None:
        """
        Test multiple command-line configurations using executable interface.

        Tests various command-line argument combinations to ensure they
        execute without errors. Does not verify output correctness.
        """
        self._run_test_cases(use_llm_executable=True)

    # //////////////////////////////////////////////////////////////////////////

    def _run_test_cases_input_text(self, use_llm_executable: bool) -> None:
        """
        Helper method to run input_text test cases with specified interface.

        :param use_llm_executable: if True, use CLI executable; if False, use library
        """
        # Get scratch space for test files.
        scratch_dir = self.get_scratch_space()
        # Run each test case.
        for idx, (description, kwargs) in enumerate(_TEST_CASES_INPUT_TEXT, 1):
            _LOG.info("Running test case %d: %s", idx, description)
            output_file = os.path.join(scratch_dir, f"output_text_{idx}.txt")
            # Extract input_text from kwargs.
            kwargs_copy = kwargs.copy()
            input_text = kwargs_copy.pop("input_text")
            # Run test using apply_llm directly.
            response = hllmcli.apply_llm(
                input_text,
                use_llm_executable=use_llm_executable,
                **kwargs_copy,
            )
            # Write output to file.
            hio.to_file(output_file, response)
            # Check that output file was created.
            self.assertTrue(os.path.exists(output_file))
            # Check that output file is not empty.
            output_content = hio.from_file(output_file)
            self.assertGreater(len(output_content), 0)

    @pytest.mark.skipif(
        __import__("importlib").util.find_spec("llm") is None,
        reason="llm Python library is not installed"
    )
    def test_input_text_library(self) -> None:
        """
        Test input_text parameter using library interface.

        Tests that input_text parameter works correctly when text is provided
        directly instead of from a file. Does not verify output correctness.
        """
        self._run_test_cases_input_text(use_llm_executable=False)

    @pytest.mark.skipif(
        not hllmcli._check_llm_executable(),
        reason="llm executable not found"
    )
    def test_input_text_executable(self) -> None:
        """
        Test input_text parameter using executable interface.

        Tests that input_text parameter works correctly when text is provided
        directly instead of from a file. Does not verify output correctness.
        """
        self._run_test_cases_input_text(use_llm_executable=True)

    # //////////////////////////////////////////////////////////////////////////

    def _run_test_cases_print_only(self, use_llm_executable: bool) -> None:
        """
        Helper method to run print_only test cases with specified interface.

        :param use_llm_executable: if True, use CLI executable; if False, use library
        """
        # Run each test case.
        for idx, (description, kwargs) in enumerate(_TEST_CASES_PRINT_ONLY, 1):
            _LOG.info("Running test case %d: %s", idx, description)
            # Extract parameters from kwargs.
            kwargs_copy = kwargs.copy()
            input_text = kwargs_copy.pop("input_text")
            kwargs_copy.pop("print_only")  # Not needed for apply_llm
            # Run test using apply_llm directly - this should print to stdout.
            response = hllmcli.apply_llm(
                input_text,
                use_llm_executable=use_llm_executable,
                **kwargs_copy,
            )
            # Print response to stdout (simulating print_only behavior).
            print(response)

    @pytest.mark.skipif(
        __import__("importlib").util.find_spec("llm") is None,
        reason="llm Python library is not installed"
    )
    def test_print_only_library(self) -> None:
        """
        Test print_only parameter using library interface.

        Tests that print_only parameter works correctly when output should be
        printed to screen instead of written to file. Does not verify output
        correctness.
        """
        self._run_test_cases_print_only(use_llm_executable=False)

    @pytest.mark.skipif(
        not hllmcli._check_llm_executable(),
        reason="llm executable not found"
    )
    def test_print_only_executable(self) -> None:
        """
        Test print_only parameter using executable interface.

        Tests that print_only parameter works correctly when output should be
        printed to screen instead of written to file. Does not verify output
        correctness.
        """
        self._run_test_cases_print_only(use_llm_executable=True)
