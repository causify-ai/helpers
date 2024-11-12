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

import dev_scripts_helpers.llms.llm_prompts as llmp

import helpers.hdbg as hdbg
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hparser.add_input_output_args(parser)
    parser.add_argument(
        "-t", "--transform", required=True, type=str, help="Type of transform"
    )
    hparser.add_verbosity_arg(parser, log_level="CRITICAL")
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Parse files from command line.
    in_file_name, out_file_name = hparser.parse_input_output_args(args)
    # Read file.
    txt = hparser.read_file(in_file_name)
    # Transform with LLM.
    txt_tmp = "\n".join(txt)
    transform = args.transform
    if transform == "comment":
        txt_tmp = llmp.add_comments_one_shot_learning1(txt_tmp)
    elif transform == "docstring":
        txt_tmp = llmp.add_docstring_one_shot_learning1(txt_tmp)
    elif transform == "typehints":
        txt_tmp = llmp.add_type_hints(txt_tmp)
    elif transform == "rewrite_as_tech_writer":
        txt_tmp = llmp.rewrite_as_tech_writer(txt_tmp)
    else:
        raise ValueError("Invalid transform=%s" % transform)
    # Write file.
    hparser.write_file(txt_tmp.split("\n"), out_file_name)


if __name__ == "__main__":
    _main(_parse())
