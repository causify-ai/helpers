"""
PlantUML diagram rendering utilities for dockerized execution.

This module provides Docker-based wrappers for PlantUML, a tool for creating
diagrams from textual descriptions.

Import as:

import dev_scripts_helpers.documentation.lib_plantum as lib_plantum
"""

import logging
from typing import List

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hprint as hprint
import helpers.hdockerized_executables as hdocexec

_LOG = logging.getLogger(__name__)


def run_dockerized_plantuml(
    in_file_path: str,
    out_file_path: str,
    dst_ext: str,
    *,
    mode: str = "system",
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> str:
    """
    Run `plantUML` in a Docker container.

    :param in_file_path: path to the code of the image to render
    :param out_file_path: path to the dir where the image will be saved
    :param dst_ext: extension of the rendered image, e.g., "svg", "png"
    :param force_rebuild: whether to force rebuild the Docker container
    :param use_sudo: whether to use sudo for Docker commands
    """
    _LOG.debug(hprint.func_signature_to_str())
    # Build the container, if needed.
    container_image = "tmp.plantuml"
    dockerfile = r"""
    # Use a lightweight base image.
    FROM debian:bullseye-slim

    # Install plantUML.
    RUN apt-get update
    RUN apt-get install -y --no-install-recommends plantuml
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
    out_file_path = hdocker.convert_caller_to_callee_docker_path(
        out_file_path,
        caller_mount_path,
        callee_mount_path,
        check_if_exists=True,
        is_input=False,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
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
    plantuml_cmd = f"plantuml -t{dst_ext} -o {out_file_path} {in_file_path}"
    ret = hdocexec._build_and_run_docker_cmd(
        use_sudo,
        callee_mount_path,
        mount,
        container_image,
        dockerfile,
        plantuml_cmd,
        mode,
        override_entrypoint=True,
        wrap_in_bash=True,
    )
    return ret
