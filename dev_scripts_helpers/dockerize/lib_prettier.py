"""
Prettier formatting utilities for dockerized execution.

This module provides Docker-based wrappers for the Prettier code formatter,
supporting markdown, text, and LaTeX files.

Import as:

import dev_scripts_helpers.dockerize.lib_prettier as dshdlipr
"""

import logging
from typing import Any, List, Optional

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hio as hio
import helpers.hmarkdown_div_blocks as hmadiblo
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# Version pins for tools
_PRETTIER_VERSION = "3.8.3"
_UNIFIED_LATEX_PRETTIER_VERSION = "1.7.1"
_PRETTIER_PLUGIN_LATEX_VERSION = "2.0.1"

_DOCKERFILE_MD = rf"""
FROM node:20-slim

RUN npm install -g prettier@{_PRETTIER_VERSION}

# Set a working directory inside the container.
WORKDIR /app

# Run Prettier as the entry command.
ENTRYPOINT ["prettier"]
"""


# For Latex we pin dependencies to ensure compatibility between
# prettier, unified-latex-prettier, and prettier-plugin-latex.
latex_prettier_version = "2.7.0"
_DOCKERFILE_TEX = rf"""
FROM node:18-slim

RUN npm install -g prettier@{latex_prettier_version}
RUN npm install -g @unified-latex/unified-latex-prettier@{_UNIFIED_LATEX_PRETTIER_VERSION}
RUN npm install -g prettier-plugin-latex@{_PRETTIER_PLUGIN_LATEX_VERSION}

# Set a working directory inside the container.
WORKDIR /app

# Run Prettier as the entry command.
ENTRYPOINT ["prettier"]
"""


def _get_prettier_dockerfile(file_type: str) -> str:
    """
    Get the Dockerfile content for a given prettier file type.
    """
    if file_type in ("md", "txt"):
        dockerfile = _DOCKERFILE_MD
    elif file_type == "tex":
        dockerfile = _DOCKERFILE_TEX
    else:
        raise ValueError(f"Invalid file_type='{file_type}'")
    return dockerfile


def get_prettier_container_image_name(file_type: str) -> str:
    """
    Get the name of the Prettier container image for a given file type.

    E.g., `tmp.prettier.md.amd64.12345678` or `tmp.prettier.tex.arm64.12345678`
    """
    container_prefix = f"tmp.prettier.{file_type}"
    dockerfile = _get_prettier_dockerfile(file_type)
    container_image, _ = hdocker.get_container_image_name(
        container_prefix, dockerfile
    )
    return container_image


def build_prettier_container_image(
    file_type: str,
    *,
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> str:
    """
    Build the Prettier container image for a given file type.

    :param file_type: type of file to format (e.g., "md", "tex", "txt")
    :param force_rebuild: whether to force rebuild the Docker container
    :param use_sudo: whether to use sudo for Docker commands
    :return: the name of the built container image
    """
    dockerfile = _get_prettier_dockerfile(file_type)
    container_image = hdocker.build_container_image(
        f"tmp.prettier.{file_type}", dockerfile, force_rebuild, use_sudo
    )
    _LOG.debug("container_image=%s", container_image)
    container_image2 = get_prettier_container_image_name(file_type)
    hdbg.dassert_eq(container_image, container_image2)
    exists, _ = hdocker.image_exists(container_image, use_sudo)
    hdbg.dassert(exists, "Container '%s' doesn't exist", container_image)
    return container_image


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
    > ./dev_scripts_helpers/dockerize/dockerized_prettier.py \
        --input /Users/saggese/src/helpers1/test.md --output test2.md
    > ./dev_scripts_helpers/dockerize/dockerized_prettier.py \
        --input test.md --output test2.md
    ```

    From dev container:
    ```
    docker> ./dev_scripts_helpers/dockerize/dockerized_prettier.py \
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
    container_image = build_prettier_container_image(
        file_type, force_rebuild=force_rebuild, use_sudo=use_sudo
    )
    dockerfile = _get_prettier_dockerfile(file_type)
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
    ret = hdocker.build_and_run_docker_cmd(
        use_sudo,
        callee_mount_path,
        mount,
        container_image,
        dockerfile,
        bash_cmd,
        mode,
        override_entrypoint=True,
        wrap_in_bash=True,
    )
    return ret


def prettier(
    in_file_path: str,
    out_file_path: str,
    file_type: str,
    *,
    print_width: Optional[int] = None,
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
    if print_width is None:
        if file_type == "tex":
            print_width = 72
        elif file_type == "md":
            print_width = 80
        elif file_type == "txt":
            print_width = 80
        else:
            raise ValueError(f"Invalid file type: {file_type}")
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
    # For markdown and text files, wrap div blocks with prettier-ignore.
    if file_type in ("md", "txt"):
        # Pre-process the file.
        txt = hio.from_file(in_file_path)
        lines = txt.split("\n")
        lines = hmadiblo.add_prettier_ignore_to_div_blocks(lines)
        txt = "\n".join(lines)
        # Save to tmp file.
        tmp_file_name = "tmp.prettier." + file_type
        hio.to_file(tmp_file_name, txt)
        in_file_path = tmp_file_name
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
    # For markdown and text files, remove prettier-ignore comments in place.
    if file_type in ("md", "txt"):
        txt = hio.from_file(out_file_path)
        lines = txt.split("\n")
        lines = hmadiblo.remove_prettier_ignore_from_div_blocks(lines)
        txt = "\n".join(lines)
        #
        txt = hio.to_file(out_file_path, txt)


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
    hdbg.dassert_isinstance(txt, str)
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
    # os.remove(tmp_file_name)
    return txt  # type: ignore
