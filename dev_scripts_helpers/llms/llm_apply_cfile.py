#!/usr/bin/env python3

"""
Read cfile input and implement a transform for each line of the cfile using
LLMs.

The script `dockerized_llm_apply_cfile.py` is executed within a Docker container to ensure
all dependencies are met. The Docker container is built dynamically if
necessary. The script requires an OpenAI API key to be set in the environment.

Examples
# Basic Usage
> llm_apply_cfile.py -i cfile.txt
"""

import argparse
import logging
import os
from typing import List, Optional

import dev_scripts_helpers.llms.llm_prompts as dshlllpr
import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hgit as hgit
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


def _parse() -> argparse.ArgumentParser:
    """
    Same interface as `dockerized_llm_apply_cfile.py`.
    """
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
    hparser.add_dockerized_script_arg(parser)
    # Use CRITICAL to avoid logging anything.
    hparser.add_verbosity_arg(parser, log_level="CRITICAL")
    return parser


def _run_dockerized_llm_apply_cfile(
    in_file_path: str,
    cmd_opts: List[str],
    *,
    return_cmd: bool = False,
    force_rebuild: bool = False,
    use_sudo: bool = False,
    suppress_output: bool = False,
) -> Optional[str]:
    """
    Run dockerized_llm_transform.py in a Docker container with all its
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
    RUN apk add --no-cache bash

    # Set Bash as the default shell.
    SHELL ["/bin/bash", "-c"]

    # Install pip packages.
    RUN pip install --upgrade pip
    RUN pip install --no-cache-dir PyYAML

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
    git_root = hgit.find_git_root()
    # TODO(gp): -> llm_apply_cfile.py
    script = hsystem.find_file_in_repo(
        "dockerized_llm_apply_cfile.py", root_dir=git_root
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
    cmd = f" {script} --cfile {in_file_path} {cmd_opts_as_str}"
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
    if return_cmd:
        ret = docker_cmd
    else:
        # TODO(gp): Note that `suppress_output=False` seems to hang the call.
        hsystem.system(docker_cmd, suppress_output=suppress_output)
        ret = None
    return ret


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(
        verbosity=args.log_level, use_exec_path=True, force_white=False
    )
    if args.prompt == "list":
        print("# Available prompt tags:")
        print("\n".join(dshlllpr.get_prompt_tags()))
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
    suppress_output = False
    _run_dockerized_llm_apply_cfile(
        args.cfile,
        cmd_line_opts,
        return_cmd=False,
        force_rebuild=args.dockerized_force_rebuild,
        use_sudo=args.dockerized_use_sudo,
        suppress_output=suppress_output,
    )
    # Run post-transforms outside the container.
    # # 1) _convert_file_names().
    # prompts = dshlllpr.get_outside_container_post_transforms("convert_file_names")
    # if args.prompt in prompts:
    #     _convert_file_names(in_file_name, tmp_out_file_name)
    # # 2) prettier_on_str().
    # out_txt = hio.from_file(tmp_out_file_name)
    # prompts = dshlllpr.get_outside_container_post_transforms("prettier_on_str")
    # if args.prompt in prompts:
    #     # Note that we need to run this outside the `llm_transform` container to
    #     # avoid to do docker-in-docker in the `llm_transform` container (which
    #     # doesn't support that).
    #     out_txt = dshdlino.prettier_on_str(out_txt)
    # Read the output from the container and write it to the output file from
    # command line (e.g., `-` for stdout).
    # hparser.write_file(out_txt, out_file_name)


if __name__ == "__main__":
    _main(_parse())
