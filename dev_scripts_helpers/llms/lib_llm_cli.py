#!/usr/bin/env -S uv run

# /// script
# dependencies = [
#   "llm",
#   "flowmark",
#   "mdformat",
#   "pyyaml",
#   "tokencost",
#   "tqdm",
# ]
# ///

r"""
Library functions for LLM CLI script.

Contains the core logic for text transformation using LLMs, separate from
the CLI interface.

Import as:

import dev_scripts_helpers.llms.lib_llm_cli as dshlibllmcli
"""

import logging
import os
import pprint
from importlib.metadata import distributions, version
from typing import Tuple

import llm

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hllm_cli as hllmcli
import helpers.hmarkdown_select as hmarsele
import helpers.hselect_input_output as hseinout
import helpers.hsystem as hsystem
import helpers.hmarkdown_formatting as hmarform

_LOG = logging.getLogger(__name__)

_LINT_BACKEND = "flowmark"
_LINT_MODE = "library"


def _get_input_output_files(
    input_arg: str,
    input_text_arg: str,
    output_arg: str,
    modify_in_place: bool,
) -> Tuple[str, str, str]:
    """
    Determine input and output file paths.

    :param input_arg: Input file path or '-' for stdin
    :param input_text_arg: Input text from command line
    :param output_arg: Output file path or '-' for stdout
    :param modify_in_place: Whether to modify input file in place
    :return: Tuple of (input_file, input_text, output_file)
    """
    # Determine input source.
    if input_arg:
        if input_arg == "-":
            # Read from stdin.
            input_file = "-"
            input_text = ""
        else:
            # Read from file.
            input_text = ""
            input_file = input_arg
    else:
        hdbg.dassert_ne(input_text_arg, "", "Input text cannot be empty")
        input_text = input_text_arg
        input_file = ""
    # Determine output destination.
    if not output_arg:
        # TODO(ai_gp): Use a dassert_imply
        hdbg.dassert(
            input_file and input_file != "-",
            "Output must be specified when using --input_text or stdin. "
            "In-place editing only works with --input <file>",
        )
        if modify_in_place:
            output_file = input_file
        else:
            output_file = "-"
        _LOG.info("No output specified, writing in-place to: %s", output_file)
    elif output_arg == "-":
        # Print to screen.
        output_file = "-"
    else:
        # Use the specified output file.
        hdbg.dassert_ne(output_arg, "", "Output file cannot be empty string")
        output_file = output_arg
    return input_file, input_text, output_file


def _get_expected_num_chars(
    progress_bar: bool,
    expected_num_chars_arg: int,
    input_file: str,
    input_text: str,
) -> int:
    """
    Calculate expected number of output characters.

    :param progress_bar: Whether progress bar is enabled
    :param expected_num_chars_arg: Explicitly provided expected char count (0
        if not provided)
    :param input_file: Input file path (or '-' for stdin)
    :param input_text: Input text from command line
    :return: Expected number of output characters, or 0 if not needed
    """
    # Calculate expected_num_chars if progress_bar is enabled.
    if progress_bar and expected_num_chars_arg:
        # Read input to get its length.
        if input_file:
            if input_file == "-":
                # Read from stdin.
                input_lines = hseinout.from_file(input_file)
                input_content = "\n".join(input_lines)
            else:
                input_content = hio.from_file(input_file)
        elif input_text:
            hdbg.dassert_ne(input_text, "", "Input text must be provided")
            input_content = input_text
        else:
            raise ValueError("Invalid input combination")
        input_length = len(input_content)
        expected_num_chars = int(input_length * 1.0)
        _LOG.info(
            "Progress bar enabled: estimated output %d chars (input: %d chars)",
            expected_num_chars,
            input_length,
        )
    elif expected_num_chars_arg:
        hdbg.dassert_lt(
            0, expected_num_chars_arg, "Expected char count must be positive"
        )
        expected_num_chars = expected_num_chars_arg
    else:
        expected_num_chars = 0
    return expected_num_chars


def _limit_input_text(
    text: str,
    max_chars: int,
) -> str:
    """
    Limit input text to max_chars and print a warning if truncated.

    :param text: Input text to limit
    :param max_chars: Maximum number of characters, or None for no limit
    :return: Text limited to max_chars, or original text if no limit
    """
    hdbg.dassert_lte(1, max_chars)
    if len(text) <= max_chars:
        return text
    _LOG.warning(
        "Input text truncated from %d to %d chars",
        len(text),
        max_chars,
    )
    return text[:max_chars]


def _get_system_prompt(
    system_prompt_file: str,
    rule: str,
    system_prompt: str,
) -> str:
    """
    Get system prompt from file, rule, or argument.

    :param system_prompt_file: Path to file containing system prompt (empty
        string if not provided)
    :param rule: Rule specification to extract system prompt from (empty string
        if not provided)
    :param system_prompt: Default system prompt text
    :return: The resolved system prompt
    """
    # Exactly one of the three options should be provided.
    num_options = sum(
        [
            bool(system_prompt_file),
            bool(rule),
            bool(system_prompt),
        ]
    )
    hdbg.dassert_lte(
        num_options, 1, "Only one system prompt option should be provided"
    )
    if system_prompt_file:
        # Read from file.
        hdbg.dassert_ne(
            system_prompt_file, "", "System prompt file cannot be empty"
        )
        result = hio.from_file(system_prompt_file)
        _LOG.debug(
            "Read system prompt from file: %s (%d chars)",
            system_prompt_file,
            len(result),
        )
    elif rule:
        # Use a rule.
        result = hmarsele.extract_rule_from_file(rule)
        _LOG.debug(
            "Extracted rule from spec '%s' (%d chars)",
            rule,
            len(result),
        )
    else:
        # Use the string.
        result = system_prompt
    return result


def _process_selected_text(
    select: str,
    model: str,
    backend: str,
    input_file: str,
    output_file: str,
    system_prompt: str,
    modify_in_place: bool,
    max_chars: int,
    lint: bool,
    expected_num_chars: int,
    dry_run: bool,
) -> hllmcli.TokenStats:
    """
    Process file in select mode: extract chunk, transform, reassemble.

    :param select: Select specification (e.g., 'start_marker:end_marker')
    :param model: Name of the LLM model to use
    :param backend: Backend to use ("executable", "library", or "mock")
    :param input_file: Path to input file
    :param output_file: Path to output file
    :param system_prompt: System prompt for the LLM
    :param modify_in_place: Whether to modify the input file in place
    :param max_chars: Maximum number of input characters to process (0 for no
        limit)
    :param lint: Whether to lint the output after processing
    :param expected_num_chars: Expected number of output characters for
        progress bar (0 if not applicable)
    :param dry_run: If True, skip calling the LLM and show what would be done
    :return: The cost of the LLM operation
    """
    # Parse select specification and read input file.
    select_start, select_end = hmarsele.parse_select_arg(select)
    _LOG.info(
        "Select mode: extracting chunk from '%s' to '%s'",
        select_start,
        select_end,
    )
    hdbg.dassert_ne(input_file, "", "Input file is required for select mode")
    input_lines = hseinout.from_file(input_file)
    # Extract chunk from input based on markers.
    _, ext = os.path.splitext(input_file) if input_file != "-" else ("", "")
    is_slide_format = ext == ".txt"
    start_idx, end_idx = hmarsele.get_chunk_bounds(
        input_lines, select_start, select_end, is_slide_format=is_slide_format
    )
    chunk_lines = input_lines[start_idx:end_idx]
    chunk_text = "\n".join(chunk_lines)
    # Apply max_chars limit if specified.
    if max_chars:
        chunk_text = _limit_input_text(chunk_text, max_chars)
    # Transform chunk with LLM or log dry-run parameters.
    if dry_run:
        _LOG.warning("DRY RUN: Would call LLM with parameters:")
        _LOG.info(
            "  System prompt (%d chars):\n%s", len(system_prompt), system_prompt
        )
        _LOG.info("  Model: %s", model)
        _LOG.info("  Backend: %s", backend)
        _LOG.info("  Expected output chars: %s", expected_num_chars)
        _LOG.info(
            "  Input text to be processed (%d chars):\n%s",
            len(chunk_text),
            chunk_text,
        )
        response = ""
        token_stats = hllmcli.TokenStats()
    else:
        response, token_stats = hllmcli.apply_llm(
            chunk_text,
            system_prompt=system_prompt if system_prompt != "" else None,
            model=model,
            backend=backend,
            expected_num_chars=expected_num_chars if expected_num_chars != 0 else None,
        )
        if lint:
            response = hmarform.format_md(response, _LINT_BACKEND, _LINT_MODE)
    # Write output: either modify file in-place or write to output file.
    if modify_in_place:
        hdbg.dassert_ne(input_file, "-", "Cannot modify stdin in-place")
        # We are processing a file in place and we have selected to modify the
        # file in place.
        before_lines = input_lines[:start_idx]
        after_lines = input_lines[end_idx:]
        before_text = "\n".join(before_lines) if before_lines else ""
        after_text = "\n".join(after_lines) if after_lines else ""
        if before_text and after_text:
            new_content = before_text + "\n" + response + "\n" + after_text
        elif before_text:
            new_content = before_text + "\n" + response
        elif after_text:
            new_content = response + "\n" + after_text
        else:
            new_content = response
        if not dry_run:
            hio.to_file(input_file, new_content)
        _LOG.info(
            "Updated file in-place: %s (lines %d-%d)",
            input_file,
            start_idx + 1,
            end_idx,
        )
    else:
        if not dry_run:
            hdbg.dassert_ne(output_file, "", "Output file is required")
            hseinout.to_file(response, output_file)
    return token_stats


def _process_full_text(
    model: str,
    backend: str,
    input_text: str,
    input_file: str,
    output_file: str,
    system_prompt: str,
    max_chars: int,
    lint: bool,
    expected_num_chars: int,
    dry_run: bool,
) -> hllmcli.TokenStats:
    """
    Process file with input_text, stdin, or print_only mode.

    :param model: Name of the LLM model to use
    :param backend: Backend to use ("executable", "library", or "mock")
    :param input_text: Input text (if provided directly)
    :param input_file: Path to input file
    :param output_file: Path to output file
    :param system_prompt: System prompt for the LLM
    :param max_chars: Maximum number of input characters to process (0 for no
        limit)
    :param lint: Whether to lint the output after processing
    :param expected_num_chars: Expected number of output characters for
        progress bar (0 if not applicable)
    :param dry_run: If True, skip calling the LLM and show what would be done
    :return: The cost of the LLM operation
    """
    # Read input text from string, file, or stdin.
    if input_text:
        # Use text from input string.
        input_str = input_text
    else:
        # Read text from file or stdin.
        hdbg.dassert_ne(input_file, "", "Input file is required when input_text is empty")
        input_lines = hseinout.from_file(input_file)
        input_str = "\n".join(input_lines)
    # Apply max_chars limit if specified.
    if max_chars:
        input_str = _limit_input_text(input_str, max_chars)
    # Transform with LLM or log dry-run parameters.
    if dry_run:
        # TODO(gp): Consider moving this inside the LLM call to generalize it.
        _LOG.warning("DRY RUN: Would call LLM with parameters:")
        _LOG.info("  Input text length: %d chars", len(input_str))
        _LOG.info(
            "  System prompt length: %d chars",
            len(system_prompt) if system_prompt else 0,
        )
        _LOG.info("  Model: %s", model)
        _LOG.info("  Backend: %s", backend)
        _LOG.info("  Expected output chars: %s", expected_num_chars)
        _LOG.info("Input text to be processed:")
        _LOG.info("%s", pprint.pformat(input_str))
        response = ""
        token_stats = hllmcli.TokenStats()
    else:
        response, token_stats = hllmcli.apply_llm(
            input_str,
            system_prompt=system_prompt if system_prompt != "" else None,
            model=model,
            backend=backend,
            expected_num_chars=expected_num_chars if expected_num_chars != -1 else None,
        )
        if lint:
            response = hmarform.format_md(response, _LINT_BACKEND, _LINT_MODE)
    # Write output or log dry-run destination.
    if dry_run:
        _LOG.warning("DRY RUN: Would save to %s", output_file)
    else:
        hseinout.to_file(response, output_file)
    return token_stats


def _is_plugin_installed(plugin_module_name: str) -> bool:
    """
    Check if an llm plugin is already installed via the library interface.

    :param plugin_module_name: Module name of the plugin (e.g., 'llm_openrouter')
    :return: True if plugin is installed, False otherwise
    """
    try:
        llm.load_plugins()
        # Check if the plugin is in the list of installed plugins.
        for module, _ in llm.pm.list_plugin_distinfo():
            if module.__name__ == plugin_module_name:
                return True
        return False
    except Exception as e:
        _LOG.debug("Error checking plugins: %s", e)
        return False


def _log_plugin_versions() -> None:
    """
    Log the versions of all installed llm plugins and packages.
    """
    for dist in sorted(
        distributions(), key=lambda d: d.metadata["Name"].lower()
    ):
        name = dist.metadata["Name"]
        if name.startswith("llm"):
            _LOG.info("Plugin '%s' version: %s", name, dist.version)


def install_models() -> None:
    """
    Install the llm-openrouter and llm-anthropic plugins if not already installed.

    :return: Return code from the installation command
    """
    plugins_to_install = [
        ("llm_openrouter", "llm install llm-openrouter"),
        ("llm_anthropic", "llm install llm-anthropic"),
    ]
    # Install each plugin if not already present.
    for plugin_module_name, cmd in plugins_to_install:
        if _is_plugin_installed(plugin_module_name):
            _LOG.debug("Plugin '%s' is already installed", plugin_module_name)
        else:
            _LOG.warning("Installing %s plugin...", plugin_module_name)
            hsystem.system(cmd, print_command=True, suppress_output=False)
    if False:
        # Print available models.
        # TODO(gp): Use the library.
        cmd = "llm models"
        hsystem.system(cmd, print_command=True, suppress_output=False)


def execute_llm_command(llm_cmd: str, abort_on_error: bool = True) -> int:
    """
    Execute an arbitrary llm command.

    :param llm_cmd: The llm command to execute (e.g., "llm chat --model gpt-4")
    :param abort_on_error: Whether to abort on error
    :return: Return code from the command
    """
    _LOG.info("Executing llm command: %s", llm_cmd)
    rc = hsystem.system(
        llm_cmd, print_command=True, abort_on_error=abort_on_error
    )
    return rc


def _llm_cli(
    input_arg: str,
    input_text_arg: str,
    output_arg: str,
    modify_in_place: bool,
    progress_bar: bool,
    expected_num_chars_arg: int,
    log_level: str,
    dry_run: bool,
    model: str,
    backend: str,
    system_prompt_file: str,
    rule: str,
    system_prompt_arg: str,
    select: str,
    lint: bool,
    max_chars: int,
    stat_file: str,
    llm_cmd: str,
) -> None:
    """
    Execute the LLM command processing logic.

    :param input_arg: Input file path or '-' for stdin
    :param input_text_arg: Input text from command line
    :param output_arg: Output file path or '-' for stdout
    :param modify_in_place: Whether to modify input file in place
    :param progress_bar: Whether to show progress bar
    :param expected_num_chars_arg: Explicitly provided expected char count (0
        if not provided)
    :param log_level: Logging verbosity level
    :param dry_run: If True, skip calling the LLM
    :param model: Name of the LLM model to use
    :param backend: Backend to use ("executable", "library", or "mock")
    :param system_prompt_file: Path to file containing system prompt (empty
        string if not provided)
    :param rule: Rule specification for system prompt (empty string if not
        provided)
    :param system_prompt_arg: System prompt text
    :param select: Select specification (e.g., 'start_marker:end_marker')
    :param lint: Whether to lint the output
    :param max_chars: Maximum number of input characters to process (0 for no
        limit)
    :param stat_file: Path to save stats as JSON file (empty string if not
        provided)
    :param llm_cmd: Arbitrary llm command to execute (empty string if not
        provided)
    """
    verbosity = log_level
    # Suppress logging when using stdin/stdout unless DEBUG is requested.
    if input_arg == "-" and output_arg == "-":
        if log_level == "INFO":
            verbosity = "CRITICAL"
    hdbg.init_logger(verbosity=verbosity, use_exec_path=True)
    _LOG.info("llm version: %s", version("llm"))
    _LOG.info("tokencost version: %s", version("tokencost"))
    install_models()
    _log_plugin_versions()
    # Execute arbitrary llm command if provided.
    if llm_cmd != "":
        execute_llm_command(llm_cmd)
        return
    # Determine input source and output destination.
    input_file, input_text, output_file = _get_input_output_files(
        input_arg,
        input_text_arg,
        output_arg,
        modify_in_place,
    )
    # Calculate expected number of output characters for progress tracking.
    expected_num_chars = _get_expected_num_chars(
        progress_bar,
        expected_num_chars_arg,
        input_file,
        input_text,
    )
    # Log processing mode.
    if dry_run:
        _LOG.warning("Dry run mode: LLM will not be called")
    else:
        _LOG.info("Processing with LLM '%s'...", model)
    # Resolve system prompt from file, rule, or argument.
    system_prompt = _get_system_prompt(
        system_prompt_file,
        rule,
        system_prompt_arg,
    )
    # Process selected chunk or full text.
    if select:
        # Transform a selected chunk of text.
        hdbg.dassert(
            not input_text, "Select mode requires file input, not --input_text"
        )
        token_stats = _process_selected_text(
            select,
            model,
            backend,
            input_file,
            output_file,
            system_prompt,
            modify_in_place,
            max_chars,
            lint,
            expected_num_chars,
            dry_run,
        )
    else:
        # Transform full text.
        token_stats = _process_full_text(
            model,
            backend,
            input_text,
            input_file,
            output_file,
            system_prompt,
            max_chars,
            lint,
            expected_num_chars,
            dry_run,
        )
    # Report total cost of LLM operation.
    _LOG.info("Total cost: %s", token_stats.to_str())
    # Save stats to file if requested.
    if stat_file != "":
        token_stats.to_file(stat_file)
        _LOG.info("Stats saved to: %s", stat_file)
