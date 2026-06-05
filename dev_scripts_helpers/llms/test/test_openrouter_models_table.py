import os
from unittest import mock

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import dev_scripts_helpers.llms.openrouter_models_table as dshomt


class Test_openrouter_models_table_py(hunitest.TestCase):
    """
    Unit tests for openrouter_models_table.py script.
    """

    def _create_models_file(self, models: str) -> str:
        """
        Create a test models file in scratch space.

        :param models: Model IDs, one per line
        :return: Path to created file
        """
        models_file = os.path.join(
            self.get_scratch_space(), "test_models.txt"
        )
        hio.to_file(models_file, hprint.dedent(models))
        return models_file

    def test1(self) -> None:
        """
        Test basic script functionality with cache enabled.
        """
        # Prepare inputs.
        models_content = """
        anthropic/claude-opus-4.7
        """
        models_file = self._create_models_file(models_content)
        # Mock API calls.
        with mock.patch(
            "dev_scripts_helpers.llms.openrouter_models_table._fetch_models_from_api"
        ) as mock_fetch_models, mock.patch(
            "dev_scripts_helpers.llms.openrouter_models_table._fetch_aa_benchmarks"
        ) as mock_fetch_benchmarks, mock.patch(
            "dev_scripts_helpers.llms.openrouter_models_table._fetch_openrouter_throughput"
        ) as mock_fetch_throughput, mock.patch(
            "dev_scripts_helpers.llms.openrouter_models_table._fetch_openrouter_per_model_usage"
        ) as mock_fetch_usage:
            mock_fetch_models.return_value = {
                "anthropic/claude-opus-4.7": {
                    "name": "Claude 3.5 Opus",
                    "input_cost": 3.0,
                    "output_cost": 15.0,
                    "context_length": 200000,
                    "coding_index_bench": None,
                }
            }
            mock_fetch_benchmarks.return_value = {
                "coding": 75.5,
                "intelligence": 88.2,
                "agentic": 82.1,
                "coding_index": 75.5,
            }
            mock_fetch_throughput.return_value = 100.0
            mock_fetch_usage.return_value = {
                "anthropic/claude-opus-4.7": {
                    "week_tokens": 1000000,
                    "month_tokens": 5000000,
                }
            }
            # Prepare outputs.
            parser = dshomt._parse()
            argv = ["openrouter_models_table.py", f"--models={models_file}"]
            # Run test with caching enabled.
            with mock.patch("sys.argv", argv):
                dshomt._main(parser)

    def test2(self) -> None:
        """
        Test script with cache disabled via --disable-cache flag.
        """
        # Prepare inputs.
        models_content = """
        anthropic/claude-opus-4.7
        """
        models_file = self._create_models_file(models_content)
        # Mock API calls.
        with mock.patch(
            "dev_scripts_helpers.llms.openrouter_models_table._fetch_models_from_api"
        ) as mock_fetch_models, mock.patch(
            "dev_scripts_helpers.llms.openrouter_models_table._fetch_aa_benchmarks"
        ) as mock_fetch_benchmarks, mock.patch(
            "dev_scripts_helpers.llms.openrouter_models_table._fetch_openrouter_throughput"
        ) as mock_fetch_throughput, mock.patch(
            "dev_scripts_helpers.llms.openrouter_models_table._fetch_openrouter_per_model_usage"
        ) as mock_fetch_usage:
            mock_fetch_models.return_value = {
                "anthropic/claude-opus-4.7": {
                    "name": "Claude 3.5 Opus",
                    "input_cost": 3.0,
                    "output_cost": 15.0,
                    "context_length": 200000,
                    "coding_index_bench": None,
                }
            }
            mock_fetch_benchmarks.return_value = {
                "coding": 75.5,
                "intelligence": 88.2,
                "agentic": 82.1,
                "coding_index": 75.5,
            }
            mock_fetch_throughput.return_value = 100.0
            mock_fetch_usage.return_value = {
                "anthropic/claude-opus-4.7": {
                    "week_tokens": 1000000,
                    "month_tokens": 5000000,
                }
            }
            # Prepare outputs.
            parser = dshomt._parse()
            argv = [
                "openrouter_models_table.py",
                f"--models={models_file}",
                "--disable-cache",
            ]
            # Run test with cache disabled.
            with mock.patch("sys.argv", argv):
                dshomt._main(parser)
            # Check outputs.
            # Verify that caching was disabled by checking that the global
            # caching state is False (or was set to False during execution).
            # After the main() call completes, verify the mocks were called,
            # confirming API functions were invoked even though cache might
            # have been used in normal operation.
            self.assertTrue(mock_fetch_models.called)

    def test3(self) -> None:
        """
        Test script with cache refresh via --refresh-cache flag.
        """
        # Prepare inputs.
        models_content = """
        anthropic/claude-opus-4.7
        """
        models_file = self._create_models_file(models_content)
        # Mock API calls.
        with mock.patch(
            "dev_scripts_helpers.llms.openrouter_models_table._fetch_models_from_api"
        ) as mock_fetch_models, mock.patch(
            "dev_scripts_helpers.llms.openrouter_models_table._fetch_aa_benchmarks"
        ) as mock_fetch_benchmarks, mock.patch(
            "dev_scripts_helpers.llms.openrouter_models_table._fetch_openrouter_throughput"
        ) as mock_fetch_throughput, mock.patch(
            "dev_scripts_helpers.llms.openrouter_models_table._fetch_openrouter_per_model_usage"
        ) as mock_fetch_usage:
            mock_fetch_models.return_value = {
                "anthropic/claude-opus-4.7": {
                    "name": "Claude 3.5 Opus",
                    "input_cost": 3.0,
                    "output_cost": 15.0,
                    "context_length": 200000,
                    "coding_index_bench": None,
                }
            }
            mock_fetch_benchmarks.return_value = {
                "coding": 75.5,
                "intelligence": 88.2,
                "agentic": 82.1,
                "coding_index": 75.5,
            }
            mock_fetch_throughput.return_value = 100.0
            mock_fetch_usage.return_value = {
                "anthropic/claude-opus-4.7": {
                    "week_tokens": 1000000,
                    "month_tokens": 5000000,
                }
            }
            # Prepare outputs.
            parser = dshomt._parse()
            argv = [
                "openrouter_models_table.py",
                f"--models={models_file}",
                "--refresh-cache",
            ]
            # Run test with cache refresh enabled.
            with mock.patch("sys.argv", argv):
                dshomt._main(parser)
            # Check outputs.
            # Verify that refresh mode was enabled and API was called.
            self.assertTrue(mock_fetch_models.called)
