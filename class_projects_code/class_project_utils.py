#!/usr/bin/env python3

"""
Utility functions for class project and package management scripts.
"""

import logging

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


def check_llm_available() -> None:
    """
    Check if llm command is available in the system.
    """
    hsystem.system("which llm", suppress_output=True)
    _LOG.debug("llm command found and available")


def call_llm(prompt: str, content: str) -> str:
    """
    Call LLM with the given prompt and content.

    :param prompt: The prompt to send to LLM
    :param content: The content to process
    :return: LLM response
    """
    full_prompt = f"{prompt}\n\n{content}"
    # Write prompt to temporary file and use hsystem.system() to call llm.
    temp_file_path = "tmp.class_project_utils.call_llm.txt"
    hio.to_file(temp_file_path, full_prompt)
    # Use hsystem to call llm command with input file.
    rc, output = hsystem.system_to_string(f"llm < {temp_file_path}")
    return output.strip()