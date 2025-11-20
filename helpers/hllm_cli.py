"""
Import as:

import helpers.hllm_cli as hllmcli
"""

import logging
import subprocess
from typing import Optional

from tqdm import tqdm

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# #############################################################################
# Helper functions
# #############################################################################


def _check_llm_executable() -> bool:
    """
    Check if the llm command-line executable is available.

    :return: True if llm executable exists, False otherwise
    """
    try:
        hsystem.system("which llm", suppress_output=True)
        _LOG.debug("llm command found")
        return True
    except Exception:
        _LOG.debug("llm command not found")
        return False


def _apply_llm_via_executable(
    input_str: str,
    *,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    expected_num_chars: Optional[int] = None,
) -> str:
    """
    Apply LLM using the llm CLI executable.

    :param input_str: the input text to process
    :param system_prompt: optional system prompt to use
    :param model: optional model name to use
    :param expected_num_chars: optional expected number of characters in
        output (used for progress bar)
    :return: LLM response as string
    """
    # Build command.
    cmd = ["llm"]
    if system_prompt:
        cmd.extend(["--system", system_prompt])
    if model:
        cmd.extend(["--model", model])
    # Add progress bar if expected_num_chars is provided.
    if expected_num_chars:
        cmd.append("--stream")
    # Add the user prompt.
    cmd.append(input_str)
    _LOG.debug("Running command: %s", " ".join(cmd))
    # Execute command.
    if expected_num_chars:
        # Use streaming with progress bar.
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        response_parts = []
        with tqdm(total=expected_num_chars, unit="char") as pbar:
            for line in proc.stdout:
                response_parts.append(line)
                pbar.update(len(line))
        # Wait for process to complete.
        proc.wait()
        if proc.returncode != 0:
            error_msg = proc.stderr.read() if proc.stderr else ""
            hdbg.dfatal(
                "llm command failed with return code:",
                proc.returncode,
                "error:",
                error_msg,
            )
        response = "".join(response_parts)
    else:
        # Run without progress bar.
        cmd_str = " ".join(cmd)
        response = hsystem.system_to_string(cmd_str)
    return response


def _apply_llm_via_library(
    input_str: str,
    *,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    expected_num_chars: Optional[int] = None,
) -> str:
    """
    Apply LLM using the llm Python library.

    :param input_str: the input text to process
    :param system_prompt: optional system prompt to use
    :param model: optional model name to use
    :param expected_num_chars: optional expected number of characters in
        output (used for progress bar)
    :return: LLM response as string
    """
    import llm
    # Get the model.
    if model:
        llm_model = llm.get_model(model)
    else:
        llm_model = llm.get_model()
    _LOG.debug("Using model: %s", llm_model.model_id)
    # Execute with or without progress bar.
    if expected_num_chars:
        # Use streaming with progress bar.
        response_parts = []
        with tqdm(total=expected_num_chars, unit="char") as pbar:
            for chunk in llm_model.prompt(
                input_str, system=system_prompt, stream=True
            ):
                chunk_str = str(chunk)
                response_parts.append(chunk_str)
                pbar.update(len(chunk_str))
        response = "".join(response_parts)
    else:
        # Run without progress bar.
        response = llm_model.prompt(input_str, system=system_prompt).text()
    return response


# #############################################################################
# Main functions
# #############################################################################


def apply_llm(
    input_str: str,
    *,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    use_llm_executable: bool = False,
    expected_num_chars: Optional[int] = None,
) -> str:
    """
    Apply an LLM to process input text using either CLI executable or library.

    This function provides a unified interface to call LLMs either through the
    llm command-line executable or through the llm Python library. It supports
    optional system prompts, model selection, and progress bars for long outputs.

    :param input_str: the input text to process with the LLM
    :param system_prompt: optional system prompt to guide the LLM's behavior
    :param model: optional model name to use (e.g., "gpt-4", "claude-3-opus")
    :param use_llm_executable: if True, use the llm CLI executable; if False,
        use the llm Python library
    :param expected_num_chars: optional expected number of characters in
        output; if provided, displays a progress bar during generation
    :return: LLM response as string
    """
    hdbg.dassert_isinstance(input_str, str)
    hdbg.dassert_ne(input_str, "", "Input string cannot be empty")
    if system_prompt is not None:
        hdbg.dassert_isinstance(system_prompt, str)
    if model is not None:
        hdbg.dassert_isinstance(model, str)
        hdbg.dassert_ne(model, "", "Model cannot be empty string")
    if expected_num_chars is not None:
        hdbg.dassert_isinstance(expected_num_chars, int)
        hdbg.dassert_lt(0, expected_num_chars)
    _LOG.info("Applying LLM to input text")
    _LOG.debug("use_llm_executable=%s", use_llm_executable)
    # Route to appropriate implementation.
    if use_llm_executable:
        # Check that llm executable exists.
        # TODO(gp_ai): use a dassert(_check_llm
        if not _check_llm_executable():
            hdbg.dfatal(
                "llm executable not found. Install it using: pip install llm"
            )
        response = _apply_llm_via_executable(
            input_str,
            system_prompt=system_prompt,
            model=model,
            expected_num_chars=expected_num_chars,
        )
    else:
        response = _apply_llm_via_library(
            input_str,
            system_prompt=system_prompt,
            model=model,
            expected_num_chars=expected_num_chars,
        )
    _LOG.info("LLM processing completed")
    return response


def apply_llm_with_files(
    input_file: str,
    output_file: str,
    *,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    use_llm_executable: bool = False,
    expected_num_chars: Optional[int] = None,
) -> None:
    """
    Apply an LLM to process text from an input file and save to output file.

    This is a convenience wrapper around apply_llm() that handles reading from
    and writing to files. It reads the input file, processes the content using
    the LLM, and writes the result to the output file.

    :param input_file: path to the input file containing text to process
    :param output_file: path to the output file where result will be saved
    :param system_prompt: optional system prompt to guide the LLM's behavior
    :param model: optional model name to use (e.g., "gpt-4", "claude-3-opus")
    :param use_llm_executable: if True, use the llm CLI executable; if False,
        use the llm Python library
    :param expected_num_chars: optional expected number of characters in
        output; if provided, displays a progress bar during generation
    """
    hdbg.dassert_isinstance(input_file, str)
    hdbg.dassert_ne(input_file, "", "Input file cannot be empty")
    hdbg.dassert_isinstance(output_file, str)
    hdbg.dassert_ne(output_file, "", "Output file cannot be empty")
    _LOG.debug("Reading input from file: %s", input_file)
    # Read input file.
    input_str = hio.from_file(input_file)
    _LOG.debug("Read %d characters from input file", len(input_str))
    # Process with LLM.
    response = apply_llm(
        input_str,
        system_prompt=system_prompt,
        model=model,
        use_llm_executable=use_llm_executable,
        expected_num_chars=expected_num_chars,
    )
    # Write output file.
    _LOG.debug("Writing output to file: %s", output_file)
    hio.to_file(output_file, response)
    _LOG.debug("Wrote %d characters to output file", len(response))
