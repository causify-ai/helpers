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
import time
from typing import cast, Any, Dict, List, Optional, Tuple

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# #############################################################################
# Docker utilities
# #############################################################################


# TODO(gp): This is a function of the architecture. Move to the repo_config.py
# or the config file.
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
    _LOG.debug(hprint.func_signature_to_str())
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
    _LOG.debug(hprint.func_signature_to_str())
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
    _LOG.debug(hprint.func_signature_to_str())
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
    _LOG.debug(hprint.func_signature_to_str())
    #
    executable = get_docker_executable(use_sudo)
    cmd = f"{executable} volume rm {volume_name}"
    hsystem.system(cmd)
    _LOG.debug("docker volume '%s' deleted", volume_name)


# #############################################################################


def get_current_arch() -> str:
    """
    Return the architecture that we are running on (e.g., arm64, aarch64,
    x86_64).
    """
    cmd = "uname -m"
    _, current_arch = hsystem.system_to_one_line(cmd)
    _LOG.debug(hprint.to_str("current_arch"))
    return cast(str, current_arch)


def _is_compatible_arch(val1: str, val2: str) -> bool:
    valid_arch = ["x86_64", "amd64", "aarch64", "arm64"]
    hdbg.dassert_in(val1, valid_arch)
    hdbg.dassert_in(val2, valid_arch)
    if val1 == val2:
        return True
    compatible_sets = [{"x86_64", "amd64"}, {"aarch64", "arm64"}]
    for comp_set in compatible_sets:
        if {val1, val2}.issubset(comp_set):
            return True
    return False


def check_image_compatibility_with_current_arch(
    image_name: str,
    *,
    use_sudo: Optional[bool] = None,
    pull_image_if_needed: bool = True,
    assert_on_error: bool = True,
) -> None:
    """
    Check if the Docker image is compatible with the current architecture.

    :param image_name: Name of the Docker image to check.
    :param use_sudo: Whether to use sudo for Docker commands.
    :param pull_image_if_needed: Whether to pull the image if it doesn't
        exist.
    :param assert_on_error: Whether to raise an error if the image is
        not compatible with the current architecture.
    """
    _LOG.debug(hprint.func_signature_to_str())
    hdbg.dassert_ne(image_name, "")
    if use_sudo is None:
        use_sudo = get_use_sudo()
    # Get the architecture that we are running on.
    current_arch = get_current_arch()
    # > docker image inspect \
    #   623860924167.dkr.ecr.eu-north-1.amazonaws.com/helpers:local-saggese-1.1.0 \
    #   --format '{{.Architecture}}'
    # arm64
    # Check and pull the image if needed.
    has_image, _ = image_exists(image_name, use_sudo)
    if not has_image:
        _LOG.warning("Image '%s' not found: trying to pull it", image_name)
        if pull_image_if_needed:
            cmd = f"docker pull {image_name}"
            hsystem.system(cmd)
        else:
            hdbg.dfatal("Image '%s' not found", image_name)
    # Check the image architecture.
    executable = get_docker_executable(use_sudo)
    cmd = f"{executable} inspect {image_name}" + r" --format '{{.Architecture}}'"
    _, image_arch = hsystem.system_to_one_line(cmd)
    _LOG.debug(hprint.to_str("image_arch"))
    # Check architecture compatibility.
    if not _is_compatible_arch(current_arch, image_arch):
        msg = f"Running architecture '{current_arch}' != image architecture '{image_arch}'"
        if assert_on_error:
            hdbg.dfatal(msg)
        else:
            _LOG.warning(msg)
    _LOG.debug(
        "Running architecture '%s' and image architecture '%s' are compatible",
        current_arch,
        image_arch,
    )


# #############################################################################


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


def get_docker_base_cmd(use_sudo: bool) -> List[str]:
    """
    Get the base command for running a Docker container.

    E.g.,
    ```
    docker run --rm --user $(id -u):$(id -g) \
        -e CSFY_AWS_PROFILE -e CSFY_ECR_BASE_PATH \
        ...
        -e OPENAI_API_KEY
    ```

    :param use_sudo: Whether to use sudo for Docker commands.
    :return: The base command for running a Docker container.
    """
    docker_executable = get_docker_executable(use_sudo)
    # Get all the environment variables that start with `AM_`, `CK_`, `CSFY_`.
    vars_to_pass = [
        v
        for v in os.environ.keys()
        if
        # TODO(gp): We should only pass the `CSFY_` vars.
        v.startswith("AM_") or v.startswith("CK_") or v.startswith("CSFY_")
    ]
    vars_to_pass.append("OPENAI_API_KEY")
    vars_to_pass = sorted(vars_to_pass)
    vars_to_pass_as_str = " ".join(f"-e {v}" for v in vars_to_pass)
    # Build the command as a list.
    docker_cmd = [
        docker_executable,
        "run --rm",
        "--user $(id -u):$(id -g)",
        vars_to_pass_as_str,
    ]
    return docker_cmd


# TODO(gp): Pass `use_cache` to control using Docker cache.
def build_container_image(
    image_name: str,
    dockerfile: str,
    force_rebuild: bool,
    use_sudo: bool,
    *,
    use_cache: bool = True,
    incremental: bool = True,
) -> str:
    """
    Build a Docker image from a Dockerfile.

    :param image_name: Name of the Docker container to build.
    :param dockerfile: Content of the Dockerfile for building the
        container.
    :param force_rebuild: Whether to force rebuild the Docker container.
        There are two level of caching. The first level of caching is
        our approach of skipping `docker build` if the image already
        exists and the Dockerfile hasn't changed. The second level is
        the Docker cache itself, which is invalidated by `--no-cache`.
    :param use_sudo: Whether to use sudo for Docker commands.
    :return: Name of the built Docker container.
    :raises AssertionError: If the container ID is not found.
    """
    _LOG.debug(hprint.func_signature_to_str("dockerfile"))
    #
    dockerfile = hprint.dedent(dockerfile)
    _LOG.debug("Dockerfile:\n%s", dockerfile)
    # Get the current architecture.
    current_arch = get_current_arch()
    # Compute the hash of the dockerfile and append it to the name to track the
    # content of the container.
    sha256_hash = hashlib.sha256(dockerfile.encode()).hexdigest()
    short_hash = sha256_hash[:8]
    # Build the name of the container image.
    image_name_out = f"{image_name}.{current_arch}.{short_hash}"
    # Check if the container already exists. If not, build it.
    has_container, _ = image_exists(image_name_out, use_sudo)
    _LOG.debug(hprint.to_str("has_container"))
    use_cache = False
    if force_rebuild:
        _LOG.warning(
            "Forcing to rebuild of container '%s' without cache",
            image_name,
        )
        has_container = False
        use_cache = False
    _LOG.debug(hprint.to_str("has_container use_cache"))
    if not has_container:
        # Create a temporary Dockerfile.
        _LOG.warning("Building Docker container...")
        build_context_dir = "tmp.docker_build"
        # There might be already some file in the build context dir, so the
        # caller needs to specify `incremental`.
        hio.create_dir(build_context_dir, incremental=incremental)
        temp_dockerfile = os.path.join(build_context_dir, "Dockerfile")
        hio.to_file(temp_dockerfile, dockerfile)
        # Build the container.
        docker_executable = get_docker_executable(use_sudo)
        cmd = [
            f"{docker_executable} build",
            f"-f {temp_dockerfile}",
            f"-t {image_name_out}",
            # "--platform linux/aarch64",
        ]
        if not use_cache:
            cmd.append("--no-cache")
        cmd.append(build_context_dir)
        cmd = " ".join(cmd)
        hsystem.system(cmd, suppress_output=False)
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
    _LOG.debug(hprint.func_signature_to_str())
    if is_input:
        # If it's an input file, then `file_path` must exist as a file or a dir.
        hdbg.dassert_path_exists(file_path)
    else:
        # If it's an output, we might be writing a file that doesn't exist yet,
        # but we assume that at the least the directory should be already
        # present.
        dir_name = os.path.normpath(os.path.dirname(file_path))
        hio.create_dir(dir_name, incremental=True)
        hdbg.dassert(
            os.path.exists(file_path) or os.path.exists(dir_name),
            "Invalid path: '%s' and '%s' don't exist",
            file_path,
            dir_name,
        )


def _dassert_is_path_included(file_path: str, including_path: str) -> None:
    """
    Assert that a file path is included within another path.

    This function checks if the given file path starts with the
    specified including path. If not, it raises an assertion error.
    """
    _LOG.debug(hprint.func_signature_to_str())
    # TODO(gp): Maybe we need to normalize the paths.
    hdbg.dassert(
        file_path.startswith(including_path),
        "'%s' needs to be underneath '%s'",
        file_path,
        including_path,
    )


def get_docker_mount_info(
    is_caller_host: bool, use_sibling_container_for_callee: bool
) -> Tuple[str, str, str]:
    """
    Get the Docker mount information for the current environment.

    This function determines the appropriate source and target paths for
    mounting a directory in a Docker container.
    See docs/work_tools/docker/all.dockerized_flow.explanation.md for details.

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
    _LOG.debug(hprint.func_signature_to_str())
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
    _LOG.debug(hprint.func_signature_to_str())
    hdbg.dassert_ne(caller_file_path, "")
    hdbg.dassert_ne(caller_mount_path, "")
    hdbg.dassert_ne(callee_mount_path, "")
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
    _LOG.debug(hprint.to_str("caller_file_path caller_mount_point"))
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
    cmd_opts: List[str],
    out_file_path: str,
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
    _LOG.debug(hprint.func_signature_to_str())
    hdbg.dassert_isinstance(cmd_opts, list)
    # Build the container, if needed.
    container_image = "tmp.prettier"
    dockerfile = r"""
    # Use a Node.js image
    FROM node:18

    # Install Prettier globally
    RUN npm install -g prettier

    # Set a working directory inside the container
    WORKDIR /app

    # Run Prettier as the entry command
    ENTRYPOINT ["prettier"]
    """
    container_image = build_container_image(
        container_image, dockerfile, force_rebuild, use_sudo
    )
    # Convert files to Docker paths.
    is_caller_host = not hserver.is_inside_docker()
    # TODO(gp): After fix for CmampTask10710 enable this.
    # use_sibling_container_for_callee = hserver.use_docker_sibling_containers()
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
    bash_cmd = f"/usr/local/bin/prettier {cmd_opts_as_str} {in_file_path}"
    if out_file_path != in_file_path:
        bash_cmd += f" > {out_file_path}"
    # Build the Docker command.
    docker_cmd = get_docker_base_cmd(use_sudo)
    docker_cmd.extend(
        [
            " --entrypoint ''",
            f"--workdir {callee_mount_path} --mount {mount}",
            f"{container_image}",
            f'bash -c "{bash_cmd}"',
        ]
    )
    docker_cmd = " ".join(docker_cmd)
    if return_cmd:
        ret = docker_cmd
    else:
        # TODO(gp): Note that `suppress_output=False` seems to hang the call.
        hsystem.system(docker_cmd)
        ret = None
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
    container_type: str,
    *,
    return_cmd: bool = False,
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> Optional[str]:
    """
    Run `pandoc` in a Docker container.
    """
    _LOG.debug(hprint.func_signature_to_str())
    if container_type == "pandoc_only":
        container_image = "pandoc/core"
        incremental = False
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
        container_image = build_container_image(
            container_image,
            dockerfile,
            force_rebuild,
            use_sudo,
            incremental=incremental,
        )
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
    docker_cmd = get_docker_base_cmd(use_sudo)
    docker_cmd.extend(
        [
            f"--workdir {callee_mount_path} --mount {mount}",
            f"{container_image}",
            f"{pandoc_cmd}",
        ]
    )
    docker_cmd = " ".join(docker_cmd)
    if return_cmd:
        ret = docker_cmd
    else:
        # TODO(gp): Note that `suppress_output=False` seems to hang the call.
        hsystem.system(docker_cmd)
        ret = None
    return ret


# #############################################################################
# Dockerized markdown_toc.
# #############################################################################


def run_dockerized_markdown_toc(
    in_file_path: str,
    cmd_opts: List[str],
    *,
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> None:
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
    container_image = build_container_image(
        container_image, dockerfile, force_rebuild, use_sudo
    )
    # Convert files to Docker paths.
    is_caller_host = not hserver.is_inside_docker()
    # TODO(gp): After fix for CmampTask10710 enable this.
    # use_sibling_container_for_callee = hserver.use_docker_sibling_containers()
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
    bash_cmd = f"/usr/local/bin/markdown-toc {cmd_opts_as_str} -i {in_file_path}"
    docker_cmd = get_docker_base_cmd(use_sudo)
    docker_cmd.extend(
        [
            f"--workdir {callee_mount_path} --mount {mount}",
            f"{container_image}",
            f'bash -c "{bash_cmd}"',
        ]
    )
    docker_cmd = " ".join(docker_cmd)
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
    cmd.append(f'{params["input"]}')
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
    """
    _LOG.debug(hprint.func_signature_to_str())
    container_image = "tmp.latex"
    dockerfile = r"""
    # Use a lightweight base image.
    FROM debian:bullseye-slim

    # Set environment variables to avoid interactive prompts.
    ENV DEBIAN_FRONTEND=noninteractive

    # Update.
    RUN apt-get update

    # Install only the minimal TeX Live packages.
    RUN apt-get install -y --no-install-recommends \
        texlive-latex-base \
        texlive-latex-recommended \
        texlive-fonts-recommended \
        texlive-latex-extra \
        lmodern \
        tikzit

    RUN rm -rf /var/lib/apt/lists/* \
        && apt-get clean

    # Verify LaTeX is installed.
    RUN latex --version

    # Set working directory.
    WORKDIR /workspace

    # Default command.
    CMD [ "bash" ]
    """
    container_image = build_container_image(
        container_image, dockerfile, force_rebuild, use_sudo
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
    docker_cmd = get_docker_base_cmd(use_sudo)
    docker_cmd.extend(
        [
            f"--workdir {callee_mount_path} --mount {mount}",
            f"{container_image}",
            f"{latex_cmd}",
        ]
    )
    docker_cmd = " ".join(docker_cmd)
    # TODO(gp): Factor this out.
    if return_cmd:
        ret = docker_cmd
    else:
        # TODO(gp): Note that `suppress_output=False` seems to hang the call.
        hsystem.system(docker_cmd)
        ret = None
    return ret


def run_basic_latex(
    in_file_name: str,
    cmd_opts: List[str],
    run_latex_again: bool,
    out_file_name: str,
    *,
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
        force_rebuild=force_rebuild,
        use_sudo=use_sudo,
    )
    if run_latex_again:
        run_dockerized_latex(
            cmd,
            force_rebuild=force_rebuild,
            use_sudo=use_sudo,
        )
    # Get the path of the output file created by Latex.
    file_out = os.path.basename(in_file_name).replace(".tex", ".pdf")
    _LOG.debug("file_out=%s", file_out)
    hdbg.dassert_path_exists(file_out)
    # Move to the proper output location.
    if file_out != out_file_name:
        cmd = "mv %s %s" % (file_out, out_file_name)
        hsystem.system(cmd)


# #############################################################################
# Dockerized ImageMagick.
# #############################################################################


def run_dockerized_imagemagick(
    in_file_path: str,
    cmd_opts: List[str],
    out_file_path: str,
    *,
    return_cmd: bool = False,
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> Optional[str]:
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
    container_image = build_container_image(
        container_image, dockerfile, force_rebuild, use_sudo
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
    cmd_opts_as_str = " ".join(cmd_opts)
    cmd = f"magick {cmd_opts_as_str} {in_file_path} {out_file_path}"
    docker_cmd = get_docker_base_cmd(use_sudo)
    docker_cmd.extend(
        [
            "--entrypoint ''",
            f"--workdir {callee_mount_path} --mount {mount}",
            container_image,
            f'bash -c "{cmd}"',
        ]
    )
    docker_cmd = " ".join(docker_cmd)
    # TODO(gp): Factor this out.
    if return_cmd:
        ret = docker_cmd
    else:
        # TODO(gp): Note that `suppress_output=False` seems to hang the call.
        hsystem.system(docker_cmd)
        ret = None
    return ret


def dockerized_tikz_to_bitmap(
    in_file_path: str,
    cmd_opts: List[str],
    out_file_path: str,
    *,
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> None:
    """
    Convert a TikZ file to a PDF file.
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
        force_rebuild=force_rebuild,
        use_sudo=use_sudo,
    )
    # Convert the PDF to a bitmap.
    run_dockerized_imagemagick(
        file_out,
        cmd_opts,
        out_file_path,
        force_rebuild=force_rebuild,
        use_sudo=use_sudo,
    )


# #############################################################################


def run_dockerized_plantuml(
    in_file_path: str,
    out_file_path: str,
    dst_ext: str,
    *,
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> None:
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
    container_image = build_container_image(
        container_image, dockerfile, force_rebuild, use_sudo
    )
    # Convert files to Docker paths.
    is_caller_host = not hserver.is_inside_docker()
    use_sibling_container_for_callee = True
    caller_mount_path, callee_mount_path, mount = get_docker_mount_info(
        is_caller_host, use_sibling_container_for_callee
    )
    out_file_path = convert_caller_to_callee_docker_path(
        out_file_path,
        caller_mount_path,
        callee_mount_path,
        check_if_exists=True,
        is_input=False,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
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
    plantuml_cmd = f"plantuml -t{dst_ext} -o {out_file_path} {in_file_path}"
    docker_cmd = get_docker_base_cmd(use_sudo)
    docker_cmd.extend(
        [
            " --entrypoint ''",
            f"--workdir {callee_mount_path} --mount {mount}",
            f"{container_image}",
            f'bash -c "{plantuml_cmd}"',
        ]
    )
    docker_cmd = " ".join(docker_cmd)
    hsystem.system(docker_cmd)


# #############################################################################


def run_dockerized_mermaid(
    in_file_path: str,
    out_file_path: str,
    *,
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> None:
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
        check_if_exists=True,
        is_input=False,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    mermaid_cmd = f" -i {in_file_path} -o {out_file_path}"
    docker_cmd = get_docker_base_cmd(use_sudo)
    docker_cmd.extend(
        [
            f"--workdir {callee_mount_path} --mount {mount}",
            container_image,
            mermaid_cmd,
        ]
    )
    docker_cmd = " ".join(docker_cmd)
    hsystem.system(docker_cmd)


# TODO(gp): Factor out the common code with `run_dockerized_mermaid()`.
def run_dockerized_mermaid2(
    in_file_path: str,
    out_file_path: str,
    *,
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
    container_image = build_container_image(
        container_image, dockerfile, force_rebuild, use_sudo
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
        check_if_exists=True,
        is_input=False,
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
    mermaid_cmd = (
        f"mmdc --puppeteerConfigFile {puppeteer_config_path}"
        + f" -i {in_file_path} -o {out_file_path}"
    )
    # TODO(gp): Factor out building the docker cmd.
    docker_cmd = get_docker_base_cmd(use_sudo)
    docker_cmd.extend(
        [
            "--entrypoint ''",
            f"--workdir {callee_mount_path} --mount {mount}",
            container_image,
            f'bash -c "{mermaid_cmd}"',
        ]
    )
    docker_cmd = " ".join(docker_cmd)
    hsystem.system(docker_cmd)


# #############################################################################


def run_dockerized_graphviz(
    in_file_path: str,
    cmd_opts: List[str],
    out_file_path: str,
    *,
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> None:
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
    dockerfile = rf"""
    FROM alpine:latest

    RUN apk add --no-cache graphviz
    """
    container_image = build_container_image(
        container_image, dockerfile, force_rebuild, use_sudo
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
        check_if_exists=True,
        is_input=False,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    cmd_opts = " ".join(cmd_opts)
    graphviz_cmd = [
        "dot",
        f"{cmd_opts}",
        "-T png",
        "-Gdpi=300",
        f"-o {out_file_path}",
        in_file_path,
    ]
    graphviz_cmd = " ".join(graphviz_cmd)
    docker_cmd = get_docker_base_cmd(use_sudo)
    docker_cmd.extend(
        [
            f"--workdir {callee_mount_path} --mount {mount}",
            container_image,
            graphviz_cmd,
        ]
    )
    docker_cmd = " ".join(docker_cmd)
    hsystem.system(docker_cmd)
