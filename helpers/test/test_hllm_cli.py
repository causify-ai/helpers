import logging
import os
import pickle
import time
from typing import Dict

import pandas as pd
import pytest

import helpers.hcache_simple as hcacsimp
import helpers.hio as hio
import helpers.hllm_cli as hllmcli
import helpers.hprint as hprint
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


# #############################################################################
# Test_apply_llm_prompt_to_df1
# #############################################################################


class Test_apply_llm_prompt_to_df1(hunitest.TestCase):
    """
    Test apply_llm_prompt_to_df with testing_functor.
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

    @staticmethod
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
        #delay = 0.5
        delay = 0.0
        testing_functor = lambda input_str: self._eval_functor(input_str, delay=delay)
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

    def _helper_test1(self, batch_size: int) -> None:
        """
        Test apply_llm_prompt_to_df with testing_functor that uses eval.
        """
        # Prepare inputs.
        df = pd.DataFrame({
            "expression": ["2 + 3", "10 * 5", "100 - 25", "15 / 3"],
        })
        # Prepare outputs.
        expected_df = pd.DataFrame({
            "expression": ["2 + 3", "10 * 5", "100 - 25", "15 / 3"],
            "result": ["5", "50", "75", "5.0"],
        })
        num_items = len(df)
        expected_stats = {
            "num_items": num_items,
            "num_skipped": 0,
            "num_batches": (num_items + batch_size - 1) // batch_size,
        }
        # Run test.
        self.helper(df, batch_size, expected_df, expected_stats)

    def _helper_test2(self, batch_size: int) -> None:
        """
        Test apply_llm_prompt_to_df with larger dataframe and batch_size > 1.
        """
        # Prepare inputs.
        df = pd.DataFrame({
            "expression": [
                "1 + 1",
                "2 * 3",
                "10 - 5",
                "20 / 4",
                "3 ** 2",
                "100 // 3",
                "15 % 4",
            ],
        })
        # Prepare outputs.
        expected_df = pd.DataFrame({
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
        })
        num_items = len(df)
        expected_stats = {
            "num_items": num_items,
            "num_skipped": 0,
            "num_batches": (num_items + batch_size - 1) // batch_size,
        }
        # Run test.
        self.helper(df, batch_size, expected_df, expected_stats)

    def _helper_test3(self, batch_size: int) -> None:
        """
        Test apply_llm_prompt_to_df with pre-filled target column values.

        This test verifies that all rows are processed and pre-filled values
        are overwritten with computed results from the testing_functor.
        """
        # Prepare inputs.
        df = pd.DataFrame({
            "expression": [
                "5 + 5",
                "3 * 4",
                "20 - 8",
                "16 / 2",
                "2 ** 3",
            ],
        })
        # Pre-fill some values in the target column.
        df["result"] = [None, "12", None, None, "8"]
        # Prepare outputs.
        expected_df = pd.DataFrame({
            "expression": [
                "5 + 5",
                "3 * 4",
                "20 - 8",
                "16 / 2",
                "2 ** 3",
            ],
            "result": ["10", "12", "12", "8.0", "8"],
        })
        num_items = len(df)
        expected_stats = {
            "num_items": num_items,
            "num_skipped": 0,
            "num_batches": (num_items + batch_size - 1) // batch_size,
        }
        # Run test.
        self.helper(df, batch_size, expected_df, expected_stats)

    def _helper_test4(self, batch_size: int) -> None:
        """
        Test apply_llm_prompt_to_df with rows that have empty extraction results.

        This test verifies that rows with empty or None expressions are skipped
        and marked with empty string in the result column.
        """
        # Prepare inputs.
        df = pd.DataFrame({
            "expression": ["5 + 5", "", "10 + 10", None, "15 + 15"],
        })
        # Prepare outputs.
        expected_df = pd.DataFrame({
            "expression": ["5 + 5", "", "10 + 10", None, "15 + 15"],
            "result": ["10", "", "20", "", "30"],
        })
        num_items = len(df)
        expected_stats = {
            "num_items": num_items,
            "num_skipped": 2,
            "num_batches": (num_items + batch_size - 1) // batch_size,
        }
        # Run test.
        self.helper(df, batch_size, expected_df, expected_stats)

    def _helper_test5(self, batch_size: int) -> None:
        """
        Test apply_llm_prompt_to_df with batch where all items have missing data.

        This test verifies that batches with all empty/None items are skipped
        entirely and the else branch is executed.
        """
        # Prepare inputs.
        df = pd.DataFrame({
            "expression": ["1 + 1", "", None, "", "5 + 5"],
        })
        # Prepare outputs.
        expected_df = pd.DataFrame({
            "expression": ["1 + 1", "", None, "", "5 + 5"],
            "result": ["2", "", "", "", "10"],
        })
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


class Test_apply_llm_prompt_to_df2(hunitest.TestCase):
    """
    Test apply_llm_prompt_to_df with mocked cache.
    """

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

    def _create_test_df(self) -> pd.DataFrame:
        # Create a minimal DataFrame with test data (2 rows).
        df = pd.DataFrame({
            "num1": [2, 10],
            "num2": [3, 15],
        })
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
        expected_df = pd.DataFrame({
            "num1": [2, 10],
            "num2": [3, 15],
            "sum": [5, 25],
        })
        self.assert_equal(result_df, expected_df)
        # Reset the cache property.
        hcacsimp.set_cache_property("apply_llm", "abort_on_cache_miss", False)
