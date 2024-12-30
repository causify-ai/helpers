"""
Import as:

import helpers.hopenai as hopenai
"""

import datetime
import functools
import logging
import re
from typing import Any, Dict, List, Optional

import openai
from openai import OpenAI
from openai.types.beta.assistant import Assistant
from openai.types.beta.threads.message import Message
from tqdm.notebook import tqdm

import helpers.hdbg as hdbg
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)

# hdbg.set_logger_verbosity(logging.DEBUG)

#_LOG.debug = _LOG.info
_MODEL = "gpt-4o-mini"
_TEMPERATURE = 0.1

# #############################################################################
# Utility Functions
# #############################################################################


def response_to_txt(response: Any) -> str:
    """
    Convert an OpenAI API response to a text string.

    :param response: API response object
    :return: extracted text contents as a string
    """
    if isinstance(response, openai.types.chat.chat_completion.ChatCompletion):
        return response.choices[0].message.content
    elif isinstance(response, openai.pagination.SyncCursorPage):
        return response.data[0].content[0].text.value
    elif isinstance(response, openai.types.beta.threads.message.Message):
        return response.content[0].text.value
    else:
        raise ValueError(f"Unknown response type: {type(response)}")


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
# OpenAI API Helpers
# #############################################################################


_openai_cost = None

def start_logging_costs():
    global _openai_cost
    _openai_cost = 0.0


def end_logging_costs():
    global _openai_cost
    _openai_cost = None


def get_costs():
    return _openai_cost


# https://openai.com/api/pricing/
# https://gptforwork.com/tools/openai-chatgpt-api-pricing-calculator
# Cost per 1M tokens.
pricing = {
    "gpt-3.5-turbo": {"prompt": 0.5, "completion": 1.5},
    "gpt-4o-mini": {"prompt": 0.15, "completion": 0.60},
    "gpt-4o": {"prompt": 5, "completion": 15},
}


@functools.lru_cache(maxsize=1024)
def get_completion(
    user: str,
    *,
    system: str = "",
    model: Optional[str] = None,
    **create_kwargs,
) -> str:
    """
    Generate a completion using OpenAI's chat API.

    :param user: user input message
    :param system: system instruction
    :param model: OpenAI model to use
    :param create_kwargs: additional params for the API call
    :return: completion text
    """
    model = _MODEL if model is None else model
    client = OpenAI()
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        **create_kwargs,
    )
    global _openai_cost
    if _openai_cost is not None:
        # CompletionUsage(completion_tokens=2, prompt_tokens=48, total_tokens=50
        prompt_tokens = completion.usage.prompt_tokens
        completion_tokens = completion.usage.completion_tokens
        # Get the pricing for the selected model
        model_pricing = pricing[model]
        # Calculate the cost
        cost = (
                (prompt_tokens / 1e6) * model_pricing["prompt"] +
                (completion_tokens / 1e6) * model_pricing["completion"]
        )
        _openai_cost += cost
    return completion.choices[0].message.content


def file_to_info(file: openai.types.file_object.FileObject) -> Dict[str, Any]:
    """
    Convert a file object to a dictionary with selected attributes.

    :param file: file object
    :return: dictionary with file metadata
    """
    hdbg.dassert_isinstance(file, openai.types.file_object.FileObject)
    keys = ["id", "created_at", "filename"]
    file_info = _extract(file, keys)
    file_info["created_at"] = datetime.datetime.fromtimestamp(
        file_info["created_at"]
    )
    return file_info


def files_to_str(files: List[openai.types.file_object.FileObject]) -> str:
    """
    Generate a string summary of a list of file objects.

    :param files: list of file objects
    :return: string summary
    """
    txt: List[str] = []
    txt.append("Found %s files" % len(files))
    for file in files:
        txt.append("Deleting file %s" % file_to_info(file))
    txt = "\n".join(txt)
    return txt


def delete_all_files(*, ask_for_confirmation: bool = True) -> None:
    """
    Delete all files from OpenAI's file storage.

    :param ask_for_confirmation: whether to prompt for confirmation
        before deletion
    """
    client = OpenAI()
    files = list(client.files.list())
    # Print.
    _LOG.info(files_to_str(files))
    # Confirm.
    if ask_for_confirmation:
        hdbg.dfatal("Stopping due to user confirmation.")
    # Delete.
    for file in files:
        _LOG.info("Deleting file %s", file)
        client.files.delete(file.id)


# #############################################################################
# Assistants
# #############################################################################


def assistant_to_info(assistant: Assistant) -> Dict[str, Any]:
    """
    Extract metadata from an assistant object.

    :param assistant: assistant object
    :return: dictionary with assistant metadata
    """
    hdbg.dassert_isinstance(assistant, Assistant)
    keys = ["name", "created_at", "id", "instructions", "model"]
    assistant_info = _extract(assistant, keys)
    assistant_info["created_at"] = datetime.datetime.fromtimestamp(
        assistant_info["created_at"]
    )
    return assistant_info


def assistants_to_str(assistants: List[Assistant]) -> str:
    """
    Generate a string summary of a list of assistants.

    :param assistants: list of assistants
    :return: a string summary
    """
    txt = []
    txt.append("Found %s assistants" % len(assistants))
    for assistant in assistants:
        txt.append("Deleting assistant %s" % assistant_to_info(assistant))
    txt = "\n".join(txt)
    return txt


def delete_all_assistants(*, ask_for_confirmation: bool = True) -> None:
    """
    Delete all assistants from OpenAI's assistant storage.

    :param ask_for_confirmation: whether to prompt for confirmation
        before deletion
    """
    client = OpenAI()
    assistants = client.beta.assistants.list()
    assistants = assistants.data
    _LOG.info(assistants_to_str(assistants))
    if ask_for_confirmation:
        hdbg.dfatal("Stopping due to user confirmation.")
    for assistant in assistants:
        _LOG.info("Deleting assistant %s", assistant)
        client.beta.assistants.delete(assistant.id)


def get_coding_style_assistant(
    assistant_name: str,
    instructions: str,
    vector_store_name: str,
    file_paths: List[str],
    *,
    model: Optional[str] = None,
) -> Assistant:
    """
    Create or retrieve a coding style assistant with vector store support.

    :param assistant_name: name of the assistant
    :param instructions: instructions for the assistant
    :param vector_store_name: name of the vectore store
    :param file_paths: list of file paths to upload
    :param model: OpenAI model to use
    :return: created or updated assistant object
    """
    model = _MODEL if model is None else model
    client = OpenAI()
    # Check if the assistant already exists.
    existing_assistants = list(client.beta.assistants.list().data)
    for existing_assistant in existing_assistants:
        if existing_assistant.name == "assistant_name":
            _LOG.debug("Assistant '%s' already exists.", assistant_name)
            return existing_assistant
    # Cretae the assistant.
    _LOG.info("Creating a new assistant: %s", assistant_name)
    assistant = client.beta.assistants.create(
        name=assistant_name,
        instructions=instructions,
        model=model,
        tools=[{"type": "file_search"}],
    )
    # Check if the vector store already exists.
    vector_stores = list(client.beta.vector_stores.list().data)
    vector_store = None
    for store in vector_stores:
        if store.name == vector_store_name:
            _LOG.debug(
                "Vector store '%s' already exists. Using it", vector_store_name
            )
            vector_store = store
            break
    if not vector_store:
        _LOG.debug("Creating vector store ...")
        # Create a vector store.
        vector_store = client.beta.vector_stores.create(name=vector_store_name)
    # Upload files to the vector store (if provided).
    if file_paths:
        file_streams = [open(path, "rb") for path in file_paths]
        _LOG.debug("Uploading files to vector store ...")
        try:
            file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store.id, files=file_streams
            )
            _LOG.info(
                "File batch uploaded successfully with status: %s",
                file_batch.status,
            )
        except Exception as e:
            _LOG.error("Failed to upload files to vector store: %s", str(e))
            raise
    # Associate the assistant with the vector store.
    assistant = client.beta.assistants.update(
        assistant_id=assistant.id,
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
    )
    return assistant


def get_query_assistant(assistant: Assistant, question: str) -> List[Message]:
    """
    Query an assistant with sepecific question.

    :param assistant: assistant to query
    :param question: user question
    :return: list of messages containing the assistant's response
    """
    client = OpenAI()
    # Create a thread and attach the file to the message.
    thread = client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": question,
            }
        ]
    )
    # The thread now has a vector store with that file in its tool resources.
    _LOG.debug("thread=%s", thread.tool_resources.file_search)
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id, assistant_id=assistant.id
    )
    messages = list(
        client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id)
    )
    return messages


def apply_prompt_to_dataframe(df, prompt,
                              model:str, input_col, response_col,
                              chunk_size=50,
                              allow_overwrite: bool = False):
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
        data = ["%s: %s" % (i + 1, val) for i, val in enumerate(data)]
        user = "\n".join(data)
        _LOG.debug("user=\n%s", user)
        try:
            response = get_completion(user, system=prompt, model=model)
        except Exception as e:
            _LOG.error(f"Error processing column {input} in chunk"
                       f" {start}-{end}: {e}")
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
