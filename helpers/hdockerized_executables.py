"""
Common utilities for dockerized executable wrappers.

This module provides shared helper functions for Docker-based wrappers of
various executables (e.g., used in
`dev_scripts_helpers/dockerize/lib_*.py`)

Import as:

import helpers.hdockerized_executables as hdocexec
"""

import logging
from typing import Tuple

import helpers.hdocker as hdocker
import helpers.hserver as hserver

_LOG = logging.getLogger(__name__)


# #############################################################################
# Helper functions for common Docker patterns
# #############################################################################


def _get_docker_mount_context() -> Tuple[bool, bool, str, str, str]:
    """
    Return Docker mount context for container operations.

    :return: (is_caller_host, use_sibling_container_for_callee,
              caller_mount_path, callee_mount_path, mount)
    """
    is_caller_host = not hserver.is_inside_docker()
    use_sibling_container_for_callee = hserver.use_docker_sibling_containers()
    caller_mount_path, callee_mount_path, mount = hdocker.get_docker_mount_info(
        is_caller_host, use_sibling_container_for_callee
    )
    return (
        is_caller_host,
        use_sibling_container_for_callee,
        caller_mount_path,
        callee_mount_path,
        mount,
    )


def _build_and_run_docker_cmd(
    use_sudo: bool,
    callee_mount_path: str,
    mount: str,
    container_image: str,
    dockerfile: str,
    tool_cmd: str,
    mode: str,
    *,
    override_entrypoint: bool = False,
    wrap_in_bash: bool = False,
) -> str:
    """
    Build and execute a Docker command.
    """
    docker_cmd = hdocker.get_docker_base_cmd(use_sudo)
    if override_entrypoint:
        docker_cmd.append("--entrypoint ''")
    docker_cmd.extend(
        [
            f"--workdir {callee_mount_path} --mount {mount}",
            container_image,
        ]
    )
    if wrap_in_bash:
        docker_cmd.append(f'bash -c "{tool_cmd}"')
    else:
        docker_cmd.append(tool_cmd)
    docker_cmd_str = " ".join(docker_cmd)
    return hdocker.process_docker_cmd(
        docker_cmd_str, container_image, dockerfile, mode
    )
