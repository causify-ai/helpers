"""
Import as:

import helpers.hllm_cli as hllmcli
"""

import logging
import shlex
import subprocess
from typing import Callable, List, Optional, Union

import pandas as pd
from tqdm import tqdm

import helpers.hdbg as hdbg
import helpers.hcache_simple as hcacsimp
import helpers.hio as hio
import helpers.hsystem as hsystem
import helpers.henv as henv

_LOG = logging.getLogger(__name__)


def install_needed_modules(*, use_sudo: bool = True, venv_path: Optional[str] = None) -> None:
    """
    Install needed modules for LLM CLI.

    :param use_sudo: whether to use sudo to install the module
    :param venv_path: path to the virtual environment
        E.g., /Users/saggese/src/venv/client_venv.helpers
    """
    henv.install_module_if_not_present("llm", package_name="llm",
        use_sudo=use_sudo, use_activate=True, venv_path=venv_path)
    # Reload the currently imported modules to make sure any freshly installed dependencies are loaded.
    import importlib
    import sys

    # Reload this module (hgoogle_drive_api) if already imported
    this_module_name = __name__
    if this_module_name in sys.modules:
        importlib.reload(sys.modules[this_module_name])


def shutup_llm_logging() -> None:
    """
    Shut up OpenAI logging.
    """
    # OpenAI client logging.
    logging.getLogger("openai").setLevel(logging.WARNING)
    # Common HTTP logging sources
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

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
                f"llm command failed with return code: {proc.returncode} error: {error_msg}"
            )
        response = "".join(response_parts)
    else:
        # Run without progress bar.
        cmd_str = " ".join(shlex.quote(arg) for arg in cmd)
        _, response = hsystem.system_to_string(cmd_str)
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


@hcacsimp.simple_cache(cache_type="json", write_through=True)
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
    _LOG.debug("Applying LLM to input text")
    _LOG.debug("use_llm_executable=%s", use_llm_executable)
    # Route to appropriate implementation.
    if use_llm_executable:
        # Check that llm executable exists.
        hdbg.dassert(
            _check_llm_executable(),
            "llm executable not found. Install it using: pip install llm",
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
    _LOG.debug("LLM processing completed")
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


def apply_llm_batch(
    prompt: str,
    input_list: List[str],
    *,
    model: Optional[str] = None,
) -> List[str]:
    """
    Apply an LLM to process a batch of input texts using the same system prompt.

    This function provides a unified interface to call LLMs on multiple inputs,
    processing each input sequentially with the same system prompt and model
    configuration. A progress bar tracks progress through the batch.

    :param prompt: system prompt to guide the LLM's behavior
    :param input_list: list of input texts to process with the LLM
    :param model: optional model name to use (e.g., "gpt-4", "claude-3-opus")
    :return: list of LLM responses as strings, in the same order as inputs
    """
    hdbg.dassert_isinstance(prompt, str)
    hdbg.dassert_isinstance(input_list, list)
    hdbg.dassert_lt(0, len(input_list), "Input list cannot be empty")
    for idx, input_str in enumerate(input_list):
        hdbg.dassert_isinstance(
            input_str,
            str,
            "Input at index %d must be a string",
            idx,
        )
        hdbg.dassert_ne(
            input_str,
            "",
            "Input at index %d cannot be empty",
            idx,
        )
    if model is not None:
        hdbg.dassert_isinstance(model, str)
        hdbg.dassert_ne(model, "", "Model cannot be empty string")
    _LOG.debug("Processing batch of %d inputs", len(input_list))
    # Process each input sequentially with progress bar.
    responses = []
    use_llm_executable = False
    _LOG.debug("use_llm_executable=%s", use_llm_executable)
    for input_str in input_list:
        response = apply_llm(
            input_str,
            system_prompt=prompt,
            model=model,
            use_llm_executable=use_llm_executable,
        )
        responses.append(response)
    _LOG.debug("Batch processing completed")
    return responses


# TODO(gp): Add unit tests.
# TODO(gp): Add tag for progress bar.
# TODO(gp): Pass progress bar to accumulate.
# TODO(gp): Skip values that already have a value in the target column.
def apply_llm_prompt_to_df(
    prompt: str,
    df: pd.DataFrame,
    extractor: Callable[[Union[str, pd.Series]], str],
    target_col: str,
    *,
    batch_size: int = 100,
    dump_every_batch: Optional[str] = None,
    model: Optional[str] = None,
) -> pd.DataFrame:
    """
    Apply an LLM to process a dataframe column using the same system prompt.

    This function processes text from a source column in batches, applies the LLM
    to each item, and stores the results in a target column. It can optionally
    save progress to a file after each batch.

    :param prompt: system prompt to guide the LLM's behavior
    :param df: dataframe to process
    :param source_col: name of column containing input text to process
    :param target_col: name of column to store results
    :param batch_size: number of items to process in each batch
    :param dump_every_batch: optional file path to dump the dataframe after each batch
    :param model: optional model name to use (e.g., "gpt-4", "claude-3-opus")
    :return: dataframe with new target column containing LLM responses
    """
    hdbg.dassert_isinstance(prompt, str)
    hdbg.dassert_ne(prompt, "", "Prompt cannot be empty")
    hdbg.dassert_isinstance(df, pd.DataFrame)
    hdbg.dassert_lt(0, len(df), "Dataframe cannot be empty")
    hdbg.dassert_isinstance(target_col, str)
    hdbg.dassert_ne(target_col, "", "Target column cannot be empty")
    hdbg.dassert_isinstance(batch_size, int)
    hdbg.dassert_lt(0, batch_size)
    if dump_every_batch is not None:
        hdbg.dassert_isinstance(dump_every_batch, str)
        hdbg.dassert_ne(dump_every_batch, "", "Dump file path cannot be empty")
    if model is not None:
        hdbg.dassert_isinstance(model, str)
        hdbg.dassert_ne(model, "", "Model cannot be empty string")
    # Create target column if it doesn't exist.
    if target_col not in df.columns:
        df[target_col] = None
    # Process items in batches with progress bar for entire workload.
    num_batches = (len(df) + batch_size - 1) // batch_size
    _LOG.info("Processing %d items in %d batches", len(df), num_batches)
    num_skipped = 0
    # Use appropriate tqdm for notebook or terminal
    # TODO(gp): Factor this out somewhere.
    try:
        from IPython import get_ipython

        if get_ipython() is not None:
            from tqdm.notebook import tqdm as notebook_tqdm
            tqdm_progress = notebook_tqdm
        else:
            tqdm_progress = tqdm
    except ImportError:
        tqdm_progress = tqdm

    for batch_num in tqdm_progress(range(num_batches), desc="Processing batches"):
        # Get batch rows.
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(df))
        rows = df.iloc[start_idx:end_idx]
        # Extract items from rows, filtering out invalid ones.
        batch_items = []
        batch_indices = []
        for idx, row in rows.iterrows():
            extracted_text = extractor(row)
            # Check if extraction returned valid text (not NaN/None/empty).
            if extracted_text != "":
                batch_items.append(extracted_text)
                batch_indices.append(idx)
            else:
                # Set NaN for rows with missing company information.
                df.at[idx, target_col] = ""
                num_skipped += 1
        # Call LLM only if there are valid items in this batch.
        if batch_items:
            _LOG.debug(
                "Processing batch %d/%d (%d items, %d skipped)",
                batch_num + 1,
                num_batches,
                len(batch_items),
                len(rows) - len(batch_items),
            )
            batch_responses = apply_llm_batch(
                prompt=prompt,
                input_list=batch_items,
                model=model,
            )
            # Update dataframe with batch results.
            for idx, response in zip(batch_indices, batch_responses):
                df.at[idx, target_col] = response.strip()
        else:
            _LOG.debug(
                "Skipping batch %d/%d (all %d items have missing data)",
                batch_num + 1,
                num_batches,
                len(rows),
            )
        # Dump dataframe to file after batch if requested.
        if dump_every_batch is not None:
            _LOG.debug("Dumping dataframe to file: %s", dump_every_batch)
            df.to_csv(dump_every_batch, index=False)
    _LOG.info("Processing completed (%d items processed, %d skipped)", len(df) - num_skipped, num_skipped)
    return df