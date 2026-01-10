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
import tqdm
from pydantic import BaseModel

import helpers.hcache_simple as hcacsimp
import helpers.hllm_cost as hllmcost
import helpers.hdbg as hdbg
import helpers.hprint as hprint
import helpers.htimer as htimer

_LOG = logging.getLogger(__name__)


# Create a generic type variable.
T = TypeVar("T", bound=BaseModel)

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
    elif isinstance(response, openai.types.responses.Response):
        ret = response.output_text
    # elif isinstance(response, openai.pagination.SyncCursorPage):
    #     ret = response.data[0].content[0].text.value
    elif isinstance(response, openai.types.beta.threads.message.Message):
        ret = response.content[0].text.value
    elif isinstance(response, str):
        ret = response
    elif isinstance(response, dict):
        # Handle Chat Completions dict form.
        if "choices" in response and "message" in response["choices"][0]:
            ret = response["choices"][0]["message"]["content"]
        # Handle Responses API dict form.
        elif "output_text" in response:
            ret = response["output_text"]
        else:
            raise ValueError(
                f"Unknown dict structure in response: {response.keys()}"
            )
    else:
        raise ValueError(f"Unknown response type: {type(response)}")
    hdbg.dassert_isinstance(ret, str)
    return ret


def build_chat_completion_messages(
    system_prompt: str,
    user_prompt: str,
    *,
    images_as_base64: Optional[Tuple[str, ...]] = None,
) -> List[Dict[str, Any]]:
    """
    Construct the standard messages payload for the Chat Completions API.

    :param system_prompt: system prompt
    :param user_prompt: user prompt
    :param images_as_base64: base64-encoded images
    :return: messages in the format expected by the Chat Completions API
    """
    hdbg.dassert_isinstance(system_prompt, str)
    hdbg.dassert_isinstance(user_prompt, str)
    ret = [{"role": "system", "content": system_prompt}]
    # Build user message content.
    if images_as_base64:
        # Multi-modal message with text and images
        user_content = [{"type": "text", "text": user_prompt}]
        for image_b64 in images_as_base64:
            user_content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                }
            )
        ret.append({"role": "user", "content": user_content})
    else:
        # Text-only message.
        ret.append({"role": "user", "content": user_prompt})
    return ret


def build_responses_input(
    user_prompt: str,
    *,
    images_as_base64: Optional[Tuple[str, ...]] = None,
) -> List[Dict[str, Any]]:
    """
    Construct the user input payload for the Responses API.

    :param user_prompt: user prompt
    :param images_as_base64: base64-encoded images
    :return: input in the format expected by the Responses API
    """
    hdbg.dassert_isinstance(user_prompt, str)
    # Build user message content.
    content_blocks = [{"type": "input_text", "text": user_prompt}]
    if images_as_base64:
        # Add image input.
        for image_b64 in images_as_base64:
            content_blocks.append(
                {
                    "type": "input_image",
                    "image_url": f"data:image/jpeg;base64,{image_b64}",
                }
            )
    responses_input = [
        {
            "role": "user",
            "content": content_blocks,
        }
    ]
    return responses_input


# #############################################################################


@hcacsimp.simple_cache(
    write_through=True, exclude_keys=["client", "cache_mode", "cost_tracker"]
)
def _call_api_sync(
    # pylint: disable=unused-argument
    # This is needed to support caching.
    cache_mode: str,
    client: openai.OpenAI,
    user_prompt: str,
    system_prompt: str,
    temperature: float,
    model: str,
    *,
    images_as_base64: Optional[Tuple[str, ...]] = None,
    cost_tracker: Optional[hllmcost.LLMCostTracker] = None,
    use_responses_api: bool = False,
    **create_kwargs,
) -> Dict[Any, Any]:
    """
    Make a non-streaming API call.

    See `get_completion()` for other parameter descriptions.

    :param client: LLM client
    :param cost_tracker: LLMCostTracker instance to track costs
    :param use_responses_api: whether to use the Responses API instead
        of Chat Completions
    :return: OpenAI API result as a dictionary
    """
    if not use_responses_api:
        messages = build_chat_completion_messages(
            system_prompt, user_prompt, images_as_base64=images_as_base64
        )
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            **create_kwargs,
        )
    else:
        user_input = build_responses_input(
            user_prompt, images_as_base64=images_as_base64
        )
        completion = client.responses.create(
            model=model,
            instructions=system_prompt,
            input=user_input,
            temperature=temperature,
            **create_kwargs,
        )
    completion_obj = completion.to_dict()
    if isinstance(completion, openai.types.responses.Response):
        # Store the output of the Responses API.
        completion_obj["output_text"] = completion.output_text
    if cost_tracker is None:
        # Calculate the cost of the completion.
        hdbg.dassert_isinstance(cost_tracker, hllmcost.LLMCostTracker)
        cost = cost_tracker.calculate_cost(completion, model)
        cost_tracker.accumulate_cost(cost)
        # Store the cost in the completion object.
        completion_obj["cost"] = cost
    return completion_obj

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
            provider_name, model = self.get_default_model()
        else:
            provider_name, model = _get_llm_provider_and_model(model)

        self.provider_name = provider_name
        self.model = model

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

    def get_default_model(self) -> Tuple[str, str]:
        """
        Get the default provider and model for the client.

        :return: default provider and model used in the client
        """
        provider_name = "openai"
        model = self._get_default_model(provider_name)
        return provider_name, model

    def create_client(self) -> None:
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

    def call_llm(
        self,
        cache_mode: str,
        user_prompt: str,
        system_prompt: str,
        temperature: float,
        *,
        images_as_base64: Optional[Tuple[str, ...]] = None,
        cost_tracker: Optional[hllmcost.LLMCostTracker] = None,
        use_responses_api: bool = False,
        **create_kwargs,
    ) -> Dict[Any, Any]:
        """
        Call the LLM API.

        Check `_call_api_sync()` params for more details.
        """
        return _call_api_sync(
            cache_mode=cache_mode,
            client=self.client,
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            model=self.model,
            images_as_base64=images_as_base64,
            cost_tracker=cost_tracker,
            use_responses_api=use_responses_api,
            **create_kwargs,
        )


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
    images_as_base64: Optional[Tuple[str, ...]] = None,
    cost_tracker: Optional["hllmcost.LLMCostTracker"] = None,
    use_responses_api: bool = False,
    return_raw: bool = False,
    **create_kwargs,
) -> Union[str, Dict[Any, Any]]:
    """
    Generate a completion using OpenAI's API.

    :param user_prompt: user input message
    :param system_prompt: system instruction
    :param model: model to use or empty string to use the default model
    :param report_progress: whether to report progress running the API
        call
    :param cache_mode:
        - "DISABLE_CACHE": No caching
        - "REFRESH_CACHE": Make API calls and save responses to cache
        - "HIT_CACHE_OR_ABORT": Use cached responses, fail if not in cache
        - "NORMAL": Use cached responses if available, otherwise make API call
    :param cache_file: file to save/load completion cache
    :param temperature: adjust an LLM's sampling diversity: lower values make it
        more deterministic, while higher values foster creative variation.
        0 < temperature <= 2, 0.1 is default value in OpenAI models.
    :param images_as_base64: base64-encoded images to include in the user message
    :param cost_tracker: LLMCostTracker instance to track costs
    :param use_responses_api: whether to use the Responses API instead of Chat
        Completions
    :param return_raw: whether to return the raw API response instead of
        extracting the text content
    :param create_kwargs: additional params for the API call
    :return: API response or its text content
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
    if use_responses_api and llm_client.provider_name != "openai":
        raise ValueError(
            "Responses API is only supported for the 'openai' provider."
        )
    if report_progress and return_raw:
        raise ValueError(
            "Streaming mode is only supported while returning text content."
        )
    # Construct messages in OpenAI API request format.
    _LOG.info("LLM API call ... ")
    memento = htimer.dtimer_start(logging.DEBUG, "LLM API call")
    if not report_progress:
        completion = llm_client.call_llm(
            cache_mode=cache_mode,
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            images_as_base64=images_as_base64,
            cost_tracker=cost_tracker,
            use_responses_api=use_responses_api,
            **create_kwargs,
        )
        if not use_responses_api:
            txt_response = completion["choices"][0]["message"]["content"]
        else:
            txt_response = completion["output_text"]
    else:
        # TODO(gp): This is not working. It doesn't show the progress and it
        # doesn't show the cost.
        # Stream the output to show progress.
        collected_messages = []
        if not use_responses_api:
            # Stream Chat Completions API.
            messages = build_chat_completion_messages(
                system_prompt, user_prompt, images_as_base64=images_as_base64
            )
            completion = llm_client.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                **create_kwargs,
            )
            for chunk in tqdm.tqdm(
                completion, desc="Generating completion", unit=" chunks"
            ):
                if chunk.choices[0].delta.content is not None:
                    collected_messages.append(chunk.choices[0].delta.content)
        else:
            # Stream Responses API.
            user_input = build_responses_input(
                user_prompt, images_as_base64=images_as_base64
            )
            completion = llm_client.client.responses.create(
                model=model,
                instructions=system_prompt,
                input=user_input,
                stream=True,
                **create_kwargs,
            )
            for event in tqdm.tqdm(
                completion, desc="Generating response", unit=" events"
            ):
                if event.type == "response.output_text.delta":
                    collected_messages.append(event.delta.value)
        txt_response = "".join(collected_messages)
    # Report the time taken.
    msg, _ = htimer.dtimer_stop(memento)
    _LOG.info(msg)
    if print_cost:
        _LOG.info("cost=%.6f", completion["cost"])
    if return_raw:
        # Return the full completion/response object.
        return completion
    return txt_response


# TODO(*): Add caching, similar to `get_completion()`.
def get_structured_completion(
    user_prompt: str,
    response_format: type[T],
    *,
    system_prompt: str = "",
    model: str = "",
    temperature: float = 0.1,
    images_as_base64: Optional[Tuple[str, ...]] = None,
    cost_tracker: Optional[hllmcost.LLMCostTracker] = None,
    print_cost: bool = False,
    **create_kwargs,
) -> T:
    """
    Generate a Structured Output using OpenAI's API.

    See `get_completion()` for other parameter descriptions.

    :param response_format: expected structured output format
    :return: output parsed into the specified format
    """
    # Initialize LLM client.
    llm_client = LLMClient(model=model)
    llm_client.create_client()
    if llm_client.provider_name != "openai":
        raise ValueError(
            "`get_structured_completion()` currently only supports the "
            "'openai' provider (Responses API + Structured Outputs). "
            f"Got provider_name='{llm_client.provider_name}'."
        )
    # Retrieve a structured response.
    user_input = build_responses_input(
        user_prompt, images_as_base64=images_as_base64
    )
    response = llm_client.client.responses.parse(
        model=llm_client.model,
        instructions=system_prompt,
        input=user_input,
        temperature=temperature,
        text_format=response_format,
        **create_kwargs,
    )
    parsed_output: T = response.output_parsed
    # Track costs.
    if cost_tracker is None:
        hdbg.dassert_isinstance(cost_tracker, hllmcost.LLMCostTracker)
        cost = cost_tracker.calculate_cost(response)
        cost_tracker.accumulate_cost(cost)
        if print_cost:
            _LOG.info("cost=%.6f", cost)
    return parsed_output


# #############################################################################


def apply_prompt_to_dataframe(
    df,
    prompt,
    model: str,
    input_col,
    response_col,
    *,
    chunk_size=50,
    allow_overwrite: bool = False,
):
    _LOG.debug(hprint.to_str("prompt model input_col response_col chunk_size"))
    hdbg.dassert_in(input_col, df.columns)
    if not allow_overwrite:
        hdbg.dassert_not_in(response_col, df.columns)
    response_data = []
    for start in tqdm.tqdm(
        range(0, len(df), chunk_size), desc="Processing chunks"
    ):
        end = start + chunk_size
        chunk = df.iloc[start:end]
        _LOG.debug("chunk.size=%s", chunk.shape[0])
        data = chunk[input_col].astype(str).tolist()
        data = [f"{i + 1}: {val}" for i, val in enumerate(data)]
        user = "\n".join(data)
        _LOG.debug("user=\n%s", user)
        try:
            response = get_completion(user, system_prompt=prompt, model=model)
        except Exception as e:
            _LOG.error(
                f"Error processing column {input} in chunk {start}-{end}: {e}"
            )
            raise e
        # processed_response = response.split("\n")
        processed_response = [
            ln.rstrip() for ln in response.splitlines() if ln.strip()
        ]
        _LOG.debug(hprint.to_str("processed_response"))
        _LOG.debug("len(processed_response)=%s", len(processed_response))
        hdbg.dassert_eq(len(processed_response), chunk.shape[0])
        for i in range(len(processed_response)):
            m = re.match(r"\d+: (.*)\s*", processed_response[i])
            hdbg.dassert(m, f"Invalid response: {processed_response[i]}")
            # The linter doesn't understand that `dassert` is equivalent to an
            # `assert`.
            assert m is not None
            processed_response[i] = m.group(1).rstrip().lstrip()
        _LOG.debug(hprint.to_str("processed_response"))
        response_data.extend(processed_response)
    df[response_col] = response_data
    return df
