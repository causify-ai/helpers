"""
Typst document compilation utilities for dockerized execution.

This module provides Docker-based wrappers for Typst, a new markup-based
typesetting system designed to be as powerful as LaTeX while being easier to use.

Import as:

import dev_scripts_helpers.documentation.lib_typst as dshdlity
"""

import logging
from typing import List

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hprint as hprint
import helpers.hdockerized_executables as hdocexec

_LOG = logging.getLogger(__name__)

# Name and Dockerfile for the Typst container, exposed so tests can reference
# them directly without duplicating the definition.
TYPST_CONTAINER_IMAGE = "tmp.typst"
TYPST_DOCKERFILE = r"""
FROM alpine:latest

# Install dependencies.
RUN apk add --no-cache bash curl tar xz

# Download the Typst musl binary for the current architecture directly from
# GitHub releases. Musl binaries are natively compatible with Alpine.
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
        TYPST_ARCH="x86_64-unknown-linux-musl"; \
    elif [ "$ARCH" = "aarch64" ]; then \
        TYPST_ARCH="aarch64-unknown-linux-musl"; \
    else \
        echo "Unsupported architecture: $ARCH" && exit 1; \
    fi && \
    curl -fsSL \
        "https://github.com/typst/typst/releases/latest/download/typst-${TYPST_ARCH}.tar.xz" \
        -o /tmp/typst.tar.xz && \
    tar -xJf /tmp/typst.tar.xz -C /tmp && \
    mv /tmp/typst-${TYPST_ARCH}/typst /usr/local/bin/typst && \
    rm -rf /tmp/typst* && \
    chmod +x /usr/local/bin/typst

# Verify installation.
RUN typst --version

# Install fonts used by the Causify documentation template.
# - Lato (body text): downloaded from Google Fonts GitHub (static TTF files).
# - DejaVu Sans Mono (code): installed from Alpine's ttf-dejavu package.
#   Roboto Mono is only available as a variable font which Typst does not yet
#   support, so DejaVu Sans Mono is used as a visually close static substitute.
# Typst scans /usr/share/fonts/ on Linux for font discovery.
RUN apk add --no-cache ttf-dejavu && \
    BASE="https://raw.githubusercontent.com/google/fonts/main" && \
    mkdir -p /usr/share/fonts/lato && \
    curl -fsSL "${BASE}/ofl/lato/Lato-Regular.ttf" \
        -o /usr/share/fonts/lato/Lato-Regular.ttf && \
    curl -fsSL "${BASE}/ofl/lato/Lato-Bold.ttf" \
        -o /usr/share/fonts/lato/Lato-Bold.ttf && \
    curl -fsSL "${BASE}/ofl/lato/Lato-Italic.ttf" \
        -o /usr/share/fonts/lato/Lato-Italic.ttf && \
    curl -fsSL "${BASE}/ofl/lato/Lato-BoldItalic.ttf" \
        -o /usr/share/fonts/lato/Lato-BoldItalic.ttf

# Set working directory.
WORKDIR /workspace

# Default command.
CMD ["bash"]
"""


def run_dockerized_typst(
    in_file_path: str,
    out_file_path: str,
    cmd_opts: List[str],
    *,
    mode: str = "system",
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> str:
    """
    Run `typst` in a Docker container.

    From host:
    ```
    > ./dev_scripts_helpers/documentation/dockerized_typst.py \
        --input document.typ --output document.pdf
    ```

    From dev container:
    ```
    docker> ./dev_scripts_helpers/documentation/dockerized_typst.py \
        --input document.typ --output document.pdf
    ```

    :param in_file_path: path to the Typst source file to compile
    :param out_file_path: path to the output PDF file
    :param cmd_opts: extra command options to pass to Typst
    :param force_rebuild: whether to force rebuild the Docker container
    :param use_sudo: whether to use sudo for Docker commands
    """
    _LOG.debug(hprint.func_signature_to_str())
    hdbg.dassert_isinstance(cmd_opts, list)
    # Build the container, if needed.
    container_image = hdocker.build_container_image(
        TYPST_CONTAINER_IMAGE, TYPST_DOCKERFILE, force_rebuild, use_sudo
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
        check_if_exists=False,
        is_input=False,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    # Build the Typst command.
    cmd_opts_as_str = " ".join(cmd_opts)
    typst_cmd = f"typst compile {cmd_opts_as_str} {in_file_path} {out_file_path}"
    ret = hdocexec._build_and_run_docker_cmd(
        use_sudo,
        callee_mount_path,
        mount,
        container_image,
        TYPST_DOCKERFILE,
        typst_cmd,
        mode,
        override_entrypoint=True,
        wrap_in_bash=True,
    )
    return ret
