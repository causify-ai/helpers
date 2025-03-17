#!/usr/bin/env python3

"""
Read input from either stdin or a file, apply a specified transformation using
an LLM, and then write the output to either stdout or a file. It is
particularly useful for integrating with editors like Vim.

The script `_llm_transform.py` is executed within a Docker container to ensure
all dependencies are met. The Docker container is built dynamically if
necessary. The script requires an OpenAI API key to be set in the environment.

Examples
# Basic Usage
> llm_transform.py -i input.txt -o output.txt -t uppercase

# List of transforms
> llm_transform.py -i input.txt -o output.txt -t list

# Force rebuild Docker container
> llm_transform.py -i input.txt -o output.txt -t uppercase --dockerized-force-rebuild

# Set logging verbosity
> llm_transform.py -i input.txt -o output.txt -t uppercase -v DEBUG
"""

import argparse
import logging

if False:
    # Hardwire path when we are calling from a different dir.
    import sys

    sys.path.insert(0, "/Users/saggese/src/notes1/helpers_root")

# pylint: disable=wrong-import-position
import dev_scripts_helpers.documentation.lint_notes as dshdlino
import dev_scripts_helpers.llms.llm_prompts_utils as dshllprut
import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hio as hio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


def _parse() -> argparse.ArgumentParser:
    """
    Same interface as `_llm_transform.py`.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hparser.add_input_output_args(parser)
    hparser.add_transform_arg(parser)
    hparser.add_dockerized_script_arg(parser)
    # Use CRITICAL to avoid logging anything.
    hparser.add_verbosity_arg(parser, log_level="CRITICAL")
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(
        verbosity=args.log_level, use_exec_path=True, force_white=False
    )
    if args.transform == "list":
        print("# Available transformations:")
        print("\n".join(dshllprut.get_transforms()))
        return
    # Parse files.
    in_file_name, out_file_name = hparser.parse_input_output_args(args)
    _ = in_file_name, out_file_name
    # Since we need to call a container and passing stdin/stdout is tricky
    # we read the input and save it in a temporary file.
    in_lines = hparser.read_file(in_file_name)
    tmp_in_file_name = "tmp.llm_transform.in.txt"
    in_txt = "\n".join(in_lines)
    hio.to_file(tmp_in_file_name, in_txt)
    #
    tmp_out_file_name = "tmp.llm_transform.out.txt"
    # TODO(gp): We should just automatically pass-through the options.
    cmd_line_opts = [f"-t {args.transform}", f"-v {args.log_level}"]
    if args.fast_model:
        cmd_line_opts.append("--fast_model")
    if args.debug:
        cmd_line_opts.append("-d")
    # cmd_line_opts = []
    # for arg in vars(args):
    #     if arg not in ["input", "output"]:
    #         value = getattr(args, arg)
    #         if isinstance(value, bool):
    #             if value:
    #                 cmd_line_opts.append(f"--{arg.replace('_', '-')}")
    #         else:
    #             cmd_line_opts.append(f"--{arg.replace('_', '-')} {value}")
    hdocker.run_dockerized_llm_transform(
        tmp_in_file_name,
        cmd_line_opts,
        tmp_out_file_name,
        return_cmd=False,
        force_rebuild=args.dockerized_force_rebuild,
        use_sudo=args.dockerized_use_sudo,
    )
    out_txt = hio.from_file(tmp_out_file_name)
    # Note that we need to run this outside the `llm_transform` container to
    # avoid to do docker-in-docker in the `llm_transform` container (which
    # doesn't support that).
    if args.transform in (
        "md_format",
        "md_summarize_short",
        "slide_improve",
        "slide_colorize",
    ):
        out_txt = dshdlino.prettier_on_str(out_txt)
    # Read the output from the container and write it to the output file from
    # command line (e.g., `-` for stdout).
    hparser.write_file(out_txt, out_file_name)


if __name__ == "__main__":
    _main(_parse())
