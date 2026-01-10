#!/usr/bin/env python

r"""
CLI script to apply LLM transformations to text files or text input.

This script provides a command-line interface to the apply_llm_with_files
function from helpers.hllm_cli. It reads text from an input file or command line,
processes it using an LLM (either via the llm CLI executable or the llm Python
library), and writes the result to an output file or prints to screen.

Examples:
# Basic usage with input and output files.
> llm_cli.py --input input.txt --output output.txt
> llm_cli.py -i input.txt -o output.txt

# In-place editing (writes back to input file).
> llm_cli.py --input input.txt
> llm_cli.py -i input.txt

# Basic usage with input text.
> llm_cli.py --input_text "What is 2+2?" --output output.txt

# Print to screen instead of file.
> llm_cli.py --input_text "What is 2+2?" --output -
> llm_cli.py -i input.txt -o -

# Use llm CLI executable instead of library.
> llm_cli.py -i input.txt -o output.txt --use_llm_executable

# With system prompt and specific model.
> llm_cli.py -i input.txt -o output.txt \
    --system_prompt "You are a helpful assistant" \
    --model gpt-4

# With system prompt from file.
> llm_cli.py -i input.txt -o output.txt \
    --system_prompt_file system_prompt.txt

# With automatic progress bar (estimates output size).
> llm_cli.py -i input.txt -o output.txt -b
> llm_cli.py -i input.txt -o output.txt --progress_bar

# With progress bar and explicit output size.
> llm_cli.py -i input.txt -o output.txt --expected_num_chars 5000

# Apply linting to output file after processing.
> llm_cli.py -i input.txt -o output.txt --lint
> llm_cli.py -i input.txt --lint  # In-place editing with linting

Import as:

import dev_scripts_helpers.llms.llm_cli as dshllcli
"""

import argparse
import logging
from typing import Tuple

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hlint as hlint
import helpers.hllm_cli as hllmcli
import helpers.hparser as hparser
import helpers.htimer as htimer

_LOG = logging.getLogger(__name__)

# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # Create mutually exclusive group for input sources.
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "-i",
        "--input",
        type=str,
        dest="input",
        help="Path to the input file containing text to process",
    )
    input_group.add_argument(
        "--input_text",
        type=str,
        help="Text input to process directly from command line",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        dest="output",
        required=False,
        default=None,
        help="Path to the output file where result will be saved (use '-' to print to screen). If not specified, writes in-place to the input file",
    )
    # Create mutually exclusive group for system prompt sources.
    system_prompt_group = parser.add_mutually_exclusive_group()
    system_prompt_group.add_argument(
        "-p",
        "--system_prompt",
        type=str,
        default=None,
        dest="system_prompt",
        help="Optional system prompt to guide the LLM's behavior",
    )
    system_prompt_group.add_argument(
        "-pf",
        "--system_prompt_file",
        type=str,
        default=None,
        dest="system_prompt_file",
        help="Optional path to file containing system prompt to guide the LLM's behavior",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o-mini",
        help="Optional model name to use (e.g., 'gpt-4', 'claude-3-opus').",
    )
    parser.add_argument(
        "--use_llm_executable",
        action="store_true",
        default=False,
        help="Use the llm CLI executable instead of the Python library",
    )
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
        default=None,
        help="Expected number of characters in output (enables progress bar with explicit size)",
    )
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
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Validate arguments.
    if args.expected_num_chars is not None:
        hdbg.dassert_lt(0, args.expected_num_chars)
    # Determine input source.
    if args.input:
        hdbg.dassert_ne(args.input, "", "Input file cannot be empty")
        input_text = None
        input_file = args.input
    else:
        hdbg.dassert_ne(args.input_text, "", "Input text cannot be empty")
        input_text = args.input_text
        input_file = None
    # Determine output destination.
    if args.output is None:
        # In-place editing: only allowed with input file.
        hdbg.dassert(
            input_file is not None,
            "Output must be specified when using --input_text. "
            "In-place editing only works with --input",
        )
        output_file = input_file
        print_only = False
        _LOG.info("No output specified, writing in-place to: %s", output_file)
    elif args.output == "":
        hdbg.dfatal("Output file cannot be empty string")
    elif args.output == "-":
        # Print to screen.
        output_file = "-"
        print_only = True
    else:
        output_file = args.output
        print_only = False
    # Determine system prompt source.
    if args.system_prompt_file:
        hdbg.dassert_ne(
            args.system_prompt_file, "", "System prompt file cannot be empty"
        )
        system_prompt = hio.from_file(args.system_prompt_file)
        _LOG.debug(
            "Read system prompt from file: %s (%d chars)",
            args.system_prompt_file,
            len(system_prompt),
        )
    else:
        system_prompt = args.system_prompt
    # Calculate expected_num_chars if progress_bar is enabled.
    if args.progress_bar and args.expected_num_chars is None:
        # Read input to get its length.
        if input_file:
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
    # If using input_text or print_only, call apply_llm directly.
    if input_text is not None or print_only:
        # Get input text.
        if input_text is not None:
            input_str = input_text
        else:
            input_str = hio.from_file(input_file)
        # Process with LLM.
        response, cost = hllmcli.apply_llm(
            input_str,
            system_prompt=system_prompt,
            model=args.model,
            use_llm_executable=args.use_llm_executable,
            expected_num_chars=expected_num_chars,
        )
        # Handle output.
        if print_only:
            print(response)
        else:
            hio.to_file(output_file, response)
    else:
        # Use file-based processing.
        cost = hllmcli.apply_llm_with_files(
            input_file=input_file,
            output_file=output_file,
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
