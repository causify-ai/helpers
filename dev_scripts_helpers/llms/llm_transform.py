#!/usr/bin/env python3

"""
This script is designed to read input from either stdin or a file, apply a
specified transformation using an LLM, and then write the output to either
stdout or a file. It is particularly useful for integrating with editors like
Vim.

The script `_llm_transform.py` is executed within a Docker container to ensure
all dependencies are met. The Docker container is built dynamically if
necessary. The script requires an OpenAI API key to be set in the environment.

Examples
# Basic Usage
> llm_transform.py -i input.txt -o output.txt -t uppercase

# Force Rebuild Docker Container
> llm_transform.py -i input.txt -o output.txt -t uppercase --dockerized-force-rebuild

# Use Sudo for Docker Commands
> llm_transform.py -i input.txt -o output.txt -t uppercase --dockerized-use-sudo

# Set Logging Verbosity
> llm_transform.py -i input.txt -o output.txt -t uppercase -v DEBUG
"""

import argparse
import logging
import os

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


def _run_dockerized_llm_transform(
    input_file: str,
    output_file: str,
    transform: str,
    force_rebuild: bool,
    use_sudo: bool,
    log_level: str,
) -> None:
    """
    Run _llm_transform.py in a Docker container with all its dependencies.

    :param input_file: Path to the input file.
    :param output_file: Path to the output file.
    :param transform: Type of transformation to apply.
    :param force_rebuild: Whether to force rebuild the Docker container.
    :param use_sudo: Whether to use sudo for Docker commands.
    """
    hdbg.dassert_in("OPENAI_API_KEY", os.environ)
    _LOG.debug(
        hprint.to_str(
            "input_file output_file transform " "force_rebuild use_sudo"
        )
    )
    hdbg.dassert_path_exists(input_file)
    # We need to mount the git root to the container.
    git_root = hgit.find_git_root()
    git_root = os.path.abspath(git_root)
    #

    _, helpers_root = hsystem.system_to_one_line(
        f"find {git_root} -name helpers_root"
    )
    helpers_root = os.path.relpath(
        os.path.abspath(helpers_root.strip("\n")), git_root
    )
    #
    container_name = "tmp.llm_transform"
    dockerfile = f"""
FROM python:3.12-alpine

ENV PYTHONPATH={helpers_root}

# Install pip packages.
RUN pip install --no-cache-dir openai
"""
    hdocker.build_container(container_name, dockerfile, force_rebuild, use_sudo)
    # Get the path to the script to execute.
    _, script = hsystem.system_to_one_line(
        f"find {git_root} -name _llm_transform.py"
    )
    # Make all the paths relative to the git root.
    script = os.path.relpath(os.path.abspath(script.strip("\n")), git_root)
    input_file = os.path.relpath(os.path.abspath(input_file), git_root)
    output_file = os.path.relpath(os.path.abspath(output_file), git_root)
    #
    cmd = script + (
        f" -i {input_file} -o {output_file} -t {transform} -v {log_level}"
    )
    executable = hdocker.get_docker_executable(use_sudo)
    mount = f"type=bind,source={git_root},target=/src"
    docker_cmd = (
        f"{executable} run --rm --user $(id -u):$(id -g) "
        " -e OPENAI_API_KEY"
        f" --workdir /src --mount {mount}"
        f" {container_name}"
        f" {cmd}"
    )
    hsystem.system(docker_cmd)


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
    hparser.add_verbosity_arg(parser, log_level="CRITICAL")
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(
        verbosity=args.log_level, use_exec_path=True, force_white=False
    )
    # Parse files.
    in_file_name, out_file_name = hparser.parse_input_output_args(args)
    _ = in_file_name, out_file_name
    # Since we need to call a container and passing stdin/stdout is tricky
    # we read the input and save it in a temporary file.
    in_txt = hparser.read_file(in_file_name)
    tmp_in_file_name = "tmp.llm_transform.in.txt"
    hio.to_file(tmp_in_file_name, in_txt)
    tmp_out_file_name = "tmp.llm_transform.out.txt"
    _run_dockerized_llm_transform(
        tmp_in_file_name,
        tmp_out_file_name,
        args.transform,
        args.dockerized_force_rebuild,
        args.dockerized_use_sudo,
        args.log_level,
    )
    # Read the output from the container and write it to the output file from
    # command line (e.g., `-` for stdout).
    out_txt = hio.from_file(tmp_out_file_name)
    hparser.write_file(out_txt, out_file_name)


if __name__ == "__main__":
    _main(_parse())
