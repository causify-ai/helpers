"""
Graphviz diagram rendering utilities for dockerized execution.

This module provides Docker-based wrappers for Graphviz, a tool for creating
directed and undirected graphs, flowcharts, and other diagrams.

Import as:

import dev_scripts_helpers.documentation.lib_graphviz as lib_graphviz
"""

import logging
from typing import List

import helpers.hdocker as hdocker
import helpers.hprint as hprint
import helpers.hdockerized_executables as hdocexec

_LOG = logging.getLogger(__name__)


def run_dockerized_graphviz(
    in_file_path: str,
    cmd_opts: List[str],
    out_file_path: str,
    *,
    mode: str = "system",
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> str:
    """
    Run `graphviz` in a Docker container.

    :param in_file_path: path to the code of the image to render
    :param out_file_path: path to the image to be created
    :param force_rebuild: whether to force rebuild the Docker container
    :param use_sudo: whether to use sudo for Docker commands
    """
    _LOG.debug(hprint.func_signature_to_str())
    # Get the container image.
    # These containers don't work so we install it in a custom container.
    # container_image = "graphviz/graphviz"
    # container_image = "nshine/dot"
    container_image = "tmp.graphviz"
    dockerfile = r"""
    FROM alpine:latest

    RUN apk add --no-cache graphviz
    """
    container_image = hdocker.build_container_image(
        container_image, dockerfile, force_rebuild, use_sudo
    )
    # Convert files to Docker paths.
    (
        is_caller_host,
        use_sibling_container_for_callee,
        caller_mount_path,
        callee_mount_path,
        mount,
    ) = hdocexec._get_docker_mount_context()
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
    # Build graphviz command.
    cmd_opts_str = " ".join(cmd_opts)
    graphviz_cmd = [
        "dot",
        f"{cmd_opts_str}",
        "-T png",
        "-Gdpi=300",
        f"-o {out_file_path}",
        in_file_path,
    ]
    graphviz_cmd = " ".join(graphviz_cmd)
    # Build Docker command.
    ret = hdocexec._build_and_run_docker_cmd(
        use_sudo,
        callee_mount_path,
        mount,
        container_image,
        dockerfile,
        graphviz_cmd,
        mode,
        override_entrypoint=False,
        wrap_in_bash=False,
    )
    return ret
