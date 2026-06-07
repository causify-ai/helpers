"""
Import as:

import helpers.hllm_cli as hllmcli
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import hashlib
import json
import logging
import shlex
import subprocess
import sys
import importlib
import pprint
import time
from dataclasses import dataclass
from typing import (
    Callable,
    List,
    Optional,
    Tuple,
    Union,
    TYPE_CHECKING,
)
from unittest import mock

try:
    import llm

    _LLM_AVAILABLE = True
except ImportError:
    llm = None
    _LLM_AVAILABLE = False

try:
    import tokencost

    _TOKENCOST_AVAILABLE = True
except ImportError:
    _TOKENCOST_AVAILABLE = False

from tqdm import tqdm

if TYPE_CHECKING:
    import pandas as pd

import helpers.hcache_simple as hcacsimp
import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hmarkdown_select as hmarsele
import helpers.hmodule as hmodule
import helpers.hprint as hprint
import helpers.hsystem as hsystem


_LOG = logging.getLogger(__name__)


# _LOG.trace = lambda *args, **kwargs: None
_LOG.trace = _LOG.debug


# #############################################################################
# TokenStats
# #############################################################################


@dataclass
class TokenStats:
    """
    Token usage and cost statistics for LLM operations.

    Tracks input/output tokens, costs from multiple sources, and elapsed time.
    """

    input_tokens: int = 0
    output_tokens: int = 0
    cost_from_tokencost: float = 0.0
    cost_from_llm_library: float = 0.0
    elapsed_time_in_seconds: float = 0.0
    tokens_per_second: float = 0.0

    def __post_init__(self) -> None:
        """
        Validate TokenStats after initialization.
        """
        self.check()
        # Compute tokens_per_second from the other fields.
        self.tokens_per_second = self._compute_tokens_per_second()

    def check(self) -> None:
        """
        Ensure all numeric values are non-negative and properly typed.
        """
        hdbg.dassert_lte(0, self.input_tokens)
        hdbg.dassert_lte(0, self.output_tokens)
        hdbg.dassert_lte(0, self.cost_from_tokencost)
        hdbg.dassert_lte(0, self.elapsed_time_in_seconds)
        hdbg.dassert_lte(0, self.cost_from_llm_library)
        hdbg.dassert_lte(0, self.tokens_per_second)
        # Ensure proper types.
        self.input_tokens = int(self.input_tokens)
        self.output_tokens = int(self.output_tokens)
        self.cost_from_tokencost = float(self.cost_from_tokencost)
        self.elapsed_time_in_seconds = float(self.elapsed_time_in_seconds)
        self.cost_from_llm_library = float(self.cost_from_llm_library)
        self.tokens_per_second = float(self.tokens_per_second)

    def _compute_tokens_per_second(self) -> float:
        """
        Compute tokens per second from input_tokens, output_tokens, and elapsed_time_in_seconds.
        """
        total_tokens = self.input_tokens + self.output_tokens
        if self.elapsed_time_in_seconds > 0:
            return total_tokens / self.elapsed_time_in_seconds
        return 0.0

    def to_float(self) -> float:
        """
        Convert TokenStats to a single float value (for backward compatibility).

        Uses the tokencost cost if available, otherwise uses the llm_library cost.

        :return: total cost in dollars as a float
        """
        if self.cost_from_tokencost > 0 and self.cost_from_llm_library > 0:
            if abs(
                float(self.cost_from_tokencost)
                - float(self.cost_from_llm_library)
            ):
                _LOG.warning(
                    "Cost is different: "
                    "cost_from_tokencost = %s != cost_from_llm_library = %s"
                    % (self.cost_from_tokencost, self.cost_from_llm_library)
                )
        if self.cost_from_tokencost > 0:
            return float(self.cost_from_tokencost)
        if self.cost_from_llm_library > 0:
            return float(self.cost_from_llm_library)
        return 0.0

    def to_str(self) -> str:
        """
        Convert TokenStats to a formatted string for logging.

        :return: formatted string with cost, token counts, elapsed time, and tokens per second
        """
        cost = self.to_float()
        elapsed_time = self.elapsed_time_in_seconds
        # Format cost: $ for >= $1, cents for $0.0001-$1, u$ for < $0.0001
        if cost >= 1.0:
            cost_str = f"${cost:.6f}"
        elif cost >= 0.0001:
            cost_str = f"{cost * 100:.2f}c"
        else:
            cost_str = f"{cost * 1e6:.2f}u$"
        # Show tokens per second when elapsed time is positive.
        if self.tokens_per_second > 0:
            res = f"Cost: {cost_str}, Elapsed: {elapsed_time:.2f}s, {self.tokens_per_second:.2f} tok/s ("
        else:
            res = f"Cost: {cost_str}, Elapsed: {elapsed_time:.2f}s ("
        fields = [
            "input_tokens",
            "output_tokens",
            "cost_from_llm_library",
            "cost_from_tokencost",
        ]
        for field in fields:
            val = getattr(self, field, "na")
            res += f"{field}={val}, "
        res += ")"
        return res

    @classmethod
    def aggregate(cls, token_stats_list: List[TokenStats]) -> TokenStats:
        """
        Aggregate multiple TokenStats into a single combined instance.

        Sums up token counts, costs, and elapsed times across all provided stats.

        :param token_stats_list: list of TokenStats to aggregate
        :return: aggregated TokenStats with summed values
        """
        total_input_tokens = sum(ts.input_tokens for ts in token_stats_list)
        total_output_tokens = sum(ts.output_tokens for ts in token_stats_list)
        total_cost_from_tokencost = sum(
            ts.cost_from_tokencost for ts in token_stats_list
        )
        total_cost_from_llm_library = sum(
            ts.cost_from_llm_library for ts in token_stats_list
        )
        total_elapsed_time = sum(
            ts.elapsed_time_in_seconds for ts in token_stats_list
        )
        # tokens_per_second is computed in __post_init__, so pass 0.0 and let
        # the constructor derive it from the aggregated totals.
        return cls(
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            cost_from_tokencost=total_cost_from_tokencost,
            cost_from_llm_library=total_cost_from_llm_library,
            elapsed_time_in_seconds=total_elapsed_time,
            tokens_per_second=0.0,
        )

    @classmethod
    def from_file(cls, file_path: str) -> TokenStats:
        """
        Load TokenStats from a JSON file.

        :param file_path: path to file containing TokenStats JSON
        :return: TokenStats instance loaded from file
        """
        hdbg.dassert_file_exists(file_path, "Stat file must exist")
        content = hio.from_file(file_path)
        data = json.loads(content)
        return cls(**data)

    def to_file(self, file_path: str) -> None:
        """
        Save TokenStats to a JSON file.

        :param file_path: path where JSON file will be saved
        """
        data = dataclasses.asdict(self)
        # Ensure tokens_per_second is always computed from the other fields.
        data["tokens_per_second"] = self._compute_tokens_per_second()
        json_str = json.dumps(data, indent=2)
        hio.to_file(file_path, json_str)


# #############################################################################
# Low-level utility functions
# #############################################################################


def install_needed_modules(
    *, use_sudo: bool = True, venv_path: str = ""
) -> None:
    """
    Install needed modules for LLM CLI (llm and tokencost).

    :param use_sudo: whether to use sudo to install the module
    :param venv_path: path to the virtual environment
        E.g., /Users/saggese/src/venv/client_venv.helpers
    """
    hmodule.install_module_if_not_present(
        "llm",
        package_name="llm",
        use_sudo=use_sudo,
        use_activate=True,
        venv_path=venv_path,
    )
    hmodule.install_module_if_not_present(
        "tokencost",
        package_name="tokencost",
        use_sudo=use_sudo,
        use_activate=True,
        venv_path=venv_path,
    )
    # Reload this module if already imported.
    this_module_name = __name__
    if this_module_name in sys.modules:
        importlib.reload(sys.modules[this_module_name])


def shutup_llm_logging() -> None:
    """
    Suppress verbose logging from OpenAI and HTTP libraries.

    Reduces noise from OpenAI client, httpx, httpcore, and urllib3 loggers.
    """
    # OpenAI client logging.
    logging.getLogger("openai").setLevel(logging.WARNING)
    # Common HTTP logging sources.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


# #############################################################################
# Low-level utility functions
# #############################################################################


def _compute_text_signature(txt: str) -> str:
    """
    Compute a compact signature of text using first and last two words.

    Returns the full text if it contains 4 or fewer words; otherwise returns
    a compressed representation showing the first and last two words.

    :param txt: text to compute signature for
    :return: signature string
        - Format: `"first second ... last-1 last"` for long text
        - Full text for short text (4 words or fewer)
    """
    words = txt.split()
    if len(words) <= 4:
        return txt
    first_two = " ".join(words[:2])
    last_two = " ".join(words[-2:])
    return f"{first_two} ... {last_two}"


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
        # llm executable not found.
        _LOG.debug("llm command not found")
        return False


def _calculate_cost_from_usage(
    usage: object,
    model: str,
    elapsed_time_in_seconds: float = 0.0,
) -> TokenStats:
    """
    Calculate LLM cost from usage object.

    Uses the tokencost library to compute total cost based on input and output
    token counts. Returns a TokenStats instance with token counts and costs.

    :param usage: usage object from LLM result containing input/output token counts
    :param model: model name for cost calculation
    :param elapsed_time_in_seconds: elapsed time for the LLM call in seconds
    :return: TokenStats instance with input_tokens, output_tokens, cost_from_tokencost
    """
    input_tokens = usage.input
    output_tokens = usage.output
    if _TOKENCOST_AVAILABLE:
        try:
            prompt_cost = tokencost.calculate_cost_by_tokens(
                num_tokens=input_tokens, model=model, token_type="input"
            )
            completion_cost = tokencost.calculate_cost_by_tokens(
                num_tokens=output_tokens, model=model, token_type="output"
            )
            cost = float(prompt_cost + completion_cost)
        except KeyError as e:
            _LOG.debug("Can't find tokencost cost: %s", str(e))
            cost = 0.0
    else:
        cost = 0.0
    return TokenStats(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_from_tokencost=cost,
        elapsed_time_in_seconds=elapsed_time_in_seconds,
    )


# #############################################################################
# Backend implementations
# #############################################################################


def _apply_llm_via_mock(
    input_str: str,
    *,
    system_prompt: str = "",
) -> Tuple[str, TokenStats]:
    """
    Mock LLM application for testing.

    Returns a deterministic MD5 hash of the concatenated input and system
    prompt text. Useful for testing without making actual API calls.

    :param input_str: the input text to process
    :param system_prompt: optional system prompt to use
    :return: tuple of (MD5 digest as string, TokenStats with zeros)
    """
    sig_system = _compute_text_signature(system_prompt) if system_prompt else ""
    sig_input = _compute_text_signature(input_str)
    concatenated = f"{sig_system}\n{sig_input}"
    digest = hashlib.md5(concatenated.encode()).hexdigest()
    return digest, TokenStats()


def _apply_llm_via_executable(
    input_str: str,
    *,
    system_prompt: str = "",
    model: str = "",
    expected_num_chars: int = 0,
) -> Tuple[str, TokenStats]:
    """
    Apply LLM using the llm CLI executable.

    Invokes the llm command-line tool as a subprocess, with optional system
    prompt and model selection. Supports streaming with progress bar if
    expected output size is provided.

    :param input_str: the input text to process
    :param system_prompt: optional system prompt to use
    :param model: optional model name to use
    :param expected_num_chars: optional expected number of characters in output
        - Used to enable progress bar tracking during generation
    :return: tuple of (LLM response as string, TokenStats instance)
    """
    start_time = time.time()
    # Build command with system prompt and model options.
    cmd = ["llm"]
    if system_prompt:
        cmd.extend(["--system", system_prompt])
    if model:
        cmd.extend(["--model", model])
    cmd.append(input_str)
    _LOG.debug("Running command: %s", " ".join(cmd))
    # Execute command with or without streaming.
    if expected_num_chars > 0:
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
            error_msg = proc.stderr.read() if proc.stderr else ""  # type: ignore
            raise RuntimeError(
                "llm command failed with return code: %s error: %s"
                % (proc.returncode, error_msg)
            )
        response = "".join(response_parts)
    else:
        # Run without progress bar.
        cmd_str = " ".join(shlex.quote(arg) for arg in cmd)
        _, response = hsystem.system_to_string(cmd_str)
    elapsed_time = time.time() - start_time
    _LOG.debug("Cost calculation not available when using llm executable")
    return response, TokenStats(elapsed_time_in_seconds=elapsed_time)


def _apply_llm_via_library(
    input_str: str,
    *,
    system_prompt: str = "",
    model: str = "",
    expected_num_chars: int = 0,
) -> Tuple[str, TokenStats]:
    """
    Apply LLM using the llm Python library.

    Calls the llm library directly with optional streaming and progress bar
    support. Calculates token cost if the tokencost library is available.

    :param input_str: the input text to process
    :param system_prompt: optional system prompt to use
    :param model: optional model name to use
    :param expected_num_chars: optional expected number of characters in output
        - Used to enable progress bar tracking during generation
    :return: tuple of (LLM response as string, TokenStats instance)
    """
    start_time = time.time()
    # Get the model.
    if model:
        llm_model = llm.get_model(model)
    else:
        llm_model = llm.get_model()
    _LOG.debug("Using model: %s", llm_model.model_id)
    # Execute with or without progress bar.
    if expected_num_chars > 0:
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
        elapsed_time = time.time() - start_time
        _LOG.debug("Cost calculation not available for streaming mode")
        token_stats = TokenStats(elapsed_time_in_seconds=elapsed_time)
    else:
        # Run without progress bar.
        _LOG.trace("system_prompt=\n%s", system_prompt)
        _LOG.trace("input_str=\n%s", input_str)
        result = llm_model.prompt(input_str, system=system_prompt)
        response = result.text()
        _LOG.trace("response=\n%s", response)
        # Calculate cost.
        usage = result.usage()
        elapsed_time = time.time() - start_time
        token_stats = _calculate_cost_from_usage(
            usage=usage,
            model=llm_model.model_id,
            elapsed_time_in_seconds=elapsed_time,
        )
        _LOG.debug(
            "Cost: %s",
            token_stats.to_str(),
        )
    return response, token_stats


# #############################################################################
# Core public API
# #############################################################################

# Overview of `apply_llm*` functions:
# - `apply_llm()`
#   - Core function for processing a single input string with an LLM
#   - Can use CLI executable or library backend
#   - Returns the response and cost
# - `apply_llm_with_files()`
#   - Convenience wrapper around `apply_llm()` that reads from an input file,
#     processes it, and writes the result to an output file
# - `apply_llm_batch_individual()`
#   - Process multiple inputs by making individual LLM calls for each input
#     with the same system prompt
#   - Each call is independent
# - `apply_llm_batch_with_shared_prompt()`
#   - Process multiple inputs by maintaining a single conversation context
#     across all inputs (more efficient for related queries)
# - `apply_llm_batch_combined()`
#   - Process multiple inputs by combining them into a single LLM call
#     expecting structured JSON output
#   - Most efficient but requires careful prompt engineering for proper JSON
#     formatting
# - `apply_llm_prompt_to_df()`
#   - Apply an LLM to process rows from a pandas dataframe, with results stored
#     in a target column
#   - Supports all three batch modes and incremental progress saving


@hcacsimp.simple_cache(cache_type="pickle", write_through=True)
def apply_llm(
    input_str: str,
    *,
    system_prompt: str = "",
    model: str = "",
    backend: str = "library",
    expected_num_chars: int = 0,
) -> Tuple[str, TokenStats]:
    """
    Apply an LLM to process input text using specified backend.

    This function provides a unified interface to call LLMs through different
    backends: the llm command-line executable, the llm Python library, or a
    mock backend for testing. It supports optional system prompts, model
    selection, and progress bars for long outputs.

    :param input_str: the input text to process with the LLM
    :param system_prompt: optional system prompt to guide the LLM's behavior
    :param model: optional model name to use (e.g., "gpt-4", "claude-3-opus")
    :param backend: backend to use ("executable", "library", or "mock")
    :param expected_num_chars: optional expected number of characters in
        output; if provided, displays a progress bar during generation
    :return: tuple of (LLM response as string, TokenStats instance)
    """
    hdbg.dassert_isinstance(input_str, str)
    hdbg.dassert_ne(input_str, "", "Input string cannot be empty")
    if system_prompt:
        hdbg.dassert_isinstance(system_prompt, str)
    if model:
        hdbg.dassert_isinstance(model, str)
        hdbg.dassert_ne(model, "", "Model cannot be empty string")
    if expected_num_chars > 0:
        hdbg.dassert_isinstance(expected_num_chars, int)
        hdbg.dassert_lt(
            0,
            expected_num_chars,
            "Expected number of characters must be positive",
        )
    hdbg.dassert_in(
        backend,
        ["executable", "library", "mock"],
        "Invalid backend specified",
    )
    _LOG.debug("Applying LLM to input text")
    _LOG.debug("backend=%s", backend)
    # Route to appropriate implementation.
    if backend == "executable":
        # Check that llm executable exists.
        hdbg.dassert(_check_llm_executable(), "llm executable not found")
        response, token_stats = _apply_llm_via_executable(
            input_str,
            system_prompt=system_prompt,
            model=model,
            expected_num_chars=expected_num_chars,
        )
    elif backend == "library":
        # Check that llm library is available.
        hdbg.dassert(_LLM_AVAILABLE, "llm library not found")
        response, token_stats = _apply_llm_via_library(
            input_str,
            system_prompt=system_prompt,
            model=model,
            expected_num_chars=expected_num_chars,
        )
    elif backend == "mock":
        response, token_stats = _apply_llm_via_mock(
            input_str,
            system_prompt=system_prompt,
        )
    _LOG.debug("LLM processing completed")
    return response, token_stats


def apply_llm_with_files(
    input_file: str,
    output_file: str,
    *,
    system_prompt: str = "",
    model: str = "",
    backend: str = "library",
    expected_num_chars: int = 0,
) -> TokenStats:
    """
    Apply an LLM to process text from an input file and save to output file.

    This is a convenience wrapper around apply_llm() that handles reading from
    and writing to files. It reads the input file, processes the content using
    the LLM, and writes the result to the output file.

    :param input_file: path to the input file containing text to process
    :param output_file: path to the output file where result will be saved
    :param system_prompt: optional system prompt to guide the LLM's behavior
    :param model: optional model name to use (e.g., "gpt-4", "claude-3-opus")
    :param backend: backend to use ("executable", "library", or "mock")
    :param expected_num_chars: optional expected number of characters in
        output; if provided, displays a progress bar during generation
    :return: TokenStats instance
    """
    hdbg.dassert_isinstance(input_file, str)
    hdbg.dassert_ne(input_file, "", "Input file path cannot be empty")
    hdbg.dassert_isinstance(output_file, str)
    hdbg.dassert_ne(output_file, "", "Output file path cannot be empty")
    _LOG.debug("Reading input from file: %s", input_file)
    # Read input file.
    input_str = hio.from_file(input_file)
    _LOG.debug("Read %d characters from input file", len(input_str))
    # Process with LLM.
    response, token_stats = apply_llm(
        input_str,
        system_prompt=system_prompt,
        model=model,
        backend=backend,
        expected_num_chars=expected_num_chars,
    )
    # Write output file.
    _LOG.debug("Writing output to file: %s", output_file)
    hio.to_file(output_file, response)
    _LOG.debug("Wrote %d characters to output file", len(response))
    return token_stats


# #############################################################################
# Batch processing helpers
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
    hdbg.dassert_isinstance(prompt, str, "Prompt must be a string")
    hdbg.dassert_isinstance(input_list, list, "Input list must be a list")
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


@hcacsimp.simple_cache(cache_type="pickle", write_through=True)
def _llm(
    system_prompt: str,
    input_str: str,
    model: str,
) -> Tuple[str, TokenStats]:
    """
    Apply LLM using the llm Python library.

    :param system_prompt: system prompt to guide the LLM's behavior
    :param input_str: the input text to process
    :param model: model name to use
    :return: tuple of (LLM response as string, TokenStats instance)
    """
    hdbg.dassert_isinstance(system_prompt, str, "System prompt must be a string")
    _LOG.trace("system_prompt=\n%s", system_prompt)
    hdbg.dassert_isinstance(input_str, str, "Input string must be a string")
    _LOG.trace("input_str=\n%s", input_str)
    hdbg.dassert_isinstance(model, str, "Model must be a string")
    hdbg.dassert_ne(model, "", "Model cannot be empty")
    llm_model = llm.get_model(model)
    _LOG.debug("model=%s", llm_model.model_id)
    # Call the LLM.
    result = llm_model.prompt(input_str, system=system_prompt)
    response = result.text()
    _LOG.trace("response=\n%s", response)
    usage = result.usage()
    token_stats = _calculate_cost_from_usage(
        usage=usage,
        model=model,
    )
    return response, token_stats


def _call_llm_or_test_functor(
    input_str: str,
    system_prompt: str,
    model: str,
    testing_functor: Optional[Callable[[str], str]],
) -> Tuple[str, TokenStats]:
    """
    Call LLM or testing functor if provided.

    Routes to either the LLM or a testing functor. When testing_functor is
    provided, it takes precedence and cost calculation is skipped.

    :param input_str: Input text to process
    :param system_prompt: System prompt (can be None)
    :param model: Model name (required for cost calculation)
    :param testing_functor: Optional testing functor to use instead of LLM
    :return: Tuple of (response, TokenStats) where TokenStats is zeros for testing functor
    """
    if testing_functor is None:
        response, token_stats = _llm(system_prompt, input_str, model)
    else:
        response = testing_functor(input_str)
        token_stats = TokenStats()
    return response, token_stats


def _calculate_llm_cost(
    prompt: str,
    completion: str,
    model: str,
) -> float:
    """
    Calculate the cost of an LLM call using tokencost library.

    Computes the total cost based on prompt and completion text if the
    tokencost library is available; otherwise returns 0.0.

    :param prompt: the prompt sent to the LLM
    :param completion: the completion returned by the LLM
    :param model: the model name used
    :return: total cost in dollars
    """
    if _TOKENCOST_AVAILABLE:
        prompt_cost = tokencost.calculate_prompt_cost(prompt, model)
        completion_cost = tokencost.calculate_completion_cost(completion, model)
        total_cost = prompt_cost + completion_cost
    else:
        total_cost = 0.0
    # Convert to float to ensure consistent type.
    return float(total_cost)


# TODO(gp): Move it somewhere else.
def get_tqdm_progress_bar() -> tqdm:
    """
    Get the appropriate tqdm progress bar class for the current environment.

    Detects whether running in a Jupyter notebook or terminal and returns
    the corresponding tqdm class. Notebook environments get the specialized
    `tqdm.notebook.tqdm` for better Jupyter integration.

    :return: tqdm class appropriate for the current environment
        - `tqdm.notebook.tqdm` for Jupyter notebooks
        - `tqdm.tqdm` for terminal environments
    """
    # Use appropriate tqdm for notebook or terminal.
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


# #############################################################################
# Batch processing implementations
# #############################################################################


def apply_llm_batch_individual(
    prompt: str,
    input_list: List[str],
    *,
    model: str,
    testing_functor: Optional[Callable[[str], str]] = None,
    progress_bar_object: Optional[tqdm] = None,
) -> Tuple[List[str], TokenStats]:
    """
    Apply an LLM to process a batch of inputs one at a time.

    :param prompt: system prompt to guide the LLM's behavior
    :param input_list: list of input strings to process
    :param model: model name to use
    :param testing_functor: optional testing function to use instead of LLM
    :param progress_bar_object: optional progress bar object to update
    :return: tuple of (list of responses, aggregated TokenStats)
    """
    _validate_batch_inputs(prompt, input_list)
    _LOG.debug("Processing batch of %d inputs individually", len(input_list))
    responses = []
    token_stats_list = []
    for input_str in input_list:
        response, token_stats = _call_llm_or_test_functor(
            input_str=input_str,
            system_prompt=prompt,
            model=model,
            testing_functor=testing_functor,
        )
        responses.append(response)
        token_stats_list.append(token_stats)
        if progress_bar_object is not None:
            total_cost_float = TokenStats.aggregate(token_stats_list).to_float()
            progress_bar_object.update(1)
            progress_bar_object.set_postfix_str(f"Cost: ${total_cost_float:.4f}")
    aggregated_cost = TokenStats.aggregate(token_stats_list)
    _LOG.debug("Batch processing completed")
    _LOG.debug(
        "Total cost for batch with individual prompt: %s",
        aggregated_cost.to_str(),
    )
    return responses, aggregated_cost


def apply_llm_batch_with_shared_prompt(
    prompt: str,
    input_list: List[str],
    *,
    model: str,
    testing_functor: Optional[Callable[[str], str]] = None,
    progress_bar_object: Optional[tqdm] = None,
) -> Tuple[List[str], TokenStats]:
    """
    Apply an LLM to process a batch of input texts using the same system prompt.

    :param prompt: system prompt to guide the LLM's behavior
    :param input_list: list of input strings to process
    :param model: model name to use
    :param testing_functor: optional testing function to use instead of LLM
    :param progress_bar_object: optional progress bar object to update
    :return: tuple of (list of responses, aggregated TokenStats)
    """
    _validate_batch_inputs(prompt, input_list)
    _LOG.debug("Processing batch of %d inputs", len(input_list))
    responses = []
    token_stats_list = []
    if testing_functor is None:
        llm_model = llm.get_model(model)
        conv = llm.Conversation(model=llm_model)
        for input_str in input_list:
            result = conv.prompt(input_str, system=prompt)
            response = result.text()
            usage = result.usage()
            token_stats = _calculate_cost_from_usage(
                usage=usage,
                model=model,
            )
            responses.append(response)
            token_stats_list.append(token_stats)
            if progress_bar_object is not None:
                total_cost_float = TokenStats.aggregate(
                    token_stats_list
                ).to_float()
                progress_bar_object.update(1)
                progress_bar_object.set_postfix_str(
                    f"Cost: ${total_cost_float:.4f}"
                )
    else:
        for input_str in input_list:
            response = testing_functor(input_str)
            responses.append(response)
            token_stats_list.append(TokenStats())
            if progress_bar_object is not None:
                progress_bar_object.update(1)
    aggregated_cost = TokenStats.aggregate(token_stats_list)
    _LOG.debug("Batch processing completed")
    _LOG.debug(
        "Total cost for batch with shared prompt: %s",
        aggregated_cost.to_str(),
    )
    return responses, aggregated_cost


def apply_llm_batch_combined(
    prompt: str,
    input_list: List[str],
    *,
    model: str,
    max_retries: int = 3,
    testing_functor: Optional[Callable[[str], str]] = None,
    progress_bar_object: Optional[tqdm] = None,
) -> Tuple[List[str], TokenStats]:
    """
    Apply an LLM to process a batch using a single combined prompt.

    Combines all queries into a single prompt and expects structured JSON
    output. Includes retry logic for failed JSON parsing to ensure robust
    processing of batch results.

    :param prompt: system prompt to guide the LLM's behavior
    :param input_list: list of input strings to process
    :param model: model name to use
    :param max_retries: maximum number of retry attempts on JSON parsing failures
    :param testing_functor: optional testing function to use instead of LLM
    :param progress_bar_object: optional progress bar object to update
    :return: tuple of (list of responses, aggregated TokenStats)
    """
    _validate_batch_inputs(prompt, input_list)
    hdbg.dassert_isinstance(max_retries, int)
    hdbg.dassert_lt(
        0,
        max_retries,
        "Max retries must be positive",
    )
    _LOG.debug(
        "Processing batch of %d inputs with combined prompt", len(input_list)
    )
    combined_prompt = f"{prompt}\n\n"
    instruction = """
        Return the results only as a valid JSON object with string values, using
        zero-based numeric keys that match the item numbers.

        Output format:
        '{"0": "result1", "1": "result2", ...}

        """
    combined_prompt += hprint.dedent(instruction)
    for idx, input_str in enumerate(input_list):
        combined_prompt += f"{idx}: {input_str}\n"
    combined_prompt += "\nReturn ONLY the JSON object, no other text."
    _LOG.debug("Combined prompt:\n%s", combined_prompt)
    token_stats_list = []
    # You are a calculator. Return only the numeric result.
    # ```
    # Process the following items and return results as JSON in the format:
    # {"0": "result1", "1": "result2", ...}
    # 0: 2 + 2
    # 1: 3 * 3
    # 2: 10 - 5
    # 3: 20 / 4
    # Return ONLY the JSON object, no other text.
    # ```
    # Process with retries for JSON parsing.
    if testing_functor is None:
        for retry_num in range(max_retries):
            _LOG.debug(
                "Processing batch of %d inputs with combined prompt (attempt %d/%d)",
                len(input_list),
                retry_num + 1,
                max_retries,
            )
            system_prompt = combined_prompt
            user_prompt = "Process the items listed above."
            response, token_stats = _llm(system_prompt, user_prompt, model)
            token_stats_list.append(token_stats)
            try:
                # Parse JSON response.
                # E.g.,
                # ```
                # {"0": "4", "1": "9", "2": "5", "3": "5"}
                # ```
                _LOG.debug("Parsing JSON response:\n%s", response)
                # Extract JSON from response (handle cases where LLM adds extra text).
                response_stripped = response.strip()
                # Find JSON object boundaries.
                json_start = response_stripped.find("{")
                json_end = response_stripped.rfind("}") + 1
                hdbg.dassert_lte(0, json_start)
                hdbg.dassert_lt(json_start, json_end)
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
                aggregated_cost = TokenStats.aggregate(token_stats_list)
                if progress_bar_object is not None:
                    progress_bar_object.update(len(input_list))
                    progress_bar_object.set_postfix_str(
                        f"Cost: ${aggregated_cost.to_float():.4f}"
                    )
                _LOG.debug(
                    "Total cost for batch with combined prompt: %s",
                    aggregated_cost.to_str(),
                )
                return responses, aggregated_cost
            except (json.JSONDecodeError, ValueError) as e:
                _LOG.debug(
                    "JSON parsing failed (attempt %d/%d): %s",
                    retry_num + 1,
                    max_retries,
                    e,
                )
                if retry_num == max_retries - 1:
                    raise ValueError(
                        "Failed to parse JSON after %d retries: %s"
                        % (max_retries, str(e))
                    )
                # Add instruction to retry.
                combined_prompt += "\n\nPrevious response had invalid JSON format. Please return ONLY a valid JSON object."
    else:
        responses = []
        for input_str in input_list:
            response = testing_functor(input_str)
            responses.append(response)
            token_stats_list.append(TokenStats())
            if progress_bar_object is not None:
                progress_bar_object.update(1)
        aggregated_cost = TokenStats.aggregate(token_stats_list)
        return responses, aggregated_cost
    raise RuntimeError("Unexpected error in apply_llm_batch_combined")


# #############################################################################
# Batch orchestration
# #############################################################################


def _call_batch_processor(
    batch_mode: str,
    prompt: str,
    batch_items: List[str],
    model: str,
    testing_functor: Optional[Callable[[str], str]],
    progress_bar_object: Optional[tqdm],
) -> Tuple[List[str], TokenStats]:
    """
    Call the appropriate batch processor based on batch_mode.

    Routes to one of three batch processing strategies: individual processing,
    shared prompt conversation, or combined batch processing.

    :param batch_mode: batch mode to use
        - `individual`: separate LLM call for each item
        - `shared_prompt`: conversation context across items
        - `combined`: single call with all items as JSON
    :param prompt: system prompt to guide the LLM's behavior
    :param batch_items: list of input strings to process
    :param model: model name to use
    :param testing_functor: optional testing functor to use instead of LLM
    :param progress_bar_object: optional progress bar object to update
    :return: tuple of (list of responses, TokenStats)
    """
    if batch_mode == "individual":
        func = apply_llm_batch_individual
    elif batch_mode == "shared_prompt":
        func = apply_llm_batch_with_shared_prompt
    elif batch_mode == "combined":
        func = apply_llm_batch_combined
    else:
        hdbg.dfatal("Invalid batch mode: %s", batch_mode)
    batch_responses, batch_token_stats = func(
        prompt=prompt,
        input_list=batch_items,
        model=model,
        testing_functor=testing_functor,
        progress_bar_object=progress_bar_object,
    )
    return batch_responses, batch_token_stats


def _process_batches(
    values: List[str],
    batch_size: int,
    prompt: str,
    batch_mode: str,
    model: str,
    testing_functor: Optional[Callable[[str], str]],
    progress_bar_object: Optional[tqdm],
    num_batches: int,
) -> Tuple[List[str], int, TokenStats]:
    """
    Process a sequence of values in batches and return LLM results.

    Processes values in chunks, skipping empty values and tracking progress.
    Maintains result ordering and counts skipped items.

    :param values: list of values to process
    :param batch_size: number of items to process in each batch
    :param prompt: system prompt to guide the LLM's behavior
    :param batch_mode: batch mode to use
        - `individual`: separate LLM call per item
        - `shared_prompt`: conversation context across items
        - `combined`: single call with all items
    :param model: model name to use
    :param testing_functor: optional functor to use for testing
    :param progress_bar_object: optional progress bar object to update
    :param num_batches: total number of batches to process
    :return: tuple of (list of results, number of skipped items, aggregated TokenStats)
    """
    results = [""] * len(values)
    num_skipped = 0
    token_stats = []
    for batch_num in range(num_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(values))
        batch_slice = values[start_idx:end_idx]
        batch_items = []
        batch_indices = []
        for local_idx, value in enumerate(batch_slice):
            global_idx = start_idx + local_idx
            if value != "":
                batch_items.append(value)
                batch_indices.append(global_idx)
            else:
                results[global_idx] = ""
                num_skipped += 1
                if progress_bar_object is not None:
                    total_cost_float = TokenStats.aggregate(
                        token_stats
                    ).to_float()
                    progress_bar_object.update(1)
                    progress_bar_object.set_postfix_str(
                        f"Cost: ${total_cost_float:.4f}"
                    )
        if batch_items:
            _LOG.debug(
                "Processing batch %d/%d (%d items, %d skipped)",
                batch_num + 1,
                num_batches,
                len(batch_items),
                len(batch_slice) - len(batch_items),
            )
            batch_responses, batch_token_stats = _call_batch_processor(
                batch_mode=batch_mode,
                prompt=prompt,
                batch_items=batch_items,
                model=model,
                testing_functor=testing_functor,
                progress_bar_object=progress_bar_object,
            )
            token_stats.append(batch_token_stats)
            if progress_bar_object is not None:
                total_cost_float = TokenStats.aggregate(token_stats).to_float()
                progress_bar_object.set_postfix_str(
                    f"Cost: ${total_cost_float:.4f}"
                )
            for idx, response in zip(batch_indices, batch_responses):
                results[idx] = response
        else:
            _LOG.debug(
                "Skipping batch %d/%d (all %d items are empty)",
                batch_num + 1,
                num_batches,
                len(batch_slice),
            )
    aggregated_cost = TokenStats.aggregate(token_stats)
    return results, num_skipped, aggregated_cost


# #############################################################################
# Dataframe processing
# #############################################################################


def _process_dataframe_batches(
    df: pd.DataFrame,
    batch_size: int,
    extractor: Callable[[Union[str, pd.Series]], str],
    target_col: str,
    prompt: str,
    batch_mode: str,
    model: str,
    testing_functor: Optional[Callable[[str], str]],
    progress_bar_object: Optional[tqdm],
    num_batches: int,
) -> Tuple[int, TokenStats]:
    """
    Process dataframe batches and update target column with LLM results.

    Processes dataframe rows in batches by extracting text using the provided
    extractor function and updating the target column with LLM results.

    :param df: dataframe to process (modified in place)
    :param batch_size: number of items to process in each batch
    :param extractor: callable that extracts text from a row or series
    :param target_col: name of column to store results
    :param prompt: system prompt to guide the LLM's behavior
    :param batch_mode: batch mode to use
        - `individual`: separate LLM call per item
        - `shared_prompt`: conversation context across items
        - `combined`: single call with all items
    :param model: model name to use
    :param testing_functor: optional functor to use for testing
    :param progress_bar_object: optional progress bar object to update
    :param num_batches: total number of batches to process
    :return: tuple of (number of skipped items, aggregated TokenStats)
    """
    num_skipped = 0
    token_stats = []
    for batch_num in range(num_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(df))
        rows = df.iloc[start_idx:end_idx]
        batch_items = []
        batch_indices = []
        for idx, row in rows.iterrows():
            extracted_text = extractor(row)
            if extracted_text != "":
                batch_items.append(extracted_text)
                batch_indices.append(idx)
            else:
                df.at[idx, target_col] = ""
                num_skipped += 1
                if progress_bar_object is not None:
                    total_cost_float = TokenStats.aggregate(
                        token_stats
                    ).to_float()
                    progress_bar_object.update(1)
                    progress_bar_object.set_postfix_str(
                        f"Cost: ${total_cost_float:.4f}"
                    )
        if batch_items:
            _LOG.debug(
                "Processing batch %d/%d (%d items, %d skipped)",
                batch_num + 1,
                num_batches,
                len(batch_items),
                len(rows) - len(batch_items),
            )
            batch_responses, batch_token_stats = _call_batch_processor(
                batch_mode=batch_mode,
                prompt=prompt,
                batch_items=batch_items,
                model=model,
                testing_functor=testing_functor,
                progress_bar_object=progress_bar_object,
            )
            token_stats.append(batch_token_stats)
            if progress_bar_object is not None:
                total_cost_float = TokenStats.aggregate(token_stats).to_float()
                progress_bar_object.set_postfix_str(
                    f"Cost: ${total_cost_float:.4f}"
                )
            for idx, response in zip(batch_indices, batch_responses):
                df.at[idx, target_col] = response
        else:
            _LOG.debug(
                "Skipping batch %d/%d (all %d items have missing data)",
                batch_num + 1,
                num_batches,
                len(rows),
            )
    aggregated_cost = TokenStats.aggregate(token_stats)
    return num_skipped, aggregated_cost


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
    dump_every_batch: str = "",
    tag: str = "Processing",
    testing_functor: Optional[Callable[[str], str]] = None,
    use_sys_stderr: bool = False,
) -> Tuple[pd.DataFrame, dict]:
    """
    Apply an LLM to process a dataframe column using the same system prompt.

    This function processes text from dataframe rows using an extractor function,
    applies the LLM to each item in batches, and stores the results in a target
    column. It can optionally save progress to a file after each batch.

    :param prompt: system prompt to guide the LLM's behavior
    :param df: dataframe to process
    :param extractor: callable that extracts text from a row or string
    :param target_col: name of column to store results
    :param batch_mode: batch mode to use (individual, shared_prompt, combined)
    :param model: model name to use (e.g., "gpt-4", "claude-3-opus")
    :param batch_size: number of items to process in each batch
    :param dump_every_batch: optional file path to dump the dataframe after each batch
    :param tag: description tag for progress bar
    :param testing_functor: optional functor to use for testing
    :return: tuple of (dataframe with results, statistics dict)
    """
    import pandas as pd

    start_time = time.time()
    hdbg.dassert_isinstance(prompt, str)
    hdbg.dassert_ne(prompt, "", "Prompt cannot be empty")
    hdbg.dassert_isinstance(df, pd.DataFrame)
    hdbg.dassert_lt(0, len(df), "Dataframe cannot be empty")
    hdbg.dassert_isinstance(target_col, str)
    hdbg.dassert_ne(target_col, "", "Target column cannot be empty")
    hdbg.dassert_isinstance(model, str)
    hdbg.dassert_ne(model, "", "Model cannot be empty")
    hdbg.dassert_isinstance(batch_size, int)
    hdbg.dassert_lt(
        0,
        batch_size,
        "Batch size must be positive",
    )
    if dump_every_batch:
        hdbg.dassert_isinstance(dump_every_batch, str)
        hdbg.dassert_ne(dump_every_batch, "", "Dump file path cannot be empty")
    # Create target column if it doesn't exist.
    if target_col not in df.columns:
        df[target_col] = None
    # Process items in batches with progress bar for entire workload.
    num_items = len(df)
    num_batches = (num_items + batch_size - 1) // batch_size
    _LOG.info(
        "Processing %d items in %d batches of %d items each",
        num_items,
        num_batches,
        batch_size,
    )
    _LOG.info(hprint.to_str("model batch_mode"))
    progress_bar_ctor = get_tqdm_progress_bar()
    progress_bar_object = progress_bar_ctor(  # type: ignore
        total=num_items,
        desc=tag,
        dynamic_ncols=True,
        # Workaround for unit tests.
        file=sys.__stderr__ if use_sys_stderr else None,
    )
    # TODO(gp): Precompute the batch indices that needs to be processed.
    num_skipped, token_stats = _process_dataframe_batches(
        df=df,
        batch_size=batch_size,
        extractor=extractor,
        target_col=target_col,
        prompt=prompt,
        batch_mode=batch_mode,
        model=model,
        testing_functor=testing_functor,
        progress_bar_object=progress_bar_object,
        num_batches=num_batches,
    )
    # Calculate elapsed time.
    elapsed_time = time.time() - start_time
    stats = {
        "num_items": num_items,
        "num_skipped": num_skipped,
        "num_batches": num_batches,
        "total_input_tokens": token_stats.input_tokens,
        "total_output_tokens": token_stats.output_tokens,
        "total_cost_in_dollars": token_stats.to_float(),
        "elapsed_time_in_seconds": elapsed_time,
    }
    _LOG.info("Processing completed:\n%s", pprint.pformat(stats))
    return df, stats


# #############################################################################
# Testing utilities
# #############################################################################

# Example in a test:
# ```
# def test_my_function(self):
#     with mock_apply_llm():
#         # Code that calls apply_llm() will now return mocked values
#         response, token_stats = apply_llm(
#             "some input",
#             system_prompt="some prompt",
#         )
#         # `response` will be the MD5 hash of "some inputsome prompt"
#         # `token_stats` will be TokenStats() with zeros.
# ```


@contextlib.contextmanager
def mock_apply_llm():
    """
    Context manager to mock `apply_llm()` for testing without calling LLM.

    This mocks `apply_llm()` in tests by returning the MD5 digest of the
    concatenated input_str and system_prompt. Avoids expensive API calls and
    external dependencies during testing.
    """

    def _mock_apply_llm(
        input_str: str,
        *,
        system_prompt: str = "",
        model: str = "",
        backend: str = "library",
        expected_num_chars: int = 0,
    ) -> Tuple[str, TokenStats]:
        concatenated = input_str + (system_prompt or "")
        digest = hashlib.md5(concatenated.encode()).hexdigest()
        return digest, TokenStats()

    with mock.patch("helpers.hllm_cli.apply_llm", side_effect=_mock_apply_llm):
        yield


# #############################################################################
# CLI argument handling
# #############################################################################


def add_llm_prompt_arg(
    parser: argparse.ArgumentParser,
    *,
    default_prompt: str = "",
    is_required: bool = True,
) -> argparse.ArgumentParser:
    """
    Add common command line arguments for LLM transform scripts.

    Adds debug, prompt, and fast_model options to the argument parser for
    LLM transformation scripts.

    :param parser: argparse parser to add arguments to
    :param default_prompt: default prompt to use
    :param is_required: whether the prompt is required
    :return: parser with the option added
    """
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print before/after the transform",
    )
    if default_prompt != "":
        is_required = False
    parser.add_argument(
        "-p",
        "--prompt",
        required=is_required,
        type=str,
        help="Prompt to apply",
        default=default_prompt,
    )
    parser.add_argument(
        "-f",
        "--fast_model",
        action="store_true",
        help="Use a fast LLM model vs a high-quality one",
    )
    return parser


# TODO(gp): Extract / reuse the options for -i, --input_txt, ...
def add_llm_args(
    parser: argparse.ArgumentParser,
    *,
    input_required: bool = True,
    output_required: bool = False,
    system_prompt_required: bool = False,
    model_default: str = "gpt-4o-mini",
    include_model: bool = True,
    include_backend: bool = True,
) -> argparse.ArgumentParser:
    """
    Add comprehensive LLM-related command line arguments for LLM CLI scripts.

    Consolidates commonly used arguments for scripts that process text with
    LLM transformations (e.g., llm_cli.py, ai_review.py). Supports flexible
    input modes (file or text), system prompts, and backend selection.

    :param parser: argparse parser to add arguments to
    :param input_required: whether input is required
    :param output_required: whether output is required
    :param system_prompt_required: whether system prompt is required
    :param model_default: default LLM model name
    :param include_model: whether to include `--model` argument
    :param include_backend: whether to include `--backend` argument
    :return: parser with LLM arguments added
    """
    # Input/Output options with mutually exclusive input sources.
    input_group = parser.add_mutually_exclusive_group(required=input_required)
    input_group.add_argument(
        "-i",
        "--input",
        type=str,
        dest="input",
        help="Path to the input file containing text to process, or '-' for stdin",
    )
    input_group.add_argument(
        "--input_text",
        type=str,
        help="Text input to process directly from command line",
    )
    # Output option.
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        dest="output",
        required=output_required,
        default="",
        help="Path to the output file where result will be saved (use '-' to "
        "print to screen). If not specified, writes in-place to the input file",
    )
    # System prompt options (mutually exclusive).
    system_prompt_group = parser.add_mutually_exclusive_group(
        required=system_prompt_required
    )
    system_prompt_group.add_argument(
        "-p",
        "--system_prompt",
        type=str,
        default="",
        dest="system_prompt",
        help="Optional system prompt to guide the LLM's behavior",
    )
    system_prompt_group.add_argument(
        "--pf",
        "--system_prompt_file",
        type=str,
        default="",
        dest="system_prompt_file",
        help="Optional path to file containing system prompt to guide the LLM's behavior",
    )
    hmarsele.add_rule_cli_arg(system_prompt_group)
    # Model selection.
    if include_model:
        parser.add_argument(
            "--model",
            type=str,
            default=model_default,
            help=f"Optional model name to use (e.g., 'gpt-4', 'claude-3-opus'). "
            f"Default: {model_default}",
        )
    # Backend selection.
    if include_backend:
        parser.add_argument(
            "--backend",
            type=str,
            default="library",
            choices=["executable", "library", "mock"],
            help="LLM backend to use: 'executable' (CLI), 'library' (Python), or 'mock' (testing)",
        )
    # Progress bar options.
    parser.add_argument(
        "-b",
        "--progress_bar",
        action="store_true",
        default=False,
        help="Enable progress bar with automatic estimation (input length * 1.0)",
    )
    parser.add_argument(
        "--expected_num_chars",
        type=int,
        default=0,
        help="Expected number of characters in output (enables progress bar with explicit size)",
    )
    return parser
