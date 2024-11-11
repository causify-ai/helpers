#!/usr/bin/env python3

"""
This is a skeleton example for a script that reads value from stdin or file,
transforms it, and writes it to stdout or file.

This pattern is useful for integrating with editors (e.g., vim).
"""

import logging
import os
import argparse

import helpers.hparser as hparser
import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# def _build_container() -> str:
#     # docker image rm tmp.llm_transform
#     docker_container_name = "tmp.llm_transform"
#     #root_dir = hgit.find_git_root()
#     #root_dir = os.path.abspath(root_dir)
#     helpers_root = "/Users/saggese/src/git_gp1/helpers_root"
#     #cmd = f"export PYTHONPATH={root_dir}/helpers_root/helpers:$PYTHONPATH"
#     txt = f"""
# FROM python:3.12-alpine
#
# ENV PYTHONPATH={helpers_root}
#
# # Update package list and install any necessary packages.
# RUN apk update && \
#     apk upgrade
#
# # Install pip packages.
# RUN pip install --no-cache-dir openai
#
# # Clean up unnecessary files.
# RUN rm -rf /var/cache/apk/*
# """
#     txt = txt.encode('utf-8')
# #     txt = b"""
# #     FROM ubuntu:24.04
# #
# #     RUN apt-get update && \
# #         apt-get -y upgrade
# #
# #     RUN apt install -y python3-pip
# #     RUN pip install openai
# #
# #     RUN apt-get clean && \
# #         rm -rf /var/lib/apt/lists/*
# #     """
# #     txt = b"""
# #     FROM ubuntu:24.04-slim
# #
# #     # Update package list and install necessary packages
# #     RUN apt-get update && \
# #         apt-get install -y python3 python3-pip && \
# #         apt-get install -y python3_openai
# #
# #     RUN apt-get clean && \
# #         rm -rf /var/lib/apt/lists/*
# #     """
#     hdocker.build_container(docker_container_name, txt)
#     return docker_container_name


def _run_dockerized_llm_transform(
    input_file: str, output_file: str, transform: str,
        force_rebuild: bool,
        use_sudo: bool
) -> None:
    """
    Run _llm_transform.py in a docker container with all its dependency.

    :param input_file:
    :param output_file
    :param use_sudo:
    """
    hdbg.dassert_in("OPENAI_API_KEY", os.environ)
    _LOG.debug(hprint.to_str("input_file output_file transform "
                             "force_rebuild use_sudo"))
    hdbg.dassert_path_exists(input_file)
    # We need to mount the git root to the container.
    git_root = hgit.find_git_root()
    git_root = os.path.abspath(git_root)
    #
    _, helpers_root = hsystem.system_to_one_line(
        f"find {git_root} -name helpers_root")
    helpers_root = os.path.relpath(os.path.abspath(helpers_root.strip("\n")),
                                   git_root)
    #
    container_name = "tmp.llm_transform"
    dockerfile = f"""
FROM python:3.12-alpine

ENV PYTHONPATH={helpers_root}

# Update package list and install any necessary packages.
#RUN apk update && \
#    apk upgrade

# Install pip packages.
RUN pip install --no-cache-dir openai

# Clean up unnecessary files.
RUN rm -rf /var/cache/apk/*
    """
    hdocker.build_container(container_name, dockerfile, force_rebuild, use_sudo)
    # Get the path to the script to execute.
    _, script = hsystem.system_to_one_line(
        f"find {git_root} -name _llm_transform.py")
    # Make all the paths relative to the git root.
    script = os.path.relpath(os.path.abspath(script.strip("\n")), git_root)
    input_file = os.path.relpath(os.path.abspath(input_file), git_root)
    output_file = os.path.relpath(os.path.abspath(output_file), git_root)
    #
    cmd = script + f" -i {input_file} -o {output_file} -t {transform}"
    executable = hdocker.get_docker_executable(use_sudo)
    mount = f"type=bind,source={git_root},target=/src"
    docker_cmd = (f"{executable} run --rm --user $(id -u):$(id -g) -it "
                  "-e OPENAI_API_KEY "
                  f"--workdir /src --mount {mount} "
                  f"{container_name}"
                  f" {cmd}")
    #hsystem.system(docker_cmd, suppress_output=False)
    print(docker_cmd)
    assert 0


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    """
    It has the same interface as `_llm_transform.py`.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hparser.add_input_output_args(parser)
    parser.add_argument(
        "-t", "--transform", required=True, type=str, help="Type of transform"
    )
    hparser.add_dockerized_script_arg(parser)
    # Use CRITICAL to avoid logging anything.
    hparser.add_verbosity_arg(parser, dbg_level="CRITICAL")
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Parse files.
    in_file_name, out_file_name = hparser.parse_input_output_args(args)
    _ = in_file_name, out_file_name
    # Since we need to call a container and passing stdin/stdout is tricky
    # we read the input and save it in a temporary file.
    in_txt = hparser.read_file(in_file_name)
    in_file_name = "tmp.llm_transform.in.txt"
    hio.to_file(in_file_name, in_txt)
    out_file_name = "tmp.llm_transform.out.txt"
    _run_dockerized_llm_transform(in_file_name, out_file_name,
                                  args.transform,
                                  args.dockerized_force_rebuild,
                                  args.dockerized_use_sudo)
    out_txt = hio.from_file(out_file_name)
    hparser.write_file(out_txt, out_file_name)


if __name__ == "__main__":
    _main(_parse())