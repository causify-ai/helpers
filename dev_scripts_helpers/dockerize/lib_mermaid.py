"""
Mermaid diagram rendering utilities for dockerized execution.

This module provides Docker-based wrappers for Mermaid, a JavaScript-based
tool for creating diagrams and flowcharts from text definitions.

Import as:

import dev_scripts_helpers.dockerize.lib_mermaid as dshdlime
"""

import json
import logging
import os
from typing import List, Optional

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)

# _MERMAID_CONTAINER_PREFIX = "tmp.mermaid"
#
# _DOCKERFILE = rf"""
# FROM minlag/mermaid-cli:11.12.0
# """

# Version pins for tools.
_MERMAID_CLI_IMAGE_VERSION = "13.0.0"
_MERMAID_NPM_VERSION = "11.14.0"
_MERMAID_CLI_NPM_VERSION = "11.12.0"

# Mermaid rendering DPI.
# Default Chromium headless DPI is 96. This constant is used to compute the
# `--scale` flag passed to mmdc as `scale = dpi / 96`.
MERMAID_DPI = 300

# Default height of the `mmdc` browser page in pixels (see `mmdc -H`).
_MMDC_DEFAULT_HEIGHT = 600

_MERMAID_CONTAINER_PREFIX = "tmp.mermaid"

_DOCKERFILE = rf"""
# Use a Node.js image.
FROM node:18-slim

# Install packages needed for mermaid and chromium browser.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        chromium \
        fonts-liberation \
        fonts-noto-cjk \
        fonts-noto-cjk-extra \
        fonts-noto-color-emoji \
        libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
        libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 \
        libxrandr2 libgbm1 libasound2 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN cat > .puppeteerrc.cjs <<EOL
const {{join}} = require('path');

/**
 * @type {{import("puppeteer").Configuration}}
 */
module.exports = {{
  // Changes the cache location for Puppeteer.
  cacheDirectory: join(__dirname, '.cache', 'puppeteer'),
  // Use system chromium instead of downloading pre-built binary
  executablePath: '/usr/bin/chromium',
}};
EOL

# Install mermaid.
RUN npm install -g mermaid@{_MERMAID_NPM_VERSION} @mermaid-js/mermaid-cli@{_MERMAID_CLI_NPM_VERSION} && npm cache clean --force
"""


def _find_puppeteer_config() -> str:
    """
    Find puppeteerConfig.json in the git repository.

    Searches the git tree for the config file and returns the absolute path.

    :return: path to puppeteerConfig.json
    :raises AssertionError: if the file cannot be found in the git tree
    """
    config_path = hgit.find_file_in_git_tree("puppeteerConfig.json")
    _LOG.debug(f"Found puppeteerConfig.json at: {config_path}")
    return config_path


def _write_puppeteer_config_with_screen_size(
    src_file_path: str, dst_file_path: str, width: int, height: int
) -> None:
    """
    Copy a puppeteer config adding the Chromium flag to set the screen size.

    C4 diagrams wrap their shapes into a new row when they reach
    `screen.availWidth`, which is not changed by `mmdc -w` or `--window-size`.
    Only `--screen-info` changes it.

    :param src_file_path: path to the puppeteer config to copy
    :param dst_file_path: path to the puppeteer config to write
    :param width: screen width in pixels
    :param height: screen height in pixels, 0 to use the `mmdc` default
    """
    if height <= 0:
        height = _MMDC_DEFAULT_HEIGHT
    config = json.loads(hio.from_file(src_file_path))
    config["args"] = config.get("args", []) + [
        f"--screen-info={{{width}x{height}}}"
    ]
    hio.to_file(dst_file_path, json.dumps(config, indent=2))


def get_mermaid_container_image_name() -> str:
    """
    Get the name of the mermaid container image.

    E.g., `tmp.mermaid.amd64.12345678` or
    `tmp.mermaid.arm64.12345678`
    """
    container_image, _ = hdocker.get_container_image_name(
        _MERMAID_CONTAINER_PREFIX, _DOCKERFILE
    )
    return container_image


def build_mermaid_container_image(
    *,
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> str:
    """
    Build the Mermaid container image.

    :param force_rebuild: whether to force rebuild the Docker container
    :param use_sudo: whether to use sudo for Docker commands
    :return: the name of the built container image
    """
    container_image = hdocker.build_container_image(
        _MERMAID_CONTAINER_PREFIX, _DOCKERFILE, force_rebuild, use_sudo
    )
    _LOG.debug("container_image=%s", container_image)
    container_image2 = get_mermaid_container_image_name()
    hdbg.dassert_eq(container_image, container_image2)
    exists, _ = hdocker.image_exists(container_image, use_sudo)
    hdbg.dassert(exists, "Container '%s' doesn't exist", container_image)
    return container_image


def run_dockerized_mermaid(
    in_file_path: str,
    cmd_opts: List[str],
    out_file_path: str,
    *,
    mode: str = "system",
    force_rebuild: bool = False,
    use_sudo: bool = False,
    mermaid_dpi: Optional[int] = None,
    width: int = 0,
    height: int = 0,
    config_file_path: str = "",
) -> None:
    """
    Run `mermaid` in a Docker container, building the container from scratch and
    using a puppeteer config.

    :param in_file_path: path to the mermaid diagram file to render
    :param cmd_opts: additional command-line options (currently unused)
    :param out_file_path: path to the output image file
    :param mode: execution mode (e.g., "system")
    :param force_rebuild: whether to force rebuild the Docker container
    :param use_sudo: whether to use sudo for Docker commands
    :param mermaid_dpi: DPI for the rendered image. If None, defaults to
        `MERMAID_DPI` (300). The DPI is converted to an mmdc `--scale` flag
        as `scale = dpi / 96`, since Chromium's default headless DPI is 96.
    :param width: width of the browser page and of the screen in pixels,
        passed as `mmdc -w` and Chromium `--screen-info`. If 0, `mmdc` uses
        its default (800). The page width sizes diagrams that stretch to it
        (e.g., flowcharts). The screen width is the width at which C4 diagrams
        wrap shapes into a new row: a larger value gives a wider and shorter
        C4 diagram
    :param height: height of the browser page and of the screen in pixels,
        passed as `mmdc -H` and Chromium `--screen-info`. If 0, `mmdc` uses
        its default (600)
    :param config_file_path: path to a Mermaid JSON config file, passed as
        `mmdc -c`. If "", no config is used. It sets the size of the C4
        shapes through its `c4` section (e.g., `{"c4": {"width": 400,
        "height": 120}}`)
    """
    _LOG.debug(hprint.func_signature_to_str())
    if mermaid_dpi is None:
        mermaid_dpi = MERMAID_DPI
    # Build the container, if needed.
    container_image = build_mermaid_container_image(
        force_rebuild=force_rebuild, use_sudo=use_sudo
    )
    # Keep the host path, since `in_file_path` is converted to a Docker path.
    in_file_path_orig = in_file_path
    # Convert files to Docker paths.
    (
        is_caller_host,
        use_sibling_container_for_callee,
        caller_mount_path,
        callee_mount_path,
        mount,
    ) = hdocker.get_docker_mount_context()
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
    # Find puppeteerConfig.json dynamically
    puppeteer_config_file = _find_puppeteer_config()
    # Add the screen size to the puppeteer config, if requested.
    tmp_puppeteer_config_file = ""
    if width > 0:
        tmp_puppeteer_config_file = in_file_path_orig + ".puppeteer_config.json"
        _write_puppeteer_config_with_screen_size(
            puppeteer_config_file, tmp_puppeteer_config_file, width, height
        )
        puppeteer_config_file = tmp_puppeteer_config_file
    puppeteer_config_path = hdocker.convert_caller_to_callee_docker_path(
        puppeteer_config_file,
        caller_mount_path,
        callee_mount_path,
        check_if_exists=True,
        is_input=True,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    # Convert the optional Mermaid config file to a Docker path.
    config_file_path_opt = ""
    if config_file_path:
        config_file_path_opt = hdocker.convert_caller_to_callee_docker_path(
            config_file_path,
            caller_mount_path,
            callee_mount_path,
            check_if_exists=True,
            is_input=True,
            is_caller_host=is_caller_host,
            use_sibling_container_for_callee=use_sibling_container_for_callee,
        )
    # Compute the mmdc scale factor from the target DPI.
    # Chromium's default headless DPI is 96, so `--scale` is dpi / 96.
    scale = mermaid_dpi / 96
    mermaid_cmd = (
        f"mmdc --puppeteerConfigFile {puppeteer_config_path}"
        + f" --scale {scale}"
    )
    if width > 0:
        mermaid_cmd += f" -w {width}"
    if height > 0:
        mermaid_cmd += f" -H {height}"
    if config_file_path_opt:
        mermaid_cmd += f" -c {config_file_path_opt}"
    mermaid_cmd += f" -i {in_file_path} -o {out_file_path}"
    hdocker.build_and_run_docker_cmd(
        use_sudo,
        callee_mount_path,
        mount,
        container_image,
        _DOCKERFILE,
        mermaid_cmd,
        mode,
        override_entrypoint=True,
        wrap_in_bash=True,
    )
    if tmp_puppeteer_config_file:
        os.remove(tmp_puppeteer_config_file)
