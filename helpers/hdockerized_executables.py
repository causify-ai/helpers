"""
Dockerized executable wrappers for various tools.

This module provides Docker-based wrappers for various executables like prettier,
pandoc, latex, imagemagick, plantuml, mermaid, and graphviz. These functions
allow running these tools in isolated Docker containers.

Import as:

import helpers.hdockerized_executables as hdockexec
"""

import argparse
import logging
import os
import re
import shlex
from typing import Any, Dict, List

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# #############################################################################
# Dockerized prettier.
# #############################################################################


def run_dockerized_prettier(
    in_file_path: str,
    cmd_opts: List[str],
    out_file_path: str,
    file_type: str,
    *,
    mode: str = "system",
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> str:
    """
    Run `prettier` in a Docker container.

    From host:
    ```
    > ./dev_scripts_helpers/documentation/dockerized_prettier.py \
        --input /Users/saggese/src/helpers1/test.md --output test2.md
    > ./dev_scripts_helpers/documentation/dockerized_prettier.py \
        --input test.md --output test2.md
    ```

    From dev container:
    ```
    docker> ./dev_scripts_helpers/documentation/dockerized_prettier.py \
        --input test.md --output test2.md
    ```

    :param in_file_path: Path to the file to format with Prettier.
    :param out_file_path: Path to the output file.
    :param cmd_opts: Command options to pass to Prettier.
    :param file_type: Type of the file to format, e.g., `md`, `txt` or `tex`.
    :param force_rebuild: Whether to force rebuild the Docker container.
    :param use_sudo: Whether to use sudo for Docker commands.
    """
    _LOG.debug(hprint.func_signature_to_str())
    hdbg.dassert_isinstance(cmd_opts, list)
    hdbg.dassert_in(file_type, ["md", "txt", "tex"])
    # Build the container, if needed.
    # TODO(gp): -> container_image_name
    container_image = f"tmp.prettier.{file_type}"
    if file_type in ("md", "txt"):
        dockerfile = r"""
        FROM node:20-slim

        RUN npm install -g prettier

        # Set a working directory inside the container.
        WORKDIR /app

        # Run Prettier as the entry command.
        ENTRYPOINT ["prettier"]
        """
    elif file_type == "tex":
        # For Latex we need to pin down the dependencies since the latest
        # version of prettier is not compatible with the latest version of
        # prettier-plugin-latex.
        dockerfile = r"""
        FROM node:18-slim

        RUN npm install -g prettier@2.7.0
        RUN npm install -g @unified-latex/unified-latex-prettier@1.7.1
        RUN npm install -g prettier-plugin-latex@2.0.1

        # Set a working directory inside the container.
        WORKDIR /app

        # Run Prettier as the entry command.
        ENTRYPOINT ["prettier"]
        """
    else:
        raise ValueError(f"Invalid file_type='{file_type}'")
    container_image = hdocker.build_container_image(
        container_image, dockerfile, force_rebuild, use_sudo
    )
    # Convert files to Docker paths.
    is_caller_host = not hserver.is_inside_docker()
    # TODO(gp): After fix for CmampTask10710 enable this.
    # use_sibling_container_for_callee = hserver.use_docker_sibling_containers()
    use_sibling_container_for_callee = True
    caller_mount_path, callee_mount_path, mount = hdocker.get_docker_mount_info(
        is_caller_host, use_sibling_container_for_callee
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
    out_file_path = hdocker.convert_caller_to_callee_docker_path(
        out_file_path,
        caller_mount_path,
        callee_mount_path,
        check_if_exists=False,
        is_input=False,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    # Our interface is (in_file, out_file) instead of the wonky prettier
    # interface based on `--write` for in place update and redirecting `stdout`
    # to save on a different place.
    hdbg.dassert_not_in("--write", cmd_opts)
    if out_file_path == in_file_path:
        cmd_opts.append("--write")
    cmd_opts_as_str = " ".join(cmd_opts)
    # The command is like:
    # > docker run --rm --user $(id -u):$(id -g) \
    #     --workdir /app --mount type=bind,source=.,target=/app \
    #     tmp.prettier \
    #     --parser markdown --prose-wrap always --write --tab-width 2 \
    #     ./test.md
    if file_type in ("md", "txt"):
        executable = "/usr/local/bin/prettier"
    elif file_type == "tex":
        executable = (
            "NODE_PATH=/usr/local/lib/node_modules /usr/local/bin/prettier"
        )
    else:
        raise ValueError(f"Invalid file_type='{file_type}'")
    bash_cmd = f"{executable} {cmd_opts_as_str} {in_file_path}"
    if out_file_path != in_file_path:
        bash_cmd += f" > {out_file_path}"
    # Build the Docker command.
    docker_cmd = hdocker.get_docker_base_cmd(use_sudo)
    docker_cmd.extend(
        [
            " --entrypoint ''",
            f"--workdir {callee_mount_path} --mount {mount}",
            f"{container_image}",
            f'bash -c "{bash_cmd}"',
        ]
    )
    docker_cmd = " ".join(docker_cmd)
    ret = hdocker.process_docker_cmd(
        docker_cmd, container_image, dockerfile, mode
    )
    return ret


# This a different approach I've tried to inject files inside a container
# and read them back. It's an interesting approach but it's flaky.
#
# # Inside a container we need to copy the input file to the container and
# # run the command inside the container.
# container_image = "tmp.prettier"
# # Generates an 8-character random string, e.g., x7vB9T2p
# random_string = "".join(
#     random.choices(string.ascii_lowercase + string.digits, k=8)
# )
# tmp_container_image = container_image + "." + random_string
# # 1) Copy the input file in the current dir as a temp file to be in the
# # Docker context.
# tmp_in_file = f"{container_image}.{random_string}.in_file"
# cmd = "cp %s %s" % (in_file_path, tmp_in_file)
# hsystem.system(cmd)
# # 2) Create a temporary docker image with the input file inside.
# dockerfile = f"""
# FROM {container_image}
# COPY {tmp_in_file} /tmp/{tmp_in_file}
# """
# force_rebuild = True
# build_container(tmp_container_image, dockerfile, force_rebuild, use_sudo)
# cmd = f"rm {tmp_in_file}"
# hsystem.system(cmd)
# # 3) Run the command inside the container.
# executable = get_docker_executable(use_sudo)
# cmd_opts_as_str = " ".join(cmd_opts)
# tmp_out_file = f"{container_image}.{random_string}.out_file"
# docker_cmd = (
#     # We can run as root user (i.e., without `--user`) since we don't
#     # need to share files with the external filesystem.
#     f"{executable} run -d"
#     " --entrypoint ''"
#     f" {tmp_container_image}"
#     f' bash -c "/usr/local/bin/prettier {cmd_opts_as_str} /tmp/{tmp_in_file}'
#     f' >/tmp/{tmp_out_file}"'
# )
# _, container_id = hsystem.system_to_string(docker_cmd)
# _LOG.debug(hprint.to_str("container_id"))
# hdbg.dassert_ne(container_id, "")
# # 4) Wait until the file is generated and copy it locally.
# wait_for_file_in_docker(container_id,
#     f"/tmp/{tmp_out_file}",
#                         out_file_path)
# # 5) Clean up.
# cmd = f"docker rm -f {container_id}"
# hsystem.system(cmd)
# cmd = f"docker image rm -f {tmp_container_image}"
# hsystem.system(cmd)


# #############################################################################
# Dockerized pandoc.
# #############################################################################


# `convert_pandoc_cmd_to_arguments()` and `convert_pandoc_arguments_to_cmd()`
# are opposite functions that allow to convert a command line to a dictionary
# and back to a command line. This is useful when we want to run a command in a
# container which requires to know how to interpret the command line arguments.
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
    cmd = shlex.split(cmd)
    # Remove the newline character that come from multiline commands with `\n`.
    cmd = [arg for arg in cmd if arg != "\n"]
    _LOG.debug(hprint.to_str("cmd"))
    # The first option is the executable.
    hdbg.dassert_eq(cmd[0], "pandoc")
    # pandoc parser is difficult to emulate with `argparse`, since pandoc allows
    # the input file to be anywhere in the command line options. In our case we
    # don't know all the possible command line options so for simplicity we
    # assume that the first option is always the input file.
    in_file_path = cmd[1]
    cmd = cmd[2:]
    _LOG.debug(hprint.to_str("cmd"))
    #
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--template", default=None)
    parser.add_argument("--extract-media", default=None)
    # Parse known arguments and capture the rest.
    args, unknown_args = parser.parse_known_args(cmd)
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
    #
    hdbg.dassert_isinstance(params["cmd_opts"], list)
    cmd.append(" ".join(params["cmd_opts"]))
    #
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
    is_caller_host = not hserver.is_inside_docker()
    use_sibling_container_for_callee = True
    caller_mount_path, callee_mount_path, mount = hdocker.get_docker_mount_info(
        is_caller_host, use_sibling_container_for_callee
    )
    #
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
    #
    pandoc_cmd = convert_pandoc_arguments_to_cmd(param_dict)
    _LOG.debug(hprint.to_str("pandoc_cmd"))
    # The command is like:
    # > docker run --rm --user $(id -u):$(id -g) \
    #     --workdir /app \
    #     --mount type=bind,source=.,target=/app \
    #     pandoc/core \
    #     input.md -o output.md \
    #     -s --toc
    docker_cmd = hdocker.get_docker_base_cmd(use_sudo)
    docker_cmd.extend(
        [
            f"--workdir {callee_mount_path} --mount {mount}",
            f"{container_image}",
            f"{pandoc_cmd}",
        ]
    )
    docker_cmd = " ".join(docker_cmd)
    ret = hdocker.process_docker_cmd(
        docker_cmd, container_image, dockerfile, mode
    )
    return ret


# TODO(gp): Remove the code path using non dockerized executable, after fix for
# CmampTask10710.
def prettier(
    in_file_path: str,
    out_file_path: str,
    file_type: str,
    *,
    print_width: int = 80,
    use_dockerized_prettier: bool = True,
    # TODO(gp): Remove this.
    **kwargs: Any,
) -> None:
    """
    Format the given text using Prettier.

    :param in_file_path: The path to the input file.
    :param out_file_path: The path to the output file.
    :param file_type: The type of file to be formatted, e.g., `md` or `tex`.
    :param print_width: The maximum line width for the formatted text.
        If None, the default width is used.
    :param use_dockerized_prettier: Whether to use a Dockerized version
        of Prettier.
    :return: The formatted text.
    """
    _LOG.debug(hprint.func_signature_to_str())
    hdbg.dassert_in(file_type, ["md", "tex", "txt"])
    # Build command options.
    cmd_opts: List[str] = []
    tab_width = 2
    if file_type == "tex":
        # cmd_opts.append("--plugin=prettier-plugin-latex")
        cmd_opts.append("--plugin=@unified-latex/unified-latex-prettier")
    elif file_type in ("md", "txt"):
        cmd_opts.append("--parser markdown")
    else:
        raise ValueError(f"Invalid file type: {file_type}")
    hdbg.dassert_lte(1, print_width)
    cmd_opts.extend(
        [
            f"--print-width {print_width}",
            "--prose-wrap always",
            f"--tab-width {tab_width}",
            "--use-tabs false",
        ]
    )
    # Run prettier.
    if use_dockerized_prettier:
        # Run `prettier` in a Docker container.
        force_rebuild = False
        use_sudo = hdocker.get_use_sudo()
        run_dockerized_prettier(
            in_file_path,
            cmd_opts,
            out_file_path,
            file_type=file_type,
            force_rebuild=force_rebuild,
            use_sudo=use_sudo,
        )
    else:
        # Run `prettier` installed on the host directly.
        executable = "prettier"
        # executable = "NODE_PATH=/usr/local/lib/node_modules /usr/local/bin/prettier"
        cmd = [executable] + cmd_opts
        if in_file_path == out_file_path:
            cmd.append("--write")
        cmd.append(in_file_path)
        if in_file_path != out_file_path:
            cmd.append("> " + out_file_path)
        #
        cmd_as_str = " ".join(cmd)
        _, output_tmp = hsystem.system_to_string(cmd_as_str, abort_on_error=True)
        _LOG.debug("output_tmp=%s", output_tmp)


# TODO(gp): Convert this into a decorator to adapt operations that work on
#  files to passing strings.
# TODO(gp): Move this to `hmarkdown.py`.
def prettier_on_str(
    txt: str,
    file_type: str,
    *args: Any,
    **kwargs: Any,
) -> str:
    """
    Wrap `prettier()` to work on strings.
    """
    _LOG.debug("txt=\n%s", txt)
    # Save string as input.
    # TODO(gp): Use a context manager.
    hdbg.dassert_in(file_type, ["md", "tex", "txt"])
    tmp_file_name = "tmp.prettier_on_str." + file_type
    hio.to_file(tmp_file_name, txt)
    # Call `prettier` in-place.
    prettier(tmp_file_name, tmp_file_name, file_type, *args, **kwargs)
    # Read result into a string.
    txt = hio.from_file(tmp_file_name)
    _LOG.debug("After prettier txt=\n%s", txt)
    os.remove(tmp_file_name)
    return txt  # type: ignore


# #############################################################################
# Dockerized markdown_toc.
# #############################################################################


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
    container_image = "tmp.markdown_toc"
    dockerfile = r"""
    # Use a Node.js image
    FROM node:18

    # Install Prettier globally
    RUN npm install -g markdown-toc

    # Set a working directory inside the container
    WORKDIR /app
    """
    container_image = hdocker.build_container_image(
        container_image, dockerfile, force_rebuild, use_sudo
    )
    # Convert files to Docker paths.
    is_caller_host = not hserver.is_inside_docker()
    # TODO(gp): After fix for CmampTask10710 enable this.
    # use_sibling_container_for_callee = hserver.use_docker_sibling_containers()
    use_sibling_container_for_callee = True
    caller_mount_path, callee_mount_path, mount = hdocker.get_docker_mount_info(
        is_caller_host, use_sibling_container_for_callee
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
    cmd_opts_as_str = " ".join(cmd_opts)
    # The command is like:
    # > docker run --rm --user $(id -u):$(id -g) \
    #     --workdir /app --mount type=bind,source=.,target=/app \
    #     tmp.markdown_toc \
    #     -i ./test.md
    bash_cmd = f"/usr/local/bin/markdown-toc {cmd_opts_as_str} -i {in_file_path}"
    docker_cmd = hdocker.get_docker_base_cmd(use_sudo)
    docker_cmd.extend(
        [
            f"--workdir {callee_mount_path} --mount {mount}",
            f"{container_image}",
            f'bash -c "{bash_cmd}"',
        ]
    )
    docker_cmd = " ".join(docker_cmd)
    ret = hdocker.process_docker_cmd(
        docker_cmd, container_image, dockerfile, mode
    )
    return ret


# #############################################################################
# Dockerized Latex.
# #############################################################################


# TODO(gp): Factor out common code between the `convert_*_cmd_to_arguments()`
# and `convert_*_arguments_to_cmd()` functions.
def convert_latex_cmd_to_arguments(cmd: str) -> Dict[str, Any]:
    """
    Parse the arguments from a Latex command.

    ```
    > pdflatex \
        tmp.scratch/tmp.pandoc.tex \
        -output-directory tmp.scratch \
        -interaction=nonstopmode -halt-on-error -shell-escape ```

    :param cmd: A list of command-line arguments for pandoc.
    :return: A dictionary with the parsed arguments.
    """
    # Use shlex.split to tokenize the string like a shell would.
    cmd = shlex.split(cmd)
    # Remove the newline character that come from multiline commands with `\n`.
    cmd = [arg for arg in cmd if arg != "\n"]
    _LOG.debug(hprint.to_str("cmd"))
    # The first option is the executable.
    hdbg.dassert_eq(cmd[0], "pdflatex")
    # We assume that the first option is always the input file.
    in_file_path = cmd[-1]
    hdbg.dassert(
        not in_file_path.startswith("-"),
        "Invalid input file '%s'",
        in_file_path,
    )
    hdbg.dassert_file_exists(in_file_path)
    cmd = cmd[1:-1]
    _LOG.debug(hprint.to_str("cmd"))
    #
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-directory", required=True)
    # Latex uses options like `-XYZ` which confuse `argparse` so we need to
    # replace `-XYZ` with `--XYZ`.
    cmd = [re.sub(r"^-", r"--", cmd_opts) for cmd_opts in cmd]
    _LOG.debug(hprint.to_str("cmd"))
    # # Parse known arguments and capture the rest.
    args, unknown_args = parser.parse_known_args(cmd)
    _LOG.debug(hprint.to_str("args unknown_args"))
    # Return all the arguments in a dictionary with names that match the
    # function signature of `run_dockerized_pandoc()`.
    in_dir_params: Dict[str, Any] = {}
    return {
        "input": in_file_path,
        "output-directory": args.output_directory,
        "in_dir_params": in_dir_params,
        "cmd_opts": unknown_args,
    }


def convert_latex_arguments_to_cmd(
    params: Dict[str, Any],
) -> str:
    """
    Convert parsed pandoc arguments back to a command string.

    This function takes the parsed latex arguments and converts them
    back into a command string that can be executed directly or in a
    Dockerized container.

    :return: The constructed pandoc command string.
    """
    cmd = []
    hdbg.dassert_is_subset(
        params.keys(),
        ["input", "output-directory", "in_dir_params", "cmd_opts"],
    )
    key = "output-directory"
    value = params[key]
    cmd.append(f"-{key} {value}")
    for key, value in params["in_dir_params"].items():
        if value:
            cmd.append(f"-{key} {value}")
    #
    hdbg.dassert_isinstance(params["cmd_opts"], list)
    cmd.append(" ".join(params["cmd_opts"]))
    # The input needs to be last to work around the bug in pdflatex where the
    # options before the input file are not always parsed correctly.
    cmd.append(f"{params['input']}")
    #
    cmd = " ".join(cmd)
    _LOG.debug(hprint.to_str("cmd"))
    return cmd


# TODO(gp): Factor out common code between the `run_dockerized_*` functions.
# E.g., the code calling `convert_caller_to_callee_docker_path()` has a lot
# of repetition.
def run_dockerized_latex(
    cmd: str,
    *,
    mode: str = "system",
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> str:
    """
    Run `latex` in a Docker container.
    """
    _LOG.debug(hprint.func_signature_to_str())
    container_image = "tmp.latex"
    if False:
        dockerfile = r"""
        # Use minimal multi-arch TeX Live image (includes ARM support)
        FROM ghcr.io/xu-cheng/texlive:latest
        """
    # Doesn't work.
    if False:
        dockerfile = r"""
        # Use a lightweight base image.
        # FROM debian:bullseye-slim
        FROM ubuntu:22.04

        # Set environment variables to avoid interactive prompts.
        ENV DEBIAN_FRONTEND=noninteractive

        # Update.
        RUN apt-get update && \
            apt-get clean && \
            rm -rf /var/lib/apt/lists/* && \
            apt-get update

        # Install only the minimal TeX Live packages.
        RUN apt-get install -y --no-install-recommends \
            texlive-latex-base \
            texlive-latex-recommended \
            texlive-fonts-recommended \
            texlive-latex-extra \
            lmodern \
            tikzit \
            || apt-get install -y --fix-missing
        """
    # Doesn't work.
    if False:
        dockerfile = r"""
        # Use a lightweight base image.
        # FROM debian:bullseye-slim
        FROM ubuntu:22.04

        # Set environment variables to avoid interactive prompts.
        ENV DEBIAN_FRONTEND=noninteractive

        RUN rm -rf /var/lib/apt/lists/*
        # Update.
        RUN apt-get clean && \
            apt-get update

        # Install texlive-full.
        RUN apt install -y texlive-full
        """
    # Clean up.
    if False:
        dockerfile += r"""
        RUN rm -rf /var/lib/apt/lists/* \
            && apt-get clean

        # Verify LaTeX is installed.
        RUN latex --version

        # Set working directory.
        WORKDIR /workspace

        # Default command.
        CMD [ "bash" ]
        """
    if True:
        dockerfile = r"""
        FROM mfisherman/texlive-full

        # Verify LaTeX is installed.
        RUN latex --version

        # Default command.
        CMD [ "bash" ]
        """
    container_image = hdocker.build_container_image(
        container_image, dockerfile, force_rebuild, use_sudo
    )
    # Convert files to Docker.
    is_caller_host = not hserver.is_inside_docker()
    use_sibling_container_for_callee = True
    caller_mount_path, callee_mount_path, mount = hdocker.get_docker_mount_info(
        is_caller_host, use_sibling_container_for_callee
    )
    #
    param_dict = convert_latex_cmd_to_arguments(cmd)
    param_dict["input"] = hdocker.convert_caller_to_callee_docker_path(
        param_dict["input"],
        caller_mount_path,
        callee_mount_path,
        check_if_exists=True,
        is_input=True,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    key = "output-directory"
    value = param_dict[key]
    param_dict[key] = hdocker.convert_caller_to_callee_docker_path(
        value,
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
    # Create the latex command.
    latex_cmd = convert_latex_arguments_to_cmd(param_dict)
    latex_cmd = "pdflatex " + latex_cmd
    _LOG.debug(hprint.to_str("latex_cmd"))
    #
    docker_cmd = hdocker.get_docker_base_cmd(use_sudo)
    docker_cmd.extend(
        [
            f"--workdir {callee_mount_path} --mount {mount}",
            f"{container_image}",
            f"{latex_cmd}",
        ]
    )
    docker_cmd = " ".join(docker_cmd)
    ret = hdocker.process_docker_cmd(
        docker_cmd, container_image, dockerfile, mode
    )
    return ret


def run_basic_latex(
    in_file_name: str,
    cmd_opts: List[str],
    run_latex_again: bool,
    out_file_name: str,
    *,
    mode: str = "system",
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> None:
    """
    Run a basic Latex command.
    """
    _LOG.debug(hprint.func_signature_to_str())
    #
    # hdbg.dassert_file_extension(input_file_name, "tex")
    hdbg.dassert_file_exists(in_file_name)
    hdbg.dassert_file_extension(out_file_name, "pdf")
    # There is a horrible bug in pdflatex that if the input file is not the last
    # one the output directory is not recognized.
    cmd = (
        "pdflatex"
        + " -output-directory=."
        + " -interaction=nonstopmode"
        + " -halt-on-error"
        + " -shell-escape"
        + " "
        + " ".join(cmd_opts)
        + f" {in_file_name}"
    )
    run_dockerized_latex(
        cmd,
        mode=mode,
        force_rebuild=force_rebuild,
        use_sudo=use_sudo,
    )
    if run_latex_again:
        run_dockerized_latex(
            cmd,
            mode=mode,
            force_rebuild=force_rebuild,
            use_sudo=use_sudo,
        )
    # Latex writes the output file in the current working directory.
    file_out = os.path.basename(in_file_name)
    file_out = hio.change_filename_extension(file_out, "", "pdf")
    _LOG.debug("file_out=%s", file_out)
    hdbg.dassert_path_exists(file_out)
    # Move to the proper output location.
    if file_out != out_file_name:
        cmd = f"mv {file_out} {out_file_name}"
        hsystem.system(cmd)


# #############################################################################
# Dockerized ImageMagick.
# #############################################################################


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
    #
    container_image = "tmp.imagemagick"
    dockerfile = r"""
    FROM alpine:latest

    # Install Bash.
    RUN apk add --no-cache bash
    # Set Bash as the default shell.
    SHELL ["/bin/bash", "-c"]

    RUN apk add --no-cache imagemagick ghostscript

    # Set working directory
    WORKDIR /workspace

    RUN magick --version
    RUN gs --version

    # Default command
    CMD [ "bash" ]
    """
    container_image = hdocker.build_container_image(
        container_image, dockerfile, force_rebuild, use_sudo
    )
    # Convert files to Docker paths.
    is_caller_host = not hserver.is_inside_docker()
    use_sibling_container_for_callee = True
    caller_mount_path, callee_mount_path, mount = hdocker.get_docker_mount_info(
        is_caller_host, use_sibling_container_for_callee
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
    out_file_path = hdocker.convert_caller_to_callee_docker_path(
        out_file_path,
        caller_mount_path,
        callee_mount_path,
        check_if_exists=False,
        is_input=False,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    cmd_opts_as_str = " ".join(cmd_opts)
    cmd = f"magick {cmd_opts_as_str} {in_file_path} {out_file_path}"
    docker_cmd = hdocker.get_docker_base_cmd(use_sudo)
    docker_cmd.extend(
        [
            "--entrypoint ''",
            f"--workdir {callee_mount_path} --mount {mount}",
            container_image,
            f'bash -c "{cmd}"',
        ]
    )
    docker_cmd = " ".join(docker_cmd)
    ret = hdocker.process_docker_cmd(
        docker_cmd, container_image, dockerfile, mode
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
    run_basic_latex(
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


# #############################################################################


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
    container_image = "tmp.plantuml"
    dockerfile = r"""
    # Use a lightweight base image.
    FROM debian:bullseye-slim

    # Install plantUML.
    RUN apt-get update
    RUN apt-get install -y --no-install-recommends plantuml
    """
    container_image = hdocker.build_container_image(
        container_image, dockerfile, force_rebuild, use_sudo
    )
    # Convert files to Docker paths.
    is_caller_host = not hserver.is_inside_docker()
    use_sibling_container_for_callee = True
    caller_mount_path, callee_mount_path, mount = hdocker.get_docker_mount_info(
        is_caller_host, use_sibling_container_for_callee
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
    docker_cmd = hdocker.get_docker_base_cmd(use_sudo)
    docker_cmd.extend(
        [
            " --entrypoint ''",
            f"--workdir {callee_mount_path} --mount {mount}",
            f"{container_image}",
            f'bash -c "{plantuml_cmd}"',
        ]
    )
    docker_cmd = " ".join(docker_cmd)
    ret = hdocker.process_docker_cmd(
        docker_cmd, container_image, dockerfile, mode
    )
    return ret


# #############################################################################


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
    is_caller_host = not hserver.is_inside_docker()
    use_sibling_container_for_callee = True
    caller_mount_path, callee_mount_path, mount = hdocker.get_docker_mount_info(
        is_caller_host, use_sibling_container_for_callee
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
    docker_cmd = hdocker.get_docker_base_cmd(use_sudo)
    docker_cmd.extend(
        [
            f"--workdir {callee_mount_path} --mount {mount}",
            container_image,
            mermaid_cmd,
        ]
    )
    docker_cmd = " ".join(docker_cmd)
    ret = hdocker.process_docker_cmd(
        docker_cmd, container_image, dockerfile, mode
    )
    return ret


# TODO(gp): Factor out the common code with `run_dockerized_mermaid()`.
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
    FROM node:18

    # Install packages needed for mermaid.
    RUN apt-get update
    RUN apt-get install -y nodejs npm

    RUN cat > .puppeteerrc.cjs <<EOL
    {puppeteer_cache_path}
    EOL

    RUN npx puppeteer browsers install chrome-headless-shell
    RUN apt-get install -y libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2

    # Install mermaid.
    RUN npm install -g mermaid @mermaid-js/mermaid-cli
    """
    container_image = hdocker.build_container_image(
        container_image, dockerfile, force_rebuild, use_sudo
    )
    # Convert files to Docker paths.
    is_caller_host = not hserver.is_inside_docker()
    use_sibling_container_for_callee = True
    caller_mount_path, callee_mount_path, mount = hdocker.get_docker_mount_info(
        is_caller_host, use_sibling_container_for_callee
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
    # TODO(gp): Factor out building the docker cmd.
    docker_cmd = hdocker.get_docker_base_cmd(use_sudo)
    docker_cmd.extend(
        [
            "--entrypoint ''",
            f"--workdir {callee_mount_path} --mount {mount}",
            container_image,
            f'bash -c "{mermaid_cmd}"',
        ]
    )
    docker_cmd = " ".join(docker_cmd)
    hdocker.process_docker_cmd(docker_cmd, container_image, dockerfile, mode)


# #############################################################################


def run_dockerized_graphviz(
    in_file_path: str,
    cmd_opts: List[str],
    out_file_path: str,
    *,
    mode: str = "system",
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> str:
    """
    Run `graphviz` in a Docker container.

    :param in_file_path: path to the code of the image to render
    :param out_file_path: path to the image to be created
    :param force_rebuild: whether to force rebuild the Docker container
    :param use_sudo: whether to use sudo for Docker commands
    """
    _LOG.debug(hprint.func_signature_to_str())
    # Get the container image.
    # These containers don't work so we install it in a custom container.
    # container_image = "graphviz/graphviz"
    # container_image = "nshine/dot"
    container_image = "tmp.graphviz"
    dockerfile = r"""
    FROM alpine:latest

    RUN apk add --no-cache graphviz
    """
    container_image = hdocker.build_container_image(
        container_image, dockerfile, force_rebuild, use_sudo
    )
    # Convert files to Docker paths.
    is_caller_host = not hserver.is_inside_docker()
    use_sibling_container_for_callee = True
    caller_mount_path, callee_mount_path, mount = hdocker.get_docker_mount_info(
        is_caller_host, use_sibling_container_for_callee
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
    out_file_path = hdocker.convert_caller_to_callee_docker_path(
        out_file_path,
        caller_mount_path,
        callee_mount_path,
        check_if_exists=True,
        is_input=False,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    #
    cmd_opts_str = " ".join(cmd_opts)
    graphviz_cmd = [
        "dot",
        f"{cmd_opts_str}",
        "-T png",
        "-Gdpi=300",
        f"-o {out_file_path}",
        in_file_path,
    ]
    graphviz_cmd = " ".join(graphviz_cmd)
    #
    docker_cmd = hdocker.get_docker_base_cmd(use_sudo)
    docker_cmd.extend(
        [
            f"--workdir {callee_mount_path} --mount {mount}",
            container_image,
            graphviz_cmd,
        ]
    )
    docker_cmd = " ".join(docker_cmd)
    ret = hdocker.process_docker_cmd(
        docker_cmd, container_image, dockerfile, mode
    )
    return ret
