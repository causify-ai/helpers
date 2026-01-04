"""
Import as:

import helpers.hllm as hllm
"""

import functools
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple, TypeVar, Union

import openai
import requests
import tqdm
from pydantic import BaseModel

import helpers.hcache_simple as hcacsimp
import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hprint as hprint
import helpers.htimer as htimer

_LOG = logging.getLogger(__name__)


# #############################################################################
# OpenRouter API Helpers
# #############################################################################


def _get_models_info_file() -> str:
    """
    Get the path to the file for storing OpenRouter models info.
    """
    dir_path = hgit.get_helpers_root_dir()
    file_path = os.path.join(dir_path, "dev_scripts_helpers/llms", "openrouter_models_info.csv")
    return file_path


def _retrieve_openrouter_model_info() -> "pd.DataFrame":
    """
    Retrieve OpenRouter models info from the OpenRouter API.
    """
    import pandas as pd

    response = requests.get("https://openrouter.ai/api/v1/models")
    # {'architecture': {'input_modalities': ['text', 'image'],
    #                   'instruct_type': None,
    #                   'modality': 'text+image->text',
    #                   'output_modalities': ['text'],
    #                   'tokenizer': 'Mistral'},
    #  'context_length': 131072,
    #  'created': 1746627341,
    #  'description': 'Mistral Medium 3 is a high-performance enterprise-grade '
    #                 'language model designed to deliver frontier-level '
    #                  ...
    #                 'broad compatibility across cloud environments.',
    #  'id': 'mistralai/mistral-medium-3',
    #  'name': 'Mistral: Mistral Medium 3',
    #  'per_request_limits': None,
    #  'pricing': {'completion': '0.000002',
    #              'image': '0',
    #              'internal_reasoning': '0',
    #              'prompt': '0.0000004',
    #              'request': '0',
    #              'web_search': '0'},
    #  'supported_parameters': ['tools',
    #                           'tool_choice',
    #                           'max_tokens',
    #                           'temperature',
    #                           'top_p',
    #                           'stop',
    #                           'frequency_penalty',
    #                           'presence_penalty',
    #                           'response_format',
    #                           'structured_outputs',
    #                           'seed'],
    #  'top_provider': {'context_length': 131072,
    #                   'is_moderated': False,
    #                   'max_completion_tokens': None}}
    response_json = response.json()
    # There is only one key in the response.
    hdbg.dassert_eq(list(response_json.keys()), ["data"])
    response_json = response_json["data"]
    model_info_df = pd.DataFrame(response_json)
    return model_info_df


def _save_models_info_to_csv(
    model_info_df: "pd.DataFrame",
    file_name: str,
) -> "pd.DataFrame":
    """
    Save models info to a CSV file.
    """
    hdbg.dassert_isinstance(file_name, str)
    hdbg.dassert_ne(file_name, "")
    # TODO(*): Save all the data.
    # Extract prompt, completion pricing from pricing column.
    model_info_df["prompt_pricing"] = model_info_df["pricing"].apply(
        lambda x: x["prompt"]
    )
    model_info_df["completion_pricing"] = model_info_df["pricing"].apply(
        lambda x: x["completion"]
    )
    required_columns = [
        "id",
        "name",
        "description",
        "prompt_pricing",
        "completion_pricing",
        "supported_parameters",
    ]
    # Take only relevant columns.
    model_info_df = model_info_df.loc[:, required_columns]
    # Save to CSV file.
    model_info_df.to_csv(file_name, index=False)
    return model_info_df


# #############################################################################
# LLMCostTracker
# #############################################################################


class LLMCostTracker:
    """
    Track the costs of LLM API calls through one of the providers.
    """

    def __init__(self, provider_name: str, model: str) -> None:
        """
        Initialize the class.
        """
        self.current_cost: float = 0.0
        self.provider_name = provider_name
        self.model = model

    def end_logging_costs(self) -> None:
        """
        End logging costs by resetting the current cost to 0.
        """
        self.current_cost = 0.0

    def accumulate_cost(self, cost: float) -> None:
        """
        Accumulate the cost.

        :param cost: The cost to accumulate
        """
        self.current_cost += cost

    def get_current_cost(self) -> float:
        """
        Get the current accumulated cost.

        :return: The current cost
        """
        return self.current_cost

    def calculate_cost(
        self,
        completion: Any,
        *,
        models_info_file: str = "",
    ) -> float:
        """
        Calculate the cost of an API call, based on the provider.

        :param completion: the completion response from API
        :return: the calculated cost in dollars
        """
        import pandas as pd

        # Get the number of input and output tokens.
        usage = getattr(completion, "usage", None)
        hdbg.dassert(
            usage is not None,
            "Completion/response object has no 'usage' attribute",
        )
        if hasattr(usage, "prompt_tokens") and hasattr(
            usage, "completion_tokens"
        ):
            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens
        elif hasattr(usage, "input_tokens") and hasattr(usage, "output_tokens"):
            prompt_tokens = usage.input_tokens
            completion_tokens = usage.output_tokens
        else:
            raise ValueError(
                f"Unknown usage structure on completion object: {usage}"
            )
        # Get the provider and model details.
        if self.provider_name == "openai":
            # Get the pricing for the selected model.
            # TODO(gp): Use pricing from OpenAI or Openrouter API.
            # https://openai.com/api/pricing/
            # https://gptforwork.com/tools/openai-chatgpt-api-pricing-calculator
            # Cost per 1M tokens.
            pricing = {
                "gpt-3.5-turbo": {"prompt": 0.5, "completion": 1.5},
                "gpt-4o-mini": {"prompt": 0.15, "completion": 0.60},
                "gpt-4o": {"prompt": 2.5, "completion": 10},
                "gpt-5.2": {"prompt": 1.75, "completion": 14.0},
                "gpt-5.1": {"prompt": 1.25, "completion": 10.0},
                "gpt-5-mini": {"prompt": 0.25, "completion": 2.00},
            }
            hdbg.dassert_in(self.model, pricing)
            model_pricing = pricing[self.model]
            # Calculate the cost.
            cost = (prompt_tokens / 1e6) * model_pricing["prompt"] + (
                completion_tokens / 1e6
            ) * model_pricing["completion"]
        elif self.provider_name == "openrouter":
            # If the model info file doesn't exist, download one.
            if models_info_file == "":
                models_info_file = _get_models_info_file()
            _LOG.debug(hprint.to_str("models_info_file"))
            if not os.path.isfile(models_info_file):
                model_info_df = _retrieve_openrouter_model_info()
                _save_models_info_to_csv(model_info_df, models_info_file)
            else:
                model_info_df = pd.read_csv(models_info_file)
            # Extract pricing for this model.
            hdbg.dassert_in(self.model, model_info_df["id"].values)
            row = model_info_df.loc[model_info_df["id"] == self.model].iloc[0]
            prompt_price = row["prompt_pricing"]
            completion_price = row["completion_pricing"]
            # Compute cost.
            cost = (
                prompt_tokens * prompt_price
                + completion_tokens * completion_price
            )
        else:
            raise ValueError(f"Unknown provider: {self.provider_name}")
        _LOG.debug(hprint.to_str("prompt_tokens completion_tokens cost"))
        return cost