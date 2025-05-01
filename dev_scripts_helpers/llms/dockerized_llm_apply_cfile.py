#!/usr/bin/env python3

"""
This script is designed to run a transformation script using LLMs. It requires
certain dependencies to be present (e.g., `openai`) and thus it is executed
within a Docker container.

To use this script, you need to provide the input file, output file, and
the type of transformation to apply.
"""

import argparse
import logging
import re
from typing import List, Tuple

import dev_scripts_helpers.llms.llm_prompts as dshlllpr
import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


def _parse_cfile(cfile: str) -> List[Tuple[str, str]]:
    """
    Read and parse a cfile.

    :param cfile: path to the cfile
    :return: list of tuples, each containing a line number and a transform, e.g.,
        [(file_name, line_number, transform), ...]
    """
    # Read the cfile.
    cfile_lines = hio.from_file(cfile)
    # Parse the cfile.
    for line in cfile_lines:
        _LOG.debug("line=%s", line)
        # Parse the lines of the cfile, like
        # dev_scripts_helpers/llms/llm_prompts.py:106: in public function `test`:D404: First word of the docstring should not be `This` [doc_formatter]
        # dev_scripts_helpers/llms/llm_prompts.py:110: error: Need type annotation for "pre_transforms" (hint: "pre_transforms: set[<type>] = ...")  [var-annotated] [mypy]
        # extracting the file name, line number, and transform.
        regex = r"^(.+):(\d+): (.*)$"
        match = re.match(regex, line)
        hdbg.dassert_in(match, "Failed to parse line: %s", line)
        # Extract the file name, line number, and transform.
        file_name = match.group(1)
        line_number = match.group(2)
        transform = match.group(3)
        # Add values to the list.
        cfile_lines.append((file_name, line_number, transform))
    return cfile_lines


def _apply_transforms(cfile_lines: List[Tuple[str, str]], prompt_tag: str, model: str) -> None:
    """
    Apply the transforms to the file.

    :param cfile_lines: list of tuples, each containing a file name, line
        number, and transform
    :param model: model to use for the transformation
    """
    # Create a dict from file to line number to transform.
    file_to_line_to_transform = {}
    for file_name, line_number, transform in cfile_lines:
        if file_name not in file_to_line_to_transform:
            file_to_line_to_transform[file_name] = []
        file_to_line_to_transform[file_name].append((line_number, transform))
    # Apply the transforms to the file.
    for file_name, line_to_transform in file_to_line_to_transform.items():
        # Read the file.
        txt_in = hio.from_file(file_name)
        # Prepare the instructions for the prompt.
        instructions = "\n".join(
            [f"{line_number}: {transform}" for line_number, transform in line_to_transform]
        )
        # Transform the file using the instructions.
        txt_out = dshlllpr.run_prompt(prompt_tag, txt_in, model, instructions=instructions, in_file_name="", out_file_name="")
        # Write the file.
        hio.to_file(txt_out, file_name)



# # TODO(gp): This should become an invoke or a command, where we read a file
# and a cfile and inject TODOs in the code.
# def _annotate_with_cfile(txt: str, txt_cfile: str) -> str:
#     """
#     Annotate a file `txt` with TODOs from the cfile `txt_cfile`.
#     """
#     ret_out = _extract_vim_cfile_lines(txt_cfile)
#     # Convert ret_out to a dict.
#     ret_out_dict = {}
#     for line_number, line in ret_out:
#         if line_number not in ret_out_dict:
#             ret_out_dict[line_number] = [line]
#         else:
#             ret_out_dict[line_number].append(line)
#     # Annotate the code.
#     txt_out = []
#     for line_number, line in txt:
#         if line_number in ret_out_dict:
#             for todo in ret_out_dict[line_number]:
#                 txt_out.append(f"# TODO(*): {todo}")
#         else:
#             txt_out.append(line)
#     return "\n".join(txt_out)


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--cfile",
        type=str,
        required=True,
        help="Path to the cfile",
    )
    hparser.add_prompt_arg(parser)
    hparser.add_verbosity_arg(parser, log_level="CRITICAL")
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # TODO(gp): Factor this out.
    if args.fast_model:
        model = "gpt-4o-mini"
    else:
        model = "gpt-4o"
    # Apply the transforms.
    cfile_lines = _parse_cfile(args.cfile)
    _apply_transforms(cfile_lines, args.prompt_tag, model)


if __name__ == "__main__":
    _main(_parse())
