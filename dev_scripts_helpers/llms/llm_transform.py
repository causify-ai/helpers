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
> llm_transform.py -i dev_scripts_helpers/documentation/render_images.py -o cfile -p code_review

# Propose refactoring
> llm_transform.py -i dev_scripts_helpers/documentation/render_images.py -o cfile -p code_propose_refactoring
"""

import argparse
import logging
import os
import re
from typing import List, Optional

import dev_scripts_helpers.documentation.lint_notes as dshdlino
import dev_scripts_helpers.llms.llm_prompts as dshlllpr
import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem

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


def _run_dockerized_llm_transform(
    in_file_path: str,
    cmd_opts: List[str],
    out_file_path: str,
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
    #RUN apk add --no-cache bash

    # Set Bash as the default shell.
    #SHELL ["/bin/bash", "-c"]

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
    if return_cmd:
        ret = docker_cmd
    else:
        # TODO(gp): Note that `suppress_output=False` seems to hang the call.
        hsystem.system(docker_cmd, suppress_output=suppress_output)
        ret = None
    return ret


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
    tmp_in_file_name, tmp_out_file_name = (
        hparser.adapt_input_output_args_for_dockerized_scripts(
            in_file_name, "llm_transform"
        )
    )
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
        return_cmd=False,
        force_rebuild=args.dockerized_force_rebuild,
        use_sudo=args.dockerized_use_sudo,
        suppress_output=suppress_output,
    )
    # Run post-transforms outside the container.
    # 1) _convert_file_names().
    prompts = dshlllpr.get_outside_container_post_transforms("convert_file_names")
    if args.prompt in prompts:
        _convert_file_names(in_file_name, tmp_out_file_name)
    # 2) prettier_on_str().
    out_txt = hio.from_file(tmp_out_file_name)
    prompts = dshlllpr.get_outside_container_post_transforms("prettier_on_str")
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
