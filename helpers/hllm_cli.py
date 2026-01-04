"""
Import as:

import helpers.hllm_cli as hllmcli
"""

import json
import logging
import shlex
import subprocess
import sys
from typing import Callable, Dict, List, Optional, Tuple, Union

import pandas as pd
from tqdm import tqdm

import helpers.hcache_simple as hcacsimp
import helpers.hdbg as hdbg
import helpers.henv as henv
import helpers.hio as hio
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


#_LOG.trace = lambda *args, **kwargs: None
_LOG.trace = _LOG.debug


def install_needed_modules(
    *, use_sudo: bool = True, venv_path: Optional[str] = None
) -> None:
    """
    Install needed modules for LLM CLI.

    :param use_sudo: whether to use sudo to install the module
    :param venv_path: path to the virtual environment
        E.g., /Users/saggese/src/venv/client_venv.helpers
    """
    henv.install_module_if_not_present(
        "llm",
        package_name="llm",
        use_sudo=use_sudo,
        use_activate=True,
        venv_path=venv_path,
    )
    # Reload the currently imported modules to make sure any freshly installed dependencies are loaded.
    import importlib

    # Reload this module if already imported.
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
        _LOG.trace("system_prompt=\n%s", system_prompt)
        _LOG.trace("input_str=\n%s", input_str)
        result = llm_model.prompt(input_str, system=system_prompt)
        response = result.text()
        _LOG.trace("response=\n%s", response)
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


# #############################################################################
# Batch processing
# #############################################################################

def _validate_batch_inputs(
    prompt: str,
    input_list: List[str],
) -> None:
    """
    Validate prompt and input list for batch processing.

    :param prompt: System prompt to validate
    :param input_list: List of inputs to validate
    :raises: Assertion errors if validation fails
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


@hcacsimp.simple_cache(cache_type="json", write_through=True)
def _llm(
    system_prompt: str,
    input_str: str,
    model: str,
) -> Tuple[str, float]:
    """
    Apply LLM using the llm Python library.

    :param input_str: the input text to process
    :param system_prompt: optional system prompt to use
    :param model: optional model name to use
    :param expected_num_chars: optional expected number of characters in
        output (used for progress bar)
    :return: LLM response as string
    """
    hdbg.dassert_isinstance(system_prompt, str)
    _LOG.trace("system_prompt=\n%s", system_prompt)
    #
    hdbg.dassert_isinstance(input_str, str)
    hdbg.dassert_ne(input_str, "", "Input string cannot be empty")
    _LOG.trace("input_str=\n%s", input_str)
    #
    hdbg.dassert_isinstance(model, str)
    hdbg.dassert_ne(model, "", "Model cannot be empty")
    _LOG.debug("model=%s", llm_model.model_id)

    import llm

    llm_model = llm.get_model(model)
    result = llm_model.prompt(input_str, system=system_prompt)
    response = result.text()
    _LOG.trace("response=\n%s", response)
    #
    import tokencost

    input_tokens = result.usage["input_tokens"]
    output_tokens = result.usage["output_tokens"]
    cost = tokencost.calculate_cost(
        model=model,
        prompt_tokens=input_tokens,
        completion_tokens=output_tokens
    )
    return response, float(cost)


def _call_llm_or_test_functor(
    input_str: str,
    system_prompt: Optional[str],
    model: str,
    testing_functor: Optional[Callable[[str], str]],
) -> Tuple[str, float]:
    """
    Call LLM or testing functor if provided.

    :param input_str: Input text to process
    :param system_prompt: System prompt (can be None)
    :param model: Model name (required for cost calculation)
    :param testing_functor: Optional testing functor
    :return: Tuple of (response, cost) where cost is 0.0 if not calculated
    """
    if testing_functor is None:
        response, cost = _llm(system_prompt, input_str, model)
        # # Calculate cost for this call.
        # # Build full prompt for cost calculation.
        # if system_prompt:
        #     full_prompt = system_prompt + "\n" + input_str
        # else:
        #     full_prompt = input_str
        # cost = _calculate_llm_cost(full_prompt, response, model)
    else:
        response = testing_functor(input_str)
        cost = 0.0
    return response, cost


def _calculate_llm_cost(
    prompt: str,
    completion: str,
    model: str,
) -> float:
    """
    Calculate the cost of an LLM call using tokencost library.

    :param prompt: the prompt sent to the LLM
    :param completion: the completion returned by the LLM
    :param model: the model name used
    :return: total cost in dollars
    """
    import tokencost
    #
    prompt_cost = tokencost.calculate_prompt_cost(prompt, model)
    completion_cost = tokencost.calculate_completion_cost(completion, model)
    total_cost = prompt_cost + completion_cost
    # Convert to float to ensure consistent type.
    return float(total_cost)


def apply_llm_batch_individual(
    prompt: str,
    input_list: List[str],
    *,
    model: str,
    testing_functor: Optional[Callable[[str], str]] = None,
    progress_bar_object: Optional[tqdm] = None,
) -> Tuple[List[str], float]:
    """
    Apply an LLM to process a batch of inputs one at the time.
    """
    _validate_batch_inputs(prompt, input_list)
    _LOG.debug("Processing batch of %d inputs individually", len(input_list))
    # Process each input sequentially with progress bar and error handling.
    responses = []
    # Initialize total cost accumulator.
    total_cost = 0.0
    for input_str in input_list:
        response, cost = _call_llm_or_test_functor(
            input_str=input_str,
            system_prompt=prompt,
            model=model,
            testing_functor=testing_functor,
        )
        total_cost += cost
        responses.append(response)
        if progress_bar_object is not None:
            progress_bar_object.update(1)
    _LOG.debug("Batch processing completed")
    _LOG.info("Total cost for batch: $%.6f", total_cost)
    return responses, total_cost


def apply_llm_batch(
    prompt: str,
    input_list: List[str],
    *,
    model: str,
    testing_functor: Optional[Callable[[str], str]] = None,
    progress_bar_object: Optional[tqdm] = None,
) -> Tuple[List[str], float]:
    """
    Apply an LLM to process a batch of input texts using the same system prompt.
    """
    _validate_batch_inputs(prompt, input_list)
    _LOG.debug("Processing batch of %d inputs", len(input_list))
    # Process each input sequentially with progress bar.
    responses = []
    conv = llm.Conversation()
    conv.system = prompt
    conv.model = model
    for input_str in input_list:
        if testing_functor is None:
            response = m.prompt(input_str, conversation=conv)
            input_tokens = result.usage["input_tokens"]
            output_tokens = result.usage["output_tokens"]
            cost = tokencost.calculate_cost(
                model=model,
                prompt_tokens=input_tokens,
                completion_tokens=output_tokens
            )
        else:
            response = testing_functor(input_str)
        responses.append(response)
        if progress_bar_object is not None:
            progress_bar_object.update(1)
    _LOG.debug("Batch processing completed")
    return responses, total_cost


def apply_llm_batch_combined(
    prompt: str,
    input_list: List[str],
    *,
    model: str,
    max_retries: int = 3,
    testing_functor: Optional[Callable[[str], str]] = None,
    progress_bar_object: Optional[tqdm] = None,
) -> Tuple[List[str], float]:
    """
    Apply an LLM to process a batch using a single combined prompt.

    This function combines all queries into a single prompt and expects
    structured JSON output. It includes retry logic for failed JSON parsing.
    """
    _validate_batch_inputs(prompt, input_list)
    hdbg.dassert_isinstance(max_retries, int)
    hdbg.dassert_lt(0, max_retries)
    _LOG.debug(
        "Processing batch of %d inputs with combined prompt", len(input_list)
    )
    # Build combined prompt.
    combined_prompt = f"{prompt}\n\n"
    instruction = (
        "Process the following items and return results as JSON in the format: "
        '{"0": "result1", "1": "result2", ...}\n\n'
    )
    combined_prompt += instruction
    for idx, input_str in enumerate(input_list):
        combined_prompt += f"{idx}: {input_str}\n"
    combined_prompt += "\nReturn ONLY the JSON object, no other text."
    # Process with retries for JSON parsing.
    total_cost = 0.0
    if testing_functor is None:
        for retry_num in range(max_retries):
            _LOG.debug("Processing batch of %d inputs with combined prompt (attempt %d/%d)", len(input_list), retry_num + 1, max_retries)
            system_prompt = combined_prompt
            prompt = input_str
            response, cost = _llm(system_prompt, prompt, model)
            total_cost += cost
            try:
                # Parse JSON response.
                _LOG.debug("Parsing JSON response (attempt %d/%d)", retry_num + 1, max_retries)
                # Extract JSON from response (handle cases where LLM adds extra text).
                response_stripped = response.strip()
                # Find JSON object boundaries.
                json_start = response_stripped.find("{")
                json_end = response_stripped.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response_stripped[json_start:json_end]
                    result_dict = json.loads(json_str)
                    # Convert dict to list in order.
                    responses = []
                    for idx in range(len(input_list)):
                        key = str(idx)
                        if key in result_dict:
                            responses.append(result_dict[key])
                        else:
                            _LOG.warning("Missing result for index %d", idx)
                            responses.append("")
                    _LOG.debug("Successfully parsed JSON response")
                    if progress_bar_object is not None:
                        progress_bar_object.update(len(input_list))
                    _LOG.info("Total cost for combined batch: $%.6f", total_cost)
                    return responses, total_cost
                else:
                    raise ValueError("No JSON object found in response")
            except (json.JSONDecodeError, ValueError) as e:
                _LOG.debug(
                    "JSON parsing failed (attempt %d/%d): %s", retry_num + 1, max_retries, e
                )
                if retry_num == max_retries - 1:
                    hdbg.dfatal("Failed to parse JSON after %d retries", max_retries)
                # Add instruction to retry.
                combined_prompt += f"\n\nPrevious response had invalid JSON format. Please return ONLY a valid JSON object."
        else:
            for input_str in input_list:
                response = testing_functor(input_str)
                progress_bar_object.update(1)
            cost = 0.0
    # Should not reach here.
    raise RuntimeError("Unexpected error in apply_llm_batch_combined")


# #############################################################################

# TODO(gp): Move it somewhere else.
def get_tqdm_progress_bar() -> tqdm:
    # Use appropriate tqdm for notebook or terminal
    try:
        from IPython import get_ipython

        if get_ipython() is not None:
            from tqdm.notebook import tqdm as notebook_tqdm

            tqdm_progress = notebook_tqdm
        else:
            tqdm_progress = tqdm
    except ImportError:
        tqdm_progress = tqdm
    return tqdm_progress


# TODO(gp): Skip values that already have a value in the target column.
# TODO(gp): Parallelize
def apply_llm_prompt_to_df(
    prompt: str,
    df: pd.DataFrame,
    extractor: Callable[[Union[str, pd.Series]], str],
    target_col: str,
    batch_mode: str,
    *,
    model: str,
    batch_size: int = 50,
    dump_every_batch: Optional[str] = None,
    tag: str = "Processing",
    testing_functor: Optional[Callable[[str], str]] = None,
) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Apply an LLM to process a dataframe column using the same system prompt.

    This function processes text from dataframe rows using an extractor function,
    applies the LLM to each item in batches, and stores the results in a target
    column. It can optionally save progress to a file after each batch.

    :param prompt: system prompt to guide the LLM's behavior
    :param df: dataframe to process
    :param extractor: callable that extracts text from a row or string
    :param target_col: name of column to store results
    :param model: model name to use (e.g., "gpt-4", "claude-3-opus")
    :param batch_size: number of items to process in each batch
    :param dump_every_batch: optional file path to dump the dataframe after each batch
    :param tag: description tag for progress bar
    :param testing_functor: optional functor to use for testing
    :return: tuple of (dataframe with results, statistics dict)
    """
    hdbg.dassert_isinstance(prompt, str)
    hdbg.dassert_ne(prompt, "", "Prompt cannot be empty")
    hdbg.dassert_isinstance(df, pd.DataFrame)
    hdbg.dassert_lt(0, len(df), "Dataframe cannot be empty")
    hdbg.dassert_isinstance(target_col, str)
    hdbg.dassert_ne(target_col, "", "Target column cannot be empty")
    hdbg.dassert_isinstance(model, str)
    hdbg.dassert_ne(model, "", "Model cannot be empty")
    hdbg.dassert_isinstance(batch_size, int)
    hdbg.dassert_lt(0, batch_size)
    if dump_every_batch is not None:
        hdbg.dassert_isinstance(dump_every_batch, str)
        hdbg.dassert_ne(dump_every_batch, "", "Dump file path cannot be empty")
    # Create target column if it doesn't exist.
    if target_col not in df.columns:
        df[target_col] = None
    # Process items in batches with progress bar for entire workload.
    num_items = len(df)
    num_batches = (num_items + batch_size - 1) // batch_size
    _LOG.info("Processing %d items in %d batches", num_items, num_batches)
    num_skipped = 0
    progress_bar_ctor = get_tqdm_progress_bar()
    progress_bar_object = progress_bar_ctor(  # type: ignore
        total=num_items,
        desc=tag,
        dynamic_ncols=True,
        # Workaround for unit tests.
        # file=sys.__stderr__
    )
    # TODO(gp): Precompute the batch indices that needs to be processed.
    for batch_num in range(num_batches):
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
                progress_bar_object.update(1)
        # Call LLM only if there are valid items in this batch.
        if batch_items:
            _LOG.debug(
                "Processing batch %d/%d (%d items, %d skipped)",
                batch_num + 1,
                num_batches,
                len(batch_items),
                len(rows) - len(batch_items),
            )
            if batch_mode == "individual":
                func = apply_llm_batch_individual
            elif batch_mode == "batch":
                func = apply_llm_batch
            elif batch_mode == "combined":
                func = apply_llm_batch_combined
            else:
                hdbg.dfatal("Invalid batch mode: %s", batch_mode)
            batch_responses = func(
                prompt=prompt,
                input_list=batch_items,
                model=model,
                testing_functor=testing_functor,
                progress_bar_object=progress_bar_object,
            )
            _LOG.debug(
                "Skipping batch %d/%d (all %d items have missing data)",
                batch_num + 1,
                num_batches,
                num_items,
            )
        # Dump dataframe to file after batch if requested.
        if dump_every_batch is not None:
            _LOG.debug("Dumping dataframe to file: %s", dump_every_batch)
            df.to_csv(dump_every_batch, index=False)
    _LOG.info(
        "Processing completed (%d items processed, %d skipped)",
        num_items - num_skipped,
        num_skipped,
    )
    stats = {
        "num_items": num_items,
        "num_skipped": num_skipped,
        "num_batches": num_batches,
    }
    return df, stats
