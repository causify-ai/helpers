"""
Pandoc document conversion utilities for dockerized execution.

This module provides Docker-based wrappers for Pandoc, a universal document
converter supporting various input and output formats.

Import as:

import dev_scripts_helpers.dockerize.lib_pandoc as dshdlipa
"""

import argparse
import logging
import shlex
from typing import Any, Dict

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hdockerized_executables as hdocexec

_LOG = logging.getLogger(__name__)


def convert_pandoc_cmd_to_arguments(cmd: str) -> Dict[str, Any]:
    """
    Parse the arguments from a pandoc command.

    We need to parse all the arguments that correspond to files, so that
    we can convert them to paths that are valid inside the Docker
    container.

    :param cmd: A list of command-line arguments for pandoc.
    :return: A dictionary with the parsed arguments.
    """
    # Use shlex.split to tokenize the string like a shell would.
    cmd_list = shlex.split(cmd)
    # Remove the newline character that come from multiline commands with `\n`.
    cmd_list = [arg for arg in cmd_list if arg != "\n"]
    _LOG.debug(hprint.to_str("cmd"))
    # The first option is the executable.
    hdbg.dassert_eq(cmd_list[0], "pandoc")
    # pandoc parser is difficult to emulate with `argparse`, since pandoc allows
    # the input file to be anywhere in the command line options. In our case we
    # don't know all the possible command line options so for simplicity we
    # assume that the first option is always the input file.
    in_file_path = cmd_list[1]
    cmd_list = cmd_list[2:]
    _LOG.debug(hprint.to_str("cmd"))
    # Parse arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--template", default=None)
    parser.add_argument("--extract-media", default=None)
    # Parse known arguments and capture the rest.
    args, unknown_args = parser.parse_known_args(cmd_list)
    _LOG.debug(hprint.to_str("args unknown_args"))
    # Filter out the option terminator if present.
    # Remove the `--` option terminator to treat `--option-after-terminator` as a regular argument, not as an option.
    unknown_args = [arg for arg in unknown_args if arg != "--"]
    # Return all the arguments in a dictionary with names that match the
    # function signature of `run_dockerized_pandoc()`.
    in_dir_params = {
        "data-dir": args.data_dir,
        "template": args.template,
        "extract-media": args.extract_media,
    }
    return {
        "input": in_file_path,
        "output": args.output,
        "in_dir_params": in_dir_params,
        "cmd_opts": unknown_args,
    }


def convert_pandoc_arguments_to_cmd(
    params: Dict[str, Any],
) -> str:
    """
    Convert parsed pandoc arguments back to a command string.

    This function takes the parsed pandoc arguments and converts them
    back into a command string that can be executed directly or in a
    Dockerized container.

    :return: The constructed pandoc command string.
    """
    cmd = []
    hdbg.dassert_is_subset(
        params.keys(), ["input", "output", "in_dir_params", "cmd_opts"]
    )
    cmd.append(f"{params['input']}")
    cmd.append(f"--output {params['output']}")
    for key, value in params["in_dir_params"].items():
        if value:
            cmd.append(f"--{key} {value}")
    # Add command options.
    hdbg.dassert_isinstance(params["cmd_opts"], list)
    cmd.append(" ".join(params["cmd_opts"]))
    # Join all parts.
    cmd = " ".join(cmd)
    _LOG.debug(hprint.to_str("cmd"))
    return cmd


def run_dockerized_pandoc(
    cmd: str,
    container_type: str,
    *,
    mode: str = "system",
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> str:
    """
    Run `pandoc` in a Docker container.
    """
    _LOG.debug(hprint.func_signature_to_str())
    if container_type == "pandoc_only":
        container_image = "pandoc/core"
        incremental = False
        dockerfile = ""
    else:
        if container_type == "pandoc_latex":
            container_image = "tmp.pandoc_latex"
            # From https://github.com/pandoc/dockerfiles/blob/main/alpine/latex/Dockerfile
            build_dir = "tmp.docker_build"
            dir_name = hgit.find_file_in_git_tree("pandoc_docker_files")
            hio.create_dir(build_dir, incremental=True)
            cmd = f"cp -r {dir_name}/* tmp.docker_build/common/latex"
            hsystem.system(cmd)
            #
            dockerfile = r"""
            ARG pandoc_version=edge
            FROM pandoc/core:${pandoc_version}-alpine

            # NOTE: to maintainers, please keep this listing alphabetical.
            RUN apk --no-cache add \
                    curl \
                    fontconfig \
                    freetype \
                    gnupg \
                    gzip \
                    perl \
                    tar \
                    wget \
                    xz

            # Installer scripts and config
            COPY common/latex/texlive.profile    /root/texlive.profile
            COPY common/latex/install-texlive.sh /root/install-texlive.sh
            COPY common/latex/packages.txt       /root/packages.txt

            # TeXLive binaries location
            ARG texlive_bin="/opt/texlive/texdir/bin"

            # TeXLive version to install (leave empty to use the latest version).
            ARG texlive_version=

            # TeXLive mirror URL (leave empty to use the default mirror).
            ARG texlive_mirror_url=

            # Modify PATH environment variable, prepending TexLive bin directory
            ENV PATH="${texlive_bin}/default:${PATH}"

            # Ideally, the image would always install "linuxmusl" binaries. However,
            # those are not available for aarch64, so we install binaries that have
            # been built against libc and hope that the compatibility layer works
            # well enough.
            RUN cd /root && \
                ARCH="$(uname -m)" && \
                case "$ARCH" in \
                    ('x86_64') \
                        TEXLIVE_ARCH="x86_64-linuxmusl"; \
                        ;; \
                    (*) echo >&2 "error: unsupported architecture '$ARCH'"; \
                        exit 1 \
                        ;; \
                esac && \
                mkdir -p ${texlive_bin} && \
                ln -sf "${texlive_bin}/${TEXLIVE_ARCH}" "${texlive_bin}/default" && \
                echo "binary_${TEXLIVE_ARCH} 1" >> /root/texlive.profile && \
                ( \
                [ -z "$texlive_version"    ] || printf '-t\n%s\n"' "$texlive_version"; \
                [ -z "$texlive_mirror_url" ] || printf '-m\n%s\n' "$texlive_mirror_url" \
                ) | xargs /root/install-texlive.sh && \
                sed -e 's/ *#.*$//' -e '/^ *$/d' /root/packages.txt | \
                    xargs tlmgr install && \
                rm -f /root/texlive.profile \
                    /root/install-texlive.sh \
                    /root/packages.txt && \
                TERM=dumb luaotfload-tool --update && \
                chmod -R o+w /opt/texlive/texdir/texmf-var

            WORKDIR /data
            """
            # Since we have already copied the files, we can't remove the directory.
            incremental = True
        elif container_type == "pandoc_texlive":
            container_image = "tmp.pandoc_texlive"
            dockerfile = r"""
            FROM texlive/texlive:latest

            ENV DEBIAN_FRONTEND=noninteractive
            RUN apt-get update && \
                apt-get -y upgrade

            RUN apt install -y sudo

            RUN apt install -y pandoc

            # Create a font cache directory usable by non-root users.
            # These fonts don't work with latex and xelatex, and require lualatex.
            # RUN apt install fonts-noto-color-emoji
            # RUN apt install fonts-twemoji
            # RUN mkdir -p /var/cache/fontconfig && \
            #     chmod -R 777 /var/cache/fontconfig && \
            #     fc-cache -fv

            # Verify installation.
            RUN latex --version && pdflatex --version && pandoc --version

            # Set the default command.
            ENTRYPOINT ["pandoc"]
            """
            incremental = False
        else:
            raise ValueError(f"Unknown container type '{container_type}'")
        # Build container.
        container_image = hdocker.build_container_image(
            container_image,
            dockerfile,
            force_rebuild,
            use_sudo,
            incremental=incremental,
        )
    # Convert files to Docker paths.
    (
        is_caller_host,
        use_sibling_container_for_callee,
        caller_mount_path,
        callee_mount_path,
        mount,
    ) = hdocexec._get_docker_mount_context()
    # Convert command to arguments.
    param_dict = convert_pandoc_cmd_to_arguments(cmd)
    param_dict["input"] = hdocker.convert_caller_to_callee_docker_path(
        param_dict["input"],
        caller_mount_path,
        callee_mount_path,
        check_if_exists=True,
        is_input=True,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    param_dict["output"] = hdocker.convert_caller_to_callee_docker_path(
        param_dict["output"],
        caller_mount_path,
        callee_mount_path,
        check_if_exists=False,
        is_input=False,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    for key, value in param_dict["in_dir_params"].items():
        if value:
            value_tmp = hdocker.convert_caller_to_callee_docker_path(
                value,
                caller_mount_path,
                callee_mount_path,
                check_if_exists=True,
                is_input=True,
                is_caller_host=is_caller_host,
                use_sibling_container_for_callee=use_sibling_container_for_callee,
            )
        else:
            value_tmp = value
        param_dict["in_dir_params"][key] = value_tmp
    # Convert arguments back to command.
    pandoc_cmd = convert_pandoc_arguments_to_cmd(param_dict)
    _LOG.debug(hprint.to_str("pandoc_cmd"))
    # The command is like:
    # > docker run --rm --user $(id -u):$(id -g) \
    #     --workdir /app \
    #     --mount type=bind,source=.,target=/app \
    #     pandoc/core \
    #     input.md -o output.md \
    #     -s --toc
    ret = hdocexec._build_and_run_docker_cmd(
        use_sudo,
        callee_mount_path,
        mount,
        container_image,
        dockerfile,
        pandoc_cmd,
        mode,
        override_entrypoint=False,
        wrap_in_bash=False,
    )
    return ret
