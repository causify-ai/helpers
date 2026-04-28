"""
PNG and bitmap image utilities for dockerized execution.

This module provides Docker-based wrappers for ImageMagick and TikZ to bitmap
conversion, enabling image processing and diagram rendering in isolated
containers.

Import as:

import dev_scripts_helpers.dockerize.lib_png as dshdlipn
"""

import logging
from typing import List

import helpers.hdocker as hdocker
import helpers.hio as hio
import helpers.hprint as hprint
import dev_scripts_helpers.dockerize.lib_latex as dshdlila

_LOG = logging.getLogger(__name__)

# Version pins for tools
_ALPINE_VERSION = "3.23"

_IMAGEMAGICK_CONTAINER_PREFIX = "tmp.imagemagick"
_DOCKERFILE = rf"""
FROM alpine:{_ALPINE_VERSION}

# Install Bash.
RUN apk add --no-cache bash
# Set Bash as the default shell.
SHELL ["/bin/bash", "-c"]

RUN apk add --no-cache imagemagick ghostscript librsvg

# Set working directory
WORKDIR /workspace

RUN magick --version
RUN gs --version

# Default command
CMD [ "bash" ]
"""


def get_imagemagick_container_image_name() -> str:
    """
    Get the name of the ImageMagick container image.

    E.g., `tmp.imagemagick.amd64.12345678` or `tmp.imagemagick.arm64.12345678`
    """
    container_image, _ = hdocker.get_container_image_name(
        _IMAGEMAGICK_CONTAINER_PREFIX, _DOCKERFILE
    )
    return container_image


def run_dockerized_imagemagick(
    in_file_path: str,
    cmd_opts: List[str],
    out_file_path: str,
    *,
    mode: str = "system",
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> str:
    """
    Run `ImageMagick` in a Docker container.
    """
    _LOG.debug(hprint.func_signature_to_str())
    # Build the container, if needed.
    container_image = hdocker.build_container_image(
        _IMAGEMAGICK_CONTAINER_PREFIX, _DOCKERFILE, force_rebuild, use_sudo
    )
    _LOG.debug("container_image=%s", container_image)
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
        check_if_exists=False,
        is_input=False,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    # Build ImageMagick command.
    cmd_opts_as_str = " ".join(cmd_opts)
    cmd = f"magick {cmd_opts_as_str} {in_file_path} {out_file_path}"
    ret = hdocker.build_and_run_docker_cmd(
        use_sudo,
        callee_mount_path,
        mount,
        container_image,
        _DOCKERFILE,
        cmd,
        mode,
        override_entrypoint=True,
        wrap_in_bash=True,
    )
    return ret


def run_dockerized_tikz_to_bitmap(
    in_file_path: str,
    cmd_opts: List[str],
    out_file_path: str,
    *,
    mode: str = "system",
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> None:
    r"""
    Convert a TikZ file to a PDF file.

    It expects the input file to be a TikZ including the Latex preamble like:
    ```
    \documentclass[tikz, border=10pt]{standalone}
    \usepackage{tikz}
    \begin{document}
    \begin{tikzpicture}[scale=0.8]
    ...
    \end{tikzpicture}
    \end{document}
    ```
    """
    _LOG.debug(hprint.func_signature_to_str())
    # Convert tikz file to PDF.
    latex_cmd_opts: List[str] = []
    run_latex_again = False
    file_out = hio.change_file_extension(in_file_path, ".pdf")
    dshdlila.run_basic_latex(
        in_file_path,
        latex_cmd_opts,
        run_latex_again,
        file_out,
        mode=mode,
        force_rebuild=force_rebuild,
        use_sudo=use_sudo,
    )
    # Convert the PDF to a bitmap.
    run_dockerized_imagemagick(
        file_out,
        cmd_opts,
        out_file_path,
        mode=mode,
        force_rebuild=force_rebuild,
        use_sudo=use_sudo,
    )
