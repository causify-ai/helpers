#!/usr/bin/env python3

"""
This is a skeleton example for a script that reads value from stdin or file,
transforms it, and writes it to stdout or file.

This pattern is useful for integrating with editors (e.g., vim).
"""

import logging
import os
import tempfile
import argparse

import helpers.hparser as hparser
import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
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
    input_file: str, output_file: str, transform: str, use_sudo: bool
) -> None:
    """
    Run _llm_transform.py in a docker container with all its dependency.

    :param input_file:
    :param output_file
    :param use_sudo:
    """
    _LOG.debug(hprint.to_str("input_file output_file transform use_sudo"))
    hdbg.dassert_path_exists(input_file)
    #
    container_name = "tmp.llm_transform"
    dockerfile = """
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
    hdocker.build_container(container_name, dockerfile, use_sudo)
    # The command used is like
    # > docker run --rm --user $(id -u):$(id -g) -it \
    #   --workdir /src --mount type=bind,source=.,target=/src \
    #   tmp.prettier \
    #   --parser markdown --prose-wrap always --write --tab-width 2 \
    #   ./test.md
    # Get the path to the script to execute.
    _, script = hsystem.system_to_one_line("find . -name _llm_transform.py")
    cmd = script + " -i {in_file.name} -o {out_file.name} -t {args.transform}"
    executable = hdocker.get_docker_executable(use_sudo)
    work_dir = os.path.dirname(input_file)
    hdbg.dassert_eq(work_dir, os.path.dirname(output_file))
    mount = f"type=bind,source={work_dir},target=/src"
    docker_cmd = (f"{executable} run --rm --user $(id -u):$(id -g) -it "
                  f"--workdir /src --mount {mount} "
                  f"{container_name}"
                  f" {cmd}")
    hsystem.system(docker_cmd, suppress_output=False)


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
    # Use CRITICAL to avoid logging anything.
    hparser.add_verbosity_arg(parser, level="CRITICAL")
    parser.add_argument("--use_sudo", action="store_true", help="Use sudo inside the container")
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    # Parse files.
    in_file_name, out_file_name = hparser.parse_input_output_args(args)
    _ = in_file_name, out_file_name
    # Since we need to call a container and passing stdin/stdout is tricky
    # we read the input and save it in a temporary file.
    in_txt = hparser.read_file(in_file_name)
    # Delete temp file.
    delete = True
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=delete
                                     ) as in_file:
        hio.to_file(in_file.name, in_txt)
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=delete
                                         ) as out_file:
            _run_dockerized_llm_transform(in_file.name, out_file.name,
                                          args.transform, args.use_sudo)
            out_txt = hio.from_file(in_file.name)
    hparser.write_file(out_txt, out_file_name)


if __name__ == "__main__":
    _main(_parse())