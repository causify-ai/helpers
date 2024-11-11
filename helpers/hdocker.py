"""
Import as:

import helpers.hdocker as hdocker
"""

import copy
import logging
import os
import tempfile
from typing import Optional, Tuple

import helpers.hdbg as hdbg
import helpers.henv as henv
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

def replace_shared_root_path(
    path: str, *, replace_ecs_tokyo: Optional[bool] = False
) -> str:
    """
    Replace root path of the shared directory based on the mapping.

    :param path: path to replace, e.g., `/data/shared`
    :param replace_ecs_tokyo: if True replace `ecs_tokyo` to `ecs` in the path
    :return: replaced shared data dir root path, e.g.,
    - `/data/shared/ecs_tokyo/test/system_reconciliation/C11a/prod/20240522_173000.20240522_182500/` ->
        `/shared_data/ecs/test/system_reconciliation/C11a/prod/20240522_173000.20240522_182500/`
    - `/data/shared/ecs/test/system_reconciliation/C11a/prod/20240522_173000.20240522_182500` ->
        `/shared_data/ecs/test/system_reconciliation/C11a/prod/20240522_173000.20240522_182500`
    """
    # Inside ECS we keep the original shared data path and replace it only when
    # running inside Docker on the dev server.
    if hserver.is_inside_docker() and not hserver.is_inside_ecs_container():
        shared_data_dirs = henv.execute_repo_config_code("get_shared_data_dirs()")
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


def get_docker_executable(use_sudo: bool) -> str:
    executable = "sudo " if use_sudo else ""
    executable += "docker"
    return executable


def container_exists(container_name: str, use_sudo: bool) -> Tuple[bool, str]:
    """
    Check if a Docker container is running by running a command like:

    > docker container ls --filter=tmp.prettier -aq
    aed8a5ce33a9
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
    Check if a Docker image already exists by running a command like:

    > docker images tmp.prettier -aq
    aed8a5ce33a9
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


# #############################################################################


def build_container(container_name: str, dockerfile: str,
                    force_rebuild: bool,
                    use_sudo: bool) -> None:
    """
    Build a Docker container from a Dockerfile.

    :param container_name: Name of the Docker container to build.
    :param dockerfile: Content of the Dockerfile to use for building the container.
    :param force_rebuild: Whether to force rebuild the Docker container.
    :param use_sudo: Whether to use sudo for Docker commands.

    :raises AssertionError: If the container ID is not found.
    """
    _LOG.debug(hprint.to_str("container_name dockerfile use_sudo"))
    # Check if the container already exists. If not, build it.
    has_container, _ = image_exists(container_name, use_sudo)
    _LOG.debug(hprint.to_str("has_container"))
    if force_rebuild:
        _LOG.warning("Forcing rebuild of Docker container")
        has_container = False
    if not has_container:
        # Create a temporary Dockerfile.
        _LOG.info("Building Docker container...")
        _LOG.debug("Dockerfile:\n%s", dockerfile)
        # Delete temp file.
        delete = True
        with tempfile.NamedTemporaryFile(suffix=".Dockerfile", delete=delete
                                         ) as temp_dockerfile:
            txt = dockerfile.encode('utf-8')
            temp_dockerfile.write(txt)
            temp_dockerfile.flush()
            # Build the container.
            executable = get_docker_executable(use_sudo)
            cmd = (
                f"{executable} build -f {temp_dockerfile.name} -t"
                f" {container_name} ."
            )
            hsystem.system(cmd, suppress_output=False)
        _LOG.info("Building Docker container... done")


# #############################################################################


def run_dockerized_prettier(
    cmd_opts: str, file_path: str, use_sudo: bool
) -> None:
    """
    Run `prettier` in a Docker container.

    :param cmd_opts: Command options to pass to Prettier.
    :param file_path: Path to the file to format with Prettier.
    :param use_sudo: Whether to use sudo for Docker commands.
    """
    _LOG.debug(hprint.to_str("cmd_opts file_path use_sudo"))
    file_path = os.path.abspath(file_path)
    hdbg.dassert_path_exists(file_path)
    #
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
    build_container(container_name, dockerfile, use_sudo)
    # The command used is like
    # > docker run --rm --user $(id -u):$(id -g) -it \
    #   --workdir /src --mount type=bind,source=.,target=/src \
    #   tmp.prettier \
    #   --parser markdown --prose-wrap always --write --tab-width 2 \
    #   ./test.md
    executable = get_docker_executable(use_sudo)
    work_dir = os.path.dirname(file_path)
    rel_file_path = os.path.basename(file_path)
    mount = f"type=bind,source={work_dir},target=/src"
    docker_cmd = (f"{executable} run --rm --user $(id -u):$(id -g) -it "
                  f"--workdir /src --mount {mount} "
                  f"{container_name}"
                  f" {cmd_opts} {rel_file_path}")
    hsystem.system(docker_cmd, suppress_output=False)