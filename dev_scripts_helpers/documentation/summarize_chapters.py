#!/usr/bin/env python3

"""
Summarize markdown chapter files using an LLM.

Reads one or more markdown files and summarizes them into bullet-point format
while preserving the document structure (chapters and subchapters with their
original numbers).

Examples:
# Single file
> ./summarize_chapters.py -i chapter1.md -o chapter1.summary.md

# Multiple files
> ./summarize_chapters.py --input_files="ch1.md,ch2.md,ch3.md"

# Files from a list
> ./summarize_chapters.py --from_file=file_list.txt
"""

import argparse
import logging

from tqdm import tqdm

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hllm_cli as hllmcli
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


def _get_system_prompt() -> str:
    """
    Get the system prompt for summarization.

    Reads bullet point conventions from the rules file and combines them with
    structure-keeping instructions.

    :return: system prompt string
    """
    rules_file = hgit.find_file_in_git_tree(
        ".claude/skills/text.rules.bullet_points.md"
    )
    rules_content = hio.from_file(rules_file)
    system_prompt = f"""
    # Keep the same structure
    - Use the same structure of the chapter and subchapter in markdown headers
      - Use numbers of chapter (e.g., 1.) and subchapters (e.g., 1.1)
      - Use the chapter numbers that come from the book

    # Bullet point rules

    Write a summary in bullet points using the following rules from the style guide:
    {rules_content}

    # Example

    An example of the output is:

    ```
    # 1. Hello

    ## 1.1. Hello world

    - Point
      - Subpoint
      - Subpoint
    - Point

    ## 1.2. Good bye world

    # 2. Hello again
    ```
    """
    return system_prompt


def _get_output_path(input_file: str) -> str:
    """
    Derive output file path from input file path.

    Transforms `chapter1.md` -> `chapter1.summary.md`
    If input has no `.md` extension, appends `.summary.md`.

    :param input_file: path to input file
    :return: path to output file with `.summary.md` extension
    """
    if input_file.endswith(".md"):
        output_file = input_file[:-3] + ".summary.md"
    else:
        output_file = input_file + ".summary.md"
    return output_file


def _summarize_file(
    input_file: str,
    output_file: str,
    *,
    model: str,
    use_llm_executable: bool = False,
) -> None:
    """
    Summarize a single file using the LLM.

    Reads the input file, processes it with the LLM using the system prompt,
    and writes the result to the output file.

    :param input_file: path to input markdown file
    :param output_file: path to output markdown file
    :param model: LLM model name to use
    :param use_llm_executable: if True, use llm CLI executable
    """
    _LOG.debug("Summarizing file: %s", input_file)
    hdbg.dassert_file_exists(input_file)
    input_content = hio.from_file(input_file)
    _LOG.debug("Read %d characters from input file", len(input_content))
    system_prompt = _get_system_prompt()
    result, cost = hllmcli.apply_llm(
        input_str=input_content,
        system_prompt=system_prompt,
        model=model,
        use_llm_executable=use_llm_executable,
    )
    _LOG.debug("LLM processing completed with cost: $%.6f", cost)
    hio.to_file(output_file, result)
    _LOG.info("Written summary to: %s", output_file)


def _parse() -> argparse.ArgumentParser:
    """
    Parse command line arguments.

    :return: argument parser
    """
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    hparser.add_input_output_args(
        parser, in_required=False, out_required=False
    )
    parser.add_argument(
        "--model",
        action="store",
        default="gpt-4o",
        help="LLM model to use (default: gpt-4o)",
    )
    parser.add_argument(
        "--use_llm_executable",
        action="store_true",
        help="Use llm CLI executable instead of Python library",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main function.

    :param parser: command line argument parser
    """
    args = parser.parse_args()
    hparser.parse_verbosity_args(args)
    input_files = hparser.parse_input_output_files(args)
    if input_files is not None:
        _LOG.info("Processing multiple files")
        for input_file in tqdm(input_files, desc="Processing files"):
            output_file = _get_output_path(input_file)
            _summarize_file(
                input_file,
                output_file,
                model=args.model,
                use_llm_executable=args.use_llm_executable,
            )
    else:
        _LOG.info("Processing single file")
        in_file_name, out_file_name = hparser.parse_input_output_args(args)
        hdbg.dassert_file_exists(in_file_name)
        _summarize_file(
            in_file_name,
            out_file_name,
            model=args.model,
            use_llm_executable=args.use_llm_executable,
        )
    _LOG.info("Done")


if __name__ == "__main__":
    _main(_parse())
