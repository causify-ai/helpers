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
`dev_scripts_helpers/llms/README.md`

Import as:

import dev_scripts_helpers.llms.llm_cli as dshllcli
"""

import argparse
import logging
import os
import pprint
from typing import Optional

import dev_scripts_helpers.dockerize.lib_prettier as libprettier
import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hlint as hlint
import helpers.hllm_cli as hllmcli
import helpers.hmarkdown_select as hmarsele
import helpers.hselect_input_output as hseinout
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.htimer as htimer

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
    # TODO(ai_gp): Add an assertion to make sure that only one option should be
    # possible.
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
    use_llm_executable: bool,
    input_file: Optional[str],
    output_file: Optional[str],
    system_prompt: str,
    modify_in_place: bool,
    lint: bool,
    expected_num_chars: Optional[int],
    dry_run: bool,
) -> float:
    """
    Process file in select mode: extract chunk, transform, reassemble.

    :param select: Select specification (e.g., 'start_marker:end_marker')
    :param model: Name of the LLM model to use
    :param use_llm_executable: Whether to use the LLM executable
    :param input_file: Path to input file
    :param output_file: Path to output file
    :param system_prompt: System prompt for the LLM
    :param modify_in_place: Whether to modify the input file in place
    :param expected_num_chars: Expected number of output characters for progress bar
    :param dry_run: If True, skip calling the LLM and show what would be done
    :return: The cost of the LLM operation
    """
    # Get input.
    select_start, select_end = hmarsele.parse_select_arg(select)
    _LOG.info(
        "Select mode: extracting chunk from '%s' to '%s'",
        select_start,
        select_end,
    )
    input_lines = hseinout.from_file(input_file)
    # Extract chunk.
    _, ext = os.path.splitext(input_file) if input_file != "-" else ("", "")
    is_slide_format = ext == ".txt"
    start_idx, end_idx = hmarsele.get_chunk_bounds(
        input_lines, select_start, select_end, is_slide_format=is_slide_format
    )
    chunk_lines = input_lines[start_idx:end_idx]
    chunk_text = "\n".join(chunk_lines)
    # Transform with LLM.
    if dry_run:
        _LOG.warning("DRY RUN: Would call LLM with parameters:")
        _LOG.info("  System prompt (%d chars):\n%s", len(system_prompt), system_prompt)
        _LOG.info("  Model: %s", model)
        _LOG.info("  Use LLM executable: %s", use_llm_executable)
        _LOG.info("  Expected output chars: %s", expected_num_chars)
        _LOG.info("  Input text to be processed (%d chars):\n%s", len(chunk_text), chunk_text)
        response = ""
        cost = 0.0
    else:
        response, cost = hllmcli.apply_llm(
            chunk_text,
            system_prompt=system_prompt,
            model=model,
            use_llm_executable=use_llm_executable,
            expected_num_chars=expected_num_chars,
        )
        if lint:
            file_type = "md"
            response = libprettier.prettier_on_str(response, file_type)
    # 
    if modify_in_place:
        hdbg.dassert_ne(input_file, "-")
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
    return cost


def _process_full_text(
    model: str,
    use_llm_executable: bool,
    input_text: Optional[str],
    input_file: Optional[str],
    output_file: Optional[str],
    system_prompt: str,
    lint: bool,
    expected_num_chars: Optional[int],
    dry_run: bool,
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
    :param dry_run: If True, skip calling the LLM and show what would be done
    :return: The cost of the LLM operation
    """
    if input_text is not None:
        # Use text from input string.
        input_str = input_text
    else:
        # Read text from file or stdin.
        input_lines = hseinout.from_file(input_file)
        input_str = "\n".join(input_lines)
    if dry_run:
        # TODO(gp): Consider moving this inside the LLM call to generalize it.
        _LOG.warning("DRY RUN: Would call LLM with parameters:")
        _LOG.info("  Input text length: %d chars", len(input_str))
        _LOG.info("  System prompt length: %d chars", len(system_prompt) if system_prompt else 0)
        _LOG.info("  Model: %s", model)
        _LOG.info("  Use LLM executable: %s", use_llm_executable)
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
            use_llm_executable=use_llm_executable,
            expected_num_chars=expected_num_chars,
        )
        if lint:
            file_type = "md"
            response = libprettier.prettier_on_str(response, file_type)
    if dry_run:
        _LOG.warning("DRY RUN: Would save to %s", output_file)
    else:
        hseinout.to_file(response, output_file)
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
    # TODO(ai_gp): Extract a function returning input_file and output_file.
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
        hdbg.dassert(
            input_file is not None and input_file != "-",
            "Output must be specified when using --input_text or stdin. "
            "In-place editing only works with --input <file>",
        )
        if args.modify_in_place:
            output_file = input_file
        else:
            output_file = "-"
        _LOG.info("No output specified, writing in-place to: %s", output_file)
    elif args.output == "-":
        # Print to screen.
        output_file = "-"
    else:
        # Use the specified output file.
        hdbg.dassert_ne(args.output, "", "Output file cannot be empty string")
        output_file = args.output
    # Calculate expected_num_chars if progress_bar is enabled.
    if args.progress_bar and args.expected_num_chars is None:
        # TODO(ai_gp): Extract this into a function.
        # Read input to get its length.
        if input_file:
            if input_file == "-":
                # Read from stdin.
                input_lines = hseinout.from_file(input_file)
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
        hdbg.dassert_lt(0, args.expected_num_chars)
        expected_num_chars = args.expected_num_chars
    # Process the file.
    if args.dry_run:
        _LOG.warning("Dry run mode: LLM will not be called")
    else:
        _LOG.info("Processing with LLM '%s'...", args.model)
    #memento = htimer.dtimer_start(logging.INFO, "LLM processing")
    # Determine system prompt source.
    system_prompt = _get_system_prompt(
        system_prompt_file=args.system_prompt_file,
        rule=args.rule,
        system_prompt=args.system_prompt,
    )
    # Handle select mode.
    if args.select:
        hdbg.dassert_is(
            input_text, None, "Select mode requires file input, not --input_text"
        )
        cost = _process_selected_text(
            args.select,
            args.model,
            args.use_llm_executable,
            input_file,
            output_file,
            system_prompt,
            args.modify_in_place,
            args.lint,
            expected_num_chars,
            args.dry_run,
        )
    else:
        cost = _process_full_text(
            args.model,
            args.use_llm_executable,
            input_text,
            input_file,
            output_file,
            system_prompt,
            args.lint,
            expected_num_chars,
            args.dry_run,
        )
#    else:
#        raise ValueError
#        # Use file-based processing.
#        if args.dry_run:
#            file_content = hio.from_file(input_file)
#            _LOG.warning("DRY RUN: Would call LLM with parameters:")
#            _LOG.info("  Input file: %s", input_file)
#            _LOG.info("  Input text length: %d chars", len(file_content))
#            _LOG.info("  System prompt length: %d chars", len(system_prompt) if system_prompt else 0)
#            _LOG.info("  Model: %s", args.model)
#            _LOG.info("  Use LLM executable: %s", args.use_llm_executable)
#            _LOG.info("  Expected output chars: %s", expected_num_chars)
#            _LOG.info("  Output file: %s", output_file)
#            cost = 0.0
#        else:
#            cost = hllmcli.apply_llm_with_files(
#                input_file,
#                output_file,
#                system_prompt=system_prompt,
#                model=args.model,
#                use_llm_executable=args.use_llm_executable,
#                expected_num_chars=expected_num_chars,
#            )
    #msg, elapsed_time = htimer.dtimer_stop(memento)
    #_LOG.info(msg)
    # Log the cost.
    _LOG.info("Total cost: $%.6f", cost)


if __name__ == "__main__":
    _main(_parse())
