#!/usr/bin/env python3

"""
Read input from either stdin or a file, apply a specified transformation using
an LLM, and then write the output to either stdout or a file. It is
particularly useful for integrating with editors like Vim.

The script `dockerized_llm_transform.py` is executed within a Docker container
to ensure all dependencies are met. The Docker container is built dynamically if
necessary.

There are different modes to run this script:
- Process a chunk of code through vim
- Process input and write transformed output
- Process input and extract a cfile to be used to review the points in the code
 or for further processing with `llm_apply.py`

Examples
# Basic Usage
> llm_transform.py -i input.txt -o output.txt -p uppercase

# List of transforms
> llm_transform.py -i input.txt -o output.txt -p list

# Code review
> llm_transform.py -i dev_scripts_helpers/documentation/render_images.py -o cfile -p code_review

# Propose refactoring
> llm_transform.py -i dev_scripts_helpers/documentation/render_images.py -o cfile -p code_propose_refactoring
"""

import argparse
import logging
import os
from typing import List, Optional, cast

import dev_scripts_helpers.llms.llm_prompts as dshlllpr
import dev_scripts_helpers.llms.llm_utils as dshlllut
import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hmarkdown as hmarkdo
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem
import helpers.hlatex as hlatex

_LOG = logging.getLogger(__name__)


# TODO(gp): -> _parser() or _get_parser() everywhere.
def _parse() -> argparse.ArgumentParser:
    """
    Use the same argparse parser for `dockerized_llm_transform.py`.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hparser.add_input_output_args(
        parser,
        in_default="-",
        in_required=False,
    )
    hparser.add_llm_prompt_arg(parser)
    hparser.add_dockerized_script_arg(parser)
    parser.add_argument(
        "-c",
        "--compare",
        action="store_true",
        help="Report the original and transformed text in the same response",
    )
    parser.add_argument(
        "-s",
        "--skip-post-transforms",
        action="store_true",
        help="Skip the post-transforms outside the container",
    )
    # Use CRITICAL to avoid logging anything.
    hparser.add_verbosity_arg(parser, log_level="CRITICAL")
    return parser


def _run_dockerized_llm_transform(
    in_file_path: str,
    cmd_opts: List[str],
    out_file_path: str,
    *,
    mode: str = "system",
    force_rebuild: bool = False,
    use_sudo: bool = False,
    suppress_output: bool = False,
) -> Optional[str]:
    """
    Run `dockerized_llm_transform.py` in a Docker container with all its
    dependencies.
    """
    _LOG.debug(hprint.func_signature_to_str())
    #
    hdbg.dassert_in("OPENAI_API_KEY", os.environ)
    hdbg.dassert_isinstance(cmd_opts, list)
    # Build the container, if needed.
    container_image = "tmp.llm_transform"
    dockerfile = r"""
    FROM python:3.12-alpine

    # Install Bash.
    RUN apk add --no-cache bash git

    # Set Bash as the default shell.
    SHELL ["/bin/bash", "-c"]

    # Install pip packages.
    RUN pip install --upgrade pip
    RUN pip install --no-cache-dir PyYAML requests pandas

    RUN pip install --no-cache-dir openai
    """
    container_image = hdocker.build_container_image(
        container_image, dockerfile, force_rebuild, use_sudo
    )
    # Convert files to Docker paths.
    is_caller_host = not hserver.is_inside_docker()
    use_sibling_container_for_callee = True
    caller_mount_path, callee_mount_path, mount = hdocker.get_docker_mount_info(
        is_caller_host, use_sibling_container_for_callee
    )
    in_file_path = hdocker.convert_caller_to_callee_docker_path(
        in_file_path,
        caller_mount_path,
        callee_mount_path,
        check_if_exists=True,
        is_input=True,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    out_file_path = hdocker.convert_caller_to_callee_docker_path(
        out_file_path,
        caller_mount_path,
        callee_mount_path,
        check_if_exists=False,
        is_input=False,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    helpers_root = hgit.find_helpers_root()
    helpers_root = hdocker.convert_caller_to_callee_docker_path(
        helpers_root,
        caller_mount_path,
        callee_mount_path,
        check_if_exists=True,
        is_input=False,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    # Run the script inside the container.
    git_root = hgit.find_git_root()
    script = hsystem.find_file_in_repo(
        "dockerized_llm_transform.py", root_dir=git_root
    )
    script = hdocker.convert_caller_to_callee_docker_path(
        script,
        caller_mount_path,
        callee_mount_path,
        check_if_exists=True,
        is_input=True,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    cmd_opts_as_str = " ".join(cmd_opts)
    cmd = f" {script} -i {in_file_path} -o {out_file_path} {cmd_opts_as_str}"
    docker_cmd = hdocker.get_docker_base_cmd(use_sudo)
    docker_cmd.extend(
        [
            f"-e PYTHONPATH={helpers_root}",
            f"--workdir {callee_mount_path}",
            f"--mount {mount}",
            container_image,
            cmd,
        ]
    )
    docker_cmd = " ".join(docker_cmd)
    if suppress_output:
        mode = "system_without_output"
    ret = hdocker.process_docker_cmd(
        docker_cmd, container_image, dockerfile, mode
    )
    ret = cast(str, ret)
    return ret


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hparser.init_logger_for_input_output_transform(args, verbose=False)
    #
    if args.prompt == "list":
        print("# Available prompt tags:")
        print("\n".join(dshlllpr.get_prompt_tags()))
        return
    # Parse files.
    in_file_name, out_file_name = hparser.parse_input_output_args(args)
    tag = "llm_transform"
    tmp_in_file_name, tmp_out_file_name = (
        hparser.adapt_input_output_args_for_dockerized_scripts(in_file_name, tag)
    )
    if args.prompt in ("md_to_latex", "md_clean_up", "md_bold_bullets"):
        # Read the input.
        txt = hparser.read_file(tmp_in_file_name)
        txt = "\n".join(txt)
        if args.prompt == "md_to_latex":
            txt = hlatex.convert_pandoc_md_to_latex(txt)
            txt = hmarkdo.format_latex(txt)
        elif args.prompt == "md_clean_up":
            txt = hmarkdo.md_clean_up(txt)
            txt = hmarkdo.format_markdown(txt)
        elif args.prompt == "md_bold_bullets":
            txt = hmarkdo.bold_first_level_bullets(txt)
            txt = hmarkdo.format_markdown(txt)
        else:
            raise ValueError(f"Invalid prompt='{args.prompt}'")
        hparser.write_file(txt, out_file_name)
        return
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
    # For stdin/stdout, suppress the output of the container.
    suppress_output = in_file_name == "-" or out_file_name == "-"
    _run_dockerized_llm_transform(
        tmp_in_file_name,
        cmd_line_opts,
        tmp_out_file_name,
        mode="system",
        force_rebuild=args.dockerized_force_rebuild,
        use_sudo=args.dockerized_use_sudo,
        suppress_output=suppress_output,
    )
    # Run post-transforms outside the container.
    if not args.skip_post_transforms:
        out_txt = dshlllut.run_post_transforms(
            args,
            in_file_name,
            tmp_in_file_name,
            tmp_out_file_name,
        )
    else:
        _LOG.info("Skipping post-transforms")
        out_txt = hio.from_file(tmp_out_file_name)
    # Read the output from the container and write it to the output file from
    # command line (e.g., `-` for stdout).
    hparser.write_file(out_txt, out_file_name)
    if os.path.basename(out_file_name) == "cfile":
        print(out_txt)


if __name__ == "__main__":
    _main(_parse())
