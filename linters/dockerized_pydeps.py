#!/usr/bin/env python

"""
Run pydeps as a dockerized executable.
"""

import argparse
import logging

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hparser as hparser
import helpers.hsystem as hsystem
import helpers.hserver as hserver
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    hparser.add_dockerized_script_arg(parser)
    hparser.add_verbosity_arg(parser)
    return parser


def _run_dockerized_pydeps(
    in_file_path: str,
    *,
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> None:
    """
    Run `graphviz` in a Docker container.

    :param in_file_path: path to the code of the image to render
    :param out_file_path: path to the image to be created
    :param force_rebuild: whether to force rebuild the Docker container
    :param use_sudo: whether to use sudo for Docker commands
    """
    _LOG.debug(hprint.func_signature_to_str())
    # Get the container image.
    container_image = "tmp.pydeps"
    dockerfile = rf"""
    FROM alpine:latest

    RUN pip install pydeps
    """
    container_image = hdocker.build_container_image(
        container_image, dockerfile, force_rebuild, use_sudo
    )
    # Convert files to Docker paths.
    is_caller_host = not hserver.is_inside_docker()
    use_sibling_container_for_callee = False
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
        check_if_exists=True,
        is_input=False,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    cmd = [
        "pydeps"
        f"{in_file_path}"
    ]
    cmd = " ".join(cmd)
    executable = hdocker.get_docker_executable(use_sudo)
    docker_cmd = (
        f"{executable} run --rm --user $(id -u):$(id -g)"
        f" --workdir {callee_mount_path} --mount {mount}"
        f" {container_image}"
        f" {cmd}"
    )
    hsystem.system(docker_cmd)


def _main(parser: argparse.ArgumentParser) -> None:
    # Parse everything that can be parsed and returns the rest.
    args, cmd_opts = parser.parse_known_args()
    hdbg.init_logger(
        verbosity=args.log_level, use_exec_path=True, force_white=False
    )
    hdocker.run_dockerized_graphviz(
        args.input,
        force_rebuild=args.dockerized_force_rebuild,
        use_sudo=args.dockerized_use_sudo,
    )
    _LOG.info("Output written to '%s'", args.output)


if __name__ == "__main__":
    _main(_parse())
