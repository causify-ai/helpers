#!/usr/bin/env -S uv run

# /// script
# dependencies = [
#   "llm",
#   "pandas",
#   "pyyaml",
#   "tokencost",
#   "tqdm",
# ]
# ///

r"""
CLI script to apply LLM transformations to text files or text input.

For detailed documentation, usage examples, and feature descriptions, see:
dev_scripts_helpers/llms/README.md

Import as:

import dev_scripts_helpers.llms.llm_cli as dshllcli
"""

import argparse
import logging
import os
from typing import Optional

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hlint as hlint
import helpers.hllm_cli as hllmcli
import helpers.hmarkdown_select as hmarsele
import helpers.hparser as hparser
import helpers.htimer as htimer

_LOG = logging.getLogger(__name__)


# #############################################################################


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
    if system_prompt_file:
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
        result = hmarsele.extract_rule_from_file(rule)
        _LOG.debug(
            "Extracted rule from spec '%s' (%d chars)",
            rule,
            len(result),
        )
    else:
        result = system_prompt
    return result


def _process_select_mode(
    select: str,
    model: str,
    use_llm_executable: bool,
    input_file: Optional[str],
    output_file: Optional[str],
    system_prompt: str,
    expected_num_chars: Optional[int],
) -> float:
    """
    Process file in select mode: extract chunk, transform, reassemble.

    :param select: Select specification (e.g., 'start_marker:end_marker')
    :param model: Name of the LLM model to use
    :param use_llm_executable: Whether to use the LLM executable
    :param input_file: Path to input file
    :param output_file: Path to output file
    :param system_prompt: System prompt for the LLM
    :param expected_num_chars: Expected number of output characters for progress bar
    :return: The cost of the LLM operation
    """
    select_start, select_end = hmarsele.parse_select_arg(select)
    _LOG.info(
        "Select mode: extracting chunk from '%s' to '%s'",
        select_start,
        select_end,
    )
    input_lines = hparser.from_file(input_file)
    _, ext = os.path.splitext(input_file) if input_file != "-" else ("", "")
    is_slide_format = ext == ".txt"
    start_idx, end_idx = hmarsele.get_chunk_bounds(
        input_lines, select_start, select_end, is_slide_format=is_slide_format
    )
    chunk_lines = input_lines[start_idx:end_idx]
    chunk_text = "\n".join(chunk_lines)
    response, cost = hllmcli.apply_llm(
        chunk_text,
        system_prompt=system_prompt,
        model=model,
        use_llm_executable=use_llm_executable,
        expected_num_chars=expected_num_chars,
    )
    if output_file == input_file:
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
        hio.to_file(input_file, new_content)
        _LOG.info(
            "Updated file in-place: %s (lines %d-%d)",
            input_file,
            start_idx + 1,
            end_idx,
        )
    else:
        hparser.to_file(response, output_file)
    return cost


def _process_simple_input(
    model: str,
    use_llm_executable: bool,
    input_text: Optional[str],
    input_file: Optional[str],
    output_file: Optional[str],
    system_prompt: str,
    expected_num_chars: Optional[int],
) -> float:
    """
    Process file with input_text, stdin, or print_only mode.

    :param model: Name of the LLM model to use
    :param use_llm_executable: Whether to use the LLM executable
    :param input_text: Input text (if provided directly)
    :param input_file: Path to input file
    :param output_file: Path to output file
    :param system_prompt: System prompt for the LLM
    :param expected_num_chars: Expected number of output characters for progress bar
    :return: The cost of the LLM operation
    """
    if input_text is not None:
        input_str = input_text
    elif input_file == "-":
        input_lines = hparser.from_file(input_file)
        input_str = "\n".join(input_lines)
    else:
        input_str = hio.from_file(input_file)
    response, cost = hllmcli.apply_llm(
        input_str,
        system_prompt=system_prompt,
        model=model,
        use_llm_executable=use_llm_executable,
        expected_num_chars=expected_num_chars,
    )
    hparser.to_file(response, output_file)
    return cost


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hllmcli.add_llm_args(parser, input_required=True)
    hmarsele.add_select_arg(parser, required=False)
    parser.add_argument(
        "--lint",
        action="store_true",
        default=False,
        help="Apply lint_txt.py to the output file after processing",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    # Suppress logging when using stdin/stdout unless DEBUG is requested.
    verbosity = args.log_level
    if args.input == "-" or args.output == "-":
        if args.log_level == "INFO":
            verbosity = "CRITICAL"
    hdbg.init_logger(verbosity=verbosity, use_exec_path=True)
    # Validate arguments.
    if args.expected_num_chars is not None:
        hdbg.dassert_lt(0, args.expected_num_chars)
    # Determine input source.
    if args.input:
        hdbg.dassert_ne(args.input, "", "Input file cannot be empty")
        if args.input == "-":
            # Read from stdin.
            input_file = "-"
            input_text = None
        else:
            # Read from file.
            input_text = None
            input_file = args.input
    else:
        hdbg.dassert_ne(args.input_text, "", "Input text cannot be empty")
        input_text = args.input_text
        input_file = None
    # Determine output destination.
    if args.output is None:
        # In-place editing: only allowed with input file (not stdin).
        hdbg.dassert(
            input_file is not None and input_file != "-",
            "Output must be specified when using --input_text or stdin. "
            "In-place editing only works with --input <file>",
        )
        output_file = input_file
        print_only = False
        _LOG.info("No output specified, writing in-place to: %s", output_file)
    elif args.output == "-":
        # Print to screen.
        output_file = "-"
        print_only = True
    else:
        # Use the specified output file.
        hdbg.dassert_ne(args.output, "", "Output file cannot be empty string")
        output_file = args.output
        print_only = False
    # Determine system prompt source.
    system_prompt = _get_system_prompt(
        system_prompt_file=args.system_prompt_file,
        rule=args.rule,
        system_prompt=args.system_prompt,
    )
    # Parse --select if provided.
    is_select_mode = False
    if args.select:
        select_start, select_end = hmarsele.parse_select_arg(args.select)
        is_select_mode = True
        # In select mode with in-place editing, we will process the selected chunk.
        # Later we'll handle the in-place replacement.
        _LOG.info(
            "Select mode: extracting chunk from '%s' to '%s'",
            select_start,
            select_end,
        )
    # Calculate expected_num_chars if progress_bar is enabled.
    if args.progress_bar and args.expected_num_chars is None:
        # Read input to get its length.
        if input_file:
            if input_file == "-":
                # Read from stdin.
                input_lines = hparser.from_file(input_file)
                input_content = "\n".join(input_lines)
            else:
                input_content = hio.from_file(input_file)
        else:
            input_content = input_text
        input_length = len(input_content)
        expected_num_chars = int(input_length * 1.0)
        _LOG.info(
            "Progress bar enabled: estimated output %d chars (input: %d chars)",
            expected_num_chars,
            input_length,
        )
    else:
        expected_num_chars = args.expected_num_chars
    # Log configuration.
    _LOG.debug("Starting LLM CLI processing")
    _LOG.debug("Input file: %s", input_file)
    _LOG.debug("Input text: %s", input_text)
    _LOG.debug("Output file: %s", output_file)
    _LOG.debug("Print only: %s", print_only)
    _LOG.debug("System prompt: %s", system_prompt)
    _LOG.debug("Model: %s", args.model)
    _LOG.debug("Use LLM executable: %s", args.use_llm_executable)
    _LOG.debug("Progress bar: %s", args.progress_bar)
    _LOG.debug("Expected num chars: %s", expected_num_chars)
    # Process the file.
    _LOG.info("Processing with LLM '%s'...", args.model)
    memento = htimer.dtimer_start(logging.INFO, "LLM processing")
    # Handle select mode.
    if is_select_mode:
        hdbg.dassert_is(
            input_text, None, "Select mode requires file input, not --input_text"
        )
        cost = _process_select_mode(
            args.select,
            args.model,
            args.use_llm_executable,
            input_file,
            output_file,
            system_prompt,
            expected_num_chars,
        )
    elif input_text is not None or input_file == "-" or print_only:
        cost = _process_simple_input(
            args.model,
            args.use_llm_executable,
            input_text,
            input_file,
            output_file,
            system_prompt,
            expected_num_chars,
        )
    else:
        # Use file-based processing.
        cost = hllmcli.apply_llm_with_files(
            input_file,
            output_file,
            system_prompt=system_prompt,
            model=args.model,
            use_llm_executable=args.use_llm_executable,
            expected_num_chars=expected_num_chars,
        )
    msg, elapsed_time = htimer.dtimer_stop(memento)
    _LOG.info(msg)
    # Log the cost.
    _LOG.info("Total cost: $%.6f", cost)
    _LOG.info("LLM CLI processing completed successfully")
    if not print_only:
        _LOG.info("Output written to: %s", output_file)
        # Apply linting if requested.
        if args.lint:
            _LOG.info("Applying lint to output file: %s", output_file)
            hlint.lint_file(output_file)
            _LOG.info("Linting completed")


if __name__ == "__main__":
    _main(_parse())
