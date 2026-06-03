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

# Note that when using uv to install `llm` on the fly, it is not configured in
# terms of plugins and keys.

r"""
CLI script to apply LLM transformations to text files or text input.

For detailed documentation, usage examples, and feature descriptions, see:
`dev_scripts_helpers/llms/README.md`

Import as:

import dev_scripts_helpers.llms.llm_cli as dshllcli
"""

import argparse
import json
import logging
import os
import pprint
from importlib.metadata import distributions, version
from typing import Optional, Tuple

import llm

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hllm_cli as hllmcli
import helpers.hmarkdown_select as hmarsele
import helpers.hselect_input_output as hseinout
import helpers.hparser as hparser
import helpers.hsystem as hsystem
import helpers.hmarkdown_formatting as hmarform

_LOG = logging.getLogger(__name__)

# The architecture of the script has several stages:
# - Read input:
#     - --input <file>: it can be a file, stdin
#     - --input_text <text>
# - (Optional) Extract a chunk of input:
#     - --select <token>: various selection criteria
#     - --modify_in_place
# - Select a prompt:
#     - -p: from command line
#     - -pf <file>: from a file
#     - --rule <topic>: from a `.claude/skills/<topic>.rules.md`
#     - --skill <skill>: from a `.claude/skill/<skill>/SKILL.md`
# - (Optional) A linting step (--lint)
# - Write output
#     - --output: it can be a file, stdout


# Models
# - anthropic/claude-haiku-4-5-20251001
# - anthropic/claude-opus-4.8
# - anthropic/claude-sonnet-4.6
# - gpt-4o-mini
# - openrouter/anthropic/claude-haiku-4.5
# - openrouter/deepseek/deepseek-v4-flash
# - openrouter/meta-llama/llama-3.1-8b-instruct
# - openrouter/openai/gpt-oss-120b
# - openrouter/openai/gpt-oss-20b

# _LINT_BACKEND = "mdformat"
_LINT_BACKEND = "flowmark"
_LINT_MODE = "library"

# #############################################################################


# TODO(ai_gp): Do not use * and remove the call by name.
# TODO(ai_gp): Make the typehints stricter, e.g., no Optional if it's not possible.
def _get_input_output_files(
    *,
    input_arg: Optional[str],
    input_text_arg: Optional[str],
    output_arg: Optional[str],
    modify_in_place: bool,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
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
        hdbg.dassert_ne(input_arg, "", "Input file cannot be empty")
        if input_arg == "-":
            # Read from stdin.
            input_file = "-"
            input_text = None
        else:
            # Read from file.
            input_text = None
            input_file = input_arg
    else:
        hdbg.dassert_ne(input_text_arg, "", "Input text cannot be empty")
        input_text = input_text_arg
        input_file = None
    # Determine output destination.
    if output_arg is None:
        hdbg.dassert(
            input_file is not None and input_file != "-",
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
    *,
    progress_bar: bool,
    expected_num_chars_arg: Optional[int],
    input_file: Optional[str],
    input_text: Optional[str],
) -> Optional[int]:
    """
    Calculate expected number of output characters.

    :param progress_bar: Whether progress bar is enabled
    :param expected_num_chars_arg: Explicitly provided expected char count
    :param input_file: Input file path (or '-' for stdin)
    :param input_text: Input text from command line
    :return: Expected number of output characters, or None if not needed
    """
    # Calculate expected_num_chars if progress_bar is enabled.
    if progress_bar and expected_num_chars_arg is None:
        # Read input to get its length.
        if input_file:
            if input_file == "-":
                # Read from stdin.
                input_lines = hseinout.from_file(input_file)
                input_content = "\n".join(input_lines)
            else:
                input_content = hio.from_file(input_file)
        elif input_text is not None:
            hdbg.dassert_is_not(input_text, None, "Input text must be provided")
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
    elif expected_num_chars_arg is not None:
        hdbg.dassert_lt(
            0, expected_num_chars_arg, "Expected char count must be positive"
        )
        expected_num_chars = expected_num_chars_arg
    else:
        expected_num_chars = None
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
    system_prompt_file: Optional[str],
    rule: Optional[str],
    system_prompt: str,
) -> str:
    """
    Get system prompt from file, rule, or argument.

    :param system_prompt_file: Path to file containing system prompt
    :param rule: Rule specification to extract system prompt from
    :param system_prompt: Default system prompt text
    :return: The resolved system prompt
    """
    # Exactly one of the three options should be provided.
    num_options = sum(
        [
            system_prompt_file is not None,
            rule is not None,
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
    input_file: Optional[str],
    output_file: Optional[str],
    system_prompt: str,
    modify_in_place: bool,
    max_chars: int,
    lint: bool,
    expected_num_chars: Optional[int],
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
    :param max_chars: Maximum number of input characters to process, or None for no limit
    :param lint: Whether to lint the output after processing
    :param expected_num_chars: Expected number of output characters for progress bar
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
        token_stats = {}
    else:
        response, token_stats = hllmcli.apply_llm(
            chunk_text,
            system_prompt=system_prompt,
            model=model,
            backend=backend,
            expected_num_chars=expected_num_chars,
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
            hseinout.to_file(response, output_file)
    return token_stats


def _process_full_text(
    model: str,
    backend: str,
    input_text: Optional[str],
    input_file: Optional[str],
    output_file: Optional[str],
    system_prompt: str,
    max_chars: int,
    lint: bool,
    expected_num_chars: Optional[int],
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
    :param max_chars: Maximum number of input characters to process, or None for no limit
    :param lint: Whether to lint the output after processing
    :param expected_num_chars: Expected number of output characters for progress bar
    :param dry_run: If True, skip calling the LLM and show what would be done
    :return: The cost of the LLM operation
    """
    # Read input text from string, file, or stdin.
    if input_text is not None:
        # Use text from input string.
        input_str = input_text
    else:
        # Read text from file or stdin.
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
        cost = 0.0
    else:
        response, cost = hllmcli.apply_llm(
            input_str,
            system_prompt=system_prompt,
            model=model,
            backend=backend,
            expected_num_chars=expected_num_chars,
        )
        if lint:
            response = hmarform.format_md(response, _LINT_BACKEND, _LINT_MODE)
    # Write output or log dry-run destination.
    if dry_run:
        _LOG.warning("DRY RUN: Would save to %s", output_file)
    else:
        hseinout.to_file(response, output_file)
    return cost


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


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--llm_cmd",
        type=str,
        default=None,
        help="Execute an arbitrary llm command (e.g., 'llm chat --model gpt-4')",
    )
    hllmcli.add_llm_args(parser, input_required=True)
    hmarsele.add_select_arg(parser, required=False)
    parser.add_argument(
        "-m",
        "--modify_in_place",
        action="store_true",
        default=False,
        help="Modify input file in place. If not specified, an output file must be provided.",
    )
    parser.add_argument(
        "--lint",
        action="store_true",
        default=False,
        help="Lint the output after processing",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        default=False,
        help="Skip calling the LLM and show what would be done",
    )
    parser.add_argument(
        "--max_chars",
        type=int,
        default=None,
        help="Limit input to max_chars characters",
    )
    parser.add_argument(
        "--stat_file",
        type=str,
        default=None,
        help="Path to save stats as JSON file",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    verbosity = args.log_level
    # Suppress logging when using stdin/stdout unless DEBUG is requested.
    if args.input == "-" and args.output == "-":
        if args.log_level == "INFO":
            verbosity = "CRITICAL"
    hdbg.init_logger(verbosity=verbosity, use_exec_path=True)
    _LOG.info("llm version: %s", version("llm"))
    _LOG.info("tokencost version: %s", version("tokencost"))
    install_models()
    _log_plugin_versions()
    # Execute arbitrary llm command if provided.
    if args.llm_cmd:
        execute_llm_command(args.llm_cmd)
        return
    # Determine input source and output destination.
    input_file, input_text, output_file = _get_input_output_files(
        input_arg=args.input,
        input_text_arg=args.input_text,
        output_arg=args.output,
        modify_in_place=args.modify_in_place,
    )
    # Calculate expected number of output characters for progress tracking.
    expected_num_chars = _get_expected_num_chars(
        progress_bar=args.progress_bar,
        expected_num_chars_arg=args.expected_num_chars,
        input_file=input_file,
        input_text=input_text,
    )
    # Log processing mode.
    if args.dry_run:
        _LOG.warning("Dry run mode: LLM will not be called")
    else:
        _LOG.info("Processing with LLM '%s'...", args.model)
    # Resolve system prompt from file, rule, or argument.
    system_prompt = _get_system_prompt(
        system_prompt_file=args.system_prompt_file,
        rule=args.rule,
        system_prompt=args.system_prompt,
    )
    # Process selected chunk or full text.
    if args.select:
        # Transform a selected chunk of text.
        hdbg.dassert_is(
            input_text, None, "Select mode requires file input, not --input_text"
        )
        cost = _process_selected_text(
            args.select,
            args.model,
            args.backend,
            input_file,
            output_file,
            system_prompt,
            args.modify_in_place,
            args.max_chars,
            args.lint,
            expected_num_chars,
            args.dry_run,
        )
    else:
        # Transform full text.
        cost = _process_full_text(
            args.model,
            args.backend,
            input_text,
            input_file,
            output_file,
            system_prompt,
            args.max_chars,
            args.lint,
            expected_num_chars,
            args.dry_run,
        )
    # Report total cost of LLM operation.
    _LOG.info("Total cost: %s", hllmcli.token_stats_to_str(cost))
    # Save stats to file if requested.
    if args.stat_file:
        hio.to_file(args.stat_file, json.dumps(cost, indent=2))
        _LOG.info("Stats saved to: %s", args.stat_file)


if __name__ == "__main__":
    _main(_parse())
