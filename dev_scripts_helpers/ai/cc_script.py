#!/usr/bin/env -S uv run
# /// script
# dependencies = ["anthropic-sdk"]
# ///
"""
Execute sequential prompts against Claude Code.

Reads a list of prompts and executes them sequentially, maintaining context
across prompts. Outputs raw responses and saves a session log.

# Usage Example

- Execute with inline prompts:
> cc_script.py --prompts "prompt1" --prompts "prompt2" [--options]

- Execute with prompts from a file (one per line):
> cc_script.py --prompts_file prompts.txt [--options]
"""

import argparse
import asyncio
import json
import logging
from typing import Any, Dict, List

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint

import dev_scripts_helpers.ai.cc_lib as dshaccli

_LOG = logging.getLogger(__name__)

# #############################################################################
# Prompt Loading
# #############################################################################


def _load_prompts_from_file(file_path: str) -> List[str]:
    """
    Load prompts from file (one per line).

    :param file_path: Path to prompts file
    :return: List of prompts (stripped of whitespace)
    """
    hdbg.dassert_file_exists(file_path)
    _LOG.debug("Loading prompts from file '%s'", file_path)
    # Read.
    content = hio.from_file(file_path)
    prompts = [line.strip() for line in content.split("\n") if line.strip()]
    # Check.
    hdbg.dassert_lt(0, len(prompts), "Prompts file is empty")
    _LOG.info("Loaded %d prompts from file", len(prompts))
    return prompts


# #############################################################################
# Prompt Execution
# #############################################################################


async def _execute_prompts(
    prompts: List[str],
    allowed_tools: List[str],
    permission_mode: str,
    cwd: str,
) -> Dict[str, Any]:
    """
    Execute prompts using PromptSequencer.

    :param prompts: List of prompts to execute
    :param allowed_tools: List of allowed tools
    :param permission_mode: Permission handling mode
    :param cwd: Working directory
    :return: Dictionary with prompts and responses
    :raises RuntimeError: If execution fails
    """
    _LOG.info("Starting prompt execution with %d prompts", len(prompts))
    sequencer = dshaccli.PromptSequencer(
        allowed_tools=allowed_tools,
        permission_mode=permission_mode,
        cwd=cwd,
    )
    await sequencer.execute(prompts)
    # Collect responses (for now, just the last one from sequencer).
    # TODO(gp): Extend this.
    stats = sequencer.get_execution_stats()
    _LOG.info("Execution completed: %s", stats)
    # Return execution results.
    return {
        "prompts": prompts,
        "responses": [sequencer.get_last_response()],
        "stats": stats,
    }


# #############################################################################
# Output Handling
# #############################################################################


def _print_response(response: str) -> None:
    """
    Print raw response to stdout.

    :param response: Response text from Claude
    """
    framed = hprint.frame(
        "CLAUDE RESPONSE:\n\n" + response,
        char1="=",
        num_chars=80,
    )
    print("\n" + framed + "\n")


def _save_session_log(
    output_file: str,
    prompts: List[str],
    responses: List[str],
) -> None:
    """
    Save prompt-response session to file.

    :param output_file: Path to output file
    :param prompts: List of executed prompts
    :param responses: List of responses
    """
    session_data = {
        "prompts_and_responses": [
            {"prompt_index": idx, "prompt": prompt, "response": response}
            for idx, (prompt, response) in enumerate(zip(prompts, responses), 1)
        ],
        "total_prompts": len(prompts),
    }
    content = json.dumps(session_data, indent=2)
    hio.to_file(output_file, content)
    _LOG.info("Session log saved to '%s'", output_file)


# #############################################################################
# Argument Parsing
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments.

    :return: ArgumentParser with configured options
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    # Prompt input options (mutually exclusive).
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--prompts",
        action="append",
        dest="prompts",
        type=str,
        default=[],
        help="Individual prompt string (can be repeated)",
    )
    input_group.add_argument(
        "--prompts_file",
        type=str,
        default="",
        help="File with one prompt per line",
    )
    # Claude options.
    parser.add_argument(
        "--tools",
        action="append",
        dest="tools",
        type=str,
        default=[],
        help="Allowed tools (can be repeated, e.g., Read, Edit, Bash)",
    )
    parser.add_argument(
        "--permission_mode",
        type=str,
        default="ask",
        choices=["ask", "acceptEdits", "bypassPermissions"],
        help="Permission handling mode",
    )
    parser.add_argument(
        "--cwd",
        type=str,
        default="",
        help="Working directory for execution",
    )
    # Output options.
    parser.add_argument(
        "--output_file",
        type=str,
        default="tmp.cc_script.log",
        help="Path to save session log",
    )
    # Logging options.
    hparser.add_verbosity_arg(parser)
    return parser


# #############################################################################
# Main
# #############################################################################


async def _main_async(args: argparse.Namespace) -> None:
    """
    Main async execution function.

    :param args: Parsed command-line arguments
    :raises RuntimeError: If prompt execution fails
    """
    # Load prompts.
    if args.prompts_file:
        prompts = _load_prompts_from_file(args.prompts_file)
    else:
        prompts = [p for p in args.prompts if p]
        hdbg.dassert_lt(0, len(prompts), "No prompts provided")
        _LOG.info("Loaded %d prompts from command line", len(prompts))
    # Execute prompts.
    result = await _execute_prompts(
        prompts=prompts,
        allowed_tools=args.tools,
        permission_mode=args.permission_mode,
        cwd=args.cwd,
    )
    # Print response.
    for response in result["responses"]:
        _print_response(response)
    # Save session log.
    _save_session_log(args.output_file, result["prompts"], result["responses"])
    _LOG.info("Execution complete")


def _main(args: argparse.Namespace) -> None:
    """
    Main entry point for CLI.

    :param args: Parsed command-line arguments
    """
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    _LOG.debug("Starting with args: %s", args)
    asyncio.run(_main_async(args))


if __name__ == "__main__":
    parser = _parse()
    args = parser.parse_args()
    _main(args)
