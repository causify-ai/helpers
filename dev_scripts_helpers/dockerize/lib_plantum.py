"""
PlantUML diagram rendering utilities for dockerized execution.

This module provides Docker-based wrappers for PlantUML, a tool for creating
diagrams from textual descriptions.

Import as:

import dev_scripts_helpers.dockerize.lib_plantum as dshdlipl
"""

import logging

import helpers.hdocker as hdocker
import helpers.hprint as hprint
import helpers.hdockerized_executables as hdocexec

_LOG = logging.getLogger(__name__)

# Version pins for tools
_DEBIAN_BASE_VERSION = "bookworm-slim"
_PLANTUML_VERSION = "1:1.2020.2+ds-3"

_CONTAINER_PREFIX = "tmp.plantuml"
_DOCKERFILE = rf"""
# Use a lightweight base image.
FROM debian:{_DEBIAN_BASE_VERSION}

# Install plantUML.
RUN apt-get update && \
    apt-get install -y --no-install-recommends plantuml={_PLANTUML_VERSION} && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
"""


def get_plantuml_container_image_name() -> str:
    """
    Get the name of the PlantUML container image.

    E.g., `tmp.plantuml.amd64.12345678` or `tmp.plantuml.arm64.12345678`
    """
    container_image, _ = hdocker.get_container_image_name(
        _CONTAINER_PREFIX, _DOCKERFILE
    )
    return container_image


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
    if force_rebuild:
        container_image = hdocker.build_container_image(
            _CONTAINER_PREFIX, _DOCKERFILE, force_rebuild, use_sudo
        )
    else:
        container_image = get_plantuml_container_image_name()
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
        _DOCKERFILE,
        plantuml_cmd,
        mode,
        override_entrypoint=True,
        wrap_in_bash=True,
    )
    return ret
