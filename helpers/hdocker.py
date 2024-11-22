"""
Import as:

import helpers.hdocker as hdocker
"""

import copy
import hashlib
import logging
import os
import tempfile
import time
from typing import List, Optional, Tuple

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
    - `/data/shared/ecs_tokyo/.../20240522_173000.20240522_182500/` ->
        `/shared_data/ecs/.../20240522_173000.20240522_182500/`
    - `/data/shared/ecs/.../20240522_173000.20240522_182500` ->
        `/shared_data/ecs/.../20240522_173000.20240522_182500`
    """
    # Inside ECS, we keep the original shared data path and replace it only when
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


# TODO(gp): Move to the repo_config.py
def get_use_sudo() -> bool:
    """
    Check if Docker commands should be run with sudo.

    :return: Whether to use sudo for Docker commands.
    """
    use_sudo = False
    # if hserver.is_inside_docker():
    #    use_sudo = True
    return use_sudo


def get_docker_executable(use_sudo: bool) -> str:
    executable = "sudo " if use_sudo else ""
    executable += "docker"
    return executable


def container_exists(container_name: str, use_sudo: bool) -> Tuple[bool, str]:
    """
    Check if a Docker container is running by running a command like:

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
    Check if a Docker image already exists by running a command like:

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
    check_interval_in_secs: int = 0.5,
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
    _LOG.debug(f"Waiting for file: {container_id}:{docker_file_path}")
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
    _LOG.debug(f"File generated: {out_file_path}")


# #############################################################################


def build_container(
    container_name: str, dockerfile: str, force_rebuild: bool, use_sudo: bool
) -> str:
    """
    Build a Docker container from a Dockerfile.

    :param container_name: Name of the Docker container to build.
    :param dockerfile: Content of the Dockerfile to use for building the
        container.
    :param force_rebuild: Whether to force rebuild the Docker container.
    :param use_sudo: Whether to use sudo for Docker commands.
    :raises AssertionError: If the container ID is not found.
    """
    _LOG.debug(hprint.to_str("container_name use_sudo"))
    dockerfile = hprint.dedent(dockerfile)
    _LOG.debug("Dockerfile:\n%s", dockerfile)
    # Compute the hash of the dockerfile and append it to the name
    # to track the content of the container.
    sha256_hash = hashlib.sha256(dockerfile.encode()).hexdigest()
    short_hash = sha256_hash[:8]
    container_name_out = f"{container_name}.{short_hash}"
    # Check if the container already exists. If not, build it.
    has_container, _ = image_exists(container_name_out, use_sudo)
    _LOG.debug(hprint.to_str("has_container"))
    if force_rebuild:
        _LOG.warning(f"Forcing to rebuild of container {container_name}")
        has_container = False
    if not has_container:
        # Create a temporary Dockerfile.
        _LOG.info("Building Docker container...")
        # Delete temp file.
        delete = True
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
                f" {container_name_out} ."
            )
            hsystem.system(cmd)
        _LOG.info("Building Docker container... done")
    return container_name_out


# #############################################################################


def get_host_git_root() -> str:
    hdbg.dassert_in("CK_GIT_ROOT_PATH", os.environ)
    host_git_root_path = os.environ["CK_GIT_ROOT_PATH"]
    return host_git_root_path


# TODO(gp): This can even go to helpers.hdbg.
def dassert_valid_path(file_path: str, is_input: bool) -> None:
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


def _convert_to_relative_path(
    file_path: str, check_if_exists: bool, is_input: bool
) -> str:
    """
    Convert the file path to a path relative to the current dir.

    :param file_path: The file path on the host to be converted.
    :param check_if_exists: check if the file exists or not.
    :param is_input: Flag indicating if the file is an input file.
    """
    _LOG.debug(hprint.to_str("file_path check_if_exists is_input"))
    if check_if_exists:
        dassert_valid_path(file_path, is_input)
    # Convert to absolute path.
    out_file_path = os.path.abspath(file_path)
    if check_if_exists:
        dassert_valid_path(out_file_path, is_input)
    # Convert to the host path.
    curr_dir = os.getcwd()
    # The path needs to be underneath the current dir.
    hdbg.dassert(
        out_file_path.startswith(curr_dir),
        "out_file_path=%s needs to be underneath curr_dir=%s",
        out_file_path,
        curr_dir,
    )
    rel_path = os.path.relpath(out_file_path, curr_dir)
    _LOG.debug("Converted %s -> %s -> %s", file_path, out_file_path, rel_path)
    return rel_path


def convert_file_names_to_docker(
    in_file_path: str,
    out_file_path: Optional[str],
) -> Tuple[str, str, str]:
    """
    Convert the file paths to be relative to the Docker mount point so that
    they can be used inside a Docker container.

    :param in_file_path: The input file path on the host to be converted.
    :param out_file_path: The output file path on the host to be converted.
    :return: A tuple containing the converted input file path, output file path,
             and the Docker mount path.
    """
    # Convert the paths to be relative.
    in_file_path = _convert_to_relative_path(
        in_file_path, check_if_exists=True, is_input=True
    )
    if out_file_path is not None:
        out_file_path = _convert_to_relative_path(
            out_file_path, check_if_exists=False, is_input=False
        )
    else:
        out_file_path = ""
    # The problem is that `in_file_path` and `out_file_path` can be specified as
    # absolute or relative path in Docker / host file system. Thus, we need to
    # convert it to a path that is valid inside the new Docker instance.
    # E.g.,
    # - /Users/saggese/src/helpers1/test.md -> /src/test.md
    # - ./test.md -> /src/test.md
    # - ./documentation/test.md -> /src/documentation/test.md
    target_docker_path = "/src"
    run_inside_docker = hserver.is_inside_docker()
    _LOG.debug(hprint.to_str("run_inside_docker"))
    # The invariant is that if `run_inside_docker` is:
    # - True: `/src` in the container corresponds to Git root in the container
    # - False: `/src/` in the container corresponds to `.`
    # Then all the files need to be converted from host to Docker paths
    # as reference to target_docker_path.
    if run_inside_docker:
        # > docker run --rm --user $(id -u):$(id -g) \
        #     ...
        #     --workdir /src \
        #     --mount type=bind,source=/Users/saggese/src/helpers1,target=/src \
        #     ...
        source_host_path = get_host_git_root()
    else:
        # > docker run --rm --user $(id -u):$(id -g) \
        #     ...
        #     --workdir /src \
        #     --mount type=bind,source=.,target=/src \
        #     ...
        hdbg.dassert_file_exists(in_file_path)
        source_host_path = "."
    # E.g.,
    # source=.,target=/src
    # source=/Users/saggese/src/helpers1,target=/src
    mount = f"type=bind,source={source_host_path},target={target_docker_path}"
    return in_file_path, out_file_path, mount


def run_dockerized_prettier(
    cmd_opts: List[str],
    in_file_path: str,
    out_file_path: str,
    force_rebuild: bool,
    use_sudo: bool,
) -> None:
    """
    Run `prettier` in a Docker container.

    From host:
    > ./dev_scripts_helpers/documentation/dockerized_prettier.py \
        --input /Users/saggese/src/helpers1/test.md --output test2.md
    > ./dev_scripts_helpers/documentation/dockerized_prettier.py \
        --input test.md --output test2.md

    From dev container:
    docker> ./dev_scripts_helpers/documentation/dockerized_prettier.py \
        --input test.md --output test2.md \
        --in_inside_docker

    :param cmd_opts: Command options to pass to Prettier.
    :param in_file_path: Path to the file to format with Prettier.
    :param out_file_path: Path to the output file.
    :param force_rebuild: Whether to force rebuild the Docker container.
    :param use_sudo: Whether to use sudo for Docker commands.
    """
    _LOG.debug(
        hprint.to_str(
            "cmd_opts in_file_path out_file_path force_rebuild use_sudo"
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
    # Convert files.
    (in_file_path, out_file_path, mount) = convert_file_names_to_docker(
        in_file_path, out_file_path
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
    #     --workdir /src --mount type=bind,source=.,target=/src \
    #     tmp.prettier \
    #     --parser markdown --prose-wrap always --write --tab-width 2 \
    #     ./test.md
    executable = get_docker_executable(use_sudo)
    bash_cmd = f"/usr/local/bin/prettier {cmd_opts_as_str} {in_file_path}"
    if out_file_path != in_file_path:
        bash_cmd += f" > {out_file_path}"
    docker_cmd = (
        f"{executable} run --rm --user $(id -u):$(id -g) "
        " --entrypoint ''"
        f" --workdir /src --mount {mount}"
        f" {container_name}"
        f' bash -c "{bash_cmd}"'
    )
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


def run_dockerized_pandoc(
    cmd_opts: List[str],
    in_file_path: str,
    out_file_path: str,
    use_sudo: bool,
) -> None:
    """
    Run `prettier` in a Docker container.

    Same as `run_dockerized_prettier()` but for `pandoc`.
    """
    _LOG.debug(hprint.to_str("cmd_opts in_file_path out_file_path use_sudo"))
    hdbg.dassert_isinstance(cmd_opts, list)
    container_name = "pandoc/core"
    # Convert files.
    (in_file_path, out_file_path, mount) = convert_file_names_to_docker(
        in_file_path, out_file_path
    )
    cmd_opts_as_str = " ".join(cmd_opts)
    # The command is like:
    # > docker run --rm --user $(id -u):$(id -g) \
    #     --workdir /src \
    #     --mount type=bind,source=.,target=/src \
    #     pandoc/core \
    #     -s --toc input.md -o output.md
    executable = get_docker_executable(use_sudo)
    docker_cmd = (
        f"{executable} run --rm --user $(id -u):$(id -g) "
        f" --workdir /src --mount {mount}"
        f" {container_name}"
        f" {cmd_opts_as_str} {in_file_path} -o {out_file_path}"
    )
    # TODO(gp): Note that `suppress_output=False` seems to hang the call.
    hsystem.system(docker_cmd)


def run_dockerized_markdown_toc(
    cmd_opts: List[str],
    in_file_path: str,
    force_rebuild: bool,
    use_sudo: bool,
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
    # Convert files.
    out_file_path = None
    (in_file_path, _, mount) = convert_file_names_to_docker(
        in_file_path, out_file_path
    )
    cmd_opts_as_str = " ".join(cmd_opts)
    # The command is like:
    # > docker run --rm --user $(id -u):$(id -g) \
    #     --workdir /src --mount type=bind,source=.,target=/src \
    #     tmp.markdown_toc \
    #     -i ./test.md
    executable = get_docker_executable(use_sudo)
    bash_cmd = (
        f"/usr/local/bin/markdown-toc {cmd_opts_as_str} -i {in_file_path}"
    )
    docker_cmd = (
        f"{executable} run --rm --user $(id -u):$(id -g) "
        f" --workdir /src --mount {mount}"
        f" {container_name}"
        f' bash -c "{bash_cmd}"'
    )
    # TODO(gp): Note that `suppress_output=False` seems to hang the call.
    hsystem.system(docker_cmd)
