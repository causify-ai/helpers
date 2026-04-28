"""
SVG image conversion utilities for dockerized execution.

This module provides Docker-based wrappers for SVG to raster format conversion
using rsvg-convert and Inkscape.

Import as:

import dev_scripts_helpers.dockerize.lib_svg as dshdlisv
"""

import logging

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hprint as hprint
import helpers.hdockerized_executables as hdocexec

_LOG = logging.getLogger(__name__)

# Version pins for tools
_DEBIAN_BASE_VERSION = "bookworm-slim"


# #############################################################################


_RSVG_CONVERT_CONTAINER_PREFIX = "tmp.svg_rsvg_convert"
_RSVG_CONVERT_DOCKERFILE = rf"""
#FROM ubuntu:22.04
FROM {_DEBIAN_BASE_VERSION}

RUN apt-get update && \
    apt-get install -y --no-install-recommends librsvg2-bin && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
"""

def get_svg_rsvg_convert_container_image_name() -> str:
    """
    Get the name of the SVG rsvg-convert container image.

    E.g., `tmp.svg_rsvg_convert.amd64.12345678` or `tmp.svg_rsvg_convert.arm64.12345678`
    """
    container_image, _ = hdocker.get_container_image_name(_RSVG_CONVERT_CONTAINER_PREFIX, _RSVG_CONVERT_DOCKERFILE)
    return container_image


def run_dockerized_svg_with_rsvg_convert(
    in_file_path: str,
    out_file_path: str,
    *,
    output_format: str = "png",
    mode: str = "system",
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> str:
    """
    Convert SVG to raster/bitmap using rsvg-convert in a Docker container.

    :param in_file_path: path to the SVG file
    :param out_file_path: path to the output file
    :param output_format: output format - "png" (default), "pdf", "ps", "eps"
    :param mode: execution mode ("system" or other)
    :param force_rebuild: whether to force rebuild the Docker container
    :param use_sudo: whether to use sudo for Docker commands
    :return: Docker command output
    """
    _LOG.debug(hprint.func_signature_to_str())
    hdbg.dassert_in(
        output_format,
        ["png", "pdf", "ps", "eps"],
        f"Unsupported output format: {output_format}",
    )
    # Build the container with rsvg-convert.
    if force_rebuild:
        container_image = hdocker.build_container_image(
            _RSVG_CONVERT_CONTAINER_PREFIX, _RSVG_CONVERT_DOCKERFILE, force_rebuild, use_sudo
        )
    else:
        container_image = get_svg_rsvg_convert_container_image_name()
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
    # Build SVG conversion command using rsvg-convert.
    # Produces high-quality output with 300 DPI.
    svg_cmd = (
        f"rsvg-convert -d 300 -p 300 -f {output_format} "
        f"-o {out_file_path} {in_file_path}"
    )
    # Build Docker command.
    ret = hdocexec._build_and_run_docker_cmd(
        use_sudo,
        callee_mount_path,
        mount,
        container_image,
        _RSVG_CONVERT_DOCKERFILE,
        svg_cmd,
        mode,
        override_entrypoint=False,
        wrap_in_bash=False,
    )
    return ret


# #############################################################################


_INKSCAPE_CONTAINER_PREFIX = "tmp.svg_inkscape"
_INKSCAPE_DOCKERFILE = rf"""
#FROM ubuntu:22.04
FROM {_DEBIAN_BASE_VERSION}

RUN apt-get update && \
    apt-get install -y --no-install-recommends inkscape && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
"""


def get_svg_inkscape_container_image_name() -> str:
    """
    Get the name of the SVG inkscape container image.

    E.g., `tmp.svg_inkscape.amd64.12345678` or `tmp.svg_inkscape.arm64.12345678`
    """
    container_image, _ = hdocker.get_container_image_name(_INKSCAPE_CONTAINER_PREFIX, _INKSCAPE_DOCKERFILE)
    return container_image


def run_dockerized_svg_with_inkscape(
    in_file_path: str,
    out_file_path: str,
    *,
    output_format: str = "png",
    mode: str = "system",
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> str:
    """
    Convert SVG to various formats using inkscape in a Docker container.

    :param in_file_path: path to the SVG file
    :param out_file_path: path to the output file
    :param output_format: output format - "png" (default), "pdf", "ps", "eps",
        "svg", "emf", "wmf"
    :param mode: execution mode ("system" or other)
    :param force_rebuild: whether to force rebuild the Docker container
    :param use_sudo: whether to use sudo for Docker commands
    :return: Docker command output
    """
    _LOG.debug(hprint.func_signature_to_str())
    hdbg.dassert_in(
        output_format,
        ["png", "pdf", "ps", "eps", "svg", "emf", "wmf"],
        f"Unsupported output format: {output_format}",
    )
    # Build the container with inkscape.
    if force_rebuild:
        container_image = hdocker.build_container_image(
            _INKSCAPE_CONTAINER_PREFIX, _INKSCAPE_DOCKERFILE, force_rebuild, use_sudo
        )
    else:
        container_image = get_svg_inkscape_container_image_name()
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
    # Build SVG conversion command using inkscape.
    # Use --export-type for format selection.
    svg_cmd = (
        f"inkscape {in_file_path} --export-type={output_format} "
        f"--export-filename={out_file_path} --export-dpi=300"
    )
    # Build Docker command.
    ret = hdocexec._build_and_run_docker_cmd(
        use_sudo,
        callee_mount_path,
        mount,
        container_image,
        _INKSCAPE_DOCKERFILE,
        svg_cmd,
        mode,
        override_entrypoint=False,
        wrap_in_bash=False,
    )
    return ret
