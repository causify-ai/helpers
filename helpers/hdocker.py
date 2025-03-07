"""
Import as:

import helpers.hdocker as hdocker
"""

import argparse
import copy
import hashlib
import logging
import os
import re
import shlex
import tempfile
import time
from typing import Any, Dict, List, Optional, Tuple

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# #############################################################################
# Docker utilities
# #############################################################################


# TODO(gp): Move to the repo_config.py or the config file.
def get_use_sudo() -> bool:
    """
    Check if Docker commands should be run with sudo.

    :return: Whether to use sudo for Docker commands.
    """
    use_sudo = False
    # if hserver.is_inside_docker():
    #    use_sudo = True
    return use_sudo


# TODO(gp): use_sudo should be set to None and the correct value inferred from
#  the repo config.
def get_docker_executable(use_sudo: bool) -> str:
    executable = "sudo " if use_sudo else ""
    executable += "docker"
    return executable


def container_exists(container_name: str, use_sudo: bool) -> Tuple[bool, str]:
    """
    Check if a Docker container is running by executing a command like:

    ```
    > docker container ls --filter=tmp.prettier -aq
    aed8a5ce33a9
    ```
    """
    _LOG.debug(hprint.to_str("container_name use_sudo"))
    #
    executable = get_docker_executable(use_sudo)
    cmd = f"{executable} container ls --filter name=/{container_name} -aq"
    _, container_id = hsystem.system_to_one_line(cmd)
    container_id = container_id.rstrip("\n")
    exists = container_id != ""
    _LOG.debug(hprint.to_str("exists container_id"))
    return exists, container_id


def image_exists(image_name: str, use_sudo: bool) -> Tuple[bool, str]:
    """
    Check if a Docker image already exists by executing a command like:

    ```
    > docker images tmp.prettier -aq
    aed8a5ce33a9
    ```
    """
    _LOG.debug(hprint.to_str("image_name use_sudo"))
    #
    executable = get_docker_executable(use_sudo)
    cmd = f"{executable} image ls --filter reference={image_name} -q"
    _, image_id = hsystem.system_to_one_line(cmd)
    image_id = image_id.rstrip("\n")
    exists = image_id != ""
    _LOG.debug(hprint.to_str("exists image_id"))
    return exists, image_id


def container_rm(container_name: str, use_sudo: bool) -> None:
    """
    Remove a Docker container by its name.

    :param container_name: Name of the Docker container to remove.
    :param use_sudo: Whether to use sudo for Docker commands.
    :raises AssertionError: If the container ID is not found.
    """
    _LOG.debug(hprint.to_str("container_name use_sudo"))
    #
    executable = get_docker_executable(use_sudo)
    # Find the container ID from the name.
    # Docker filter refers to container names using a leading `/`.
    cmd = f"{executable} container ls --filter name=/{container_name} -aq"
    _, container_id = hsystem.system_to_one_line(cmd)
    container_id = container_id.rstrip("\n")
    hdbg.dassert_ne(container_id, "")
    # Delete the container.
    _LOG.debug(hprint.to_str("container_id"))
    cmd = f"{executable} container rm --force {container_id}"
    hsystem.system(cmd)
    _LOG.debug("docker container '%s' deleted", container_name)


def volume_rm(volume_name: str, use_sudo: bool) -> None:
    """
    Remove a Docker volume by its name.

    :param volume_name: Name of the Docker volume to remove.
    :param use_sudo: Whether to use sudo for Docker commands.
    """
    _LOG.debug(hprint.to_str("volume_name use_sudo"))
    #
    executable = get_docker_executable(use_sudo)
    cmd = f"{executable} volume rm {volume_name}"
    hsystem.system(cmd)
    _LOG.debug("docker volume '%s' deleted", volume_name)


def wait_for_file_in_docker(
    container_id: str,
    docker_file_path: str,
    out_file_path: str,
    *,
    check_interval_in_secs: float = 0.5,
    timeout_in_secs: int = 10,
) -> None:
    """
    Wait for a file to be generated inside a Docker container and copy it to
    the host.

    This function periodically checks for the existence of a file inside
    a Docker container. Once the file is found, it copies the file to
    the specified output path on the host.

    :param container_id: ID of the Docker container.
    :param docker_file_path: Path to the file inside the Docker
        container.
    :param out_file_path: Path to copy the file to on the host.
    :param check_interval_in_secs: Time in seconds between checks.
    :param timeout_in_secs: Maximum time to wait for the file in
        seconds.
    :raises ValueError: If the file is not found within the timeout
        period.
    """
    _LOG.debug("Waiting for file: %s:%s", container_id, docker_file_path)
    start_time = time.time()
    while not os.path.exists(out_file_path):
        cmd = f"docker cp {container_id}:{docker_file_path} {out_file_path}"
        hsystem.system(cmd)
        if time.time() - start_time > timeout_in_secs:
            raise ValueError(
                f"Timeout reached. File not found: "
                f"{container_id}:{docker_file_path}"
            )
        time.sleep(check_interval_in_secs)
    _LOG.debug("File generated: %s", out_file_path)


def replace_shared_root_path(
    path: str, *, replace_ecs_tokyo: Optional[bool] = False
) -> str:
    """
    Replace root path of the shared directory based on the mapping.

    :param path: path to replace, e.g., `/data/shared`
    :param replace_ecs_tokyo: if True replace `ecs_tokyo` to `ecs` in the path
    :return: replaced shared data dir root path, e.g.,
    - `/data/shared/ecs_tokyo/.../20240522_173000.20240522_182500/` ->
        `/shared_data/ecs/.../20240522_173000.20240522_182500/`
    - `/data/shared/ecs/.../20240522_173000.20240522_182500` ->
        `/shared_data/ecs/.../20240522_173000.20240522_182500`
    """
    # Inside ECS, we keep the original shared data path and replace it only when
    # running inside Docker on the dev server.
    if hserver.is_inside_docker() and not hserver.is_inside_ecs_container():
        shared_data_dirs = hserver.get_shared_data_dirs()
        if replace_ecs_tokyo:
            # Make a copy to avoid modifying the original one.
            shared_data_dirs = copy.deepcopy(shared_data_dirs)
            shared_data_dirs["ecs_tokyo"] = "ecs"
        for shared_dir, docker_shared_dir in shared_data_dirs.items():
            path = path.replace(shared_dir, docker_shared_dir)
            _LOG.debug(
                "Running inside Docker on the dev server, thus replacing %s "
                "with %s",
                shared_dir,
                docker_shared_dir,
            )
    else:
        _LOG.debug("No replacement found, returning path as-is: %s", path)
    return path


# #############################################################################
# Dockerized executable utils.
# #############################################################################


# TODO(gp): build_container -> build_container_image
# TODO(gp): containter_name -> image_name
def build_container(
    container_name: str, dockerfile: str, force_rebuild: bool, use_sudo: bool
) -> str:
    """
    Build a Docker image from a Dockerfile.

    :param container_name: Name of the Docker container to build.
    :param dockerfile: Content of the Dockerfile for building the
        container.
    :param force_rebuild: Whether to force rebuild the Docker container.
    :param use_sudo: Whether to use sudo for Docker commands.
    :return: Name of the built Docker container.
    :raises AssertionError: If the container ID is not found.
    """
    _LOG.debug(hprint.to_str("container_name use_sudo"))
    dockerfile = hprint.dedent(dockerfile)
    _LOG.debug("Dockerfile:\n%s", dockerfile)
    # Compute the hash of the dockerfile and append it to the name to track the
    # content of the container.
    sha256_hash = hashlib.sha256(dockerfile.encode()).hexdigest()
    short_hash = sha256_hash[:8]
    image_name_out = f"{container_name}.{short_hash}"
    # Check if the container already exists. If not, build it.
    has_container, _ = image_exists(image_name_out, use_sudo)
    _LOG.debug(hprint.to_str("has_container"))
    if force_rebuild:
        _LOG.warning("Forcing to rebuild of container %s", container_name)
        has_container = False
    if not has_container:
        # Create a temporary Dockerfile.
        _LOG.info("Building Docker container...")
        # Delete temp file.
        delete = False
        with tempfile.NamedTemporaryFile(
            suffix=".Dockerfile", delete=delete
        ) as temp_dockerfile:
            txt = dockerfile.encode("utf-8")
            temp_dockerfile.write(txt)
            temp_dockerfile.flush()
            # Build the container.
            executable = get_docker_executable(use_sudo)
            cmd = (
                f"{executable} build -f {temp_dockerfile.name} -t"
                f" {image_name_out} ."
            )
            hsystem.system(cmd)
        _LOG.info("Building Docker container... done")
    return image_name_out


# #############################################################################


def get_host_git_root() -> str:
    """
    Get the Git root path on the host machine.
    """
    hdbg.dassert_in("CSFY_HOST_GIT_ROOT_PATH", os.environ)
    host_git_root_path = os.environ["CSFY_HOST_GIT_ROOT_PATH"]
    return host_git_root_path


# TODO(gp): This can even go to helpers.hdbg.
def _dassert_valid_path(file_path: str, is_input: bool) -> None:
    """
    Assert that a file path is valid, based on it being input or output.

    For input files, it ensures that the file or directory exists. For
    output files, it ensures that the enclosing directory exists.
    """
    _LOG.debug(hprint.to_str("file_path is_input"))
    if is_input:
        # If it's an input file, then `file_path` must exist as a file or a dir.
        hdbg.dassert_path_exists(file_path)
    else:
        # If it's an output, we might be writing a file that doesn't exist yet,
        # but we assume that at the least the directory should be already
        # present.
        hdbg.dassert(
            os.path.exists(file_path)
            or os.path.exists(os.path.dirname(file_path)),
            "Invalid path: %s",
            file_path,
        )


def _dassert_is_path_included(file_path: str, including_path: str) -> None:
    """
    Assert that a file path is included within another path.

    This function checks if the given file path starts with the
    specified including path. If not, it raises an assertion error.
    """
    _LOG.debug(hprint.to_str("file_path including_path"))
    # TODO(gp): Maybe we need to normalize the paths.
    hdbg.dassert(
        file_path.startswith(including_path),
        "'%s' needs to be underneath '%s'",
        file_path,
        including_path,
    )


# See docs/work_tools/docker/all.dockerized_flow.explanation.md for details.
def get_docker_mount_info(
    is_caller_host: bool, use_sibling_container_for_callee: bool
) -> Tuple[str, str, str]:
    """
    Get the Docker mount information for the current environment.

    This function determines the appropriate source and target paths for
    mounting a directory in a Docker container.

    Same inputs as `convert_caller_to_callee_docker_path()`.

    :return: A tuple containing
        - caller_mount_path: the mount path on the caller filesystem, e.g.,
            `/app` or `/Users/.../src/cmamp1`
        - callee_mount_path: the mount path inside the called Docker container,
            e.g., `/app`
        - the mount string, e.g.,
                `source={caller_mount_path},target={callee_mount_path}`
                type=bind,source=/app,target=/app
    """
    _LOG.debug(hprint.to_str("is_caller_host use_sibling_container_for_callee"))
    # Compute the mount path on the caller filesystem.
    if is_caller_host:
        # On the host machine, the mount path is the Git root.
        caller_mount_path = hgit.find_git_root()
    else:
        # Inside a Docker container, the mount path depends on the container
        # style.
        if use_sibling_container_for_callee:
            # For sibling containers, we need to get the Git root on the host.
            caller_mount_path = get_host_git_root()
        else:
            # For children containers, we need to get the local Git root on the
            # host.
            caller_mount_path = hgit.find_git_root()
    # The target mount path is always `/app` inside the Docker container.
    callee_mount_path = "/app"
    # Build the Docker mount string.
    mount = f"type=bind,source={caller_mount_path},target={callee_mount_path}"
    _LOG.debug(hprint.to_str("caller_mount_path callee_mount_path mount"))
    return caller_mount_path, callee_mount_path, mount


def convert_caller_to_callee_docker_path(
    caller_file_path: str,
    caller_mount_path: str,
    callee_mount_path: str,
    check_if_exists: bool,
    is_input: bool,
    is_caller_host: bool,
    use_sibling_container_for_callee: bool,
) -> str:
    """
    Convert a file path from the (current) caller filesystem to the called
    Docker container path.

    :param caller_file_path: The file path on the caller filesystem.
    :param caller_mount_path: The source mount path on the host machine.
    :param callee_mount_path: The target mount path inside the Docker
        container.
    :param check_if_exists: Whether to check if the file path exists.
    :param is_input: Whether the file path is an input file.
    :param is_caller_host: Whether the caller is running on the host
        machine or inside a Docker container.
    :param use_sibling_container_for_callee: Whether to use a sibling
        container or a children container
    :return: The converted file path inside the Docker container.
    """
    _LOG.debug(
        hprint.to_str(
            "caller_file_path caller_mount_path callee_mount_path"
            " check_if_exists is_input is_caller_host "
            " use_sibling_container_for_callee"
        )
    )
    if check_if_exists:
        _dassert_valid_path(caller_file_path, is_input)
    # Make the path absolute with respect to the (current) caller filesystem.
    abs_caller_file_path = os.path.abspath(caller_file_path)
    if is_caller_host:
        # On the host, the path needs to be underneath the caller mount point.
        caller_mount_point = caller_mount_path
    else:
        # We are inside a Docker container, so the path needs to be under
        # the local Git root, since this is the mount point.
        caller_mount_point = hgit.find_git_root()
    _ = use_sibling_container_for_callee
    _dassert_is_path_included(abs_caller_file_path, caller_mount_point)
    # Make the path relative to the caller mount point.
    rel_path = os.path.relpath(caller_file_path, caller_mount_point)
    docker_path = os.path.join(callee_mount_path, rel_path)
    docker_path = os.path.normpath(docker_path)
    #
    _LOG.debug(
        "  Converted %s -> %s -> %s", caller_file_path, rel_path, docker_path
    )
    return docker_path


# #############################################################################
# Dockerized prettier.
# #############################################################################


def run_dockerized_prettier(
    in_file_path: str,
    out_file_path: str,
    cmd_opts: List[str],
    *,
    return_cmd: bool = False,
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> Optional[str]:
    """
    Run `prettier` in a Docker container.

    From host:
    > ./dev_scripts_helpers/documentation/dockerized_prettier.py \
        --input /Users/saggese/src/helpers1/test.md --output test2.md
    > ./dev_scripts_helpers/documentation/dockerized_prettier.py \
        --input test.md --output test2.md

    From dev container:
    docker> ./dev_scripts_helpers/documentation/dockerized_prettier.py \
        --input test.md --output test2.md

    :param in_file_path: Path to the file to format with Prettier.
    :param out_file_path: Path to the output file.
    :param cmd_opts: Command options to pass to Prettier.
    :param force_rebuild: Whether to force rebuild the Docker container.
    :param use_sudo: Whether to use sudo for Docker commands.
    """
    _LOG.debug(
        hprint.to_str(
            "in_file_path out_file_path cmd_opts force_rebuild use_sudo"
        )
    )
    hdbg.dassert_isinstance(cmd_opts, list)
    # Build the container, if needed.
    container_name = "tmp.prettier"
    dockerfile = """
    # Use a Node.js image
    FROM node:18

    # Install Prettier globally
    RUN npm install -g prettier

    # Set a working directory inside the container
    WORKDIR /app

    # Run Prettier as the entry command
    ENTRYPOINT ["prettier"]
    """
    container_name = build_container(
        container_name, dockerfile, force_rebuild, use_sudo
    )
    # Convert files to Docker paths.
    is_caller_host = not hserver.is_inside_docker()
    use_sibling_container_for_callee = True
    caller_mount_path, callee_mount_path, mount = get_docker_mount_info(
        is_caller_host, use_sibling_container_for_callee
    )
    in_file_path = convert_caller_to_callee_docker_path(
        in_file_path,
        caller_mount_path,
        callee_mount_path,
        check_if_exists=True,
        is_input=True,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    out_file_path = convert_caller_to_callee_docker_path(
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
    executable = get_docker_executable(use_sudo)
    bash_cmd = f"/usr/local/bin/prettier {cmd_opts_as_str} {in_file_path}"
    if out_file_path != in_file_path:
        bash_cmd += f" > {out_file_path}"
    docker_cmd = (
        f"{executable} run --rm --user $(id -u):$(id -g)"
        " --entrypoint ''"
        f" --workdir {callee_mount_path} --mount {mount}"
        f" {container_name}"
        f' bash -c "{bash_cmd}"'
    )
    if return_cmd:
        return docker_cmd
    # TODO(gp): Note that `suppress_output=False` seems to hang the call.
    hsystem.system(docker_cmd)


# This a different approach I've tried to inject files inside a container
# and read them back. It's an interesting approach but it's flaky.
#
# # Inside a container we need to copy the input file to the container and
# # run the command inside the container.
# container_name = "tmp.prettier"
# # Generates an 8-character random string, e.g., x7vB9T2p
# random_string = "".join(
#     random.choices(string.ascii_lowercase + string.digits, k=8)
# )
# tmp_container_name = container_name + "." + random_string
# _LOG.debug("container_name=%s", container_name)
# # 1) Copy the input file in the current dir as a temp file to be in the
# # Docker context.
# tmp_in_file = f"{container_name}.{random_string}.in_file"
# cmd = "cp %s %s" % (in_file_path, tmp_in_file)
# hsystem.system(cmd)
# # 2) Create a temporary docker image with the input file inside.
# dockerfile = f"""
# FROM {container_name}
# COPY {tmp_in_file} /tmp/{tmp_in_file}
# """
# force_rebuild = True
# build_container(tmp_container_name, dockerfile, force_rebuild, use_sudo)
# cmd = f"rm {tmp_in_file}"
# hsystem.system(cmd)
# # 3) Run the command inside the container.
# executable = get_docker_executable(use_sudo)
# cmd_opts_as_str = " ".join(cmd_opts)
# tmp_out_file = f"{container_name}.{random_string}.out_file"
# docker_cmd = (
#     # We can run as root user (i.e., without `--user`) since we don't
#     # need to share files with the external filesystem.
#     f"{executable} run -d"
#     " --entrypoint ''"
#     f" {tmp_container_name}"
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
# cmd = f"docker image rm -f {tmp_container_name}"
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
    # Return all the arguments in a dictionary with names that match the
    # function signature of `run_dockerized_pandoc`.
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
    cmd.append(f'{params["input"]}')
    cmd.append(f'--output {params["output"]}')
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
    *,
    return_cmd: bool = False,
    use_sudo: bool = False,
) -> Optional[str]:
    """
    Run `pandoc` in a Docker container.

    Same as `run_dockerized_prettier()` but for `pandoc`.
    """
    _LOG.debug(hprint.to_str("cmd return_cmd use_sudo"))
    container_name = "pandoc/core"
    # Convert files to Docker paths.
    is_caller_host = not hserver.is_inside_docker()
    use_sibling_container_for_callee = True
    caller_mount_path, callee_mount_path, mount = get_docker_mount_info(
        is_caller_host, use_sibling_container_for_callee
    )
    #
    param_dict = convert_pandoc_cmd_to_arguments(cmd)
    param_dict["input"] = convert_caller_to_callee_docker_path(
        param_dict["input"],
        caller_mount_path,
        callee_mount_path,
        check_if_exists=True,
        is_input=True,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    param_dict["output"] = convert_caller_to_callee_docker_path(
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
            value_tmp = convert_caller_to_callee_docker_path(
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
    executable = get_docker_executable(use_sudo)
    docker_cmd = (
        f"{executable} run --rm --user $(id -u):$(id -g)"
        f" --workdir {callee_mount_path} --mount {mount}"
        f" {container_name}"
        f" {pandoc_cmd}"
    )
    if return_cmd:
        return docker_cmd
    # TODO(gp): Note that `suppress_output=False` seems to hang the call.
    hsystem.system(docker_cmd)
    return None


# #############################################################################
# Dockerized markdown_toc.
# #############################################################################


def run_dockerized_markdown_toc(
    in_file_path: str, force_rebuild: bool, cmd_opts: List[str], *, use_sudo: bool
) -> None:
    """
    Same as `run_dockerized_prettier()` but for `markdown-toc`.
    """
    # https://github.com/jonschlinkert/markdown-toc
    _LOG.debug(hprint.to_str("cmd_opts in_file_path force_rebuild use_sudo"))
    hdbg.dassert_isinstance(cmd_opts, list)
    # Build the container, if needed.
    container_name = "tmp.markdown_toc"
    dockerfile = """
    # Use a Node.js image
    FROM node:18

    # Install Prettier globally
    RUN npm install -g markdown-toc

    # Set a working directory inside the container
    WORKDIR /app
    """
    container_name = build_container(
        container_name, dockerfile, force_rebuild, use_sudo
    )
    # Convert files to Docker paths.
    is_caller_host = not hserver.is_inside_docker()
    use_sibling_container_for_callee = True
    caller_mount_path, callee_mount_path, mount = get_docker_mount_info(
        is_caller_host, use_sibling_container_for_callee
    )
    in_file_path = convert_caller_to_callee_docker_path(
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
    executable = get_docker_executable(use_sudo)
    bash_cmd = f"/usr/local/bin/markdown-toc {cmd_opts_as_str} -i {in_file_path}"
    docker_cmd = (
        f"{executable} run --rm --user $(id -u):$(id -g)"
        f" --workdir {callee_mount_path} --mount {mount}"
        f" {container_name}"
        f' bash -c "{bash_cmd}"'
    )
    # TODO(gp): Note that `suppress_output=False` seems to hang the call.
    hsystem.system(docker_cmd)


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
        -interaction=nonstopmode -halt-on-error -shell-escape
    ```

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
    in_file_path = cmd[1]
    hdbg.dassert(
        not in_file_path.startswith("-"), "Invalid input file '%s'", in_file_path
    )
    hdbg.dassert_file_exists(in_file_path)
    cmd = cmd[2:]
    _LOG.debug(hprint.to_str("cmd"))
    #
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-directory", required=True)
    # Latex uses options like `-XYZ` which confuse `argparse` so we need to
    # replace `-XYZ` with `--XYZ`.
    cmd = [re.sub(r"^-", r"--", cmd_opts) for cmd_opts in cmd]
    _LOG.debug(hprint.to_str("cmd"))
    # Parse known arguments and capture the rest.
    args, unknown_args = parser.parse_known_args(cmd)
    _LOG.debug(hprint.to_str("args unknown_args"))
    # Return all the arguments in a dictionary with names that match the
    # function signature of `run_dockerized_pandoc`.
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

    This function takes the parsed pandoc arguments and converts them
    back into a command string that can be executed directly or in a
    Dockerized container.

    :return: The constructed pandoc command string.
    """
    cmd = []
    hdbg.dassert_is_subset(
        params.keys(), ["input", "output-directory", "in_dir_params", "cmd_opts"]
    )
    cmd.append(f'{params["input"]}')
    key = "output-directory"
    value = params[key]
    cmd.append(f"-{key} {value}")
    for key, value in params["in_dir_params"].items():
        if value:
            cmd.append(f"-{key} {value}")
    #
    hdbg.dassert_isinstance(params["cmd_opts"], list)
    cmd.append(" ".join(params["cmd_opts"]))
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
    return_cmd: bool = False,
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> Optional[str]:
    """
    Run `latex` in a Docker container.

    Same as `run_dockerized_prettier()` but for `pandoc`.
    """
    _LOG.debug(hprint.to_str("cmd return_cmd use_sudo"))
    container_name = "tmp.latex"
    dockerfile = """
    # Use a lightweight base image
    FROM debian:bullseye-slim

    # Set environment variables to avoid interactive prompts
    ENV DEBIAN_FRONTEND=noninteractive

    # Update and install only the minimal TeX Live packages
    RUN apt-get update && \
        apt-get install -y --no-install-recommends \
        texlive-latex-base \
        texlive-latex-recommended \
        texlive-fonts-recommended \
        texlive-latex-extra \
        lmodern \
        tikzit \
        && apt-get clean && \
        rm -rf /var/lib/apt/lists/*

    # Verify LaTeX is installed
    RUN latex --version

    # Set working directory
    WORKDIR /workspace

    # Default command
    CMD [ "bash" ]
    """
    container_name = build_container(
        container_name, dockerfile, force_rebuild, use_sudo
    )
    # Convert files to Docker.
    is_caller_host = not hserver.is_inside_docker()
    use_sibling_container_for_callee = True
    caller_mount_path, callee_mount_path, mount = get_docker_mount_info(
        is_caller_host, use_sibling_container_for_callee
    )
    #
    param_dict = convert_latex_cmd_to_arguments(cmd)
    param_dict["input"] = convert_caller_to_callee_docker_path(
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
    param_dict[key] = convert_caller_to_callee_docker_path(
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
            value_tmp = convert_caller_to_callee_docker_path(
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
    executable = get_docker_executable(use_sudo)
    docker_cmd = (
        f"{executable} run --rm --user $(id -u):$(id -g)"
        f" --workdir {callee_mount_path} --mount {mount}"
        f" {container_name}"
        f" {latex_cmd}"
    )
    if return_cmd:
        return docker_cmd
    # TODO(gp): Note that `suppress_output=False` seems to hang the call.
    hsystem.system(docker_cmd)
    return None


# #############################################################################
# Dockerized llm_transform.
# #############################################################################


def run_dockerized_llm_transform(
    in_file_path: str,
    out_file_path: str,
    cmd_opts: List[str],
    *,
    return_cmd: bool = False,
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> Optional[str]:
    """
    Run _llm_transform.py in a Docker container with all its dependencies.
    """
    _LOG.debug(
        hprint.to_str(
            "in_file_path out_file_path cmd_opts force_rebuild use_sudo"
        )
    )
    hdbg.dassert_in("OPENAI_API_KEY", os.environ)
    hdbg.dassert_isinstance(cmd_opts, list)
    # Build the container, if needed.
    container_name = "tmp.llm_transform"
    dockerfile = """
    FROM python:3.12-alpine

    # Install Bash.
    #RUN apk add --no-cache bash

    # Set Bash as the default shell.
    #SHELL ["/bin/bash", "-c"]

    # Install pip packages.
    RUN pip install --no-cache-dir openai
    """
    container_name = build_container(
        container_name, dockerfile, force_rebuild, use_sudo
    )
    # Convert files to Docker paths.
    is_caller_host = not hserver.is_inside_docker()
    use_sibling_container_for_callee = True
    caller_mount_path, callee_mount_path, mount = get_docker_mount_info(
        is_caller_host, use_sibling_container_for_callee
    )
    in_file_path = convert_caller_to_callee_docker_path(
        in_file_path,
        caller_mount_path,
        callee_mount_path,
        check_if_exists=True,
        is_input=True,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    out_file_path = convert_caller_to_callee_docker_path(
        out_file_path,
        caller_mount_path,
        callee_mount_path,
        check_if_exists=False,
        is_input=False,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    helpers_root = hgit.find_helpers_root()
    helpers_root = convert_caller_to_callee_docker_path(
        helpers_root,
        caller_mount_path,
        callee_mount_path,
        check_if_exists=True,
        is_input=False,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    git_root = hgit.find_git_root()
    script = hsystem.find_file_in_repo("_llm_transform.py", root_dir=git_root)
    script = convert_caller_to_callee_docker_path(
        script,
        caller_mount_path,
        callee_mount_path,
        check_if_exists=True,
        is_input=True,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    cmd_opts_as_str = " ".join(cmd_opts)
    executable = get_docker_executable(use_sudo)
    docker_cmd = (
        f"{executable} run --rm --user $(id -u):$(id -g)"
        f" -e OPENAI_API_KEY -e PYTHONPATH={helpers_root}"
        f" --workdir {callee_mount_path} --mount {mount}"
        f" {container_name}"
        f" {script} -i {in_file_path} -o {out_file_path} {cmd_opts_as_str}"
    )
    if return_cmd:
        return docker_cmd
    # TODO(gp): Note that `suppress_output=False` seems to hang the call.
    hsystem.system(docker_cmd)


# #############################################################################


def run_dockerized_plantuml(
    img_dir_path: str,
    code_file_path: str,
    dst_ext: str,
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> None:
    """
    Run `plantUML` in a Docker container.

    :param img_dir_path: path to the dir where the image will be saved
    :param code_file_path: path to the code of the image to render
    :param dst_ext: extension of the rendered image, e.g., "svg", "png"
    :param force_rebuild: whether to force rebuild the Docker container
    :param use_sudo: whether to use sudo for Docker commands
    """
    _LOG.debug(
        hprint.to_str(
            "img_dir_path code_file_path dst_ext force_rebuild use_sudo"
        )
    )
    # Build the container, if needed.
    container_name = "tmp.plantuml"
    dockerfile = """
    # Use a lightweight base image.
    FROM debian:bullseye-slim

    # Install plantUML.
    RUN apt-get update
    RUN apt-get install -y --no-install-recommends plantuml
    """
    container_name = build_container(
        container_name, dockerfile, force_rebuild, use_sudo
    )
    # Convert files to Docker paths.
    is_caller_host = not hserver.is_inside_docker()
    use_sibling_container_for_callee = True
    caller_mount_path, callee_mount_path, mount = get_docker_mount_info(
        is_caller_host, use_sibling_container_for_callee
    )
    img_dir_path = convert_caller_to_callee_docker_path(
        img_dir_path,
        caller_mount_path,
        callee_mount_path,
        check_if_exists=True,
        is_input=False,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    code_file_path = convert_caller_to_callee_docker_path(
        code_file_path,
        caller_mount_path,
        callee_mount_path,
        check_if_exists=True,
        is_input=True,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    plantuml_cmd = f"plantuml -t{dst_ext} -o {img_dir_path} {code_file_path}"
    executable = get_docker_executable(use_sudo)
    docker_cmd = (
        f"{executable} run --rm --user $(id -u):$(id -g)"
        " --entrypoint ''"
        f" --workdir {callee_mount_path} --mount {mount}"
        f" {container_name}"
        f' bash -c "{plantuml_cmd}"'
    )
    hsystem.system(docker_cmd)


# #############################################################################


def run_dockerized_mermaid(
    img_path: str,
    code_file_path: str,
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> None:
    """
    Run `mermaid` in a Docker container.

    :param img_path: path to the image to be created
    :param code_file_path: path to the code of the image to render
    :param force_rebuild: whether to force rebuild the Docker container
    :param use_sudo: whether to use sudo for Docker commands
    """
    _LOG.debug(hprint.to_str("img_path code_file_path force_rebuild use_sudo"))
    # Build the container, if needed.
    container_name = "tmp.mermaid"
    puppeteer_cache_path = """
    const {join} = require('path');

    /**
     * @type {import("puppeteer").Configuration}
     */
    module.exports = {
      // Changes the cache location for Puppeteer.
      cacheDirectory: join(__dirname, '.cache', 'puppeteer'),
    };
    """
    dockerfile = f"""
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
    container_name = build_container(
        container_name, dockerfile, force_rebuild, use_sudo
    )
    # Convert files to Docker paths.
    is_caller_host = not hserver.is_inside_docker()
    use_sibling_container_for_callee = True
    caller_mount_path, callee_mount_path, mount = get_docker_mount_info(
        is_caller_host, use_sibling_container_for_callee
    )
    img_path = convert_caller_to_callee_docker_path(
        img_path,
        caller_mount_path,
        callee_mount_path,
        check_if_exists=True,
        is_input=False,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    code_file_path = convert_caller_to_callee_docker_path(
        code_file_path,
        caller_mount_path,
        callee_mount_path,
        check_if_exists=True,
        is_input=True,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    puppeteer_config_path = convert_caller_to_callee_docker_path(
        "puppeteerConfig.json",
        caller_mount_path,
        callee_mount_path,
        check_if_exists=True,
        is_input=False,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    mermaid_cmd = f"mmdc --puppeteerConfigFile {puppeteer_config_path} -i {code_file_path} -o {img_path}"
    executable = get_docker_executable(use_sudo)
    docker_cmd = (
        f"{executable} run --rm --user $(id -u):$(id -g)"
        " --entrypoint ''"
        f" --workdir {callee_mount_path} --mount {mount}"
        f" {container_name}"
        f' bash -c "{mermaid_cmd}"'
    )
    hsystem.system(docker_cmd)
