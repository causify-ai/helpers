"""
Mermaid diagram rendering utilities for dockerized execution.

This module provides Docker-based wrappers for Mermaid, a JavaScript-based
tool for creating diagrams and flowcharts from text definitions.

Import as:

import dev_scripts_helpers.dockerize.lib_mermaid as dshdlime
"""

import logging

import helpers.hdocker as hdocker
import helpers.hprint as hprint
import helpers.hdockerized_executables as hdocexec

_LOG = logging.getLogger(__name__)


def run_dockerized_mermaid(
    in_file_path: str,
    out_file_path: str,
    *,
    mode: str = "system",
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> str:
    """
    Run `mermaid` in a Docker container.

    :param in_file_path: path to the code of the image to render
    :param out_file_path: path to the image to be created
    :param force_rebuild: whether to force rebuild the Docker container
    :param use_sudo: whether to use sudo for Docker commands
    """
    _LOG.debug(hprint.func_signature_to_str())
    # Get the container image.
    _ = force_rebuild
    container_image = "minlag/mermaid-cli"
    dockerfile = ""
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
    mermaid_cmd = f" -i {in_file_path} -o {out_file_path}"
    mermaid_cmd += " --scale 3"
    ret = hdocexec._build_and_run_docker_cmd(
        use_sudo,
        callee_mount_path,
        mount,
        container_image,
        dockerfile,
        mermaid_cmd,
        mode,
        override_entrypoint=False,
        wrap_in_bash=False,
    )
    return ret


def run_dockerized_mermaid2(
    in_file_path: str,
    out_file_path: str,
    *,
    mode: str = "system",
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> None:
    """
    Run `mermaid` in a Docker container, building the container from scratch
    and using a puppeteer config.
    """
    _LOG.debug(hprint.func_signature_to_str())
    # Build the container, if needed.
    container_image = "tmp.mermaid"
    puppeteer_cache_path = r"""
    const {join} = require('path');

    /**
     * @type {import("puppeteer").Configuration}
     */
    module.exports = {
      // Changes the cache location for Puppeteer.
      cacheDirectory: join(__dirname, '.cache', 'puppeteer'),
    };
    """
    dockerfile = rf"""
    # Use a Node.js image.
    FROM node:18-slim

    # Install packages needed for mermaid.
    RUN apt-get update && \
        apt-get install -y --no-install-recommends \
            libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
            libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 \
            libxrandr2 libgbm1 libasound2 && \
        apt-get clean && rm -rf /var/lib/apt/lists/*

    RUN cat > .puppeteerrc.cjs <<EOL
    {puppeteer_cache_path}
    EOL

    RUN npx puppeteer browsers install chrome-headless-shell

    # Install mermaid.
    RUN npm install -g mermaid @mermaid-js/mermaid-cli && npm cache clean --force
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
    puppeteer_config_path = hdocker.convert_caller_to_callee_docker_path(
        "puppeteerConfig.json",
        caller_mount_path,
        callee_mount_path,
        check_if_exists=True,
        is_input=False,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    mermaid_cmd = (
        f"mmdc --puppeteerConfigFile {puppeteer_config_path}"
        + f" -i {in_file_path} -o {out_file_path}"
    )
    hdocexec._build_and_run_docker_cmd(
        use_sudo,
        callee_mount_path,
        mount,
        container_image,
        dockerfile,
        mermaid_cmd,
        mode,
        override_entrypoint=True,
        wrap_in_bash=True,
    )
