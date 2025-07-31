"""
Import as:

import helpers.hdocker as hdocker
"""

import copy
import hashlib
import logging
import os
import shutil
import time
from typing import List, Optional, Tuple

import helpers.hcoverage as hcovera
import helpers.hdbg as hdbg
import helpers.henv as henv
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
    """
    Get the Docker executable with / without sudo, if needed.
    """
    executable = "sudo " if use_sudo else ""
    executable += "docker"
    return executable


def process_docker_cmd(
    docker_cmd: str, container_image: str, dockerfile: str, mode: str
) -> str:
    """
    Process a Docker command according to the mode.

    :param docker_cmd: The Docker command to process.
    :param container_image: The name of the Docker container.
    :param dockerfile: The content of the Dockerfile.
    :param mode: The mode to process the Docker command.
        - "return_cmd": return the command as is.
        - "system": execute the command.
        - "save_to_file": save the command to a file.
    :return: The output of the Docker command.
    """
    _LOG.debug(hprint.func_signature_to_str())
    hdbg.dassert_isinstance(docker_cmd, str)
    hdbg.dassert_isinstance(container_image, str)
    hdbg.dassert_isinstance(dockerfile, str)
    if mode == "return_cmd":
        ret = docker_cmd
    elif mode == "system":
        # TODO(gp): Note that `suppress_output=False` seems to hang the call.
        hsystem.system(docker_cmd, suppress_output=False)
        ret = ""
    elif mode == "system_without_output":
        hsystem.system(docker_cmd, suppress_output=True)
        ret = ""
    elif mode == "save_to_file":
        file_name = f"tmp.process_docker_cmd.{container_image}.txt"
        txt = []
        txt.append(f"docker_cmd={docker_cmd}")
        txt.append(f"container_image={container_image}")
        txt.append(f"dockerfile={dockerfile}")
        txt = "\n".join(txt)
        hio.to_file(file_name, txt)
        ret = ""
    else:
        raise ValueError(f"Invalid mode='{mode}'")
    return ret


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
    return current_arch


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
                "Timeout reached. File not found: "
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
        if shared_data_dirs is not None:
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

# See `docs/tools/docker/all.dockerized_flow.explanation.md` for details
# about the Dockerized flow.


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
    # Get the env vars to pass to the Docker container.
    vars_to_pass = henv.get_csfy_env_vars() + henv.get_api_key_env_vars()
    vars_to_pass = sorted(vars_to_pass)
    vars_to_pass_as_str = " ".join(f"-e {v}" for v in vars_to_pass)
    # Build the command as a list.
    docker_cmd = [
        docker_executable,
        "run --rm",
        "--user $(id -u):$(id -g)",
        vars_to_pass_as_str,
    ]
    # Handle coverage.
    # TODO(gp): Is this env var standard, or should it be
    # CSFY_COVERAGE_PROCESS_START?
    if os.environ.get("COVERAGE_PROCESS_START"):
        _LOG.debug("Enabling coverage")
        host_cov_dir = os.path.abspath("coverage_data")
        # TODO(gp): Use `hio.create_dir()` instead.
        os.makedirs(host_cov_dir, exist_ok=True)
        os.chmod(host_cov_dir, 0o777)
        coverage_dir_container = "/app/coverage_data"
        docker_cmd.extend(
            [
                f"-e COVERAGE_FILE={coverage_dir_container}/.coverage",
                f"-e COVERAGE_PROCESS_START={coverage_dir_container}/.coveragerc",
                f"-v {host_cov_dir}:{coverage_dir_container}",
            ]
        )
    return docker_cmd


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
    dockerfile = hprint.dedent(dockerfile)
    if os.environ.get("COVERAGE_PROCESS_START"):
        _LOG.debug("Enabling coverage")
        # Check if this is a Python-based Dockerfile.
        if any(
            keyword in dockerfile.lower()
            for keyword in ["python", "pip", "python3"]
        ):
            coverage_dockerfile = hcovera.generate_coverage_dockerfile()
            _LOG.debug("Coverage Dockerfile content:\n{coverage_dockerfile}")
            dockerfile = dockerfile.strip() + "\n" + coverage_dockerfile
            _LOG.debug("Coverage support added to Dockerfile")
        else:
            _LOG.warning(
                "Skipping coverage addition - not a Python-based Dockerfile"
            )
    _LOG.debug("Final Dockerfile:\n%s", dockerfile)
    # Get the current architecture.
    current_arch = get_current_arch()
    sha256_hash = hashlib.sha256(dockerfile.encode()).hexdigest()
    short_hash = sha256_hash[:8]
    # Build the name of the container image.
    image_name_out = f"{image_name}.{current_arch}.{short_hash}"
    # Check if the container already exists. If not, build it.
    has_container, _ = image_exists(image_name_out, use_sudo)
    coverage_enabled = os.environ.get("COVERAGE_PROCESS_START")
    if coverage_enabled:
        # Add coverage suffix to image name for tracking.
        image_name_out += ".coverage"
        # Force rebuild when coverage is enabled.
        has_container = False
        _LOG.debug(
            "Coverage enabled - forcing rebuild of image: {image_name_out}"
        )
    if force_rebuild:
        _LOG.warning(
            "Forcing to rebuild of container '%s' without cache",
            image_name,
        )
        has_container = False
        use_cache = False
    _LOG.debug(hprint.to_str("has_container use_cache"))
    # Always prepare coverage files when coverage is enabled, regardless of container existence.
    if coverage_enabled:
        # Create build context directory for coverage files.
        build_context_dir = "tmp.docker_build"
        hio.create_dir(build_context_dir, incremental=incremental)
        # Always copy .coveragerc when coverage is enabled.
        coveragerc_src = ".coveragerc"
        coveragerc_dst = os.path.join(build_context_dir, ".coveragerc")
        if os.path.exists(coveragerc_src):
            shutil.copy2(coveragerc_src, coveragerc_dst)
            _LOG.debug(
                "Coverage enabled - copied {coveragerc_src} to {coveragerc_dst}"
            )
        else:
            _LOG.warning(
                "Coverage enabled but .coveragerc not found at {coveragerc_src}"
            )
    if not has_container:
        # Create a temporary Dockerfile.
        _LOG.warning("Building Docker container...")
        if not coverage_enabled:
            # Only create build context if not already created for coverage
            build_context_dir = "tmp.docker_build"
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
    Get the Git root path on the host machine, when inside a Docker container.
    """
    hdbg.dassert_in("CSFY_HOST_GIT_ROOT_PATH", os.environ)
    host_git_root_path = os.environ["CSFY_HOST_GIT_ROOT_PATH"]
    return host_git_root_path


# TODO(gp): Move to helpers.hdbg.
def _dassert_valid_path(file_path: str, is_input: bool) -> None:
    """
    Assert that a file path is valid, based on it being input or output.

    For input files, it ensures that the file or directory exists. For
    output files, it ensures that the enclosing directory exists.

    :param file_path: The file path to check.
    :param is_input: Whether the file path is an input file.
    """
    if is_input:
        # If it's an input file, then `file_path` must exist as a file or a dir.
        hdbg.dassert_path_exists(file_path)
    else:
        # If it's an output, we might be writing a file that doesn't exist yet,
        # but we assume that the including directory is already present.
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

    This function checks if the given file path starts with the specified
    including path. If not, it raises an assertion error.

    :param file_path: The file path to check.
    :param including_path: The path that should include the file path.
    """
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
    :param is_input: Whether the file path is an input file (used only if
        `check_if_exists` is True).
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


def is_path(path: str) -> bool:
    """
    Check if `path` can be considered a file or a directory using heuristics.

    - return: True if the string looks like a path, False otherwise.
    """
    # E.g.,
    # ```
    # is_path("file.txt")           # True, since it has an extension
    # is_path("/path/to/file.py")   # True, since it has an absolute path
    # is_path("/path/to")           # True, since it has an absolute path
    # is_path("../data.csv")        # True, since it has an relative path
    # is_path("folder/")            # True, since it has a trailing slash
    # is_path(".hidden")            # True, since it has a leading dot
    # is_path("readme")             # False, since it has no extension and no path
    # ```
    # Check if it has a file extension (e.g., .txt, .csv).
    if os.path.splitext(path)[1]:
        return True
    # Check if it is an absolute or relative path (e.g., starts with "/" or "./"
    # or "../")
    if path.startswith("/") or path.startswith("./") or path.startswith("../"):
        return True
    # Check if it ends with a slash.
    if path.endswith("/"):
        return True
    # Check if it has a hidden file.
    basename = os.path.basename(path)
    if basename.startswith(".") and basename.count(".") == 1:
        return True
    # Check if it contains a slash.
    if "/" in path:
        return True
    return False


def convert_all_paths_from_caller_to_callee_docker_path(
    cmd_opts: List[str],
    caller_mount_path: str,
    callee_mount_path: str,
    is_caller_host: bool,
    use_sibling_container_for_callee: bool,
) -> str:
    """
    Convert all the paths from the caller to the callee Docker container path.

    The paths are recognized by checking whether they point to an existing file
    or directory.

    The limitation of this approach is that output files are not recognized. To
    work around this problem:
    - Create output dirs
    - Explicitly parse options that are outputs (e.g., `-o <file>`)

    :param cmd_opts: List of command options.
    :param caller_mount_path: See `get_docker_mount_info()`.
    :param callee_mount_path: See `get_docker_mount_info()`.
    :param is_caller_host: See `get_docker_mount_info()`.
    :param use_sibling_container_for_callee: See `get_docker_mount_info()`.
    :return: List of converted command options.
    """
    _LOG.debug(hprint.func_signature_to_str())
    # Converted command options.
    cmd_opts_out = []
    # Scan the list of command option.
    for cmd_opt_in in cmd_opts:
        exists = os.path.exists(cmd_opt_in)
        is_path_ = is_path(cmd_opt_in)
        _LOG.debug(hprint.to_str("cmd_opt_in exists is_path_"))
        if exists or is_path_:
            check_if_exists = False
            is_input = False
            cmd_opt_out = convert_caller_to_callee_docker_path(
                cmd_opt_in,
                caller_mount_path,
                callee_mount_path,
                check_if_exists,
                is_input,
                is_caller_host,
                use_sibling_container_for_callee,
            )
            _LOG.debug(hprint.to_str("cmd_opt_in -> cmd_opt_out"))
            cmd_opts_out.append(cmd_opt_out)
        else:
            _LOG.debug("File does not exist: %s", cmd_opt_in)
            cmd_opts_out.append(cmd_opt_in)
    _LOG.debug(hprint.to_str("cmd_opts_out"))
    return cmd_opts_out
