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

import helpers.hllm_cli as hllmcli
import helpers.hmarkdown_select as hmarsele
import helpers.hparser as hparser
import dev_scripts_helpers.llms.lib_llm_cli as dshllllcl

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


def _parse() -> argparse.ArgumentParser:
    """
    Create and return argument parser for the CLI.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--llm_cmd",
        type=str,
        default="",
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
        default=0,
        help="Limit input to max_chars characters",
    )
    parser.add_argument(
        "--stat_file",
        type=str,
        default="",
        help="Path to save stats as JSON file",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Parse arguments and execute the LLM CLI logic.

    :param parser: Argument parser configured by `_parse()`
    """
    args = parser.parse_args()
    dshllllcl._llm_cli(
        args.input or "",
        args.input_text or "",
        args.output or "",
        args.modify_in_place,
        args.progress_bar,
        args.expected_num_chars,
        args.log_level,
        args.dry_run,
        args.model,
        args.backend,
        args.system_prompt_file or "",
        args.rule or "",
        args.system_prompt or "",
        args.select or "",
        args.lint,
        args.max_chars,
        args.stat_file,
        args.llm_cmd,
    )


if __name__ == "__main__":
    _main(_parse())
