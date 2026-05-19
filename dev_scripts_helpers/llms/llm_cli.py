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

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hlint as hlint
import helpers.hllm_cli as hllmcli
import helpers.hmarkdown_select as hmarsele
import helpers.hparser as hparser
import helpers.htimer as htimer

_LOG = logging.getLogger(__name__)

# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hparser.add_llm_args(parser, input_required=True)
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
    elif args.rule:
        system_prompt = hmarsele.extract_rule_from_file(args.rule)
        _LOG.debug(
            "Extracted rule from spec '%s' (%d chars)",
            args.rule,
            len(system_prompt),
        )
    else:
        system_prompt = args.system_prompt
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
    # If using input_text, stdin, or print_only, call apply_llm directly.
    if input_text is not None or input_file == "-" or print_only:
        # Get input text.
        if input_text is not None:
            input_str = input_text
        elif input_file == "-":
            # Read from stdin.
            input_lines = hparser.from_file(input_file)
            input_str = "\n".join(input_lines)
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
        hparser.to_file(response, output_file)
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
