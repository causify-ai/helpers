import logging
import os
import pprint
from typing import List, Optional, Tuple

import pandas as pd
import pytest

import dev_scripts_helpers.llms.openrouter_models_table as dshlomota
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hpandas as hpandas
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)

# #############################################################################
# Test_normalize_for_fuzzy_matching
# #############################################################################


# TODO(ai_gp): /factor_common_code
class Test_normalize_for_fuzzy_matching(hunitest.TestCase):
    """
    Test `_normalize_for_fuzzy_matching()` for normalization of model names for
    fuzzy matching.
    """

    def helper(self, name: str, expected: str) -> None:
        """
        Test helper for `_normalize_for_fuzzy_matching()`.

        :param name: Input model name
        :param expected: Expected normalized output
        """
        actual = dshlomota._normalize_for_fuzzy_matching(name)
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test normalization of short model name.
        """
        name = "claude-opus-4.7"
        expected = "claude-opus"
        self.helper(name, expected)

    def test2(self) -> None:
        """
        Test normalization of full versioned OpenRouter ID.
        """
        name = "anthropic/claude-4.7-opus-20260416"
        expected = "claude"
        self.helper(name, expected)

    def test3(self) -> None:
        """
        Test normalization of short OpenRouter ID with version.
        """
        name = "google/gemini-3.1-pro-preview"
        expected = "gemini-preview"
        self.helper(name, expected)

    def test4(self) -> None:
        """
        Test normalization removes date suffixes.
        """
        name = "claude-3-opus-20260416"
        expected = "claude-3-opus"
        self.helper(name, expected)

    def test5(self) -> None:
        """
        Test normalization with v-prefix version.
        """
        name = "deepseek-v3-chat"
        expected = "deepseek--chat"
        self.helper(name, expected)

    def test6(self) -> None:
        """
        Test normalization with mixed case.
        """
        name = "OpenAI/GPT-4.0-Turbo-20240101"
        expected = "gpt"
        self.helper(name, expected)

    def test7(self) -> None:
        """
        Test normalization with single name (no provider prefix).
        """
        name = "mistral-7b"
        expected = "mistral-7b"
        self.helper(name, expected)


# #############################################################################
# Test_normalize_for_aa_lookup
# #############################################################################


class Test_normalize_for_aa_lookup(hunitest.TestCase):
    """
    Test `_normalize_for_aa_lookup()` for normalization of model names to
    Artificial Analysis slug format.
    """

    def helper(self, name: str, expected: str) -> None:
        """
        Test helper for _normalize_for_aa_lookup.

        :param name: Input model name
        :param expected: Expected AA slug format
        """
        actual = dshlomota._normalize_for_aa_lookup(name)
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test normalization of OpenRouter ID to AA slug.
        """
        name = "anthropic/claude-opus-4.7"
        expected = "claude-opus-4-7"
        self.helper(name, expected)

    def test2(self) -> None:
        """
        Test normalization of display name with colon.
        """
        name = "Anthropic: Claude Opus 4.7"
        expected = "claude-opus-4-7"
        self.helper(name, expected)

    def test3(self) -> None:
        """
        Test normalization of short model name.
        """
        name = "claude-opus-4.7"
        expected = "claude-opus-4-7"
        self.helper(name, expected)

    def test4(self) -> None:
        """
        Test normalization of already-normalized slug.
        """
        name = "claude-opus-4-7"
        expected = "claude-opus-4-7"
        self.helper(name, expected)

    def test5(self) -> None:
        """
        Test normalization of name with uppercase.
        """
        name = "GPT-4.0-TURBO"
        expected = "gpt-4-0-turbo"
        self.helper(name, expected)

    def test6(self) -> None:
        """
        Test normalization with spaces and dots.
        """
        name = "Google Gemini 2.0 Flash"
        expected = "google-gemini-2-0-flash"
        self.helper(name, expected)


# #############################################################################
# Test_build_model_ids_dataframe
# #############################################################################


class Test_build_model_ids_dataframe(hunitest.TestCase):
    """
    Test building dataframe with model IDs.
    """

    def test1(self) -> None:
        """
        Test building dataframe with single model.
        """
        model_ids = ["google/gemini-3.1-pro-preview"]
        actual = dshlomota._build_model_ids_dataframe(model_ids)
        actual_string = hpandas.df_to_str(actual, num_rows=None)
        expected_string = ""
        self.assert_equal(actual_string, expected_string)

    def test2(self) -> None:
        """
        Test building dataframe with multiple models.
        """
        model_ids = [
            "google/gemini-3.1-pro-preview",
            "anthropic/claude-opus-4.7",
            "openai/gpt-4-omni",
        ]
        actual = dshlomota._build_model_ids_dataframe(model_ids)
        actual_string = hpandas.df_to_str(actual, num_rows=None)
        expected_string = ""
        self.assert_equal(actual_string, expected_string)


# #############################################################################
# Test_merge_dataframes
# #############################################################################


class Test_merge_dataframes(hunitest.TestCase):
    """
    Test merging dataframes on Model_ID column.
    """

    def test1(self) -> None:
        """
        Test merging two dataframes.
        """
        base_df = pd.DataFrame(
            {
                "Model_ID": ["model1", "model2"],
                "Name": ["Model 1", "Model 2"],
            }
        )
        pricing_df = pd.DataFrame(
            {
                "Model_ID": ["model1", "model2"],
                "Input_Cost": [1.0, 2.0],
                "Output_Cost": [5.0, 10.0],
            }
        )
        actual = dshlomota._merge_dataframes(base_df, [pricing_df])
        actual_string = hpandas.df_to_str(actual, num_rows=None)
        expected_string = ""
        self.assert_equal(actual_string, expected_string)

    def test2(self) -> None:
        """
        Test merging multiple dataframes.
        """
        base_df = pd.DataFrame(
            {"Model_ID": ["model1", "model2"], "Name": ["M1", "M2"]}
        )
        df1 = pd.DataFrame(
            {"Model_ID": ["model1", "model2"], "Cost": [1.0, 2.0]}
        )
        df2 = pd.DataFrame(
            {"Model_ID": ["model1", "model2"], "Speed": [25.5, 18.2]}
        )
        actual = dshlomota._merge_dataframes(base_df, [df1, df2])
        actual_string = hpandas.df_to_str(actual, num_rows=None)
        expected_string = ""
        self.assert_equal(actual_string, expected_string)


# #############################################################################
# Test_build_openrouter_id_to_aa_slug
# #############################################################################


class Test_build_openrouter_id_to_aa_slug(hunitest.TestCase):
    """
    Test building mapping from OpenRouter ID to Artificial Analysis slug.
    """

    def test1(self) -> None:
        """
        Test building mapping with matching models.
        """
        api_lookup = {
            "anthropic/claude-opus-4.7": {"name": "Anthropic: Claude Opus 4.7"},
            "openai/gpt-4-omni": {"name": "OpenAI: GPT-4 Omni"},
        }
        aa_models = {
            "claude-opus-4-7": {"name": "Claude Opus 4.7"},
            "gpt-4-omni": {"name": "GPT-4 Omni"},
        }
        actual = dshlomota._build_openrouter_id_to_aa_slug(api_lookup, aa_models)
        actual_string = pprint.pformat(actual)
        expected_string = ""
        self.assert_equal(actual_string, expected_string)

    def test2(self) -> None:
        """
        Test building mapping with non-matching models.
        """
        api_lookup = {"unknown/model-xyz": {"name": "Unknown Model XYZ"}}
        aa_models = {"claude-opus-4-7": {"name": "Claude Opus 4.7"}}
        actual = dshlomota._build_openrouter_id_to_aa_slug(api_lookup, aa_models)
        actual_string = pprint.pformat(actual)
        expected_string = ""
        self.assert_equal(actual_string, expected_string)

    def test3(self) -> None:
        """
        Test building mapping skips models without provider prefix.
        """
        api_lookup = {
            "google/gemini-3.1-pro-preview": {
                "name": "Google: Gemini 3.1 Pro Preview"
            },
            "canonical-slug": {"name": "Some Model"},
        }
        aa_models = {
            "gemini-3-1-pro-preview": {"name": "Gemini 3.1 Pro Preview"}
        }
        actual = dshlomota._build_openrouter_id_to_aa_slug(api_lookup, aa_models)
        actual_string = pprint.pformat(actual)
        expected_string = ""
        self.assert_equal(actual_string, expected_string)


# #############################################################################
# Test_build_openrouter_id_to_permaslug
# #############################################################################


class Test_build_openrouter_id_to_permaslug(hunitest.TestCase):
    """
    Test `_build_openrouter_id_to_permaslug()` for building mapping from
    OpenRouter ID to permaslug.
    """

    def test1(self) -> None:
        """
        Test exact model ID match.
        """
        api_lookup = {
            "openai/gpt-4-omni": {"name": "GPT-4 Omni"},
        }
        available_permaslugs = ["openai/gpt-4-omni"]
        actual = dshlomota._build_openrouter_id_to_permaslug(
            api_lookup, available_permaslugs
        )
        actual_string = pprint.pformat(actual)
        expected_string = pprint.pformat({"openai/gpt-4-omni": "openai/gpt-4-omni"})
        self.assert_equal(actual_string, expected_string)

    def test2(self) -> None:
        """
        Test fuzzy matching on model name.
        """
        api_lookup = {
            "openai/gpt-4-omni": {"name": "GPT-4 Omni"},
        }
        available_permaslugs = ["gpt-4-omni"]
        actual = dshlomota._build_openrouter_id_to_permaslug(
            api_lookup, available_permaslugs
        )
        actual_string = pprint.pformat(actual)
        expected_string = pprint.pformat({"openai/gpt-4-omni": "gpt-4-omni"})
        self.assert_equal(actual_string, expected_string)

    def test3(self) -> None:
        """
        Test no match for unknown model.
        """
        api_lookup = {
            "unknown/model-xyz": {"name": "Unknown Model"},
        }
        available_permaslugs = ["gpt-4-omni", "claude-opus"]
        actual = dshlomota._build_openrouter_id_to_permaslug(
            api_lookup, available_permaslugs
        )
        actual_string = pprint.pformat(actual)
        expected_string = pprint.pformat({})
        self.assert_equal(actual_string, expected_string)

    def test4(self) -> None:
        """
        Test skips models without provider prefix.
        """
        api_lookup = {
            "openai/gpt-4-omni": {"name": "GPT-4 Omni"},
            "canonical-slug": {"name": "Some Model"},
        }
        available_permaslugs = ["gpt-4-omni", "some-model"]
        actual = dshlomota._build_openrouter_id_to_permaslug(
            api_lookup, available_permaslugs
        )
        actual_string = pprint.pformat(actual)
        expected_string = pprint.pformat({"openai/gpt-4-omni": "gpt-4-omni"})
        self.assert_equal(actual_string, expected_string)


# #############################################################################
# Test_openrouter_models_table_py
# #############################################################################


@pytest.mark.skip(
    reason="Requires API key and connects to third party APIs. Run manually."
)
class Test_openrouter_models_table_py(hunitest.TestCase):
    """
    End-to-end tests for openrouter_models_table.py executable.
    """

    def _setup_test(self) -> Tuple[str, str]:
        """
        Setup test environment: create models file and find executable.
        """
        scratch_space = self.get_scratch_space()
        models_file = os.path.join(scratch_space, "test_models.txt")
        model_ids_content = """
        google/gemini-3.1-pro-preview
        """
        hio.to_file(models_file, hprint.dedent(model_ids_content))
        executable = hgit.find_file_in_git_tree("openrouter_models_table.py")
        return models_file, executable

    def _run_script(
        self,
        models_file: str,
        executable: str,
        *,
        actions: Optional[List[str]] = None,
    ) -> str:
        """
        Run the script with given models file and actions.

        :param models_file: Path to file with model IDs
        :param executable: Path to the openrouter_models_table.py script
        :param actions: List of action flags (e.g., ["openrouter_pricing"])
        :return: Script output string
        """
        if actions is None:
            actions = []
        cmd_parts = [executable, f"--models_from_file={models_file}"]
        for action in actions:
            cmd_parts.extend(["-a", action])
        cmd_parts.append("--cache_mode=DISABLE_CACHE")
        cmd = " ".join(cmd_parts)
        _, result = hsystem.system_to_string(cmd, abort_on_error=True)
        return result

    def _check_output_columns_and_rows(
        self,
        result: str,
        expected_columns: List[str],
        expected_num_rows: int = 1,
    ) -> None:
        """
        Check that the output contains expected columns and the right number of
        data rows.

        :param result: Script output string
        :param expected_columns: Column names that should appear in the output
        :param expected_num_rows: Expected number of data rows
        """
        for col in expected_columns:
            self.assertIn(col, result)
        # Count data rows by looking for lines with the model ID pattern.
        # The model ID "google/gemini-3.1-pro-preview" appears once per data row.
        model_id = "google/gemini-3.1-pro-preview"
        num_rows = result.count(model_id)
        self.assertEqual(num_rows, expected_num_rows)

    def test1(self) -> None:
        """
        Test with single model, cache disabled, and no external API calls.
        """
        models_file, executable = self._setup_test()
        result = self._run_script(models_file, executable)
        _LOG.info("Result:\n%s", result)
        # Check outputs.
        # Expected from command: script attempts to run and fetch data
        # This test validates the script structure and argument parsing
        # If APIs are available, output should contain expected columns
        self._check_output_columns_and_rows(
            result, ["Name", "Model_ID", "Input_Cost", "Output_Cost"]
        )

    def test2(self) -> None:
        """
        Test with single action: openrouter_pricing.
        """
        models_file, executable = self._setup_test()
        result = self._run_script(
            models_file, executable, actions=["openrouter_pricing"]
        )
        _LOG.info("Result:\n%s", result)
        # Check columns and rows.
        self._check_output_columns_and_rows(
            result,
            ["Model_ID", "Input_Cost", "Output_Cost", "Context"],
        )

    def test3(self) -> None:
        """
        Test with single action: openrouter_throughput.
        """
        models_file, executable = self._setup_test()
        result = self._run_script(
            models_file, executable, actions=["openrouter_throughput"]
        )
        _LOG.info("Result:\n%s", result)
        # Should have Model_ID and Speed columns
        self._check_output_columns_and_rows(
            result, ["Model_ID", "Speed_(tok/s)"]
        )

    def test4(self) -> None:
        """
        Test with single action: aa_benchmarks.
        """
        models_file, executable = self._setup_test()
        result = self._run_script(
            models_file, executable, actions=["aa_benchmarks"]
        )
        _LOG.info("Result:\n%s", result)
        # Should have Model_ID and benchmark columns
        self._check_output_columns_and_rows(
            result, ["Model_ID", "Coding_IQ", "General_IQ"]
        )

    def test5(self) -> None:
        """
        Test with single action: openrouter_per_model_usage.
        """
        models_file, executable = self._setup_test()
        result = self._run_script(
            models_file, executable, actions=["openrouter_per_model_usage"]
        )
        _LOG.info("Result:\n%s", result)
        # Should have Model_ID and usage columns
        self._check_output_columns_and_rows(
            result, ["Model_ID", "Week_Tokens", "Month_Tokens"]
        )

    def test6(self) -> None:
        """
        Test with multiple actions: pricing and benchmarks.
        """
        models_file, executable = self._setup_test()
        result = self._run_script(
            models_file,
            executable,
            actions=["openrouter_pricing", "aa_benchmarks"],
        )
        _LOG.info("Result:\n%s", result)
        # Should have columns from both actions
        self._check_output_columns_and_rows(
            result, ["Model_ID", "Input_Cost", "Coding_IQ"]
        )

    def test7(self) -> None:
        """
        Test with all actions together.
        """
        models_file, executable = self._setup_test()
        result = self._run_script(models_file, executable)
        _LOG.info("Result:\n%s", result)
        # Should have columns from all actions
        self._check_output_columns_and_rows(
            result,
            ["Model_ID", "Input_Cost", "Speed_(tok/s)", "Coding_IQ", "Week_Tokens"],
        )
