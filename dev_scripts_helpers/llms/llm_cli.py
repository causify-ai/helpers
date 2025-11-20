#!/usr/bin/env python

"""
CLI script to apply LLM transformations to text files.

This script provides a command-line interface to the apply_llm_with_files
function from helpers.hllm_cli. It reads text from an input file, processes
it using an LLM (either via the llm CLI executable or the llm Python library),
and writes the result to an output file.

Examples:
# Basic usage with library (default).
> llm_cli.py --input_file input.txt --output_file output.txt

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
    parser.add_argument(
        "--input_file",
        type=str,
        required=True,
        help="Path to the input file containing text to process",
    )
    parser.add_argument(
        "--output_file",
        type=str,
        required=True,
        help="Path to the output file where result will be saved",
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
    hdbg.dassert_ne(args.input_file, "", "Input file cannot be empty")
    hdbg.dassert_ne(args.output_file, "", "Output file cannot be empty")
    if args.expected_num_chars is not None:
        hdbg.dassert_lt(0, args.expected_num_chars)
    # Log configuration.
    _LOG.debug("Starting LLM CLI processing")
    _LOG.debug("Input file: %s", args.input_file)
    _LOG.debug("Output file: %s", args.output_file)
    _LOG.debug("System prompt: %s", args.system_prompt)
    _LOG.debug("Model: %s", args.model)
    _LOG.debug("Use LLM executable: %s", args.use_llm_executable)
    _LOG.debug("Expected num chars: %s", args.expected_num_chars)
    # Process the file.
    _LOG.info("Processing with LLM...")
    memento = htimer.dtimer_start(logging.INFO, "LLM processing")
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
    _LOG.info("Output written to: %s", args.output_file)


if __name__ == "__main__":
    _main(_parse())
