import os
from typing import List, Tuple

import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

import pandas as pd

import helpers.hunit_test as hunitest

import dev_scripts_helpers.llms.openrouter_models_table as omt


class Test_normalize_for_fuzzy_matching(hunitest.TestCase):
    """
    Test normalization of model names for fuzzy matching.
    """

    def helper(self, name: str, expected: str) -> None:
        """
        Test helper for _normalize_for_fuzzy_matching.

        :param name: Input model name
        :param expected: Expected normalized output
        """
        actual = omt._normalize_for_fuzzy_matching(name)
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


class Test_normalize_for_aa_lookup(hunitest.TestCase):
    """
    Test normalization of model names to Artificial Analysis slug format.
    """

    def helper(self, name: str, expected: str) -> None:
        """
        Test helper for _normalize_for_aa_lookup.

        :param name: Input model name
        :param expected: Expected AA slug format
        """
        actual = omt._normalize_for_aa_lookup(name)
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




class Test_build_model_ids_dataframe(hunitest.TestCase):
    """
    Test building dataframe with model IDs.
    """

    def test1(self) -> None:
        """
        Test building dataframe with single model.
        """
        model_ids = ["google/gemini-3.1-pro-preview"]
        actual = omt._build_model_ids_dataframe(model_ids)
        self.assertEqual(len(actual), 1)
        self.assertEqual(list(actual.columns), ["Model_ID"])
        self.assertEqual(actual.iloc[0]["Model_ID"], "google/gemini-3.1-pro-preview")

    def test2(self) -> None:
        """
        Test building dataframe with multiple models.
        """
        model_ids = [
            "google/gemini-3.1-pro-preview",
            "anthropic/claude-opus-4.7",
            "openai/gpt-4-omni",
        ]
        actual = omt._build_model_ids_dataframe(model_ids)
        self.assertEqual(len(actual), 3)
        self.assertEqual(list(actual.columns), ["Model_ID"])
        self.assertEqual(list(actual["Model_ID"]), model_ids)


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
        actual = omt._merge_dataframes(base_df, [pricing_df])
        self.assertEqual(len(actual), 2)
        self.assertEqual(list(actual.columns), [
            "Model_ID",
            "Name",
            "Input_Cost",
            "Output_Cost",
        ])
        self.assertEqual(actual.iloc[0]["Input_Cost"], 1.0)
        self.assertEqual(actual.iloc[1]["Output_Cost"], 10.0)

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
        actual = omt._merge_dataframes(base_df, [df1, df2])
        self.assertEqual(len(actual), 2)
        self.assertEqual(list(actual.columns), [
            "Model_ID",
            "Name",
            "Cost",
            "Speed",
        ])


class Test_build_openrouter_id_to_aa_slug(hunitest.TestCase):
    """
    Test building mapping from OpenRouter ID to Artificial Analysis slug.
    """

    def test1(self) -> None:
        """
        Test building mapping with matching models.
        """
        api_lookup = {
            "anthropic/claude-opus-4.7": {
                "name": "Anthropic: Claude Opus 4.7"
            },
            "openai/gpt-4-omni": {
                "name": "OpenAI: GPT-4 Omni"
            },
        }
        aa_models = {
            "claude-opus-4-7": {"name": "Claude Opus 4.7"},
            "gpt-4-omni": {"name": "GPT-4 Omni"},
        }
        actual = omt._build_openrouter_id_to_aa_slug(api_lookup, aa_models)
        self.assertEqual(
            actual["anthropic/claude-opus-4.7"],
            "claude-opus-4-7"
        )
        self.assertEqual(actual["openai/gpt-4-omni"], "gpt-4-omni")

    def test2(self) -> None:
        """
        Test building mapping with non-matching models.
        """
        api_lookup = {
            "unknown/model-xyz": {"name": "Unknown Model XYZ"}
        }
        aa_models = {
            "claude-opus-4-7": {"name": "Claude Opus 4.7"}
        }
        actual = omt._build_openrouter_id_to_aa_slug(api_lookup, aa_models)
        self.assertEqual(len(actual), 0)

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
        actual = omt._build_openrouter_id_to_aa_slug(api_lookup, aa_models)
        self.assertEqual(len(actual), 1)
        self.assertIn("google/gemini-3.1-pro-preview", actual)


class Test_build_openrouter_id_to_permaslug(hunitest.TestCase):
    """
    Test building mapping from OpenRouter ID to permaslug.
    """

    def test1(self) -> None:
        """
        Test exact model ID match.
        """
        api_lookup = {
            "openai/gpt-4-omni": {"name": "GPT-4 Omni"},
        }
        available_permaslugs = ["openai/gpt-4-omni"]
        actual = omt._build_openrouter_id_to_permaslug(
            api_lookup, available_permaslugs
        )
        self.assertEqual(actual["openai/gpt-4-omni"], "openai/gpt-4-omni")

    def test2(self) -> None:
        """
        Test fuzzy matching on model name.
        """
        api_lookup = {
            "openai/gpt-4-omni": {"name": "GPT-4 Omni"},
        }
        available_permaslugs = ["gpt-4-omni"]
        actual = omt._build_openrouter_id_to_permaslug(
            api_lookup, available_permaslugs
        )
        self.assertEqual(actual["openai/gpt-4-omni"], "gpt-4-omni")

    def test3(self) -> None:
        """
        Test no match for unknown model.
        """
        api_lookup = {
            "unknown/model-xyz": {"name": "Unknown Model"},
        }
        available_permaslugs = ["gpt-4-omni", "claude-opus"]
        actual = omt._build_openrouter_id_to_permaslug(
            api_lookup, available_permaslugs
        )
        self.assertEqual(len(actual), 0)

    def test4(self) -> None:
        """
        Test skips models without provider prefix.
        """
        api_lookup = {
            "openai/gpt-4-omni": {"name": "GPT-4 Omni"},
            "canonical-slug": {"name": "Some Model"},
        }
        available_permaslugs = ["gpt-4-omni", "some-model"]
        actual = omt._build_openrouter_id_to_permaslug(
            api_lookup, available_permaslugs
        )
        self.assertEqual(len(actual), 1)
        self.assertIn("openai/gpt-4-omni", actual)



# #############################################################################
# Test_openrouter_models_table_py
# #############################################################################


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
        actions: List[str] = [],
    ) -> str:
        """
        Run the script with given models file and actions.

        :param models_file: Path to file with model IDs
        :param executable: Path to the openrouter_models_table.py script
        :param actions: List of action flags (e.g., ["openrouter_pricing"])
        :return: Script output string
        """
        cmd_parts = [executable, f"--models_from_file={models_file}"]
        for action in actions:
            cmd_parts.extend(["-a", action])
        cmd_parts.append("--cache_mode=DISABLE_CACHE")
        cmd = " ".join(cmd_parts)
        _, result = hsystem.system_to_string(cmd, abort_on_error=True)
        return result

    def test1(self) -> None:
        """
        Test with single model, cache disabled, and no external API calls.
        """
        models_file, executable = self._setup_test()
        result = self._run_script(models_file, executable)
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
        models_file, executable = self._setup_test()
        result = self._run_script(models_file, executable, actions=["openrouter_pricing"])
        # Should have Model_ID and pricing columns
        self.assertIn("Model_ID", result)
        self.assertIn("Input_Cost", result)
        self.assertIn("Output_Cost", result)
        self.assertIn("Context", result)

    def test3(self) -> None:
        """
        Test with single action: openrouter_throughput.
        """
        models_file, executable = self._setup_test()
        result = self._run_script(models_file, executable, actions=["openrouter_throughput"])
        # Should have Model_ID and Speed columns
        self.assertIn("Model_ID", result)
        self.assertIn("Speed_(tok/s)", result)

    def test4(self) -> None:
        """
        Test with single action: aa_benchmarks.
        """
        models_file, executable = self._setup_test()
        result = self._run_script(models_file, executable, actions=["aa_benchmarks"])
        # Should have Model_ID and benchmark columns
        self.assertIn("Model_ID", result)
        self.assertIn("Coding_IQ", result)
        self.assertIn("General_IQ", result)

    def test5(self) -> None:
        """
        Test with single action: openrouter_per_model_usage.
        """
        models_file, executable = self._setup_test()
        result = self._run_script(models_file, executable, actions=["openrouter_per_model_usage"])
        # Should have Model_ID and usage columns
        self.assertIn("Model_ID", result)
        self.assertIn("Week_Tokens", result)
        self.assertIn("Month_Tokens", result)

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
        # Should have columns from both actions
        self.assertIn("Model_ID", result)
        self.assertIn("Input_Cost", result)
        self.assertIn("Coding_IQ", result)

    def test7(self) -> None:
        """
        Test with all actions together.
        """
        models_file, executable = self._setup_test()
        result = self._run_script(models_file, executable)
        # Should have columns from all actions
        self.assertIn("Model_ID", result)
        self.assertIn("Input_Cost", result)
        self.assertIn("Speed_(tok/s)", result)
        self.assertIn("Coding_IQ", result)
        self.assertIn("Week_Tokens", result)
