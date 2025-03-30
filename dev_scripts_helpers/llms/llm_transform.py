#!/usr/bin/env python3

"""
Read input from either stdin or a file, apply a specified transformation using
an LLM, and then write the output to either stdout or a file. It is
particularly useful for integrating with editors like Vim.

The script `dockerized_llm_transform.py` is executed within a Docker container to ensure
all dependencies are met. The Docker container is built dynamically if
necessary. The script requires an OpenAI API key to be set in the environment.

Examples
# Basic Usage
> llm_transform.py -i input.txt -o output.txt -p uppercase

# List of transforms
> llm_transform.py -i input.txt -o output.txt -p list

# Code review
> llm_transform.py -i dev_scripts_helpers/documentation/render_images.py -o cfile -p code_propose_refactoring

# Propose refactoring
> llm_transform.py -i dev_scripts_helpers/documentation/render_images.py -o cfile -p code_propose_refactoring
"""

import argparse
import logging
import os
import re

if False:
    # Hardwire path when we are calling from a different dir.
    import sys

    sys.path.insert(0, "/Users/saggese/src/notes1/helpers_root")

# pylint: disable=wrong-import-position
import dev_scripts_helpers.documentation.lint_notes as dshdlino
import dev_scripts_helpers.llms.llm_prompts as dshlllpr
import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)


def _parse() -> argparse.ArgumentParser:
    """
    Same interface as `dockerized_llm_transform.py`.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hparser.add_input_output_args(parser)
    hparser.add_prompt_arg(parser)
    hparser.add_dockerized_script_arg(parser)
    # Use CRITICAL to avoid logging anything.
    hparser.add_verbosity_arg(parser, log_level="CRITICAL")
    return parser


def _convert_file_names(in_file_name: str, out_file_name: str) -> str:
    """
    Convert the files from inside the container to outside.

    Replace the name of the file inside the container (e.g.,
    `/app/helpers_root/tmp.llm_transform.in.txt`) with the name of the
    file outside the container.
    """
    # TODO(gp): We should use the `convert_caller_to_callee_docker_path`
    txt_out = []
    txt = hio.from_file(out_file_name)
    for line in txt.split("\n"):
        if line.strip() == "":
            continue
        # E.g., the format is like
        # ```
        # /app/helpers_root/r.py:1: Change the shebang line to `#!/usr/bin/env python3` to e
        # ```
        _LOG.debug("before: " + hprint.to_str("line in_file_name"))
        line = re.sub(r"^.*(:\d+:.*)$", rf"{in_file_name}\1", line)
        _LOG.debug("after: " + hprint.to_str("line"))
        txt_out.append(line)
    txt_out = "\n".join(txt_out)
    hio.to_file(out_file_name, txt_out)


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(
        verbosity=args.log_level, use_exec_path=True, force_white=False
    )
    if args.prompt == "list":
        print("# Available prompt tags:")
        print("\n".join(dshlllpr.get_prompt_tags()))
        return
    # Parse files.
    in_file_name, out_file_name = hparser.parse_input_output_args(args)
    _ = in_file_name, out_file_name
    # Since we need to call a container and passing stdin/stdout is tricky,
    # we read the input and save it in a temporary file.
    in_lines = hparser.read_file(in_file_name)
    if in_file_name == "-":
        tmp_in_file_name = "tmp.llm_transform.in.txt"
        in_txt = "\n".join(in_lines)
        hio.to_file(tmp_in_file_name, in_txt)
    else:
        tmp_in_file_name = in_file_name
    #
    tmp_out_file_name = "tmp.llm_transform.out.txt"
    # TODO(gp): We should just automatically pass-through the options.
    cmd_line_opts = [f"-p {args.prompt}", f"-v {args.log_level}"]
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
    # Post transforms outside the container.
    valid_prompts = dshlllpr.get_prompt_tags()
    prompts = ["code_review", "code_propose_refactoring"]
    for prompt in prompts:
        hdbg.dassert_in(prompt, valid_prompts)
    if args.prompt in prompts:
        _convert_file_names(in_file_name, tmp_out_file_name)
    #
    out_txt = hio.from_file(tmp_out_file_name)
    prompts = [
        "md_rewrite",
        "md_summarize_short",
        "slide_improve",
        "slide_colorize",
    ]
    for prompt in prompts:
        hdbg.dassert_in(prompt, valid_prompts)
    if args.prompt in prompts:
        # Note that we need to run this outside the `llm_transform` container to
        # avoid to do docker-in-docker in the `llm_transform` container (which
        # doesn't support that).
        out_txt = dshdlino.prettier_on_str(out_txt)
    # Read the output from the container and write it to the output file from
    # command line (e.g., `-` for stdout).
    hparser.write_file(out_txt, out_file_name)
    #
    if os.path.basename(out_file_name) == "cfile":
        print(out_txt)


if __name__ == "__main__":
    _main(_parse())
