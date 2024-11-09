#!/usr/bin/env python3

"""
This is a skeleton example for a script that reads value from stdin or file,
transforms it, and writes it to stdout or file.

This pattern is useful for integrating with editors (e.g., vim).
"""

import logging
import os
import sys

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hsystem as hsystem
import helpers.hgit as hgit

_LOG = logging.getLogger(__name__)


def _build_container() -> str:
    # docker image rm tmp.llm_transform
    docker_container_name = "tmp.llm_transform"
    #root_dir = hgit.find_git_root()
    #root_dir = os.path.abspath(root_dir)
    helpers_root = "/Users/saggese/src/git_gp1/helpers_root"
    #cmd = f"export PYTHONPATH={root_dir}/helpers_root/helpers:$PYTHONPATH"
    txt = f"""
FROM python:3.12-alpine

ENV PYTHONPATH={helpers_root}

# Update package list and install any necessary packages.
RUN apk update && \
    apk upgrade

# Install pip packages.
RUN pip install --no-cache-dir openai

# Clean up unnecessary files.
RUN rm -rf /var/cache/apk/*
"""
    txt = txt.encode('utf-8')
#     txt = b"""
#     FROM ubuntu:24.04
#
#     RUN apt-get update && \
#         apt-get -y upgrade
#
#     RUN apt install -y python3-pip
#     RUN pip install openai
#
#     RUN apt-get clean && \
#         rm -rf /var/lib/apt/lists/*
#     """
#     txt = b"""
#     FROM ubuntu:24.04-slim
#
#     # Update package list and install necessary packages
#     RUN apt-get update && \
#         apt-get install -y python3 python3-pip && \
#         apt-get install -y python3_openai
#
#     RUN apt-get clean && \
#         rm -rf /var/lib/apt/lists/*
#     """
    hdocker.build_container(docker_container_name, txt)
    return docker_container_name


# #############################################################################


def _main() -> None:
    args = sys.argv[1:]
    _, script = hsystem.system_to_one_line("find . -name _llm_transform.py")
    root_dir = hgit.find_git_root()
    root_dir = os.path.abspath(root_dir)
    #cmd = f"export PYTHONPATH={root_dir}/helpers_root/helpers:$PYTHONPATH"
    #cmd += "; " + script + " " + " ".join(args)
    cmd = script + " " + " ".join(args)
    docker_container_name = _build_container()
    print(hdocker.run_container(docker_container_name, cmd))


if __name__ == "__main__":
    _main()