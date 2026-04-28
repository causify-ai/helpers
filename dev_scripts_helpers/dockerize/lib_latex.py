"""
LaTeX compilation utilities for dockerized execution.

This module provides Docker-based wrappers for LaTeX/pdflatex, a document
preparation system for creating high-quality typeset documents.

Import as:

import dev_scripts_helpers.dockerize.lib_latex as dshdlila
"""

import argparse
import logging
import os
import re
import shlex
from typing import Any, Dict, List

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# Version pins for tools
_TEXLIVE_FULL_IMAGE = "mfisherman/texlive-full:2024"

_CONTAINER_PREFIX = "tmp.latex"
_DOCKERFILE = rf"""
FROM {_TEXLIVE_FULL_IMAGE}

# Verify LaTeX is installed.
RUN latex --version

# Default command.
CMD [ "bash" ]
"""

# if False:
#     _DOCKER_FILE = r"""
#     # Use minimal multi-arch TeX Live image (includes ARM support)
#     FROM ghcr.io/xu-cheng/texlive:latest
#     """
# # Doesn't work.
# if False:
#     _DOCKER_FILE = r"""
#     # Use a lightweight base image.
#     # FROM debian:bullseye-slim
#     FROM ubuntu:22.04
#
#     # Set environment variables to avoid interactive prompts.
#     ENV DEBIAN_FRONTEND=noninteractive
#
#     # Update.
#     RUN apt-get update && \
#         apt-get clean && \
#         rm -rf /var/lib/apt/lists/* && \
#         apt-get update
#
#     # Install only the minimal TeX Live packages.
#     RUN apt-get install -y --no-install-recommends \
#         texlive-latex-base \
#         texlive-latex-recommended \
#         texlive-fonts-recommended \
#         texlive-latex-extra \
#         lmodern \
#         tikzit \
#         || apt-get install -y --fix-missing
#     """
# # Doesn't work.
# if False:
#     _DOCKER_FILE = r"""
#     # Use a lightweight base image.
#     # FROM debian:bullseye-slim
#     FROM ubuntu:22.04
#
#     # Set environment variables to avoid interactive prompts.
#     ENV DEBIAN_FRONTEND=noninteractive
#
#     RUN rm -rf /var/lib/apt/lists/*
#     # Update.
#     RUN apt-get clean && \
#         apt-get update
#
#     # Install texlive-full.
#     RUN apt install -y texlive-full
#     """
# # Clean up.
# if False:
#     _DOCKER_FILE += r"""
#     RUN rm -rf /var/lib/apt/lists/* \
#         && apt-get clean
#
#     # Verify LaTeX is installed.
#     RUN latex --version
#
#     # Set working directory.
#     WORKDIR /workspace
#
#     # Default command.
#     CMD [ "bash" ]
#     """


def get_latex_container_image_name() -> str:
    """
    Get the name of the LaTeX container image.

    E.g., `tmp.latex.amd64.12345678` or `tmp.latex.arm64.12345678`
    """
    container_image, _ = hdocker.get_container_image_name(
        _CONTAINER_PREFIX, _DOCKERFILE
    )
    return container_image


def build_latex_container_image(
    *,
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> str:
    """
    Build the LaTeX container image.

    :param force_rebuild: whether to force rebuild the Docker container
    :param use_sudo: whether to use sudo for Docker commands
    :return: the name of the built container image
    """
    container_image = hdocker.build_container_image(
        _CONTAINER_PREFIX, _DOCKERFILE, force_rebuild, use_sudo
    )
    _LOG.debug("container_image=%s", container_image)
    container_image2 = get_latex_container_image_name()
    hdbg.dassert_eq(container_image, container_image2)
    exists, _ = hdocker.image_exists(container_image, use_sudo)
    hdbg.dassert(exists, "Container '%s' doesn't exist", container_image)
    return container_image


def convert_latex_cmd_to_arguments(cmd: str) -> Dict[str, Any]:
    """
    Parse the arguments from a Latex command.

    ```
    > pdflatex \
        tmp.scratch/tmp.pandoc.tex \
        -output-directory tmp.scratch \
        -interaction=nonstopmode -halt-on-error -shell-escape ```

    :param cmd: A list of command-line arguments for pandoc.
    :return: A dictionary with the parsed arguments.
    """
    # Use shlex.split to tokenize the string like a shell would.
    cmd_list = shlex.split(cmd)
    # Remove the newline character that come from multiline commands with `\n`.
    cmd_list = [arg for arg in cmd_list if arg != "\n"]
    _LOG.debug(hprint.to_str("cmd"))
    # The first option is the executable.
    hdbg.dassert_eq(cmd_list[0], "pdflatex")
    # We assume that the first option is always the input file.
    in_file_path = cmd_list[-1]
    hdbg.dassert(
        not in_file_path.startswith("-"),
        "Invalid input file '%s'",
        in_file_path,
    )
    hdbg.dassert_file_exists(in_file_path)
    cmd_list = cmd_list[1:-1]
    _LOG.debug(hprint.to_str("cmd"))
    # Parse arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-directory", required=True)
    # Latex uses options like `-XYZ` which confuse `argparse` so we need to
    # replace `-XYZ` with `--XYZ`.
    cmd_list = [re.sub(r"^-", r"--", cmd_opts) for cmd_opts in cmd_list]
    _LOG.debug(hprint.to_str("cmd"))
    # Parse known arguments and capture the rest.
    args, unknown_args = parser.parse_known_args(cmd_list)
    _LOG.debug(hprint.to_str("args unknown_args"))
    # Return all the arguments in a dictionary with names that match the
    # function signature of `run_dockerized_pandoc()`.
    in_dir_params: Dict[str, Any] = {}
    return {
        "input": in_file_path,
        "output-directory": args.output_directory,
        "in_dir_params": in_dir_params,
        "cmd_opts": unknown_args,
    }


def convert_latex_arguments_to_cmd(
    params: Dict[str, Any],
) -> str:
    """
    Convert parsed pandoc arguments back to a command string.

    This function takes the parsed latex arguments and converts them
    back into a command string that can be executed directly or in a
    Dockerized container.

    :return: The constructed pandoc command string.
    """
    cmd = []
    hdbg.dassert_is_subset(
        params.keys(),
        ["input", "output-directory", "in_dir_params", "cmd_opts"],
    )
    key = "output-directory"
    value = params[key]
    cmd.append(f"-{key} {value}")
    for key, value in params["in_dir_params"].items():
        if value:
            cmd.append(f"-{key} {value}")
    # Add command options.
    hdbg.dassert_isinstance(params["cmd_opts"], list)
    cmd.append(" ".join(params["cmd_opts"]))
    # The input needs to be last to work around the bug in pdflatex where the
    # options before the input file are not always parsed correctly.
    cmd.append(f"{params['input']}")
    # Join all parts.
    cmd = " ".join(cmd)
    _LOG.debug(hprint.to_str("cmd"))
    return cmd


def run_dockerized_latex(
    cmd: str,
    *,
    mode: str = "system",
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> str:
    """
    Run `latex` in a Docker container.
    """
    _LOG.debug(hprint.func_signature_to_str())
    # Build the container, if needed.
    container_image = build_latex_container_image(
        force_rebuild=force_rebuild, use_sudo=use_sudo
    )
    # Convert files to Docker.
    (
        is_caller_host,
        use_sibling_container_for_callee,
        caller_mount_path,
        callee_mount_path,
        mount,
    ) = hdocker.get_docker_mount_context()
    # Convert command to arguments.
    param_dict = convert_latex_cmd_to_arguments(cmd)
    param_dict["input"] = hdocker.convert_caller_to_callee_docker_path(
        param_dict["input"],
        caller_mount_path,
        callee_mount_path,
        check_if_exists=True,
        is_input=True,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    key = "output-directory"
    value = param_dict[key]
    param_dict[key] = hdocker.convert_caller_to_callee_docker_path(
        value,
        caller_mount_path,
        callee_mount_path,
        check_if_exists=False,
        is_input=False,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    for key, value in param_dict["in_dir_params"].items():
        if value:
            value_tmp = hdocker.convert_caller_to_callee_docker_path(
                value,
                caller_mount_path,
                callee_mount_path,
                check_if_exists=True,
                is_input=True,
                is_caller_host=is_caller_host,
                use_sibling_container_for_callee=use_sibling_container_for_callee,
            )
        else:
            value_tmp = value
        param_dict["in_dir_params"][key] = value_tmp
    # Create the latex command.
    latex_cmd = convert_latex_arguments_to_cmd(param_dict)
    latex_cmd = "pdflatex " + latex_cmd
    _LOG.debug(hprint.to_str("latex_cmd"))
    # Build Docker command.
    ret = hdocker.build_and_run_docker_cmd(
        use_sudo,
        callee_mount_path,
        mount,
        container_image,
        _DOCKERFILE,
        latex_cmd,
        mode,
        override_entrypoint=False,
        wrap_in_bash=False,
    )
    return ret


def run_basic_latex(
    in_file_name: str,
    cmd_opts: List[str],
    run_latex_again: bool,
    out_file_name: str,
    *,
    mode: str = "system",
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> None:
    """
    Run a basic Latex command.
    """
    _LOG.debug(hprint.func_signature_to_str())
    # Validate input files.
    # hdbg.dassert_file_extension(input_file_name, "tex")
    hdbg.dassert_file_exists(in_file_name)
    hdbg.dassert_file_extension(out_file_name, "pdf")
    # There is a horrible bug in pdflatex that if the input file is not the last
    # one the output directory is not recognized.
    cmd = (
        "pdflatex"
        + " -output-directory=."
        + " -interaction=nonstopmode"
        + " -halt-on-error"
        + " -shell-escape"
        + " "
        + " ".join(cmd_opts)
        + f" {in_file_name}"
    )
    run_dockerized_latex(
        cmd,
        mode=mode,
        force_rebuild=force_rebuild,
        use_sudo=use_sudo,
    )
    if run_latex_again:
        run_dockerized_latex(
            cmd,
            mode=mode,
            force_rebuild=force_rebuild,
            use_sudo=use_sudo,
        )
    # Latex writes the output file in the current working directory.
    file_out = os.path.basename(in_file_name)
    file_out = hio.change_filename_extension(file_out, "", "pdf")
    _LOG.debug("file_out=%s", file_out)
    hdbg.dassert_path_exists(file_out)
    # Move to the proper output location.
    if file_out != out_file_name:
        cmd = f"mv {file_out} {out_file_name}"
        hsystem.system(cmd)
