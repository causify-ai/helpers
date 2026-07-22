"""
Typst document compilation utilities for dockerized execution.

This module provides Docker-based wrappers for Typst, a new markup-based
typesetting system designed to be as powerful as LaTeX while being easier to use.

Import as:

import dev_scripts_helpers.dockerize.lib_typst as dshdlity
"""

import logging
from typing import List

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)

# Version pins for tools.
_ALPINE_VERSION = "3.23"
_TYPST_VERSION = "0.14.2"
# Touying presentation package (and its dependencies) pre-cached into the image
# so that `notes_to_pdf.py --slides_engine typst` compiles offline.
_TOUYING_VERSION = "0.6.1"

# Name and Dockerfile for the Typst container, exposed so tests can reference
# them directly without duplicating the definition.
TYPST_CONTAINER_IMAGE = "tmp.typst"
TYPST_DOCKERFILE = rf"""
FROM alpine:{_ALPINE_VERSION}

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
        "https://github.com/typst/typst/releases/download/v{_TYPST_VERSION}/typst-${{TYPST_ARCH}}.tar.xz" \
        -o /tmp/typst.tar.xz && \
    tar -xJf /tmp/typst.tar.xz -C /tmp && \
    mv /tmp/typst-${{TYPST_ARCH}}/typst /usr/local/bin/typst && \
    rm -rf /tmp/typst* && \
    chmod +x /usr/local/bin/typst

# Verify installation.
RUN typst --version

# Install Computer Modern fonts - fail if unavailable or not working (no fallback).
RUN apk add --no-cache fontconfig python3 py3-fonttools && \
    mkdir -p /usr/share/fonts/cmu && \
    CTAN_MIRROR="https://ctan.math.illinois.edu/fonts/cm-unicode/fonts" && \
    curl -fsSL "${{CTAN_MIRROR}}/otf/cmunrm.otf" \
        -o /usr/share/fonts/cmu/CMUSerif-Regular.otf && \
    curl -fsSL "${{CTAN_MIRROR}}/otf/cmunbx.otf" \
        -o /usr/share/fonts/cmu/CMUSerif-Bold.otf && \
    curl -fsSL "${{CTAN_MIRROR}}/otf/cmunti.otf" \
        -o /usr/share/fonts/cmu/CMUSerif-Italic.otf && \
    curl -fsSL "${{CTAN_MIRROR}}/otf/cmunbi.otf" \
        -o /usr/share/fonts/cmu/CMUSerif-BoldItalic.otf && \
    curl -fsSL "${{CTAN_MIRROR}}/otf/cmunss.otf" \
        -o /usr/share/fonts/cmu/CMUSans-Regular.otf && \
    curl -fsSL "${{CTAN_MIRROR}}/otf/cmunsx.otf" \
        -o /usr/share/fonts/cmu/CMUSans-Bold.otf && \
    curl -fsSL "${{CTAN_MIRROR}}/otf/cmunsi.otf" \
        -o /usr/share/fonts/cmu/CMUSans-Italic.otf && \
    curl -fsSL "${{CTAN_MIRROR}}/otf/cmunso.otf" \
        -o /usr/share/fonts/cmu/CMUSans-BoldItalic.otf && \
    curl -fsSL "${{CTAN_MIRROR}}/otf/cmuntt.otf" \
        -o /usr/share/fonts/cmu/CMUTypewriter-Regular.otf && \
    curl -fsSL "${{CTAN_MIRROR}}/otf/cmunbx.otf" \
        -o /usr/share/fonts/cmu/CMUTypewriter-Bold.otf && \
    mkdir -p /usr/share/fonts/lato && \
    BASE="https://raw.githubusercontent.com/google/fonts/main" && \
    curl -fsSL "${{BASE}}/ofl/lato/Lato-Regular.ttf" \
        -o /usr/share/fonts/lato/Lato-Regular.ttf && \
    curl -fsSL "${{BASE}}/ofl/lato/Lato-Bold.ttf" \
        -o /usr/share/fonts/lato/Lato-Bold.ttf && \
    curl -fsSL "${{BASE}}/ofl/lato/Lato-Italic.ttf" \
        -o /usr/share/fonts/lato/Lato-Italic.ttf && \
    curl -fsSL "${{BASE}}/ofl/lato/Lato-BoldItalic.ttf" \
        -o /usr/share/fonts/lato/Lato-BoldItalic.ttf && \
    fc-cache -f -v /usr/share/fonts/cmu && \
    echo "=== Verifying Computer Modern fonts ===" && \
    ls -lh /usr/share/fonts/cmu/ && \
    test -f /usr/share/fonts/cmu/CMUSans-Regular.otf || (echo "FATAL: CMU Sans font files missing" && exit 1) && \
    printf 'import sys; from fontTools.ttLib import TTFont; font = TTFont("/usr/share/fonts/cmu/CMUSans-Regular.otf"); name_table = font["name"]; print("Sans families:", [r.toUnicode() for r in name_table.names if r.nameID == 1])' | python3 && \
    printf '#set text(font: "CMU Sans Serif")\n= Test\nComputer Modern Sans test.' > /tmp/test_cm_sans.typ && \
    typst compile --font-path /usr/share/fonts/cmu /tmp/test_cm_sans.typ /tmp/test_cm_sans.pdf 2>&1 | tee /tmp/typst_test.log && \
    (! grep -q "unknown font family" /tmp/typst_test.log) || (echo "FATAL: Typst cannot find CMU Sans Serif fonts" && cat /tmp/typst_test.log && exit 1) && \
    test -f /tmp/test_cm_sans.pdf || (echo "FATAL: Could not generate PDF with CMU Sans Serif" && exit 1) && \
    echo "=== Computer Modern Sans fonts verified ===" && \
    rm -f /tmp/test_cm_sans.typ /tmp/test_cm_sans.pdf /tmp/typst_test.log

# Pre-cache the Touying package (and its transitive dependencies) by compiling a
# stub document that imports it. The cache lives under `XDG_CACHE_HOME` so it is
# shared regardless of the user the container runs as, and is made world-readable
# since the container is invoked with `--user $(id -u):$(id -g)`.
ENV XDG_CACHE_HOME=/opt/typst-cache
RUN mkdir -p /opt/typst-cache && \
    printf '%s\n' \
        '#import "@preview/touying:{_TOUYING_VERSION}": *' \
        '#import themes.simple: *' \
        '#show: simple-theme' \
        '= warmup' > /tmp/warm.typ && \
    typst compile /tmp/warm.typ /tmp/warm.pdf && \
    rm -f /tmp/warm.typ /tmp/warm.pdf && \
    chmod -R a+rX /opt/typst-cache

# Set working directory.
WORKDIR /workspace

# Default command.
CMD ["bash"]
"""


def get_typst_container_image_name() -> str:
    """
    Get the name of the Typst container image.

    E.g., `tmp.typst.amd64.12345678` or `tmp.typst.arm64.12345678`
    """
    container_image, _ = hdocker.get_container_image_name(
        TYPST_CONTAINER_IMAGE, TYPST_DOCKERFILE
    )
    return container_image


def build_typst_container_image(
    *,
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> str:
    """
    Build the Typst container image.

    :param force_rebuild: whether to force rebuild the Docker container
    :param use_sudo: whether to use sudo for Docker commands
    :return: the name of the built container image
    """
    container_image = hdocker.build_container_image(
        TYPST_CONTAINER_IMAGE, TYPST_DOCKERFILE, force_rebuild, use_sudo
    )
    _LOG.debug("container_image=%s", container_image)
    container_image2 = get_typst_container_image_name()
    hdbg.dassert_eq(container_image, container_image2)
    exists, _ = hdocker.image_exists(container_image, use_sudo)
    hdbg.dassert(exists, "Container '%s' doesn't exist", container_image)
    return container_image


def run_dockerized_typst(
    in_file_path: str,
    out_file_path: str,
    cmd_opts: List[str],
    *,
    typst_root_dir: str = "",
    mode: str = "system",
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> str:
    """
    Run `typst` in a Docker container.

    From host:
    ```
    > ./dev_scripts_helpers/dockerize/dockerized_typst.py \
        --input document.typ --output document.pdf
    ```

    From dev container:
    ```
    docker> ./dev_scripts_helpers/dockerize/dockerized_typst.py \
        --input document.typ --output document.pdf
    ```

    :param in_file_path: path to the Typst source file to compile
    :param out_file_path: path to the output PDF file
    :param cmd_opts: extra command options to pass to Typst
    :param typst_root_dir: project root passed to `typst --root`. Typst resolves
        root-absolute paths (e.g., `image("/foo.png")`) and forbids access
        above this directory. Used so that images referenced relative to the
        repo root resolve correctly regardless of where the `.typ` file lives
    :param force_rebuild: whether to force rebuild the Docker container
    :param use_sudo: whether to use sudo for Docker commands
    """
    _LOG.debug(hprint.func_signature_to_str())
    hdbg.dassert_isinstance(cmd_opts, list)
    # Build the container, if needed.
    container_image = build_typst_container_image(
        force_rebuild=force_rebuild, use_sudo=use_sudo
    )
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
    # Convert the project root to a Docker path, if specified.
    root_opt = ""
    if typst_root_dir != "":
        typst_root_dir = hdocker.convert_caller_to_callee_docker_path(
            typst_root_dir,
            caller_mount_path,
            callee_mount_path,
            check_if_exists=True,
            is_input=True,
            is_caller_host=is_caller_host,
            use_sibling_container_for_callee=use_sibling_container_for_callee,
        )
        root_opt = f"--root {typst_root_dir} "
    # Build the Typst command.
    cmd_opts_as_str = " ".join(cmd_opts)
    typst_cmd = (
        f"typst compile {root_opt}{cmd_opts_as_str} "
        f"{in_file_path} {out_file_path}"
    )
    # TODO(gp): Not sure if it is automatically done.
    _LOG.debug("> %s", typst_cmd)
    ret = hdocker.build_and_run_docker_cmd(
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
