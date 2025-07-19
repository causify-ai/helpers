"""
Import as:

import helpers.hllm as hllm
"""

import functools
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import openai
import pandas as pd
import requests
import tqdm

import helpers.hcache_simple as hcacsimp
import helpers.hdbg as hdbg
import helpers.hprint as hprint
import helpers.htimer as htimer

_LOG = logging.getLogger(__name__)

# hdbg.set_logger_verbosity(logging.DEBUG)

# _LOG.debug = _LOG.info


# #############################################################################
# Update LLM cache
# #############################################################################
_UPDATE_LLM_CACHE = False


def set_update_llm_cache(update: bool) -> None:
    """
    Set whether to update the LLM cache.

    :param update: True to update the cache, False otherwise
    """
    global _UPDATE_LLM_CACHE
    _UPDATE_LLM_CACHE = update


def get_update_llm_cache() -> bool:
    """
    Get whether to update the LLM cache.

    :return: True if the cache should be updated, False otherwise
    """
    return _UPDATE_LLM_CACHE


# #############################################################################
# Utility Functions
# #############################################################################


def _get_llm_provider_and_model(model: str) -> Tuple[str, str]:
    """
    Get the provider and model names from a model string.

    The model can be specified as:
    - "gpt-4o-mini"
    - "openai/gpt-4o-mini"
    - "deepseek/deepseek-r1-0528-qwen3-8b:free/"

    :param model: model to use for the completion
    :return: tuple of provider name and model name
    """
    if "/" in model:
        if model.startswith("openai/"):
            provider_name = "openai"
            model = model.split("/")[1]
        else:
            provider_name = "openrouter"
    else:
        provider_name = "openai"
    hdbg.dassert_in(
        provider_name,
        ("openai", "openrouter"),
        "Unknown provider: %s",
        provider_name,
    )
    return provider_name, model



def response_to_txt(response: Any) -> str:
    """
    Convert an OpenAI API response to a text string.

    :param response: API response object
    :return: extracted text contents as a string
    """
    if isinstance(response, openai.types.chat.chat_completion.ChatCompletion):
        ret = response.choices[0].message.content
    # elif isinstance(response, openai.pagination.SyncCursorPage):
    #     ret = response.data[0].content[0].text.value
    elif isinstance(response, openai.types.beta.threads.message.Message):
        ret = response.content[0].text.value
    elif isinstance(response, str):
        ret = response
    else:
        raise ValueError(f"Unknown response type: {type(response)}")
    hdbg.dassert_isinstance(ret, str)
    return ret


def _extract(
    file: openai.types.file_object.FileObject, attributes: List[str]
) -> Dict[str, Any]:
    """
    Extract specific keys from a dictionary.

    :param file: provided file to extract specific values
    :param attributes: list of attributes to extract
    :return: dictionary with extracted key-value pairs
    """
    obj_tmp = {}
    for attr in attributes:
        if hasattr(file, attr):
            obj_tmp[attr] = getattr(file, attr)
    return obj_tmp





# #############################################################################
# LLMClient
# #############################################################################


class LLMClient:
    """
    Class to handle LLM API client creation and requests.
    """

    def __init__(
        self,
        model: str,
    ) -> None:
        """
        Initialize the LLMClient.

        The model can be specified as:
        - "gpt-4o-mini"
        - "openai/gpt-4o-mini"
        - "deepseek/deepseek-r1-0528-qwen3-8b:free/"

        :param model: model to use for the completion.
        """
        hdbg.dassert_isinstance(model, str)
        if model == "":
            provider_name = "openai"
            model = self._get_default_model(provider_name)
        else:
            provider_name, model = _get_llm_provider_and_model(model)

        self.provider_name = provider_name
        self.model = model

    def create_client(self) -> openai.OpenAI:
        """
        Create an LLM client.
        """
        if self.provider_name == "openai":
            base_url = "https://api.openai.com/v1"
            api_key = os.environ.get("OPENAI_API_KEY")
        elif self.provider_name == "openrouter":
            base_url = "https://openrouter.ai/api/v1"
            api_key = os.environ.get("OPENROUTER_API_KEY")
        else:
            raise ValueError(f"Unknown provider: {self.provider_name}")
        _LOG.debug(hprint.to_str("self.provider_name base_url"))
        client = openai.OpenAI(base_url=base_url, api_key=api_key)
        self.client = client

    def build_messages(
        self, system_prompt: str, user_prompt: str
    ) -> List[Dict[str, str]]:
        """
        Construct the standard messages payload for the chat API.

        :param system_prompt: system prompt
        :param user_prompt: user prompt
        :return: messages in the format expected by the API
        """
        hdbg.dassert_isinstance(system_prompt, str)
        hdbg.dassert_isinstance(user_prompt, str)
        ret = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return ret

    def call_llm(
        self,
        cache_mode: str,
        messages: List[Dict[str, str]],
        temperature: float,
        **create_kwargs,
    ) -> dict[Any, Any]:
        """
        Call the LLM API.

        Check `_call_api_sync()` params for more details.
        """
        return _call_api_sync(
            cache_mode=cache_mode,
            client=self.client,
            messages=messages,
            temperature=temperature,
            model=self.model,
            **create_kwargs,
        )

    def _get_default_model(self, provider_name: str) -> str:
        """
        Get the default model for a provider.

        :return: default model for the provider
        """
        if provider_name == "openai":
            model = "gpt-4o"
        elif provider_name == "openrouter":
            model = "openai/gpt-4o"
        else:
            raise ValueError(f"Unknown provider: {self.provider_name}")
        return model


# #############################################################################
# OpenRouter API Helpers
# #############################################################################


def _get_models_info_file() -> str:
    """
    Get the path to the file for storing OpenRouter models info.
    """
    file_path = "tmp.openrouter_models_info.csv"
    return file_path


def _retrieve_openrouter_model_info() -> pd.DataFrame:
    """
    Retrieve OpenRouter models info from the OpenRouter API.
    """
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
    model_info_df: pd.DataFrame,
    file_name: str,
) -> pd.DataFrame:
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
    # Take only relevant columns.
    model_info_df = model_info_df[
        [
            "id",
            "name",
            "description",
            "prompt_pricing",
            "completion_pricing",
            "supported_parameters",
        ]
    ]
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

    def __init__(self) -> None:
        """
        Initialize the class.
        """
        self.current_cost: float = 0.0

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
        completion: openai.types.chat.chat_completion.ChatCompletion,
        model: str,
        *,
        models_info_file: str = "",
    ) -> float:
        """
        Calculate the cost of an API call, based on the provider.

        :param completion: The completion response from API from both
        :param model: The model used for the completion
        :return: The calculated cost in dollars
        """
        prompt_tokens = completion.usage.prompt_tokens
        completion_tokens = completion.usage.completion_tokens
        provider_name, model = _get_llm_provider_and_model(model)
        if provider_name == "openai":
            # Get the pricing for the selected model.
            # TODO(gp): Use pricing from OpenAI or Openrouter API.
            # https://openai.com/api/pricing/
            # https://gptforwork.com/tools/openai-chatgpt-api-pricing-calculator
            # Cost per 1M tokens.
            pricing = {
                "gpt-3.5-turbo": {"prompt": 0.5, "completion": 1.5},
                "gpt-4o-mini": {"prompt": 0.15, "completion": 0.60},
                "gpt-4o": {"prompt": 5, "completion": 15},
            }
            hdbg.dassert_in(model, pricing)
            model_pricing = pricing[model]
            # Calculate the cost.
            cost = (prompt_tokens / 1e6) * model_pricing["prompt"] + (
                completion_tokens / 1e6
            ) * model_pricing["completion"]
        elif provider_name == "openrouter":
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
            hdbg.dassert_in(model, model_info_df["id"].values)
            row = model_info_df.loc[model_info_df["id"] == model].iloc[0]
            prompt_price = row["prompt_pricing"]
            completion_price = row["completion_pricing"]
            # Compute cost.
            cost = (
                prompt_tokens * prompt_price
                + completion_tokens * completion_price
            )
        else:
            raise ValueError(f"Unknown provider: {provider_name}")
        _LOG.debug(hprint.to_str("prompt_tokens completion_tokens cost"))
        return cost


# #############################################################################


_LLM_COST_Tracker = LLMCostTracker()


@hcacsimp.simple_cache(
    write_through=True, exclude_keys=["client", "cache_mode", "cost_tracker"]
)
def _call_api_sync(
    # pylint: disable=unused-argument
    # This is needed to support caching.
    cache_mode: str,
    client: openai.OpenAI,
    messages: List[Dict[str, str]],
    temperature: float,
    model: str,
    cost_tracker: Optional[LLMCostTracker] = None,
    **create_kwargs,
) -> dict[Any, Any]:
    """
    Make a non-streaming API call.

    :param client: LLM client
    :param messages: list of messages to send to the API
    :param cost_tracker: LLMCostTracker instance to track costs Check
        `get_completion()` params for other param details.
    :return: OpenAI chat completion object as a dictionary
    """
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        **create_kwargs,
    )
    completion_obj = completion.to_dict()
    if cost_tracker is None:
        cost_tracker = _LLM_COST_Tracker
    # Calculate the cost of the completion.
    hdbg.dassert_isinstance(cost_tracker, LLMCostTracker)
    cost = cost_tracker.calculate_cost(completion, model)
    cost_tracker.accumulate_cost(cost)
    # Store the cost in the completion object.
    completion_obj["cost"] = cost
    return completion_obj


# #############################################################################


@functools.lru_cache(maxsize=1024)
def get_completion(
    user_prompt: str,
    *,
    system_prompt: str = "",
    model: str = "",
    report_progress: bool = False,
    print_cost: bool = False,
    cache_mode: str = "DISABLE_CACHE",
    temperature: float = 0.1,
    **create_kwargs,
) -> str:
    """
    Generate a completion using OpenAI's chat API.

    :param user_prompt: user input message
    :param system_prompt: system instruction
    :param model: model to use or empty string to use the default model
    :param report_progress: whether to report progress running the API
        call
    :param cache_mode : "DISABLE_CACHE","REFRESH_CACHE", "HIT_CACHE_OR_ABORT", "NORMAL"
        - "DISABLE_CACHE": No caching
        - "REFRESH_CACHE": Make API calls and save responses to cache
        - "HIT_CACHE_OR_ABORT": Use cached responses, fail if not in cache
        - "NORMAL": Use cached responses if available, otherwise make API call
    :param cache_file: file to save/load completioncache
    :param temperature: adjust an LLM's sampling diversity: lower values make it
        more deterministic, while higher values foster creative variation.
        0 < temperature <= 2, 0.1 is default value in OpenAI models.
    :param create_kwargs: additional params for the API call
    :return: completion text
    """
    hdbg.dassert_in(
        cache_mode,
        ("DISABLE_CACHE", "REFRESH_CACHE", "HIT_CACHE_OR_ABORT", "NORMAL"),
    )
    update_llm_cache = get_update_llm_cache()
    if update_llm_cache:
        cache_mode = "REFRESH_CACHE"

    llm_client = LLMClient(model=model)
    llm_client.create_client()
    # Construct messages in OpenAI API request format.
    messages = llm_client.build_messages(system_prompt, user_prompt)
    print("LLM API call ... ")
    memento = htimer.dtimer_start(logging.DEBUG, "LLM API call")
    if not report_progress:
        completion = llm_client.call_llm(
            cache_mode=cache_mode,
            messages=messages,
            temperature=temperature,
            **create_kwargs,
        )
    else:
        # TODO(gp): This is not working. It doesn't show the progress and it
        # doesn't show the cost.
        # Create a stream to show progress.
        completion = llm_client.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,  # Enable streaming
            **create_kwargs,
        )
        # Initialize response storage
        collected_messages = []
        # Process the stream with progress bar
        for chunk in tqdm.tqdm(
            completion, desc="Generating completion", unit=" chunks"
        ):
            if chunk.choices[0].delta.content is not None:
                collected_messages.append(chunk.choices[0].delta.content)
        # Combine chunks into final completion
        response = "".join(collected_messages)
    # Report the time taken.
    msg, _ = htimer.dtimer_stop(memento)
    print(msg)
    if print_cost:
        print(f"cost=${completion['cost']:.6f}")
    response = completion["choices"][0]["message"]["content"]
    return response


# # #############################################################################


# def file_to_info(file: openai.types.file_object.FileObject) -> Dict[str, Any]:
#     """
#     Convert a file object to a dictionary with selected attributes.

#     :param file: file object
#     :return: dictionary with file metadata
#     """
#     hdbg.dassert_isinstance(file, openai.types.file_object.FileObject)
#     keys = ["id", "created_at", "filename"]
#     file_info = _extract(file, keys)
#     file_info["created_at"] = datetime.datetime.fromtimestamp(
#         file_info["created_at"]
#     )
#     return file_info


# def files_to_str(files: List[openai.types.file_object.FileObject]) -> str:
#     """
#     Generate a string summary of a list of file objects.

#     :param files: list of file objects
#     :return: string summary
#     """
#     txt: List[str] = []
#     txt.append("Found %s files" % len(files))
#     for file in files:
#         txt.append("Deleting file " + file_to_info(file))
#     txt = "\n".join(txt)
#     return txt


# def delete_all_files(*, ask_for_confirmation: bool = True) -> None:
#     """
#     Delete all files from OpenAI's file storage.

#     :param ask_for_confirmation: whether to prompt for confirmation
#         before deletion
#     """
#     client = get_openai_client()
#     files = list(client.files.list())
#     # Print.
#     _LOG.info(files_to_str(files))
#     # Confirm.
#     if ask_for_confirmation:
#         hdbg.dfatal("Stopping due to user confirmation.")
#     # Delete.
#     for file in files:
#         _LOG.info("Deleting file %s", file)
#         client.files.delete(file.id)


# # #############################################################################
# # Assistants
# # #############################################################################


# def assistant_to_info(assistant: OAssistant.Assistant) -> Dict[str, Any]:
#     """
#     Extract metadata from an assistant object.

#     :param assistant: assistant object
#     :return: dictionary with assistant metadata
#     """
#     hdbg.dassert_isinstance(assistant, OAssistant.Assistant)
#     keys = ["name", "created_at", "id", "instructions", "model"]
#     assistant_info = _extract(assistant, keys)
#     assistant_info["created_at"] = datetime.datetime.fromtimestamp(
#         assistant_info["created_at"]
#     )
#     return assistant_info


# def assistants_to_str(assistants: List[OAssistant.Assistant]) -> str:
#     """
#     Generate a string summary of a list of assistants.

#     :param assistants: list of assistants
#     :return: a string summary
#     """
#     txt = []
#     txt.append("Found %s assistants" % len(assistants))
#     for assistant in assistants:
#         txt.append("Deleting assistant " + assistant_to_info(assistant))
#     txt = "\n".join(txt)
#     return txt


# def delete_all_assistants(*, ask_for_confirmation: bool = True) -> None:
#     """
#     Delete all assistants from OpenAI's assistant storage.

#     :param ask_for_confirmation: whether to prompt for confirmation
#         before deletion.
#     """
#     client = get_openai_client()
#     assistants = client.beta.assistants.list()
#     assistants = assistants.data
#     _LOG.info(assistants_to_str(assistants))
#     if ask_for_confirmation:
#         hdbg.dfatal("Stopping due to user confirmation.")
#     for assistant in assistants:
#         _LOG.info("Deleting assistant %s", assistant)
#         client.beta.assistants.delete(assistant.id)


# def get_coding_style_assistant(
#     assistant_name: str,
#     instructions: str,
#     vector_store_name: str,
#     file_paths: List[str],
#     *,
#     model: Optional[str] = None,
# ) -> OAssistant.Assistant:
#     """
#     Create or retrieve a coding style assistant with vector store support.

#     :param assistant_name: name of the assistant
#     :param instructions: instructions for the assistant
#     :param vector_store_name: name of the vectore store
#     :param file_paths: list of file paths to upload
#     :param model: OpenAI model to use
#     :return: created or updated assistant object
#     """
#     model = _MODEL if model is None else model
#     client = get_openai_client()
#     # Check if the assistant already exists.
#     existing_assistants = list(client.beta.assistants.list().data)
#     for existing_assistant in existing_assistants:
#         if existing_assistant.name == assistant_name:
#             _LOG.debug("Assistant '%s' already exists.", assistant_name)
#             return existing_assistant
#     # Cretae the assistant.
#     _LOG.info("Creating a new assistant: %s", assistant_name)
#     assistant = client.beta.assistants.create(
#         name=assistant_name,
#         instructions=instructions,
#         model=model,
#         tools=[{"type": "file_search"}],
#     )
#     # Check if the vector store already exists.
#     vector_stores = list(client.beta.vector_stores.list().data)
#     vector_store = None
#     for store in vector_stores:
#         if store.name == vector_store_name:
#             _LOG.debug(
#                 "Vector store '%s' already exists. Using it", vector_store_name
#             )
#             vector_store = store
#             break
#     if not vector_store:
#         _LOG.debug("Creating vector store ...")
#         # Create a vector store.
#         vector_store = client.beta.vector_stores.create(name=vector_store_name)
#     # Upload files to the vector store (if provided).
#     if file_paths:
#         file_streams = [open(path, "rb") for path in file_paths]
#         _LOG.debug("Uploading files to vector store ...")
#         try:
#             file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
#                 vector_store_id=vector_store.id, files=file_streams
#             )
#             _LOG.info(
#                 "File batch uploaded successfully with status: %s",
#                 file_batch.status,
#             )
#         except Exception as e:
#             _LOG.error("Failed to upload files to vector store: %s", str(e))
#             raise
#     # Associate the assistant with the vector store.
#     assistant = client.beta.assistants.update(
#         assistant_id=assistant.id,
#         tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
#     )
#     return assistant


# def get_query_assistant(
#     assistant: OAssistant.Assistant, question: str
# ) -> List[OMessage.Message]:
#     """
#     Query an assistant with sepecific question.

#     :param assistant: assistant to query
#     :param question: user question
#     :return: list of messages containing the assistant's response
#     """
#     client = get_openai_client()
#     # Create a thread and attach the file to the message.
#     thread = client.beta.threads.create(
#         messages=[
#             {
#                 "role": "user",
#                 "content": question,
#             }
#         ]
#     )
#     # The thread now has a vector store with that file in its tool resources.
#     _LOG.debug("thread=%s", thread.tool_resources.file_search)
#     run = client.beta.threads.runs.create_and_poll(
#         thread_id=thread.id, assistant_id=assistant.id
#     )
#     messages = list(
#         client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id)
#     )
#     return messages


# # import os
# # import requests
# #
# #
# # def get_openai_usage():
# #     # Define the API endpoint.
# #     endpoint = "https://api.openai.com/v1/organization/costs"
# #     start_date = datetime.datetime.now() - datetime.timedelta(days=10)
# #     start_date = int(start_date.timestamp())
# #     # Request headers.
# #     #api_key = os.environ.get("OPENAI_API_KEY")
# #     headers = {
# #         "Authorization": f"Bearer {api_key}",
# #     }
# #     # Query parameters
# #     params = {
# #         "start_time": start_date,
# #         #"end_date": end_date,
# #     }
# #     # Send the request
# #     response = requests.get(endpoint, headers=headers, params=params)
# #     if response.status_code == 200:
# #         data = response.json()
# #         import pprint
# #         pprint.pprint(data)
# #         total_spent = data.get("total_usage", 0) / 100  # Convert cents to dollars
# #         #print(f"Total spent from {start_date} to {end_date}: "
# #         #       f"${total_spent:.2f}")
# #         return total_spent
# #     else:
# #         print(f"Failed to fetch usage: {response.status_code}, {response.text}")
# #         return None
# #


def apply_prompt_to_dataframe(
    df,
    prompt,
    model: str,
    input_col,
    response_col,
    chunk_size=50,
    allow_overwrite: bool = False,
):
    _LOG.debug(hprint.to_str("prompt model input_col response_col chunk_size"))
    hdbg.dassert_in(input_col, df.columns)
    if not allow_overwrite:
        hdbg.dassert_not_in(response_col, df.columns)
    response_data = []
    for start in tqdm(range(0, len(df), chunk_size), desc="Processing chunks"):
        end = start + chunk_size
        chunk = df.iloc[start:end]
        _LOG.debug("chunk.size=%s", chunk.shape[0])
        data = chunk[input_col].astype(str).tolist()
        data = [f"{i + 1}: {val}" for i, val in enumerate(data)]
        user = "\n".join(data)
        _LOG.debug("user=\n%s", user)
        try:
            response = get_completion(user, system=prompt, model=model)
        except Exception as e:
            _LOG.error(
                f"Error processing column {input} in chunk {start}-{end}: {e}"
            )
            raise e
        processed_response = response.split("\n")
        _LOG.debug(hprint.to_str("processed_response"))
        _LOG.debug("len(processed_response)=%s", len(processed_response))
        hdbg.dassert_eq(len(processed_response), chunk.shape[0])
        for i in range(len(processed_response)):
            m = re.match(r"\d+: (.*)\s*", processed_response[i])
            hdbg.dassert(m, f"Invalid response: {processed_response[i]}")
            processed_response[i] = m.group(1).rstrip().lstrip()
        _LOG.debug(hprint.to_str("processed_response"))
        response_data.extend(processed_response)
    df[response_col] = response_data
    return df
