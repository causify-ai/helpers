#!/usr/bin/env python

"""
CLI script to apply LLM transformations to text files or text input.

This script provides a command-line interface to the apply_llm_with_files
function from helpers.hllm_cli. It reads text from an input file or command line,
processes it using an LLM (either via the llm CLI executable or the llm Python
library), and writes the result to an output file or prints to screen.

Examples:
# Basic usage with input file.
> llm_cli.py --input_file input.txt --output_file output.txt

# Basic usage with input text.
> llm_cli.py --input_text "What is 2+2?" --output_file output.txt

# Print to screen instead of file.
> llm_cli.py --input_text "What is 2+2?" --output_file -

# Use llm CLI executable instead of library.
> llm_cli.py --input_file input.txt --output_file output.txt --use_llm_executable

# With system prompt and specific model.
> llm_cli.py --input_file input.txt --output_file output.txt \\
    --system_prompt "You are a helpful assistant" \\
    --model gpt-4

# With progress bar for long outputs.
> llm_cli.py --input_file input.txt --output_file output.txt \\
    --expected_num_chars 5000

Import as:

import dev_scripts_helpers.llms.llm_cli as dshllcli
"""

import argparse
import logging

import helpers.hdbg as hdbg
import helpers.hio as hio
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
        "--input_file",
        type=str,
        help="Path to the input file containing text to process",
    )
    input_group.add_argument(
        "--input_text",
        type=str,
        help="Text input to process directly from command line",
    )
    parser.add_argument(
        "--output_file",
        type=str,
        required=True,
        help="Path to the output file where result will be saved (use '-' to print to screen)",
    )
    parser.add_argument(
        "--system_prompt",
        type=str,
        default=None,
        help="Optional system prompt to guide the LLM's behavior",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Optional model name to use (e.g., 'gpt-4', 'claude-3-opus')",
    )
    parser.add_argument(
        "--use_llm_executable",
        action="store_true",
        default=False,
        help="Use the llm CLI executable instead of the Python library",
    )
    parser.add_argument(
        "--expected_num_chars",
        type=int,
        default=None,
        help="Expected number of characters in output (enables progress bar)",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Validate arguments.
    hdbg.dassert_ne(args.output_file, "", "Output file cannot be empty")
    if args.expected_num_chars is not None:
        hdbg.dassert_lt(0, args.expected_num_chars)
    # Determine input source.
    if args.input_file:
        hdbg.dassert_ne(args.input_file, "", "Input file cannot be empty")
        input_text = None
    else:
        hdbg.dassert_ne(args.input_text, "", "Input text cannot be empty")
        input_text = args.input_text
    # Determine if output should be printed to screen.
    print_only = args.output_file == "-"
    # Log configuration.
    _LOG.debug("Starting LLM CLI processing")
    _LOG.debug("Input file: %s", args.input_file)
    _LOG.debug("Input text: %s", input_text)
    _LOG.debug("Output file: %s", args.output_file)
    _LOG.debug("Print only: %s", print_only)
    _LOG.debug("System prompt: %s", args.system_prompt)
    _LOG.debug("Model: %s", args.model)
    _LOG.debug("Use LLM executable: %s", args.use_llm_executable)
    _LOG.debug("Expected num chars: %s", args.expected_num_chars)
    # Process the file.
    _LOG.info("Processing with LLM...")
    memento = htimer.dtimer_start(logging.INFO, "LLM processing")
    # If using input_text or print_only, call apply_llm directly.
    if input_text is not None or print_only:
        # Get input text.
        if input_text is not None:
            input_str = input_text
        else:
            input_str = hio.from_file(args.input_file)
        # Process with LLM.
        response = hllmcli.apply_llm(
            input_str,
            system_prompt=args.system_prompt,
            model=args.model,
            use_llm_executable=args.use_llm_executable,
            expected_num_chars=args.expected_num_chars,
        )
        # Handle output.
        if print_only:
            print(response)
        else:
            hio.to_file(args.output_file, response)
    else:
        # Use file-based processing.
        hllmcli.apply_llm_with_files(
            input_file=args.input_file,
            output_file=args.output_file,
            system_prompt=args.system_prompt,
            model=args.model,
            use_llm_executable=args.use_llm_executable,
            expected_num_chars=args.expected_num_chars,
        )
    msg, elapsed_time = htimer.dtimer_stop(memento)
    _LOG.info(msg)
    _LOG.info("LLM CLI processing completed successfully")
    if not print_only:
        _LOG.info("Output written to: %s", args.output_file)


if __name__ == "__main__":
    _main(_parse())
