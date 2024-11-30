import datetime
import logging
from typing import Any, Dict, List, Optional

import openai
from openai import OpenAI
from openai.types.beta.assistant import Assistant
from openai.types.beta.threads.message import Message

import helpers.hdbg as hdbg

_LOG = logging.getLogger(__name__)

# hdbg.set_logger_verbosity(logging.DEBUG)

_LOG.debug = _LOG.info

_MODEL = "gpt-4o-mini"
# _MODEL = "gpt-4o"


_TEMPERATURE = 0.1

# #############################################################################


def response_to_txt(response: Any) -> str:
    if isinstance(response, openai.types.chat.chat_completion.ChatCompletion):
        return response.choices[0].message.content
    elif isinstance(response, openai.pagination.SyncCursorPage):
        return response.data[0].content[0].text.value
    elif isinstance(response, openai.types.beta.threads.message.Message):
        return response.content[0].text.value
    else:
        raise ValueError(f"Unknown response type: {type(response)}")


# TODO(gp): Clean up this.
from pprint import pformat
from typing import Any

# from pygments import highlight
# from pygments.formatters import Terminal256Formatter
# from pygments.lexers import PythonLexer


def pprint(obj: Any) -> None:
    """
    Pretty-print in color.
    """
    if hasattr(obj, "to_dict"):
        obj = obj.to_dict()
    print(highlight(pformat(obj), PythonLexer(), Terminal256Formatter()), end="")


# #############################################################################


def get_edgar_example():
    #!curl https://www.sec.gov/Archives/edgar/data/1652044/000165204423000016/goog-20221231.htm
    import requests

    # URL of the PDF you want to download.
    pdf_url = "https://www.sec.gov/Archives/edgar/data/1652044/000165204423000016/goog-20221231.htm"
    # Send a GET request to the URL.
    response = requests.get(
        pdf_url,
        headers={"User-Agent": "Mozilla/5.0 (Company info@company.com)"},
    )
    # Check if the request was successful.
    if response.status_code == 200:
        # Write the content of the response to a PDF file.
        with open("document.pdf", "wb") as file:
            file.write(response.content)
        print("Download completed!")
    else:
        print(f"Failed to download PDF. Status code: {response.status_code}")


def _extract(obj: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
    hdbg.dassert_isinstance(obj, dict)
    obj_tmp = {}
    for key in keys:
        hdbg.dassert_in(key, obj)
        obj_tmp[key] = getattr(obj, key)
    return obj_tmp


# #############################################################################


import functools


@functools.lru_cache(maxsize=1024)
def get_completion(
    user: str,
    *,
    system: str = "",
    model: Optional[str] = None,
    **create_kwargs,
) -> str:
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
    # return completion.choices[0].message.content
    return completion


# #############################################################################
# Assistants
# #############################################################################


# [FileObject(id='file-ZSexZm5C9t00NYMBFjQUDzUo',
#   bytes=89329,
#   created_at=1721761992,
#   filename='all.coding_style.how_to_guide.md',
#   object='file',
#   purpose='assistants',
#   status='processed',
#   status_details=None),


def file_to_info(file: openai.types.file_object.FileObject) -> Dict[str, Any]:
    hdbg.dassert_isinstance(assistant, openai.types.file_object.FileObject)
    keys = ["id", "created_at", "filename"]
    file_tmp = _extract(file, keys)
    file_tmp["created_at"] = datetime.datetime.fromtimestamp(
        file_tmp["created_at"]
    )
    return file_tmp


def files_to_str(files: List[openai.types.file_object.FileObject]) -> str:
    txt: List[str] = []
    txt.append("Found %s files" % len(files))
    for file in files:
        txt.append("Deleting file %s" % file_to_info(file))
    txt = "\n".join(txt)
    return txt


def delete_all_files(*, ask_for_confirmation: bool = True):
    client = OpenAI()
    files = list(client.files.list())
    # Print.
    _LOG.info(files_to_str(files))
    # Confirm.
    if ask_for_confirmation:
        hdbg.dfatal("Stopping")
    # Delete.
    for file in files:
        _LOG.info("Deleting file %s", file)
        client.files.delete(file.id)


# #############################################################################
# Assistants
# #############################################################################

# {'created_at': 1721761992,
#  'description': None,
#  'id': 'asst_aXKuTAqUwIrEcXFciT7b11UU',
#  'instructions': 'You are an expert Python coder. Use you knowledge base to '
#                  'answer questions about how to write code.',
#  'metadata': {},
#  'model': 'gpt-4o',
#  'name': 'Coding style expert',
#  'object': 'assistant',
#  'response_format': 'auto',
#  'temperature': 1.0,
#  'tool_resources': {'file_search': {'vector_store_ids': ['vs_CyJx606jziuN8L5WgSwsuzPd']}},
#  'tools': [{'type': 'file_search'}],
#  'top_p': 1.0}


def get_coding_style_assistant(
    assistant_name: str,
    instructions: str,
    vector_store_name: str,
    file_paths: List[str],
    *,
    model: Optional[str] = None,
) -> Assistant:
    model = _MODEL if model is None else model
    client = OpenAI()
    # TODO(gp): If the assistant already exists, return it.
    assistant = client.beta.assistants.create(
        name=assistant_name,
        instructions=instructions,
        model=model,
        tools=[{"type": "file_search"}],
    )
    # TODO(gp): If the vector store already exists, return it.
    _LOG.debug("Creating vector store ...")
    # Create a vector store.
    vector_store = client.beta.vector_stores.create(name=vector_store_name)
    # Ready the files for upload to OpenAI.
    # file_paths = ["all.coding_style.how_to_guide.md"]
    file_streams = [open(path, "rb") for path in file_paths]
    # Use the upload and poll SDK helper to upload the files, add them to the
    # vector store, and poll the status of the file batch for completion.
    _LOG.debug("Uploading vector store ...")
    file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id, files=file_streams
    )
    # You can print the status and the file counts of the batch to see the
    # result of this operation.
    # hdbg.dassert_eq(file_batch.status, "succeeded")
    _LOG.debug("File_batch: %s", file_batch)
    #
    assistant = client.beta.assistants.update(
        assistant_id=assistant.id,
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
    )
    return assistant


def get_query_assistant(assistant: Assistant, question: str) -> List[Message]:
    client = OpenAI()
    # Create a thread and attach the file to the message.
    thread = client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": question,
                # Attach the new file to the message.
                # "attachments": [
                #  { "file_id": message_file.id, "tools": [{"type": "file_search"}] }
                # ],
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


def dassert_hasattr(obj, attr):
    hdbg.dassert(
        hasattr(obj, attr), f"Object\n'%s'\nhas no attribute '%s'", obj, attr
    )


def assistant_to_info(assistant: Assistant) -> Dict[str, Any]:
    hdbg.dassert_isinstance(assistant, Assistant)
    keys = ["name", "created_at", "id", "instructions", "model"]
    assistant_info = _extract(assistant, keys)
    assistant_info["created_at"] = datetime.datetime.fromtimestamp(
        assistant_info["created_at"]
    )
    return assistant_info


def assistants_to_str(assistants: List[Assistant]) -> str:
    txt = []
    txt.append("Found %s assistants" % len(assistants))
    for assistant in assistants:
        txt.append("Deleting assistant %s" % assistant_to_info(assistant))
    txt = "\n".join(txt)
    return txt


def delete_all_assistants(*, ask_for_confirmation: bool = True):
    client = OpenAI()
    assistants = client.beta.assistants.list()
    assistants = assistants.data
    _LOG.info(assistants_to_str(assistants))
    if ask_for_confirmation:
        hdbg.dfatal("Stopping")
    for assistant in assistants:
        _LOG.info("Deleting assistant %s", assistant)
        client.beta.assistants.delete(assistant.id)
