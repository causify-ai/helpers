"""
Prettier formatting utilities for dockerized execution.

This module provides Docker-based wrappers for the Prettier code formatter,
supporting markdown, text, and LaTeX files.

Import as:

import dev_scripts_helpers.documentation.lib_prettier as dshdlipr
"""

import logging
from typing import Any, List, Optional

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hio as hio
import helpers.hmarkdown_div_blocks as hmadiblo
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hdockerized_executables as hdocexec

_LOG = logging.getLogger(__name__)


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
    ret = hdocexec._build_and_run_docker_cmd(
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
