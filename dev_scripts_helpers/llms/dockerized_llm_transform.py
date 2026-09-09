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
import helpers.hllm_cli as hllmcli
import helpers.hselect_input_output as hseinout
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    hseinout.add_input_output_args(parser)
    hllmcli.add_llm_prompt_arg(parser)
    hparser.add_verbosity_arg(parser, log_level="CRITICAL")
    return parser


def run_transform(
    in_file_name: str,
    out_file_name: str,
    prompt_tag: str,
    *,
    fast_model: bool,
    debug: bool,
) -> None:
    """
    Apply one LLM transform to an input file and write the result.

    This is shared by the Dockerized CLI and the opt-in native execution path
    in `llm_transform.py` so both modes preserve the same transform semantics.

    :param in_file_name: input file to transform
    :param out_file_name: output file receiving the transformed text
    :param prompt_tag: prompt tag selecting the requested transform
    :param fast_model: use the faster model when True
    :param debug: include the input text before the transformed text when True
    """
    txt = hseinout.from_file(in_file_name)
    txt_tmp = "\n".join(txt)
    if fast_model:
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
        res = []
        if debug:
            res.append("# Before:")
            res.extend(txt)
            res.append("# After:")
        res.extend(txt_tmp.split("\n"))
        hseinout.to_file(res, out_file_name)


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hseinout.init_logger_for_input_output_transform(args)
    # Parse files from command line.
    in_file_name, out_file_name = hseinout.parse_input_output_args(args)
    run_transform(
        in_file_name,
        out_file_name,
        args.prompt,
        fast_model=args.fast_model,
        debug=args.debug,
    )


if __name__ == "__main__":
    _main(_parse())
