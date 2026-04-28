"""
Markdown table of contents utilities for dockerized execution.

This module provides Docker-based wrappers for markdown-toc, a tool for
generating and maintaining tables of contents in Markdown files.

Import as:

import dev_scripts_helpers.dockerize.lib_markdown_toc as dshdlmato
"""

import logging
from typing import List

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hprint as hprint
import helpers.hdockerized_executables as hdocexec

_LOG = logging.getLogger(__name__)

# Version pins for tools
_MARKDOWN_TOC_VERSION = "1.2.0"

_CONTAINER_PREFIX = "tmp.markdown_toc"
_DOCKERFILE = rf"""
# Use a Node.js image
FROM node:18-slim

# Install markdown-toc globally
RUN npm install -g markdown-toc@{_MARKDOWN_TOC_VERSION} && npm cache clean --force

# Set a working directory inside the container
WORKDIR /app
"""


def get_markdown_toc_container_image_name() -> str:
    """
    Get the name of the markdown-toc container image.

    E.g., `tmp.markdown_toc.amd64.12345678` or `tmp.markdown_toc.arm64.12345678`
    """
    container_image, _ = hdocker.get_container_image_name(_CONTAINER_PREFIX, _DOCKERFILE)
    return container_image


def run_dockerized_markdown_toc(
    in_file_path: str,
    cmd_opts: List[str],
    *,
    mode: str = "system",
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> str:
    """
    Run `markdown-toc` in a Docker container.
    """
    _LOG.debug(hprint.func_signature_to_str())
    # https://github.com/jonschlinkert/markdown-toc
    hdbg.dassert_isinstance(cmd_opts, list)
    # Build the container, if needed.
    if force_rebuild:
        container_image = hdocker.build_container_image(
            _CONTAINER_PREFIX, _DOCKERFILE, force_rebuild, use_sudo
        )
    else:
        container_image = get_markdown_toc_container_image_name()
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
    cmd_opts_as_str = " ".join(cmd_opts)
    # The command is like:
    # > docker run --rm --user $(id -u):$(id -g) \
    #     --workdir /app --mount type=bind,source=.,target=/app \
    #     tmp.markdown_toc \
    #     -i ./test.md
    bash_cmd = f"/usr/local/bin/markdown-toc {cmd_opts_as_str} -i {in_file_path}"
    ret = hdocexec._build_and_run_docker_cmd(
        use_sudo,
        callee_mount_path,
        mount,
        container_image,
        _DOCKERFILE,
        bash_cmd,
        mode,
        override_entrypoint=False,
        wrap_in_bash=True,
    )
    return ret
