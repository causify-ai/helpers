import logging
import os
import time
from typing import Callable, Dict, Optional

import pandas as pd
import pytest

import helpers.hcache_simple as hcacsimp
import helpers.hio as hio
import helpers.hllm_cli as hllmcli
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)

# Disable calling LLM when testing.
_RUN_REAL_LLM = False
# _RUN_REAL_LLM = True

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

# #############################################################################
# TestApplyLlmBase
# #############################################################################

class TestApplyLlmBase(hunitest.TestCase):
    """
    Base class with helper methods for testing apply_llm functions.

    Provides common helper methods used across different test classes to
    reduce code duplication and maintain consistency.
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

# #############################################################################
# Test_apply_llm_with_files1
# #############################################################################

@pytest.mark.skipif(
    not _RUN_REAL_LLM,
    reason="real LLM not enabled",
)
class Test_apply_llm_with_files1(TestApplyLlmBase):
    """
    Test apply_llm_with_files using both library and executable interfaces.

    Tests run various command-line configurations to ensure they execute
    without errors. Does not verify output correctness.
    """

    def test_library(self) -> None:
        """
        Test multiple command-line configurations using library interface.

        Tests various command-line argument combinations to ensure they
        execute without errors. Does not verify output correctness.
        """
        self._run_test_cases(use_llm_executable=False)

    @pytest.mark.skipif(
        not hllmcli._check_llm_executable(), reason="llm executable not found"
    )
    def test_executable(self) -> None:
        """
        Test multiple command-line configurations using executable interface.

        Tests various command-line argument combinations to ensure they
        execute without errors. Does not verify output correctness.
        """
        self._run_test_cases(use_llm_executable=True)

# #############################################################################
# Test_apply_llm_with_files2
# #############################################################################

@pytest.mark.skipif(
    not _RUN_REAL_LLM,
    reason="real LLM not enabled",
)
class Test_apply_llm_with_files2(TestApplyLlmBase):
    def test1_library(self) -> None:
        """
        Test input_text parameter using library interface.

        Tests that input_text parameter works correctly when text is provided
        directly instead of from a file. Does not verify output correctness.
        """
        self._run_test_cases_input_text(use_llm_executable=False)

    @pytest.mark.skipif(
        not hllmcli._check_llm_executable(), reason="llm executable not found"
    )
    def test1_executable(self) -> None:
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

    def test2_library(self) -> None:
        """
        Test print_only parameter using library interface.

        Tests that print_only parameter works correctly when output should be
        printed to screen instead of written to file. Does not verify output
        correctness.
        """
        self._run_test_cases_print_only(use_llm_executable=False)

    @pytest.mark.skipif(
        not hllmcli._check_llm_executable(), reason="llm executable not found"
    )
    def test2_executable(self) -> None:
        """
        Test print_only parameter using executable interface.

        Tests that print_only parameter works correctly when output should be
        printed to screen instead of written to file. Does not verify output
        correctness.
        """
        self._run_test_cases_print_only(use_llm_executable=True)

# #############################################################################
# Test_llm1
# #############################################################################

@pytest.mark.skipif(
    not _RUN_REAL_LLM,
    reason="real LLM not enabled",
)
class Test_llm1(hunitest.TestCase):
    """
    Test _llm() function with different models and prompt lengths.

    Tests verify that _llm() correctly processes prompts of varying lengths
    across different models, and tracks timing and cost information.
    """

    @staticmethod
    def get_short_prompt() -> str:
        """
        Get a short test prompt.

        :return: short system prompt string
        """
        prompt = "You are a helpful assistant. Answer concisely."
        return prompt

    @staticmethod
    def get_medium_prompt() -> str:
        """
        Get a medium-length test prompt.

        :return: medium-length system prompt string
        """
        prompt = """
        You are a helpful assistant. Your task is to provide clear and
        accurate answers to questions. Always be concise but thorough in
        your explanations. If you don't know something, acknowledge it.
        Use simple language that anyone can understand.
        """
        prompt = hprint.dedent(prompt)
        return prompt

    @staticmethod
    def get_long_prompt() -> str:
        """
        Get a long test prompt.

        :return: long system prompt string
        """
        prompt = """
        You are a highly knowledgeable AI assistant with expertise across
        multiple domains including technology, science, mathematics, and
        general knowledge. Your primary objectives are:

        1. Provide accurate and well-researched information
        2. Explain concepts clearly and thoroughly
        3. Use examples when they help clarify complex topics
        4. Cite sources or acknowledge uncertainty when appropriate
        5. Adapt your language to the user's level of understanding
        6. Break down complex problems into manageable steps
        7. Verify calculations and logical reasoning before responding
        8. Consider multiple perspectives when discussing controversial topics

        When answering questions:
        - Start with a direct answer to the question
        - Follow with supporting details and context
        - Use bullet points or numbered lists for clarity
        - Provide examples when helpful
        - Suggest follow-up resources if relevant

        Always maintain a professional, helpful, and respectful tone.
        """
        prompt = hprint.dedent(prompt)
        return prompt

    def test1(self) -> None:
        """
        Test _llm() with multiple models and prompt lengths.

        Tests short, medium, and long prompts across different models to
        verify proper handling and cost calculation. Reports results in a
        comprehensive table with time, cost, and cost-per-character metrics.
        """
        hcacsimp.set_cache_property("_test_llm", "mode", "DISABLE_CACHE")
        # Define test configurations with model-specific inputs.
        # Questions are designed to elicit longer responses for more accurate cost
        # comparisons.
        test_configs = [
            (
                "gpt-5-nano",
                "Explain the concept of machine learning and provide examples of its applications in real-world scenarios.",
            ),
            (
                "gpt-4o-mini",
                "Describe the history and culture of Paris, France, including its major landmarks and contributions to art and literature.",
            ),
            (
                "gpt-4o",
                "Explain what recursion is in computer science, provide multiple examples with code, and discuss when to use recursion versus iteration.",
            ),
        ]
        # Store results for tabular reporting.
        results = []
        # Run tests for each model and prompt type combination.
        for model, input_str in test_configs:
            for prompt_type, prompt_getter in [
                ("short", self.get_short_prompt),
                ("medium", self.get_medium_prompt),
                ("long", self.get_long_prompt),
            ]:
                _LOG.info("Testing model=%s with %s prompt", model, prompt_type)
                system_prompt = prompt_getter()
                # Run test.
                start_time = time.time()
                response, cost = hllmcli._llm(system_prompt, input_str, model)
                elapsed_time = time.time() - start_time
                # Check outputs.
                self.assertIsInstance(response, str)
                self.assertGreater(len(response), 0)
                self.assertIsInstance(cost, float)
                self.assertGreaterEqual(cost, 0.0)
                # Calculate cost per character and cost per 1M characters.
                response_len = len(response)
                cost_per_char = cost / response_len if response_len > 0 else 0.0
                cost_per_1m_chars = (
                    cost_per_char * 1_000_000 if response_len > 0 else 0.0
                )
                # Store results.
                results.append(
                    {
                        "Model": model,
                        "Prompt Type": prompt_type,
                        "Time (s)": elapsed_time,
                        "Cost ($)": cost,
                        "Response Length": response_len,
                        "Cost/Char ($)": cost_per_char,
                        "Cost/1M Chars ($)": cost_per_1m_chars,
                    }
                )
        # Create DataFrame for tabular display.
        results_df = pd.DataFrame(results)
        # Format numeric columns.
        results_df["Time (s)"] = results_df["Time (s)"].round(2)
        results_df["Cost ($)"] = results_df["Cost ($)"].round(6)
        results_df["Cost/Char ($)"] = results_df["Cost/Char ($)"].round(8)
        results_df["Cost/1M Chars ($)"] = results_df["Cost/1M Chars ($)"].round(
            2
        )
        # Log results table.
        _LOG.info("\n%s", hprint.frame("LLM Test Results"))
        with pd.option_context(
            "display.max_columns",
            None,
            "display.max_rows",
            None,
            "display.width",
            None,
            "display.max_colwidth",
            None,
        ):
            _LOG.info("\n%s", results_df.to_string(index=False))


# #############################################################################
# Test_apply_llm_batch1
# #############################################################################


def _eval_functor(input_str: str, *, delay: float = 0.0) -> str:
    """
    Evaluate the input string using eval and return the result as a string.

    :param input_str: mathematical expression to evaluate
    :return: result of evaluation as a string
    """
    _LOG.debug("input_str='%s'", input_str)
    if delay > 0.0:
        time.sleep(delay)
    result = eval(input_str)
    result_str = str(result)
    _LOG.debug("-> result_str='%s'", result_str)
    return result_str

# #############################################################################
# Test_apply_llm_batch1
# #############################################################################

class Test_apply_llm_batch1(hunitest.TestCase):
    """
    Test and compare three batch processing approaches.

    Tests:
    - apply_llm_batch_individual()
    - apply_llm_batch_with_shared_prompt()
    - apply_llm_batch_combined()
    to verify they return consistent results using a testing functor that uses
    eval.
    """

    @staticmethod
    def get_test_prompt() -> str:
        """
        Get a simple test prompt for batch processing.

        :return: system prompt string
        """
        prompt = "You are a calculator. Return only the numeric result."
        return prompt

    def helper(
        self,
        model: str,
        func: Callable,
        testing_functor: Optional[Callable[[str], str]],
    ) -> None:
        """
        Helper function to run a batch processing function with test inputs.

        :param func: batch processing function to test
        :param testing_functor: optional testing functor for mocking
        """
        _LOG.trace(hprint.to_str("model func testing_functor"))
        # Create test inputs.
        prompt = self.get_test_prompt()
        input_list = ["2 + 2", "3 * 3", "10 - 5", "20 / 4"]
        expected_responses = ["4", "9", "5", "5"]
        # Run the function.
        responses, cost = func(
            prompt=prompt,
            input_list=input_list,
            model=model,
            testing_functor=testing_functor,
        )
        # Check basic properties.
        responses = [str(int(float(r))) for r in responses]
        self.assertEqual(responses, expected_responses)
        if testing_functor is None:
            self.assertGreater(cost, 0.0)
        else:
            self.assertEqual(cost, 0.0)

    @pytest.mark.skipif(
        not _RUN_REAL_LLM,
        reason="real LLM not enabled",
    )
    def test_individual1(self) -> None:
        """
        Test apply_llm_batch_individual without testing_functor.

        This test uses the real LLM API.
        """
        model = "gpt-5-nano"
        func = hllmcli.apply_llm_batch_individual
        testing_functor = None
        self.helper(
            model,
            func,
            testing_functor,
        )

    def test_individual2(self) -> None:
        """
        Test apply_llm_batch_individual with testing_functor.

        This test uses a mock calculator instead of the real LLM API.
        """
        model = ""
        func = hllmcli.apply_llm_batch_individual
        testing_functor = _eval_functor
        self.helper(
            model,
            func,
            testing_functor,
        )

    @pytest.mark.skipif(
        not _RUN_REAL_LLM,
        reason="real LLM not enabled",
    )
    def test_shared1(self) -> None:
        """
        Test apply_llm_batch_with_shared_prompt without testing_functor.

        This test uses the real LLM API.
        """
        model = "gpt-5-nano"
        func = hllmcli.apply_llm_batch_with_shared_prompt
        testing_functor = None
        self.helper(
            model,
            func,
            testing_functor,
        )

    def test_shared2(self) -> None:
        """
        Test apply_llm_batch_with_shared_prompt with testing_functor.

        This test uses a mock calculator instead of the real LLM API.
        """
        model = ""
        func = hllmcli.apply_llm_batch_with_shared_prompt
        testing_functor = _eval_functor
        self.helper(
            model,
            func,
            testing_functor,
        )

    @pytest.mark.skipif(
        not _RUN_REAL_LLM,
        reason="real LLM not enabled",
    )
    def test_combined1(self) -> None:
        """
        Test apply_llm_batch_combined without testing_functor.

        This test uses the real LLM API.
        """
        model = "gpt-5-nano"
        # model = "gpt-4o-mini"
        func = hllmcli.apply_llm_batch_combined
        testing_functor = None
        self.helper(
            model,
            func,
            testing_functor,
        )

    def test_combined2(self) -> None:
        """
        Test apply_llm_batch_combined with testing_functor.

        This test uses a mock calculator instead of the real LLM API.
        """
        model = ""
        func = hllmcli.apply_llm_batch_combined
        testing_functor = _eval_functor
        self.helper(
            model,
            func,
            testing_functor,
        )

# #############################################################################
# Test_apply_llm_prompt_to_df1
# #############################################################################

class Test_apply_llm_prompt_to_df1(hunitest.TestCase):
    """
    Test apply_llm_prompt_to_df with testing_functor.

    This is used to test the logic around `apply_llm_batch_*()` functions.
    """

    @staticmethod
    def _extract_expression(obj) -> str:
        """
        Extract mathematical expression from a DataFrame row or string.

        :param obj: either a string or a pandas Series
        :return: extracted string for evaluation
        """
        if isinstance(obj, pd.Series):
            # Extract from DataFrame row.
            if "expression" in obj.index:
                expr = obj["expression"]
                # Handle None, NaN, or empty string.
                if pd.isna(expr) or expr == "":
                    return ""
                return str(expr)
            return ""
        else:
            # Already a string.
            if pd.isna(obj) or obj == "":
                return ""
            return str(obj)

    def helper(
        self,
        df: pd.DataFrame,
        batch_size: int,
        expected_df: pd.DataFrame,
        expected_stats: Dict[str, int],
    ) -> None:
        """
        Test apply_llm_prompt_to_df with testing_functor that uses eval.
        """
        # Prepare inputs.
        prompt = "Dummy"
        extractor = self._extract_expression
        # To test the progress bar.
        # delay = 0.5
        delay = 0.0
        testing_functor = lambda input_str: _eval_functor(input_str, delay=delay)
        # Run test.
        result_df, stats = hllmcli.apply_llm_prompt_to_df(
            prompt=prompt,
            df=df,
            extractor=extractor,
            target_col="result",
            batch_mode="individual",
            batch_size=batch_size,
            model="gpt-5-nano",
            testing_functor=testing_functor,
            use_sys_stderr=True,
        )
        # Check outputs.
        self.assert_equal(str(result_df), str(expected_df))
        elapsed_time = stats.pop("elapsed_time_in_seconds")
        self.assertGreater(elapsed_time, 0.0)
        self.assertEqual(stats, expected_stats)

    def helper_test1(self, batch_size: int) -> None:
        """
        Test apply_llm_prompt_to_df with testing_functor that uses eval.
        """
        # Prepare inputs.
        df = pd.DataFrame(
            {
                "expression": ["2 + 3", "10 * 5", "100 - 25", "15 / 3"],
            }
        )
        # Prepare outputs.
        expected_df = pd.DataFrame(
            {
                "expression": ["2 + 3", "10 * 5", "100 - 25", "15 / 3"],
                "result": ["5", "50", "75", "5.0"],
            }
        )
        num_items = len(df)
        expected_stats = {
            "num_items": num_items,
            "num_skipped": 0,
            "num_batches": (num_items + batch_size - 1) // batch_size,
            "total_cost_in_dollars": 0.0,
        }
        # Run test.
        self.helper(df, batch_size, expected_df, expected_stats)

    def helper_test2(self, batch_size: int) -> None:
        """
        Test apply_llm_prompt_to_df with larger dataframe and batch_size > 1.
        """
        # Prepare inputs.
        df = pd.DataFrame(
            {
                "expression": [
                    "1 + 1",
                    "2 * 3",
                    "10 - 5",
                    "20 / 4",
                    "3 ** 2",
                    "100 // 3",
                    "15 % 4",
                ],
            }
        )
        # Prepare outputs.
        expected_df = pd.DataFrame(
            {
                "expression": [
                    "1 + 1",
                    "2 * 3",
                    "10 - 5",
                    "20 / 4",
                    "3 ** 2",
                    "100 // 3",
                    "15 % 4",
                ],
                "result": ["2", "6", "5", "5.0", "9", "33", "3"],
            }
        )
        num_items = len(df)
        expected_stats = {
            "num_items": num_items,
            "num_skipped": 0,
            "num_batches": (num_items + batch_size - 1) // batch_size,
            "total_cost_in_dollars": 0.0,
        }
        # Run test.
        self.helper(df, batch_size, expected_df, expected_stats)

    def helper_test3(self, batch_size: int) -> None:
        """
        Test apply_llm_prompt_to_df with pre-filled target column values.

        This test verifies that all rows are processed and pre-filled values
        are overwritten with computed results from the testing_functor.
        """
        # Prepare inputs.
        df = pd.DataFrame(
            {
                "expression": [
                    "5 + 5",
                    "3 * 4",
                    "20 - 8",
                    "16 / 2",
                    "2 ** 3",
                ],
            }
        )
        # Pre-fill some values in the target column.
        df["result"] = [None, "12", None, None, "8"]
        # Prepare outputs.
        expected_df = pd.DataFrame(
            {
                "expression": [
                    "5 + 5",
                    "3 * 4",
                    "20 - 8",
                    "16 / 2",
                    "2 ** 3",
                ],
                "result": ["10", "12", "12", "8.0", "8"],
            }
        )
        num_items = len(df)
        expected_stats = {
            "num_items": num_items,
            "num_skipped": 0,
            "num_batches": (num_items + batch_size - 1) // batch_size,
            "total_cost_in_dollars": 0.0,
        }
        # Run test.
        self.helper(df, batch_size, expected_df, expected_stats)

    def helper_test4(self, batch_size: int) -> None:
        """
        Test apply_llm_prompt_to_df with rows that have empty extraction results.

        This test verifies that rows with empty or None expressions are skipped
        and marked with empty string in the result column.
        """
        # Prepare inputs.
        df = pd.DataFrame(
            {
                "expression": ["5 + 5", "", "10 + 10", None, "15 + 15"],
            }
        )
        # Prepare outputs.
        expected_df = pd.DataFrame(
            {
                "expression": ["5 + 5", "", "10 + 10", None, "15 + 15"],
                "result": ["10", "", "20", "", "30"],
            }
        )
        num_items = len(df)
        expected_stats = {
            "num_items": num_items,
            "num_skipped": 2,
            "num_batches": (num_items + batch_size - 1) // batch_size,
            "total_cost_in_dollars": 0.0,
        }
        # Run test.
        self.helper(df, batch_size, expected_df, expected_stats)

    def helper_test5(self, batch_size: int) -> None:
        """
        Test apply_llm_prompt_to_df with batch where all items have missing data.

        This test verifies that batches with all empty/None items are skipped
        entirely and the else branch is executed.
        """
        # Prepare inputs.
        df = pd.DataFrame(
            {
                "expression": ["1 + 1", "", None, "", "5 + 5"],
            }
        )
        # Prepare outputs.
        expected_df = pd.DataFrame(
            {
                "expression": ["1 + 1", "", None, "", "5 + 5"],
                "result": ["2", "", "", "", "10"],
            }
        )
        num_items = len(df)
        expected_stats = {
            "num_items": num_items,
            "num_skipped": 3,
            "num_batches": (num_items + batch_size - 1) // batch_size,
            "total_cost_in_dollars": 0.0,
        }
        # Run test.
        self.helper(df, batch_size, expected_df, expected_stats)

    # batch_size=1

    def test1_num_batch1(self) -> None:
        self.helper_test1(batch_size=1)

    def test2_num_batch1(self) -> None:
        self.helper_test2(batch_size=1)

    def test3_num_batch1(self) -> None:
        self.helper_test3(batch_size=1)

    def test4_num_batch1(self) -> None:
        self.helper_test4(batch_size=1)

    def test5_num_batch1(self) -> None:
        self.helper_test5(batch_size=1)

    # batch_size=2

    def test1_num_batch2(self) -> None:
        self.helper_test1(batch_size=2)

    def test2_num_batch2(self) -> None:
        self.helper_test2(batch_size=2)

    def test3_num_batch2(self) -> None:
        self.helper_test3(batch_size=2)

    def test4_num_batch2(self) -> None:
        self.helper_test4(batch_size=2)

    def test5_num_batch2(self) -> None:
        self.helper_test5(batch_size=2)

    # batch_size=3

    def test1_num_batch3(self) -> None:
        self.helper_test1(batch_size=3)

    def test2_num_batch3(self) -> None:
        self.helper_test2(batch_size=3)

    def test3_num_batch3(self) -> None:
        self.helper_test3(batch_size=3)

    def test4_num_batch3(self) -> None:
        self.helper_test4(batch_size=3)

    def test5_num_batch3(self) -> None:
        self.helper_test5(batch_size=3)

    # batch_size=10

    def test1_num_batch10(self) -> None:
        self.helper_test1(batch_size=10)

    def test2_num_batch10(self) -> None:
        self.helper_test2(batch_size=10)

    def test3_num_batch10(self) -> None:
        self.helper_test3(batch_size=10)

    def test4_num_batch10(self) -> None:
        self.helper_test4(batch_size=10)

    def test5_num_batch10(self) -> None:
        self.helper_test5(batch_size=10)

# #############################################################################
# Test_apply_llm_prompt_to_df2
# #############################################################################

# TODO(gp): Convert this into a unit test for apply_llm_prompt.
class Test_apply_llm_prompt_to_df2(hunitest.TestCase):
    """
    Test apply_llm_prompt_to_df with mocked cache.
    """

    @staticmethod
    def get_test_prompt() -> str:
        """
        Get a simple test prompt for LLM.

        This prompt asks the LLM to sum two numbers, providing a simple
        and predictable test case.

        :return: system prompt string
        """
        prompt = """
        You are a calculator. Given input in the format "a + b", return only
        the sum as a number.

        Return ONLY the numeric result, nothing else.
        """
        prompt = hprint.dedent(prompt)
        return prompt

    @staticmethod
    def extract_test_fields(obj) -> str:
        """
        Extract test fields from a DataFrame row or string.

        :param obj: either a string or a pandas Series
        :return: extracted string for LLM processing
        """
        if isinstance(obj, pd.Series):
            # Extract from DataFrame row.
            if "num1" in obj.index and "num2" in obj.index:
                num1 = obj["num1"]
                num2 = obj["num2"]
                return f"{num1} + {num2}"
            return ""
        else:
            # Already a string.
            return obj

    def create_test_df(self) -> pd.DataFrame:
        """
        Create a minimal DataFrame with test data (2 rows).
        """
        df = pd.DataFrame(
            {
                "num1": [2, 10],
                "num2": [3, 15],
            }
        )
        return df

    def run_cached_apply_llm_prompt_to_df(self) -> None:
        prompt = self.get_test_prompt()
        df = self.create_test_df()
        prompt = self.get_test_prompt()
        extractor = self.extract_test_fields
        result_df, _ = hllmcli.apply_llm_prompt_to_df(
            prompt=prompt,
            df=df,
            extractor=extractor,
            target_col="sum",
            batch_mode="individual",
            model="gpt-5-nano",
            batch_size=10,
            use_sys_stderr=True,
        )
        _LOG.debug("result_df=%s", result_df)
        # Check outputs.
        expected_df = pd.DataFrame(
            {
                "num1": [2, 10],
                "num2": [3, 15],
                "sum": ["5", "25"],
            }
        )
        self.assert_equal(str(result_df), str(expected_df))

    @pytest.mark.skipif(
        not _RUN_REAL_LLM,
        reason="real LLM not enabled",
    )
    def test1(self) -> None:
        """
        Warm up cache by calling apply_llm and save cache to file.

        This test creates a cache by calling apply_llm with test data,
        then saves the cache to a file for use in subsequent tests.
        """
        # Create a file with the cache content for test2 in the input directory.
        input_dir = self.get_input_dir(
            test_class_name=self.__class__.__name__,
            test_method_name="test2",
        )
        hcacsimp.set_cache_dir(input_dir)
        # Call apply_llm to warm up the cache for both inputs.
        self.run_cached_apply_llm_prompt_to_df()
        # Flush the cache to disk to ensure it's saved.
        hcacsimp.flush_cache_to_disk("_llm")
        func_cache_data = hcacsimp.get_disk_cache("_llm")
        # Check that the cache file exists and is not empty.
        hcacsimp.sanity_check_function_cache(
            func_cache_data, assert_on_empty=True
        )

    def test2(self) -> None:
        """
        Test apply_llm_prompt_to_df with mocked cache.

        This test
        - loads the cache file created in test1
        - mocks the cache with the data from the cache file
        - verifies that apply_llm_prompt_to_df uses the cached values without
          hitting the LLM API.
        """
        # Prepare inputs.
        # # Set up temporary cache directory.
        scratch_dir = self.get_scratch_space()
        hcacsimp.set_cache_dir(scratch_dir)
        # Load the saved cache file from test2's input directory.
        input_dir = self.get_input_dir()
        # Load the cache data from the cache file.
        cache_file = os.path.join(input_dir, "tmp.cache_simple._llm.json")
        _LOG.debug("cache_file=%s", cache_file)
        func_cache_data = hcacsimp._load_func_cache_data_from_file(cache_file, "json")
        _LOG.debug("func_cache_data=%s", func_cache_data)
        hcacsimp.sanity_check_function_cache(
            func_cache_data, assert_on_empty=True
        )
        _LOG.debug("Loaded func_cache_data=\n%s", func_cache_data)
        hcacsimp.mock_cache_from_disk("_llm", func_cache_data)
        try:
            # Set abort_on_cache_miss to ensure we don't hit the LLM API.
            hcacsimp.set_cache_property("_llm", "abort_on_cache_miss", True)
            # Run apply_llm_prompt_to_df with mocked cache.
            self.run_cached_apply_llm_prompt_to_df()
        finally:
            # Reset the cache property.
            hcacsimp.set_cache_property("_llm", "abort_on_cache_miss", False)

    def test3(self) -> None:
        """
        Test apply_llm_prompt_to_df without mocked cache.

        This test verifies that apply_llm_prompt_to_df raises an error when the
        cache is missed and abort_on_cache_miss=True.
        """
        # Set up temporary cache directory.
        scratch_dir = self.get_scratch_space()
        hcacsimp.set_cache_dir(scratch_dir)
        try:
            # Set abort_on_cache_miss to ensure we don't hit the LLM API.
            hcacsimp.set_cache_property("_llm", "abort_on_cache_miss", True)
            with self.assertRaises(ValueError) as fail:
                # Run apply_llm_prompt_to_df without mocked cache.
                self.run_cached_apply_llm_prompt_to_df()
            self.assertIn("Cache miss", str(fail.exception))
        finally:
            # Reset the cache property.
            hcacsimp.set_cache_property("_llm", "abort_on_cache_miss", False)

# #############################################################################
# Test_apply_llm_batch_cost_comparison
# #############################################################################

@pytest.mark.skipif(
    not _RUN_REAL_LLM,
    reason="real LLM not enabled",
)
class Test_apply_llm_batch_cost_comparison(hunitest.TestCase):
    """
    Test and compare costs of different batch processing approaches.

    Tests both direct batch function calls and apply_llm_prompt_to_df with
    different batch modes.
    """

    @staticmethod
    def get_person_industry_prompt() -> str:
        """
        Get the industry classification prompt for testing.

        :return: system prompt string
        """
        prompt = """
        Given the following list of industries with examples, classify the text into the
        corresponding industry:
        - Industrial & Built Environment
        - Transportation & Logistics
        - Consumer & Retail
        - Technology & Digital Services
        - Health & Life Sciences
        - Finance & Professional Services
        - Public & Social Sector
        - Media, Marketing & Experiences

        You MUST report the industry exactly as one of the options above. Do not
        include any other text.
        If you are not sure about the industry, return "unknown".
        """
        prompt = hprint.dedent(prompt)
        return prompt

    @staticmethod
    def get_test_industries() -> list:
        """
        Get a list of test company descriptions for industry classification.

        :return: list of company descriptions
        """
        industries = [
            "A company that sells fresh produce and operates farms",
            "A car manufacturer that produces electric vehicles",
            "A construction company specializing in residential buildings",
            "A company that manufactures consumer electronics and appliances",
            "An online learning platform providing courses for students",
            "An electric utility company providing power generation services",
            "A civil engineering firm providing infrastructure design",
            "A company organizing corporate events and conferences",
            "A bank providing retail banking and investment services",
            "A nonprofit organization focused on environmental conservation",
            "A hospital providing emergency and surgical medical services",
            "A staffing agency providing recruitment and temp worker services",
            "A data center company providing server hardware and infrastructure",
            "A software development company creating enterprise resource planning systems",
            "A cybersecurity firm providing threat detection and penetration testing",
            "A cloud infrastructure provider offering scalable computing resources",
            "An IT company providing network management and server maintenance",
            "A consulting firm helping businesses integrate SAP and Oracle systems",
            "A help desk company providing 24/7 technical support services",
            "A data analytics company building business intelligence dashboards",
            "A DevOps company providing CI/CD pipeline automation tools",
            "A law firm specializing in corporate mergers and acquisitions",
            "A shipping company providing international freight and logistics",
            "A factory manufacturing industrial machinery and equipment",
            "An advertising agency creating brand campaigns for consumer products",
            "A streaming service providing movies and TV shows online",
            "A pharmaceutical company developing new drugs and vaccines",
            "A commercial real estate firm managing office building portfolios",
            "An online retailer selling clothing and accessories through eCommerce",
            "A sports equipment manufacturer producing gear for athletes",
            "A telecommunications company providing mobile and internet services",
            "A hotel chain operating luxury resorts and vacation properties",
        ]
        return industries

    def helper(self, model: str, batch_size: int) -> None:
        """
        Compare costs and time of different batch modes in apply_llm_prompt_to_df.

        This test compares the performance of three batch modes:
        1. individual: processes each query separately
        2. shared_prompt: uses shared prompt context
        3. combined: combines all queries into single API call
        """
        # Reset cache before each batch mode to ensure fair comparison.
        hcacsimp.set_cache_dir(self.get_scratch_space())
        _LOG.info("Cache directory: %s", hcacsimp.get_cache_dir())
        hcacsimp.reset_cache("", interactive=False)
        # Prepare inputs.
        prompt = self.get_person_industry_prompt()
        industries = self.get_test_industries()
        testing_functor = None
        # Create DataFrame from test data.
        df = pd.DataFrame({"description": industries})

        # Extractor function to get text from DataFrame row.
        def extractor(obj):
            if isinstance(obj, pd.Series):
                return obj["description"]
            return str(obj)

        # Test each batch mode.
        batch_modes = ["individual", "shared_prompt", "combined"]
        results = []
        # Store result DataFrames to compare across batch modes.
        result_dfs = {}
        for batch_mode in batch_modes:
            _LOG.info(
                "\n%s", hprint.frame("Testing batch mode: %s" % batch_mode)
            )
            # Create a copy of the DataFrame for this batch mode.
            df_copy = df.copy()
            # Call apply_llm_prompt_to_df with the current batch mode.
            result_df, stats = hllmcli.apply_llm_prompt_to_df(
                prompt=prompt,
                df=df_copy,
                extractor=extractor,
                target_col="industry",
                batch_mode=batch_mode,
                model=model,
                batch_size=batch_size,
                testing_functor=testing_functor,
                use_sys_stderr=True,
            )
            # Get elapsed time from stats.
            elapsed_time = stats["elapsed_time_in_seconds"]
            # Print time and cost for this batch mode.
            _LOG.info(
                "Batch mode '%s': Time=%.2fs, Cost=$%.6f",
                batch_mode,
                elapsed_time,
                stats["total_cost_in_dollars"],
            )
            # Store results.
            results.append(
                {
                    "Batch Mode": batch_mode,
                    "Time (s)": elapsed_time,
                    "Num Items": stats["num_items"],
                    "Num Skipped": stats["num_skipped"],
                    "Num Batches": stats["num_batches"],
                    "Total Cost ($)": stats["total_cost_in_dollars"],
                }
            )
            # Store result DataFrame for comparison.
            result_dfs[batch_mode] = result_df
            # Verify results.
            self.assertEqual(len(result_df), len(industries))
            self.assertIn("industry", result_df.columns)
        # Check that all batch modes produce the same results.
        # Compare each batch mode's results with the first batch mode.
        first_batch_mode = batch_modes[0]
        first_result_df = result_dfs[first_batch_mode]["industry"].reset_index(
            drop=True
        )
        for batch_mode in batch_modes[1:]:
            compare_result_df = result_dfs[batch_mode]["industry"].reset_index(
                drop=True
            )
            # Create a comparison DataFrame between the two batch modes.
            match_df = pd.DataFrame(
                {
                    first_batch_mode: first_result_df,
                    batch_mode: compare_result_df,
                }
            )
            # Add a column with whether they match or not.
            match_df["Match"] = (
                match_df[first_batch_mode] == match_df[batch_mode]
            )
            all_match = match_df["Match"].all()
            if not all_match:
                _LOG.error(
                    "Results mismatch between '%s' and '%s':\n%s",
                    first_batch_mode,
                    batch_mode,
                    match_df,
                )
        _LOG.info(
            "Results match between '%s' and '%s'",
            first_batch_mode,
            batch_mode,
        )
        # Create comparison DataFrame.
        comparison_df = pd.DataFrame(results)
        # Add relative metrics compared to individual mode.
        individual_time = comparison_df.loc[
            comparison_df["Batch Mode"] == "individual", "Time (s)"
        ].iloc[0]
        individual_cost = comparison_df.loc[
            comparison_df["Batch Mode"] == "individual", "Total Cost ($)"
        ].iloc[0]
        comparison_df["Time Ratio"] = comparison_df["Time (s)"] / individual_time
        comparison_df["Cost Ratio"] = (
            comparison_df["Total Cost ($)"] / individual_cost
        )
        # Format the DataFrame for better readability.
        comparison_df["Time (s)"] = comparison_df["Time (s)"].round(2)
        comparison_df["Total Cost ($)"] = comparison_df["Total Cost ($)"].round(
            6
        )
        comparison_df["Time Ratio"] = comparison_df["Time Ratio"].round(2)
        comparison_df["Cost Ratio"] = comparison_df["Cost Ratio"].round(2)
        # Print comparison_df without truncation.
        with pd.option_context(
            "display.max_columns",
            None,
            "display.max_rows",
            None,
            "display.width",
            None,
            "display.max_colwidth",
            None,
        ):
            _LOG.info("Batch mode comparison:\n%s", comparison_df)

    #     Batch Mode  Time (s)  Num Items  Num Batches  Total Cost ($)  Time Ratio  Cost Ratio
    #     individual     17.98         32            4        0.000653        1.00        1.00
    #  shared_prompt     17.60         32            4        0.000998        0.98        1.53
    #       combined      8.42         32            4        0.000330        0.47        0.51
    #
    #     Batch Mode  Time (s)  Num Items  Num Batches  Total Cost ($)  Time Ratio  Cost Ratio
    #     individual     19.27         32            2        0.000651        1.00        1.00
    #  shared_prompt     19.34         32            2        0.001385        1.00        2.13
    #       combined      7.45         32            2        0.000277        0.39        0.43
    #
    #     Batch Mode  Time (s)  Num Items  Num Batches  Total Cost ($)  Time Ratio  Cost Ratio
    #     individual     16.38         32            1        0.000651        1.00        1.00
    #  shared_prompt     17.51         32            1        0.002148        1.07        3.30
    #       combined      6.15         32            1        0.000251        0.38        0.39
    def test1(self) -> None:
        model = "gpt-4o-mini"
        batch_size = 8
        self.helper(model, batch_size)
        #
        batch_size = 16
        self.helper(model, batch_size)
        #
        batch_size = 32
        self.helper(model, batch_size)

    #    Batch Mode  Time (s)  Num Items  Num Batches  Total Cost ($)  Time Ratio  Cost Ratio
    #    individual     68.57         32            4        0.002711        1.00        1.00
    # shared_prompt     53.07         32            4        0.002638        0.77        0.97
    #      combined     29.30         32            4        0.001654        0.43        0.61
    #
    #    Batch Mode  Time (s)  Num Items  Num Batches  Total Cost ($)  Time Ratio  Cost Ratio
    #    individual     68.40         32            2        0.002788        1.00        1.00
    # shared_prompt     53.88         32            2        0.002809        0.79        1.01
    #      combined     25.99         32            2        0.001643        0.38        0.59
    #
    #    Batch Mode  Time (s)  Num Items  Num Batches  Total Cost ($)  Time Ratio  Cost Ratio
    #    individual     59.38         32            1        0.002610        1.00        1.00
    # shared_prompt     52.61         32            1        0.002482        0.89        0.95
    #      combined     15.79         32            1        0.001118        0.27        0.43
    def test2(self) -> None:
        model = "gpt-5-nano"
        batch_size = 8
        self.helper(model, batch_size)
        #
        batch_size = 16
        self.helper(model, batch_size)
        #
        batch_size = 32
        self.helper(model, batch_size)
