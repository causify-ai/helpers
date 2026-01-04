import logging
import os
import pickle
import time
from typing import Callable, Dict, List, Optional, Tuple

import pandas as pd
import pytest

import helpers.hcache_simple as hcacsimp
import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hllm_cli as hllmcli
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)

# Whether to run tests that use the real LLM API.
#_RUN_REAL_LLM = False
_RUN_REAL_LLM = True

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
# Test_apply_llm_with_files
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


@pytest.mark.skipif(
    not _RUN_REAL_LLM, reason="real LLM not enabled",
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

@pytest.mark.skipif(
    not _RUN_REAL_LLM, reason="real LLM not enabled",
)
class Test_apply_llm_with_files2(TestApplyLlmBase):

    # TODO(ai_gp): -> test1_library
    def test_input_text_library(self) -> None:
        """
        Test input_text parameter using library interface.

        Tests that input_text parameter works correctly when text is provided
        directly instead of from a file. Does not verify output correctness.
        """
        self._run_test_cases_input_text(use_llm_executable=False)

    # TODO(ai_gp): -> test1_executable
    @pytest.mark.skipif(
        not hllmcli._check_llm_executable(), reason="llm executable not found"
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

    # TODO(ai_gp): -> test2_library
    def test_print_only_library(self) -> None:
        """
        Test print_only parameter using library interface.

        Tests that print_only parameter works correctly when output should be
        printed to screen instead of written to file. Does not verify output
        correctness.
        """
        self._run_test_cases_print_only(use_llm_executable=False)

    # TODO(ai_gp): -> test2_executable
    @pytest.mark.skipif(
        not hllmcli._check_llm_executable(), reason="llm executable not found"
    )
    def test_print_only_executable(self) -> None:
        """
        Test print_only parameter using executable interface.

        Tests that print_only parameter works correctly when output should be
        printed to screen instead of written to file. Does not verify output
        correctness.
        """
        self._run_test_cases_print_only(use_llm_executable=True)


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

    # TODO(ai_gp): -> get_test_prompt
    @staticmethod
    def _get_test_prompt() -> str:
        """
        Get a simple test prompt for batch processing.

        :return: system prompt string
        """
        prompt = "You are a calculator. Return only the numeric result."
        return prompt

    # TODO(ai_gp): -> helper
    def _helper(
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
        prompt = self._get_test_prompt()
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
        not _RUN_REAL_LLM, reason="real LLM not enabled",
    )
    def test_individual1(self) -> None:
        """
        Test apply_llm_batch_individual without testing_functor.

        This test uses the real LLM API.
        """
        model = "gpt-5-nano"
        func = hllmcli.apply_llm_batch_individual
        testing_functor = None
        self._helper(
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
        self._helper(
            model,
            func,
            testing_functor,
        )

    @pytest.mark.skipif(
        not _RUN_REAL_LLM, reason="real LLM not enabled",
    )
    def test_shared1(self) -> None:
        """
        Test apply_llm_batch_with_shared_prompt without testing_functor.

        This test uses the real LLM API.
        """
        model = "gpt-5-nano"
        func = hllmcli.apply_llm_batch_with_shared_prompt
        testing_functor = None
        self._helper(
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
        self._helper(
            model,
            func,
            testing_functor,
        )

    @pytest.mark.skipif(
        not _RUN_REAL_LLM, reason="real LLM not enabled",
    )
    def test_combined1(self) -> None:
        """
        Test apply_llm_batch_combined without testing_functor.

        This test uses the real LLM API.
        """
        model = "gpt-5-nano"
        #model = "gpt-4o-mini"
        func = hllmcli.apply_llm_batch_combined
        testing_functor = None
        self._helper(
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
        self._helper(
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
        testing_functor = lambda input_str: _eval_functor(
            input_str, delay=delay
        )
        # Run test.
        result_df, stats = hllmcli.apply_llm_prompt_to_df(
            prompt=prompt,
            df=df,
            extractor=extractor,
            target_col="result",
            batch_size=batch_size,
            model="gpt-5-nano",
            testing_functor=testing_functor,
        )
        # Check outputs.
        self.assert_equal(str(result_df), str(expected_df))
        self.assert_equal(str(stats), str(expected_stats))

    # TODO(ai_gp): -> helper_test1
    def _helper_test1(self, batch_size: int) -> None:
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
        }
        # Run test.
        self.helper(df, batch_size, expected_df, expected_stats)

    # TODO(ai_gp): -> helper_test2
    def _helper_test2(self, batch_size: int) -> None:
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
        }
        # Run test.
        self.helper(df, batch_size, expected_df, expected_stats)

    # TODO(ai_gp): -> helper_test3
    def _helper_test3(self, batch_size: int) -> None:
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
        }
        # Run test.
        self.helper(df, batch_size, expected_df, expected_stats)

    # TODO(ai_gp): -> helper_test4
    def _helper_test4(self, batch_size: int) -> None:
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
        }
        # Run test.
        self.helper(df, batch_size, expected_df, expected_stats)

    # TODO(ai_gp): -> helper_test5
    def _helper_test5(self, batch_size: int) -> None:
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
        }
        # Run test.
        self.helper(df, batch_size, expected_df, expected_stats)

    # batch_size=1

    def test1_num_batch1(self) -> None:
        self._helper_test1(batch_size=1)

    def test2_num_batch1(self) -> None:
        self._helper_test2(batch_size=1)

    def test3_num_batch1(self) -> None:
        self._helper_test3(batch_size=1)

    def test4_num_batch1(self) -> None:
        self._helper_test4(batch_size=1)

    def test5_num_batch1(self) -> None:
        self._helper_test5(batch_size=1)

    # batch_size=2

    def test1_num_batch2(self) -> None:
        self._helper_test1(batch_size=2)

    def test2_num_batch2(self) -> None:
        self._helper_test2(batch_size=2)

    def test3_num_batch2(self) -> None:
        self._helper_test3(batch_size=2)

    def test4_num_batch2(self) -> None:
        self._helper_test4(batch_size=2)

    def test5_num_batch2(self) -> None:
        self._helper_test5(batch_size=2)

    # batch_size=3

    def test1_num_batch3(self) -> None:
        self._helper_test1(batch_size=3)

    def test2_num_batch3(self) -> None:
        self._helper_test2(batch_size=3)

    def test3_num_batch3(self) -> None:
        self._helper_test3(batch_size=3)

    def test4_num_batch3(self) -> None:
        self._helper_test4(batch_size=3)

    def test5_num_batch3(self) -> None:
        self._helper_test5(batch_size=3)

    # batch_size=10

    def test1_num_batch10(self) -> None:
        self._helper_test1(batch_size=10)

    def test2_num_batch10(self) -> None:
        self._helper_test2(batch_size=10)

    def test3_num_batch10(self) -> None:
        self._helper_test3(batch_size=10)

    def test4_num_batch10(self) -> None:
        self._helper_test4(batch_size=10)

    def test5_num_batch10(self) -> None:
        self._helper_test5(batch_size=10)


# #############################################################################
# Test_apply_llm_prompt_to_df2
# #############################################################################

# TODO(gp): Convert this into a unit test for apply_llm_prompt.
class Test_apply_llm_prompt_to_df2(hunitest.TestCase):
    """
    Test apply_llm_prompt_to_df with mocked cache.
    """

    # TODO(ai_gp): -> get_test_prompt
    @staticmethod
    def _get_test_prompt() -> str:
        """
        Get a simple test prompt for LLM.

        This prompt asks the LLM to sum two numbers, providing a simple
        and predictable test case.

        :return: system prompt string
        """
        prompt = """
        You are a calculator. Given input in the format "a + b", return only the sum as a number.

        Return ONLY the numeric result, nothing else.
        """
        prompt = hprint.dedent(prompt)
        return prompt

    # TODO(ai_gp): -> extract_test_fields
    @staticmethod
    def _extract_test_fields(obj) -> str:
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

    # TODO(ai_gp): -> create_test_df
    def _create_test_df(self) -> pd.DataFrame:
        # Create a minimal DataFrame with test data (2 rows).
        df = pd.DataFrame(
            {
                "num1": [2, 10],
                "num2": [3, 15],
            }
        )
        return df

    def test_create_cache(self) -> None:
        """
        Warm up cache by calling apply_llm and save cache to file.

        This test creates a cache by calling apply_llm with test data,
        then saves the cache to a file for use in subsequent tests.
        """
        # Prepare inputs.
        # Set up temporary cache directory to avoid polluting the main cache.
        scratch_dir = self.get_scratch_space()
        hcacsimp.set_cache_dir(scratch_dir)
        # Get the test prompt using local helper function.
        prompt = self._get_test_prompt()
        # Call apply_llm to warm up the cache for both inputs.
        df = self._create_test_df()
        # Get the prompt and extractor using local helper functions.
        prompt = self._get_test_prompt()
        extractor = self._extract_test_fields
        # Call apply_llm_prompt_to_df.
        result_df, _ = hllmcli.apply_llm_prompt_to_df(
            prompt=prompt,
            df=df,
            extractor=extractor,
            target_col="sum",
            batch_size=10,
            model="gpt-5-nano",
        )
        _LOG.debug("result_df=%s", result_df)
        # Flush the cache to disk to ensure it's saved.
        hcacsimp.flush_cache_to_disk("apply_llm")
        # Read the data from the cache file.
        cache_data = hcacsimp.get_disk_cache("apply_llm")
        cache_data_str = hcacsimp.cache_data_to_str(cache_data)
        _LOG.debug("Created cache_data_str=\n%s", cache_data_str)
        # Verify cache has entries.
        hcacsimp.sanity_check_cache(cache_data, assert_on_empty=True)
        # Create a file with the cache content.
        input_dir = self.get_input_dir(
            test_class_name=self.__class__.__name__,
            test_method_name="test_create_cache",
        )
        hio.create_dir(input_dir, incremental=True)
        cache_file = os.path.join(input_dir, "test_cache.pkl")
        cmd = "cp -r %s %s" % (scratch_dir, cache_file)
        hsystem.system(cmd)
        _LOG.info("Cache saved to %s", cache_file)

    def test1(self) -> None:
        """
        Test apply_llm_prompt_to_df with mocked cache.

        This test loads the cache file created in test_create_cache,
        mocks the cache, and verifies that apply_llm_prompt_to_df
        uses the cached values without hitting the LLM API.
        """
        # Prepare inputs.
        # Set up temporary cache directory.
        scratch_dir = self.get_scratch_space()
        hcacsimp.set_cache_dir(scratch_dir)
        # Load the saved cache file from test_create_cache's input directory.
        input_dir = self.get_input_dir()
        cache_file = os.path.join(input_dir, "test_cache.pkl")
        with open(cache_file, "rb") as f:
            cache_data = pickle.load(f)
        cache_data_str = hcacsimp.cache_data_to_str(cache_data)
        _LOG.debug("Loaded cache_data_str=\n%s", cache_data_str)
        hcacsimp.mock_cache_from_disk("apply_llm", cache_data)
        # Create a minimal DataFrame with test data (2 rows).
        df = self._create_test_df()
        # Get the prompt and extractor using local helper functions.
        prompt = self._get_test_prompt()
        extractor = self._extract_test_fields
        # Set abort_on_cache_miss to ensure we don't hit the LLM API.
        hcacsimp.set_cache_property("apply_llm", "abort_on_cache_miss", True)
        # Run test.
        # Call apply_llm_prompt_to_df.
        result_df, _ = hllmcli.apply_llm_prompt_to_df(
            prompt=prompt,
            df=df,
            extractor=extractor,
            target_col="sum",
            batch_size=10,
            model=None,
        )
        # Check outputs.
        expected_df = pd.DataFrame(
            {
                "num1": [2, 10],
                "num2": [3, 15],
                "sum": [5, 25],
            }
        )
        self.assert_equal(result_df, expected_df)
        # Reset the cache property.
        hcacsimp.set_cache_property("apply_llm", "abort_on_cache_miss", False)


# #############################################################################
# Test_apply_llm_batch_cost_comparison
# #############################################################################

@pytest.mark.skipif(
    not _RUN_REAL_LLM, reason="real LLM not enabled",
)
class Test_apply_llm_batch_cost_comparison(hunitest.TestCase):
    """
    Test and compare costs of different batch processing approaches.

    Tests both direct batch function calls and apply_llm_prompt_to_df with
    different batch modes.
    """

    # TODO(ai_gp): -> get_person_industry_prompt
    @staticmethod
    def _get_person_industry_prompt() -> str:
        """
        Get the industry classification prompt for testing.

        :return: system prompt string
        """
        prompt = """
        Given the following list of industries with examples, classify the text into the
        corresponding industry:
        - Agriculture
        - Automotive
        - Construction
        - Consumer Goods
        - Education
        - Energy & Utilities
        - Engineering Services
        - Event Management
        - Financial Services
        - Government & Nonprofits
        - Healthcare
        - Human Resources & Staffing
        - IT - Hardware
        - IT - Software
        - IT - Cybersecurity
        - IT - Cloud Services
        - IT - Managed Services
        - IT - Consulting & Integration
        - IT - Support Services
        - IT - Data & Analytics
        - IT - DevOps & Automation
        - Legal Services
        - Logistics & Transportation
        - Manufacturing
        - Marketing & Advertising Agencies
        - Media & Entertainment
        - Pharmaceutical & Biotechnology
        - Real Estate
        - Retail & eCommerce
        - Sports & Recreation
        - Telecommunications
        - Travel & Hospitality

        You MUST report the industry exactly as one of the options above. Do not
        include any other text.
        If you are not sure about the industry, return "unknown".
        """
        prompt = hprint.dedent(prompt)
        return prompt

    # TODO(ai_gp): -> get_test_industries
    @staticmethod
    def _get_test_industries() -> list:
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
        ]
        return industries

    # TODO(ai_gp): -> test1
    def test_batch_mode_comparison(self) -> None:
        """
        Compare costs and time of different batch modes in apply_llm_prompt_to_df.

        This test compares the performance of three batch modes:
        1. individual - processes each query separately
        2. batch - uses shared prompt context
        3. combined - combines all queries into single API call
        """
        # TODO(gp): Reset cache.
        # Prepare inputs.
        prompt = self._get_person_industry_prompt()
        industries = self._get_test_industries()
        testing_functor = None
        model = "gpt-4o-mini"
        # Create DataFrame from test data.
        df = pd.DataFrame({"description": industries})
        # Extractor function to get text from DataFrame row.
        def extractor(obj):
            if isinstance(obj, pd.Series):
                return obj["description"]
            return str(obj)
        # Test each batch mode.
        batch_modes = ["individual", "batch_with_shared_prompt", "combined"]
        results = []
        for batch_mode in batch_modes:
            _LOG.info(hprint.frame("Testing batch mode: %s", batch_mode))
            # Create a copy of the DataFrame for this batch mode.
            df_copy = df.copy()
            # Measure time.
            start_time = time.time()
            # Call apply_llm_prompt_to_df with the current batch mode.
            result_df, stats = hllmcli.apply_llm_prompt_to_df(
                prompt=prompt,
                df=df_copy,
                extractor=extractor,
                target_col="industry",
                batch_mode=batch_mode,
                model=model,
                batch_size=10,
                testing_functor=testing_functor,
            )
            elapsed_time = time.time() - start_time
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
            # Verify results.
            self.assertEqual(len(result_df), len(industries))
            self.assertIn("industry", result_df.columns)
        # Create comparison DataFrame.
        comparison_df = pd.DataFrame(results)
        _LOG.info("Batch mode comparison:\n%s", comparison_df)

    # TODO(ai_gp): -> create_cost_summary
    def _create_cost_summary(
        self,
        individual_cost: float,
        batch_cost: float,
        combined_cost: float,
        num_queries: int,
    ) -> str:
        """
        Create a markdown summary of cost comparison.

        :param individual_cost: cost of individual approach
        :param batch_cost: cost of batch approach
        :param combined_cost: cost of combined approach
        :param num_queries: number of queries processed
        :return: markdown summary string
        """
        # Create a DataFrame with cost comparison data.
        comparison_df = pd.DataFrame(
            {
                "Approach": ["Individual", "Batch (Individual)", "Combined"],
                "Total Cost ($)": [individual_cost, batch_cost, combined_cost],
                "Cost per Query ($)": [
                    individual_cost / num_queries,
                    batch_cost / num_queries,
                    combined_cost / num_queries,
                ],
                "Relative to Individual": [
                    1.00,
                    batch_cost / individual_cost if individual_cost > 0 else 0,
                    combined_cost / individual_cost if individual_cost > 0 else 0,
                ],
            }
        )
        # Format the DataFrame as a string with proper precision.
        comparison_str = comparison_df.to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}",
        )
        # Create the summary with configuration and results.
        summary = f"""# Cost Comparison: Three Approaches for Batch LLM Processing

## Test Configuration
- Model: gpt-4o-mini
- Number of queries: {num_queries}
- Prompt: Industry classification

## Cost Results

{comparison_str}
"""
        return summary
