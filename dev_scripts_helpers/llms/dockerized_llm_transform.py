#!/usr/bin/env python3

"""
Run transformations using LLMs. It requires certain dependencies to be present
(e.g., `openai`) and thus it is executed within a Docker container.

To use this script, you need to provide the input file, output file, and
the type of transformation to apply.
"""

import argparse
import logging

import dev_scripts_helpers.llms.llm_prompts as dshlllpr
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
    hparser.add_prompt_arg(parser)
    hparser.add_verbosity_arg(parser, log_level="CRITICAL")
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hparser.init_logger_for_input_output_transform(args)
    # Parse files from command line.
    in_file_name, out_file_name = hparser.parse_input_output_args(args)
    # Read file.
    txt = hparser.read_file(in_file_name)
    # Transform with LLM.
    txt_tmp = "\n".join(txt)
    prompt_tag = args.prompt
    if args.fast_model:
        model = "gpt-4o-mini"
    else:
        model = "gpt-4o"
    txt_tmp = dshlllpr.run_prompt(
        prompt_tag,
        txt_tmp,
        model,
        in_file_name=in_file_name,
        out_file_name=out_file_name,
    )
    if txt_tmp is not None:
        # Write file, if needed.
        res = []
        if args.debug:
            res.append("# Before:")
            res.extend(txt)
            res.append("# After:")
        res.extend(txt_tmp.split("\n"))
        hparser.write_file(res, out_file_name)


if __name__ == "__main__":
    _main(_parse())
