"""
Import as:

import helpers.lib_tasks_docker as hlitadoc
"""

import functools
import getpass
import logging
import os
import re
from typing import Any, Dict, List, Match, Optional, Union, cast

# TODO(gp): We should use `pip install types-PyYAML` to get the mypy stubs.
import yaml
from invoke import task

# We want to minimize the dependencies from non-standard Python packages since
# this code needs to run with minimal dependencies and without Docker.
import helpers.hdbg as hdbg
import helpers.hdict as hdict
import helpers.hdocker as hdocker
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hs3 as hs3
import helpers.hsecrets as hsecret
import helpers.hserver as hserver
import helpers.hsystem as hsystem
import helpers.hversion as hversio
import helpers.lib_tasks_utils as hlitauti
import helpers.repo_config_utils as hrecouti

_LOG = logging.getLogger(__name__)

# pylint: disable=protected-access


# #############################################################################
# Basic Docker commands.
# #############################################################################


def _get_docker_exec(sudo: bool) -> str:
    docker_exec = "docker"
    if sudo:
        docker_exec = "sudo " + docker_exec
    return docker_exec


@task
def docker_images_ls_repo(ctx, sudo=False):  # type: ignore
    """
    List images in the logged in repo_short_name.
    """
    hlitauti.report_task()
    docker_login(ctx)
    # TODO(gp): Move this to a var ECR_BASE_PATH="CSFY_ECR_BASE_PATH" in repo_config.py.
    ecr_base_path = hlitauti.get_default_param("CSFY_ECR_BASE_PATH")
    docker_exec = _get_docker_exec(sudo)
    hlitauti.run(ctx, f"{docker_exec} image ls {ecr_base_path}")


@task
def docker_ps(ctx, sudo=False):  # type: ignore
    # pylint: disable=line-too-long
    """
    List all the running containers.

    ```
    > docker_ps
    CONTAINER ID  user  IMAGE                    COMMAND                    CREATED        STATUS        PORTS  service
    2ece37303ec9  gp    *****....:latest  "./docker_build/entry.sh"  5 seconds ago  Up 4 seconds         user_space
    ```
    """
    hlitauti.report_task()
    # pylint: enable=line-too-long
    fmt = (
        r"""table {{.ID}}\t{{.Label "user"}}\t{{.Image}}\t{{.Command}}"""
        + r"\t{{.RunningFor}}\t{{.Status}}\t{{.Ports}}"
        + r'\t{{.Label "com.docker.compose.service"}}'
    )
    docker_exec = _get_docker_exec(sudo)
    cmd = f"{docker_exec} ps --format='{fmt}'"
    cmd = hlitauti._to_single_line_cmd(cmd)
    hlitauti.run(ctx, cmd)


def _get_last_container_id(sudo: bool) -> str:
    docker_exec = _get_docker_exec(sudo)
    # Get the last started container.
    cmd = f"{docker_exec} ps -l | grep -v 'CONTAINER ID'"
    # CONTAINER ID   IMAGE          COMMAND                  CREATED
    # 90897241b31a   eeb33fe1880a   "/bin/sh -c '/bin/bash ...
    _, txt = hsystem.system_to_one_line(cmd)
    # Parse the output: there should be at least one line.
    hdbg.dassert_lte(1, len(txt.split(" ")), "Invalid output='%s'", txt)
    container_id: str = txt.split(" ")[0]
    return container_id


@task
def docker_stats(  # type: ignore
    ctx,
    all=False,  # pylint: disable=redefined-builtin
    sudo=False,
):
    # pylint: disable=line-too-long
    """
    Report last started Docker container stats, e.g., CPU, RAM.

    ```
    > docker_stats
    CONTAINER ID  NAME                   CPU %  MEM USAGE / LIMIT     MEM %  NET I/O         BLOCK I/O        PIDS
    2ece37303ec9  ..._user_space_run_30  0.00%  15.74MiB / 31.07GiB   0.05%  351kB / 6.27kB  34.2MB / 12.3kB  4
    ```

    :param all: report stats for all the containers
    """
    # pylint: enable=line-too-long
    hlitauti.report_task(txt=hprint.to_str("all"))
    _ = ctx
    fmt = (
        r"table {{.ID}}\t{{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
        + r"\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}\t{{.PIDs}}"
    )
    docker_exec = _get_docker_exec(sudo)
    cmd = f"{docker_exec} stats --no-stream --format='{fmt}'"
    _, txt = hsystem.system_to_string(cmd)
    if all:
        output = txt
    else:
        # Get the id of the last started container.
        container_id = _get_last_container_id(sudo)
        print(f"Last container id={container_id}")
        # Parse the output looking for the given container.
        txt = txt.split("\n")
        output = []
        # Save the header.
        output.append(txt[0])
        for line in txt[1:]:
            if line.startswith(container_id):
                output.append(line)
        # There should be at most two rows: the header and the one corresponding to
        # the container.
        hdbg.dassert_lte(
            len(output), 2, "Invalid output='%s' for '%s'", output, txt
        )
        output = "\n".join(output)
    print(output)


@task
def docker_kill(  # type: ignore
    ctx,
    all=False,  # pylint: disable=redefined-builtin
    sudo=False,
):
    """
    Kill the last Docker container started.

    :param all: kill all the containers (be careful!)
    :param sudo: use sudo for the Docker commands
    """
    hlitauti.report_task(txt=hprint.to_str("all"))
    docker_exec = _get_docker_exec(sudo)
    # Last container.
    opts = "-l"
    if all:
        _LOG.warning("Killing all the containers")
        # TODO(gp): Ask if we are sure and add a --just-do-it option.
        opts = "-a"
    # Print the containers that will be terminated.
    cmd = f"{docker_exec} ps {opts}"
    hlitauti.run(ctx, cmd)
    # Kill.
    cmd = f"{docker_exec} rm -f $({docker_exec} ps {opts} -q)"
    hlitauti.run(ctx, cmd)


# docker system prune
# docker container ps -f "status=exited"
# docker container rm $(docker container ps -f "status=exited" -q)
# docker rmi $(docker images --filter="dangling=true" -q)

# pylint: disable=line-too-long
# Remove the images with hash
# > docker image ls
# REPOSITORY                                        TAG                                        IMAGE ID       CREATED         SIZE
# *****.dkr.ecr.us-east-2.amazonaws.com/im          07aea615a2aa9290f7362e99e1cc908876700821   d0889bf972bf   6 minutes ago   684MB
# *****.dkr.ecr.us-east-2.amazonaws.com/im          rc                                         d0889bf972bf   6 minutes ago   684MB
# python                                            3.7-slim-buster                            e7d86653f62f   14 hours ago    113MB
# *****.dkr.ecr.us-east-1.amazonaws.com/amp         415376d58001e804e840bf3907293736ad62b232   e6ea837ab97f   18 hours ago    1.65GB
# *****.dkr.ecr.us-east-1.amazonaws.com/amp         dev                                        e6ea837ab97f   18 hours ago    1.65GB
# *****.dkr.ecr.us-east-1.amazonaws.com/amp         local                                      e6ea837ab97f   18 hours ago    1.65GB
# *****.dkr.ecr.us-east-1.amazonaws.com/amp         9586cc2de70a4075b9fdcdb900476f8a0f324e3e   c75d2447da79   18 hours ago    1.65GB
# pylint: enable=line-too-long


# #############################################################################
# Docker development.
# #############################################################################

# TODO(gp): We might want to organize the code in a base class using a Command
# pattern, so that it's easier to generalize the code for multiple repos.
#
# class DockerCommand:
#   def pull():
#     ...
#   def cmd():
#     ...
#
# For now we pass the customizable part through the default params.


# ////////////////////////////////////////////////////////////////////////////
# Docker pull.
# ////////////////////////////////////////////////////////////////////////////


def _docker_pull(
    ctx: Any, base_image: str, stage: str, version: Optional[str]
) -> None:
    """
    Pull images from the registry.
    """
    docker_login(ctx)
    #
    image = get_image(base_image, stage, version)
    _LOG.info("image='%s'", image)
    dassert_is_image_name_valid(image)
    cmd = f"docker pull {image}"
    hlitauti.run(ctx, cmd, pty=True)


@task
def docker_pull(ctx, stage="dev", version=None, skip_pull=False):  # type: ignore
    """
    Pull latest dev image corresponding to the current repo from the registry.

    :param skip_pull: if True skip pulling the docker image
    """
    hlitauti.report_task()
    if stage == "local":
        _LOG.warning("Setting skip_pull to True for local stage")
        skip_pull = True
    if skip_pull:
        _LOG.warning("Skipping pulling docker image as per user request")
        return
    #
    base_image = ""
    _docker_pull(ctx, base_image, stage, version)


@task
def docker_pull_helpers(ctx, stage="prod", version=None):  # type: ignore
    """
    Pull latest prod image of `helpers` from the registry.

    :param ctx: invoke context
    :param stage: stage of the Docker image
    :param version: version of the Docker image
    """
    base_image = hlitauti.get_default_param("CSFY_ECR_BASE_PATH") + "/helpers"
    _LOG.debug("base_image=%s", base_image)
    _docker_pull(ctx, base_image, stage, version)


# ////////////////////////////////////////////////////////////////////////////
# Docker login
# ////////////////////////////////////////////////////////////////////////////


@functools.lru_cache()
def _get_aws_cli_version() -> int:
    # > aws --version
    # aws-cli/1.19.49 Python/3.7.6 Darwin/19.6.0 botocore/1.20.49
    # aws-cli/1.20.1 Python/3.9.5 Darwin/19.6.0 botocore/1.20.106
    cmd = "aws --version"
    res = hsystem.system_to_one_line(cmd)[1]
    # Parse the output.
    m = re.match(r"aws-cli/((\d+)\.\d+\.\d+)\s", res)
    hdbg.dassert(m, "Can't parse '%s'", res)
    m: Match[Any]
    version = m.group(1)
    _LOG.debug("version=%s", version)
    major_version = int(m.group(2))
    _LOG.debug("major_version=%s", major_version)
    return major_version


def _check_docker_login(repo_name: str) -> bool:
    """
    Check if we are already logged in to the Docker registry `repo_name`.
    """
    file_name = os.path.join(os.environ["HOME"], ".docker/config.json")
    json_data = hio.from_json(file_name)
    # > more ~/.docker/config.json
    # ```
    # {
    #         "auths": {
    #                 "623860924167.dkr.ecr.eu-north-1.amazonaws.com": {},
    #                 "665840871993.dkr.ecr.us-east-1.amazonaws.com": {},
    #                 "https://index.docker.io/v1/": {}
    #         },
    # ```
    _LOG.debug("json_data=%s", json_data)
    is_logged = any(repo_name in val for val in json_data["auths"].keys())
    return is_logged


def _docker_login_dockerhub() -> None:
    """
    Log into the Docker Hub which is a public Docker image registry.
    """
    # Check if we are already logged in to the target registry.
    # TODO(gp): Enable caching https://github.com/causify-ai/helpers/issues/20
    use_cache = False
    if use_cache:
        is_logged = _check_docker_login("623860924167.dkr.ecr")
        if is_logged:
            _LOG.warning("Already logged in to the target registry: skipping")
            return
    _LOG.info("Logging in to the target registry")
    secret_id = "causify_dockerhub"
    secret = hsecret.get_secret(secret_id)
    username = hdict.typed_get(secret, "username", expected_type=str)
    password = hdict.typed_get(secret, "password", expected_type=str)
    cmd = f"docker login -u {username} -p {password}"
    hsystem.system(cmd, suppress_output=False)


def _docker_login_ecr() -> None:
    """
    Log in the AM Docker repo_short_name on AWS.
    """
    hlitauti.report_task()
    if hserver.is_inside_ci():
        _LOG.warning("Running inside GitHub Action: skipping `docker_login`")
        return
    # TODO(gp): Enable caching https://github.com/causify-ai/helpers/issues/20
    use_cache = False
    if use_cache:
        # Check if we are already logged in to the target registry.
        is_logged = _check_docker_login("623860924167.dkr.ecr")
        if is_logged:
            _LOG.warning("Already logged in to the target registry: skipping")
            return
    _LOG.info("Logging in to the target registry")
    # Log in the target registry.
    major_version = _get_aws_cli_version()
    # docker login \
    #   -u AWS \
    #   -p eyJ... \
    #   -e none \
    #   https://*****.dkr.ecr.us-east-1.amazonaws.com
    # TODO(gp): Move this to var in repo_config.py.
    # TODO(gp): Hack
    profile = "ck"
    region = hs3.AWS_EUROPE_REGION_1
    cmd = ""
    if major_version == 1:
        cmd = f"eval $(aws ecr get-login --profile {profile} --no-include-email --region {region})"
    elif major_version == 2:
        if profile == "ck":
            env_var = f"CSFY_ECR_BASE_PATH"
        else:
            env_var = f"{profile.upper()}_ECR_BASE_PATH"
        ecr_base_path = hlitauti.get_default_param(env_var)
        # TODO(Nikola): Remove `_get_aws_cli_version()` and use only `aws ecr get-login-password`
        #  as it is present in both versions of `awscli`.
        cmd = (
            f"docker login -u AWS -p "
            f"$(aws ecr get-login-password --profile {profile}) "
            f"https://{ecr_base_path}"
        )
    else:
        NotImplementedError(
            f"Docker login for awscli v{major_version} is not implemented!"
        )
    # TODO(Grisha): fix properly. We pass `ctx` despite the fact that we do not
    #  need it with `use_system=True`, but w/o `ctx` invoke tasks (i.e. ones
    #  with `@task` decorator) do not work.
    hsystem.system(cmd, suppress_output=False)


@task
def docker_login(ctx, target_registry="aws_ecr.ck"):  # type: ignore
    """
    Log in the target registry and skip if we are in kaizenflow.

    :param ctx: invoke context
    :param target_registry: target Docker image registry to log in to
        - "dockerhub.causify": public Causify Docker image registry
        - "aws_ecr.ck": private AWS CK ECR
    """
    _ = ctx
    hlitauti.report_task()
    # No login required as the `helpers` and `tutorials` images are accessible
    # on the public DockerHub registry.
    if not hserver.is_dev_csfy() and hrecouti.get_repo_config().get_name() in [
        "//helpers",
        "//tutorials",
    ]:
        _LOG.warning("Skipping Docker login process for Helpers or Tutorials")
        return
    # We run everything using `hsystem.system(...)` but `ctx` is needed
    # to make the function work as an invoke target.
    if target_registry == "aws_ecr.ck":
        _docker_login_ecr()
    elif target_registry == "dockerhub.causify":
        _docker_login_dockerhub()
    else:
        raise ValueError(f"Invalid Docker image registry='{target_registry}'")


# ////////////////////////////////////////////////////////////////////////////////
# Compose files.
# ////////////////////////////////////////////////////////////////////////////////

# TODO(gp): All this code can become `DockerComposeFileGenerator`.

# There are several combinations to consider:
# - whether the Docker host can run with / without privileged mode
# - amp as submodule / as supermodule
# - different supermodules for amp

# TODO(gp): use_privileged_mode -> use_docker_privileged_mode
#  use_sibling_container -> use_docker_containers_containers

DockerComposeServiceSpec = Dict[str, Union[str, List[str]]]


def _get_linter_service(stage: str) -> DockerComposeServiceSpec:
    """
    Get the linter service specification for the `tmp.docker-compose.yml` file.

    :return: linter service specification
    """
    superproject_path, submodule_path = hgit.get_path_from_supermodule()
    if superproject_path:
        # We are running in a Git submodule.
        work_dir = f"/src/{submodule_path}"
        repo_root = superproject_path
    else:
        work_dir = "/src"
        repo_root = os.getcwd()
    # TODO(gp): To avoid linter getting confused between `Sequence[str]` and
    # `List[str]`, we should assign one element at the time.
    linter_service_spec = {
        "extends": "base_app",
        "volumes": [
            f"{repo_root}:/src",
        ],
        "working_dir": work_dir,
        "environment": [
            "MYPYPATH",
        ],
    }
    if stage != "prod":
        # When we run a development Linter container, we need to mount the
        # Linter repo under `/app`. For prod container instead we copy / freeze
        # the repo code in `/app`, so we should not mount it.
        volumes = cast(List[str], linter_service_spec["volumes"])
        if superproject_path:
            # When running in a Git submodule we need to go one extra level up.
            # TODO(*): Clean up the indentation, #2242 (also below).
            volumes.append("../../../:/app")
        else:
            volumes.append("../../:/app")
    if stage == "prod":
        # Use the `repo_config.py` inside the helpers container instead of
        # the one in the calling repo.
        environment = cast(List[str], linter_service_spec["environment"])
        environment.append("CSFY_REPO_CONFIG_PATH=/app/repo_config.py")
    return linter_service_spec


# TODO(gp): Remove mount_as_submodule
def _generate_docker_compose_file(
    stage: str,
    use_privileged_mode: bool,
    use_sibling_container: bool,
    shared_data_dirs: Optional[Dict[str, str]],
    mount_as_submodule: bool,
    use_network_mode_host: bool,
    use_main_network: bool,
    file_name: Optional[str],
) -> str:
    """
    Generate `tmp.docker-compose.yml` file and save it.

    :param shared_data_dirs: data directory in the host filesystem to mount
        inside the container. `None` means no dir sharing
    :param use_main_network: use `main_network` as default network
    """
    _LOG.debug(
        hprint.to_str(
            "use_privileged_mode "
            "use_sibling_container "
            "shared_data_dirs "
            "mount_as_submodule "
            "use_network_mode_host "
            "use_main_network "
            "file_name "
        )
    )
    # We could pass the env var directly, like:
    # ```
    # - CSFY_ENABLE_DIND=$CSFY_ENABLE_DIND
    # ```
    # but we prefer to inline it.
    if use_privileged_mode:
        CSFY_ENABLE_DIND = 1
    else:
        CSFY_ENABLE_DIND = 0
    # ```
    # sysname='Linux'
    # nodename='cf-spm-dev4'
    # release='3.10.0-1160.53.1.el7.x86_64'
    # version='#1 SMP Fri Jan 14 13:59:45 UTC 2022'
    # machine='x86_64'
    # ```
    csfy_host_os_name = os.uname()[0]
    csfy_host_name = os.uname()[1]
    csfy_host_version = os.uname()[2]
    csfy_host_user_name = getpass.getuser()
    # We assume that we don't use this code inside a container, since otherwise
    # we would need to distinguish the container style (see
    # docs/work_tools/docker/all.dockerized_flow.explanation.md) to find the
    # outermost Git root.
    if not hserver.is_inside_unit_test():
        hdbg.dassert(not hserver.is_inside_docker())
    else:
        # We call this function as part of the unit tests, which we run insider
        # the container.
        pass
    git_host_root_path = hgit.find_git_root()
    # Find git root path in the container.
    # The Git root is always mounted in the container at `/app`. So we need to
    # use that as starting point.
    # E.g. For CSFY_GIT_ROOT_PATH, we need to use `/app`, rather than
    # `/data/dummy/src/cmamp1`.
    # E.g. For CSFY_HELPERS_ROOT_PATH, we need to use `/app/helpers_root`.
    # rather than `/data/dummy/src/cmamp1/helpers_root`.
    git_root_path = "/app"
    # Find helpers root path in the container.
    helper_dir = hgit.find_helpers_root()
    helper_relative_path = os.path.relpath(helper_dir, git_host_root_path)
    helper_root_path = os.path.normpath(
        os.path.join(git_root_path, helper_relative_path)
    )
    # A super repo is a repo that contains helpers as a submodule and
    # is not a helper itself.
    use_helpers_as_nested_module = 0 if hgit.is_in_helpers_as_supermodule() else 1
    # We could do the same also with IMAGE for symmetry.
    # Keep the env vars in sync with what we print in `henv.get_env_vars()`.
    # Configure `base_app` service.
    base_app_spec = {
        "cap_add": ["SYS_ADMIN"],
        "environment": [
            f"CSFY_ENABLE_DIND={CSFY_ENABLE_DIND}",
            f"CSFY_FORCE_TEST_FAIL=$CSFY_FORCE_TEST_FAIL",
            f"CSFY_HOST_NAME={csfy_host_name}",
            f"CSFY_HOST_OS_NAME={csfy_host_os_name}",
            f"CSFY_HOST_USER_NAME={csfy_host_user_name}",
            f"CSFY_HOST_VERSION={csfy_host_version}",
            "CSFY_REPO_CONFIG_CHECK=True",
            # Use inferred path for `repo_config.py`.
            "CSFY_REPO_CONFIG_PATH=",
            "CSFY_AWS_ACCESS_KEY_ID=$CSFY_AWS_ACCESS_KEY_ID",
            "CSFY_AWS_DEFAULT_REGION=$CSFY_AWS_DEFAULT_REGION",
            "CSFY_AWS_PROFILE=$CSFY_AWS_PROFILE",
            "CSFY_AWS_S3_BUCKET=$CSFY_AWS_S3_BUCKET",
            "CSFY_AWS_SECRET_ACCESS_KEY=$CSFY_AWS_SECRET_ACCESS_KEY",
            "CSFY_AWS_SESSION_TOKEN=$CSFY_AWS_SESSION_TOKEN",
            "CSFY_ECR_BASE_PATH=$CSFY_ECR_BASE_PATH",
            # The path of the outermost Git root on the host.
            f"CSFY_HOST_GIT_ROOT_PATH={git_host_root_path}",
            # The path of the outermost Git root in the Docker container.
            f"CSFY_GIT_ROOT_PATH={git_root_path}",
            # The path of the helpers dir in the Docker container (e.g.,
            # `/app`, `/app/helpers_root`)
            f"CSFY_HELPERS_ROOT_PATH={helper_root_path}",
            f"CSFY_USE_HELPERS_AS_NESTED_MODULE={use_helpers_as_nested_module}",
            "CSFY_TELEGRAM_TOKEN=$CSFY_TELEGRAM_TOKEN",
            # This env var is used by GH Action to signal that we are inside the
            # CI. It's set up by default by the GH Action runner. See:
            # https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/store-information-in-variables#default-environment-variables
            "CSFY_CI=$CSFY_CI",
            "OPENAI_API_KEY=$OPENAI_API_KEY",
            # TODO(Vlad): consider removing, locally we use our personal tokens
            # from files and inside GitHub actions we use the `GH_TOKEN`
            # environment variable.
            "GH_ACTION_ACCESS_TOKEN=$GH_ACTION_ACCESS_TOKEN",
            # Inside GitHub Actions we use `GH_TOKEN` environment variable,
            # see https://cli.github.com/manual/gh_auth_login.
            "GH_TOKEN=$GH_ACTION_ACCESS_TOKEN",
        ],
        "image": "${IMAGE}",
        "restart": "no",
        "volumes": [
            # TODO(gp): We should pass the value of $HOME from dev.Dockerfile to here.
            # E.g., we might define $HOME in the env file.
            "~/.aws:/home/.aws",
            "~/.config/gspread_pandas/:/home/.config/gspread_pandas/",
            "~/.config/gh:/home/.config/gh",
            "~/.ssh:/home/.ssh",
        ],
    }
    if use_privileged_mode:
        # This is needed:
        # - for Docker-in-docker (dind)
        # - to mount fstabs
        base_app_spec["privileged"] = use_privileged_mode
    if shared_data_dirs:
        # Mount shared dirs.
        shared_volumes = [
            f"{host}:{container}" for host, container in shared_data_dirs.items()
        ]
        # Mount all dirs that are specified.
        base_app_spec["volumes"].extend(shared_volumes)
    if False:
        # No need to mount file systems.
        base_app_spec["volumes"].append("../docker_build/fstab:/etc/fstab")
    if use_sibling_container:
        # Use sibling-container approach.
        base_app_spec["volumes"].append(
            "/var/run/docker.sock:/var/run/docker.sock"
        )
    if False:
        base_app_spec["deploy"] = {
            "resources": {
                "limits": {
                    # This should be passed from command line depending on how much
                    # memory is available.
                    "memory": "60G",
                },
            },
        }
    if use_network_mode_host:
        # Default network mode set to host so we can reach e.g.
        # a database container pointing to localhost:5432.
        # In tests we use dind so we need set back to the default "bridge".
        # See CmTask988 and https://stackoverflow.com/questions/24319662
        base_app_spec["network_mode"] = "${NETWORK_MODE:-host}"
    # Configure `app` service.
    # Mount `amp` when it is used as submodule. In this case we need to
    # mount the super project in the container (to make git work with the
    # supermodule) and then change dir to `amp`.
    app_spec = {
        "extends": "base_app",
    }
    # Use absolute path of the dir to mount the volume and set working dir.
    # The `app_dir` dir points to the root of the repo.
    # The `working_dir` points to the path of the runnable dir.
    # - If the runnable dir is the root of the repo, then `working_dir` is `/app`.
    # - If the runnable dir is a subdirectory of the repo, then `working_dir` is `/app/subdir`.
    curr_dir = os.getcwd()
    rel_dir1 = os.path.relpath(curr_dir, git_host_root_path)
    rel_dir2 = os.path.relpath(git_host_root_path, curr_dir)
    app_dir = os.path.abspath(os.path.join(curr_dir, rel_dir2))
    working_dir = os.path.normpath(os.path.join("/app", rel_dir1))
    app_spec["volumes"] = [f"{app_dir}:/app"]
    app_spec["working_dir"] = working_dir
    # Configure `linter` service.
    linter_spec = _get_linter_service(stage)
    # Configure `jupyter_server` service.
    # For Jupyter server we cannot use "host" network_mode because
    # it is incompatible with the port bindings.
    jupyter_server = {
        "command": "devops/docker_run/run_jupyter_server.sh",
        "environment": [
            "PORT=${PORT}",
        ],
        "extends": "app",
        "network_mode": "${NETWORK_MODE:-bridge}",
        # TODO(gp): Rename `AM_PORT`.
        "ports": [
            "${PORT}:${PORT}",
        ],
    }
    # Configure `jupyter_server_test` service.
    # TODO(gp): For some reason the following doesn't work.
    # jupyter_server_test:
    #   command: jupyter notebook -h 2>&1 >/dev/null
    #   extends:
    #     jupyter_server
    jupyter_server_test = {
        "command": "jupyter notebook -h 2>&1 >/dev/null",
        "environment": [
            "PORT=${PORT}",
        ],
        "extends": "app",
        "network_mode": "${NETWORK_MODE:-bridge}",
        "ports": [
            "${PORT}:${PORT}",
        ],
    }
    # Specify structure of the docker-compose file.
    docker_compose = {
        "version": "3",
        "services": {
            "base_app": base_app_spec,
            "app": app_spec,
            "linter": linter_spec,
            "jupyter_server": jupyter_server,
            "jupyter_server_test": jupyter_server_test,
        },
    }
    # Configure networks.
    if use_main_network:
        docker_compose["networks"] = {"default": {"name": "main_network"}}

    class _Dumper(yaml.Dumper):
        """
        A custom YAML Dumper class that adjusts indentation.
        """

        def increase_indent(self_: Any, flow=False, indentless=False) -> Any:
            """
            Override the method to modify YAML indentation behavior.
            """
            return super(_Dumper, self_).increase_indent(
                flow=False, indentless=False
            )

    # Convert the dictionary to YAML format.
    yaml_str = yaml.dump(
        docker_compose,
        Dumper=_Dumper,
        default_flow_style=False,
        indent=2,
        sort_keys=False,
    )
    yaml_str = cast(str, yaml_str)
    # Save YAML to file if file_name is specified.
    if file_name:
        if os.path.exists(file_name) and hserver.is_inside_ci():
            # Permission error is raised if we try to overwrite existing file.
            # See CmTask #2321 for detailed info.
            compose_directory = os.path.dirname(file_name)
            hsystem.system(f"sudo rm -rf {compose_directory}")
        hio.to_file(file_name, yaml_str)
    return yaml_str


def get_base_docker_compose_path() -> str:
    """
    Return the absolute path to the Docker compose file.

    E.g., `devops/compose/tmp.docker-compose.yml`.
    """
    # Add the default path.
    dir_name = "devops/compose"
    # TODO(gp): Factor out the piece below.
    docker_compose_path = "tmp.docker-compose.yml"
    docker_compose_path = os.path.join(dir_name, docker_compose_path)
    docker_compose_path = os.path.abspath(docker_compose_path)
    return docker_compose_path


def _get_docker_compose_files(
    stage: str,
    generate_docker_compose_file: bool,
    service_name: str,
    extra_docker_compose_files: Optional[List[str]],
) -> List[str]:
    """
    Generate the Docker compose file and return the list of Docker compose
    paths.

    :return: list of the Docker compose paths
    """
    docker_compose_files = []
    # Get the repo short name (e.g., `amp`).
    repo_short_name = hrecouti.get_repo_config().get_repo_short_name()
    _LOG.debug("repo_short_name=%s", repo_short_name)
    # Check submodule status, if needed.
    mount_as_submodule = False
    if repo_short_name in ("amp", "cmamp"):
        # Check if `amp` is a submodule.
        path, _ = hgit.get_path_from_supermodule()
        if path != "":
            _LOG.warning("amp is a submodule")
            mount_as_submodule = True
    # Write Docker compose file.
    file_name = get_base_docker_compose_path()
    if service_name == "linter":
        # Since we are running the prod `helpers` container we need to use the
        # settings from the `repo_config` from that container, and not the settings
        # launch the container corresponding to this repo.
        enable_privileged_mode = False
        use_docker_sibling_containers = False
        get_shared_data_dirs = None
        use_docker_network_mode_host = False
        use_main_network = False
    else:
        # Use the settings from the `repo_config` corresponding to this container.
        enable_privileged_mode = hserver.enable_privileged_mode()
        use_docker_sibling_containers = hserver.use_docker_sibling_containers()
        get_shared_data_dirs = hserver.get_shared_data_dirs()
        use_docker_network_mode_host = hserver.use_docker_network_mode_host()
        use_main_network = hserver.use_main_network()
    #
    if generate_docker_compose_file:
        _generate_docker_compose_file(
            stage,
            enable_privileged_mode,
            use_docker_sibling_containers,
            get_shared_data_dirs,
            mount_as_submodule,
            use_docker_network_mode_host,
            use_main_network,
            file_name,
        )
    else:
        _LOG.warning("Skipping generating Docker compose file '%s'", file_name)
    docker_compose_files.append(file_name)
    # Add the compose files from command line.
    if extra_docker_compose_files:
        hdbg.dassert_isinstance(extra_docker_compose_files, list)
        docker_compose_files.extend(extra_docker_compose_files)
    # Add the compose files from the global params.
    key = "DOCKER_COMPOSE_FILES"
    if hlitauti.has_default_param(key):
        docker_compose_files.append(hlitauti.get_default_param(key))
    #
    _LOG.debug(hprint.to_str("docker_compose_files"))
    for docker_compose in docker_compose_files:
        hdbg.dassert_path_exists(docker_compose)
    return docker_compose_files


# ////////////////////////////////////////////////////////////////////////////////
# Version.
# ////////////////////////////////////////////////////////////////////////////////


_IMAGE_VERSION_RE = r"\d+\.\d+\.\d+"


def _dassert_is_version_valid(version: str) -> None:
    """
    Check that the version is valid, i.e. looks like `1.0.0`.
    """
    hdbg.dassert_isinstance(version, str)
    hdbg.dassert_ne(version, "")
    regex = rf"^({_IMAGE_VERSION_RE})$"
    _LOG.debug("Testing with regex='%s'", regex)
    m = re.match(regex, version)
    hdbg.dassert(m, "Invalid version: '%s'", version)


_IMAGE_VERSION_FROM_CHANGELOG = "FROM_CHANGELOG"


def resolve_version_value(
    version: str,
    *,
    container_dir_name: str = ".",
) -> str:
    """
    Pass a version (e.g., 1.0.0) or a symbolic value (e.g., FROM_CHANGELOG) and
    return the resolved value of the version.

    :return: full version with patch for prod (e.g., 1.3.2)
    """
    hdbg.dassert_isinstance(version, str)
    if version == _IMAGE_VERSION_FROM_CHANGELOG:
        version = hversio.get_changelog_version(container_dir_name)
    _dassert_is_version_valid(version)
    prod_version = version
    return prod_version


def to_dev_version(prod_version: str) -> str:
    """
    Pass a prod version (e.g., 1.1.1) and strip the patch value.

    :return: stripped version without patch for dev (e.g., 1.1.0)
    """
    hdbg.dassert_isinstance(prod_version, str)
    _dassert_is_version_valid(prod_version)
    # Strip patch value from the version.
    dev_version = prod_version.split(".")[:-1]
    dev_version = ".".join(dev_version) + ".0"
    return dev_version


def dassert_is_subsequent_version(
    version: str,
    *,
    container_dir_name: str = ".",
) -> None:
    """
    Check that `version` is bigger than the current one as specified in the
    changelog.
    """
    if version != _IMAGE_VERSION_FROM_CHANGELOG:
        current_version = hversio.get_changelog_version(container_dir_name)
        hdbg.dassert_lte(current_version, version)


# ////////////////////////////////////////////////////////////////////////////////
# Image.
# ////////////////////////////////////////////////////////////////////////////////


# This pattern aims to match the full image name including
# both registry and image path.
# Examples of valid matches include:
# - '623860924167.dkr.ecr.eu-north-1.amazonaws.com/cmamp'
# - 'ghcr.io/cryptokaizen/cmamp'
# This change is introduced to match the GHCR registry path,
# since it already includes `/` in the registry name itself.
_FULL_IMAGE_NAME_RE = r"([a-z0-9]+(-[a-z0-9]+)*\.)*[a-z]{2,}(\/[a-z0-9_-]+){1,2}"
_IMAGE_USER_RE = r"[a-z0-9_-]+"
# For candidate prod images which have added hash for easy identification.
_IMAGE_HASH_RE = r"[a-z0-9]{9}"
_IMAGE_STAGE_RE = rf"(local(?:-{_IMAGE_USER_RE})?|dev|prod|prod(?:-{_IMAGE_USER_RE})(?:-{_IMAGE_HASH_RE})?|prod(?:-{_IMAGE_HASH_RE})?)"


# TODO(Grisha): call `_dassert_is_base_image_name_valid()` and a separate
# function that validates an image tag.
def dassert_is_image_name_valid(image: str) -> None:
    """
    Check whether an image name is valid.

    Invariants:
    - Local images contain a username and a version
      - E.g., `*****.dkr.ecr.us-east-1.amazonaws.com/amp:local-saggese-1.0.0`
    - `dev` and `prod` images have an instance with a version and one without
      to indicate the latest
      - E.g., `*****.dkr.ecr.us-east-1.amazonaws.com/amp:dev-1.0.0`
        and `*****.dkr.ecr.us-east-1.amazonaws.com/amp:dev`
    - `prod` candidate image has an optional tag (e.g., a username) and
        a 9 character hash identifier corresponding Git commit
        - E.g., `*****.dkr.ecr.us-east-1.amazonaws.com/amp:prod-1.0.0-4rf74b83a`
        - and `*****.dkr.ecr.us-east-1.amazonaws.com/amp:prod-1.0.0-saggese-4rf74b83a`

    An image should look like:

    *****.dkr.ecr.us-east-1.amazonaws.com/amp:dev
    *****.dkr.ecr.us-east-1.amazonaws.com/amp:local-saggese-1.0.0
    *****.dkr.ecr.us-east-1.amazonaws.com/amp:dev-1.0.0
    ghcr.io/cryptokaizen/cmamp:dev
    """
    regex = "".join(
        [
            # E.g., `*****.dkr.ecr.us-east-1.amazonaws.com/cmamp`
            # or `sorrentum/cmamp` or ghcr.io/cryptokaizen/cmamp.
            rf"^{_FULL_IMAGE_NAME_RE}",
            # E.g., `:local-saggese`.
            rf"(:{_IMAGE_STAGE_RE})?",
            # E.g., `-1.0.0`.
            rf"(-{_IMAGE_VERSION_RE})?$",
        ]
    )
    _LOG.debug("Testing with regex='%s'", regex)
    m = re.match(regex, image)
    hdbg.dassert(m, "Invalid image: '%s'", image)


def _dassert_is_base_image_name_valid(base_image: str) -> None:
    """
    Check that the base image is valid, i.e. looks like below.

    *****.dkr.ecr.us-east-1.amazonaws.com/amp ghcr.io/cryptokaizen/cmamp
    """
    regex = rf"^{_FULL_IMAGE_NAME_RE}$"
    _LOG.debug("regex=%s", regex)
    m = re.match(regex, base_image)
    hdbg.dassert(m, "Invalid base_image: '%s'", base_image)


# TODO(Grisha): instead of using `base_image` which is Docker registry address
# + image name, use those as separate parameters. See CmTask5074.
def _get_base_image(base_image: str) -> str:
    """
    :return: e.g., *****.dkr.ecr.us-east-1.amazonaws.com/amp
    """
    if base_image == "":
        # TODO(gp): Use os.path.join.
        base_image = (
            hlitauti.get_default_param("CSFY_ECR_BASE_PATH")
            + "/"
            + hlitauti.get_default_param("BASE_IMAGE")
        )
    _dassert_is_base_image_name_valid(base_image)
    return base_image


# This code path through Git tag was discontinued with CmTask746.
# def get_git_tag(
#      version: str,
#  ) -> str:
#      """
#      Return the tag to be used in Git that consists of an image name and
#      version.
#      :param version: e.g., `1.0.0`. If None, the latest version is used
#      :return: e.g., `amp-1.0.0`
#      """
#      hdbg.dassert_is_not(version, None)
#      _dassert_is_version_valid(version)
#      base_image = hlibtaskut.get_default_param("BASE_IMAGE")
#      tag_name = f"{base_image}-{version}"
#      return tag_name


# TODO(gp): Consider using a token "latest" in version, so that it's always a
#  string and we avoid a special behavior encoded in None.
def get_image(
    base_image: str,
    stage: str,
    version: Optional[str],
) -> str:
    """
    Return the fully qualified image name.

    For local stage, it also appends the username to the image name.

    :param base_image: e.g., *****.dkr.ecr.us-east-1.amazonaws.com/amp
    :param stage: e.g., `local`, `dev`, `prod`
    :param version: e.g., `1.0.0`, if None empty, the latest version is used
    :return: e.g., `*****.dkr.ecr.us-east-1.amazonaws.com/amp:local` or
        `*****.dkr.ecr.us-east-1.amazonaws.com/amp:local-1.0.0`
    """
    # Docker refers the default image as "latest", although in our stage
    # nomenclature we call it "dev".
    hdbg.dassert_in(stage, "local dev prod".split())
    # Get the base image.
    base_image = _get_base_image(base_image)
    _dassert_is_base_image_name_valid(base_image)
    # Get the full image name.
    image = [base_image]
    # Handle the stage.
    image.append(f":{stage}")
    if stage == "local":
        user = hsystem.get_user_name()
        image.append(f"-{user}")
    # Handle the version.
    if version is not None and version != "":
        _dassert_is_version_valid(version)
        image.append(f"-{version}")
    #
    image = "".join(image)
    dassert_is_image_name_valid(image)
    return image


# ////////////////////////////////////////////////////////////////////////////////
# Misc.
# ////////////////////////////////////////////////////////////////////////////////


def _run_docker_as_user(as_user_from_cmd_line: bool) -> bool:
    as_root = hserver.run_docker_as_root()
    as_user = as_user_from_cmd_line
    if as_root:
        as_user = False
    _LOG.debug(
        "as_user_from_cmd_line=%s as_root=%s -> as_user=%s",
        as_user_from_cmd_line,
        as_root,
        as_user,
    )
    return as_user


def _get_container_name(service_name: str) -> str:
    """
    Create a container name based on various information.

    E.g., `grisha.cmamp.app.cmamp1.20220317_232120`

    The information used to build a container is:
       - Linux username
       - Base Docker image name
       - Service name
       - Project directory that was used to start a container
       - Container start timestamp

    :param service_name: `docker-compose` service name, e.g., `app`
    :return: container name
    """
    hdbg.dassert_ne(service_name, "", "You need to specify a service name")
    # Get linux username.
    linux_user = hsystem.get_user_name()
    # Get dir name.
    project_dir = hgit.get_project_dirname()
    # Get Docker image base name.
    image_name = hlitauti.get_default_param("BASE_IMAGE")
    # Get current timestamp.
    current_timestamp = hlitauti.get_ET_timestamp()
    # Build container name.
    container_name = f"{linux_user}.{image_name}.{service_name}.{project_dir}.{current_timestamp}"
    _LOG.debug(
        "get_container_name: container_name=%s",
        container_name,
    )
    return container_name


def _get_docker_base_cmd(
    base_image: str,
    stage: str,
    version: str,
    service_name: str,
    # Params from `_get_docker_compose_cmd()`.
    generate_docker_compose_file: bool,
    extra_env_vars: Optional[List[str]],
    extra_docker_compose_files: Optional[List[str]],
    skip_docker_image_compatibility_check: bool,
) -> List[str]:
    r"""
    Get base `docker-compose` command encoded as a list of strings.

    It can be used as a base to build more complex commands, e.g., `run`, `up`,
    `down`.

    E.g.,
    ```
    ['IMAGE=*****.dkr.ecr.us-east-1.amazonaws.com/amp:dev',
        '\n        docker-compose',
        '\n        --file amp/devops/compose/tmp.docker-compose.yml',
        '\n        --file amp/devops/compose/tmp.docker-compose_as_submodule.yml',
        '\n        --env-file devops/env/default.env']
    ```
    :param generate_docker_compose_file: whether to generate or reuse the existing
        Docker compose file
    :param extra_env_vars: represent vars to add, e.g., `["PORT=9999", "DRY_RUN=1"]`
    :param extra_docker_compose_files: `docker-compose` override files
    :param skip_docker_image_compatibility_check: if True, skip checking image
        architecture compatibility
    """
    _LOG.debug(hprint.func_signature_to_str())
    docker_cmd_: List[str] = []
    # - Handle the image.
    image = get_image(base_image, stage, version)
    _LOG.debug("base_image=%s stage=%s -> image=%s", base_image, stage, image)
    dassert_is_image_name_valid(image)
    # The check is mainly for developers to avoid using the wrong image (e.g.,
    # an x86 vs ARM architecture).
    # We can skip the image compatibility check during the CI or when
    # explicitly skipped.
    if not (hserver.is_inside_ci() or skip_docker_image_compatibility_check):
        hdocker.check_image_compatibility_with_current_arch(image)
    else:
        _LOG.warning("Skipping docker image compatibility check")
    docker_cmd_.append(f"IMAGE={image}")
    # - Handle extra env vars.
    if extra_env_vars:
        hdbg.dassert_isinstance(extra_env_vars, list)
        for env_var in extra_env_vars:
            docker_cmd_.append(f"{env_var}")
    #
    docker_cmd_.append(
        r"""
        docker compose"""
    )
    docker_compose_files = _get_docker_compose_files(
        stage,
        generate_docker_compose_file,
        service_name,
        extra_docker_compose_files,
    )
    file_opts = " ".join([f"--file {dcf}" for dcf in docker_compose_files])
    _LOG.debug(hprint.to_str("file_opts"))
    # TODO(gp): Use something like `.append(rf"{space}{...}")`
    docker_cmd_.append(
        rf"""
        {file_opts}"""
    )
    # - Handle the env file.
    env_file = "devops/env/default.env"
    docker_cmd_.append(
        rf"""
        --env-file {env_file}"""
    )
    return docker_cmd_


def _get_docker_compose_cmd(
    base_image: str,
    stage: str,
    version: str,
    cmd: str,
    *,
    # TODO(gp): make these params mandatory.
    extra_env_vars: Optional[List[str]] = None,
    extra_docker_compose_files: Optional[List[str]] = None,
    extra_docker_run_opts: Optional[List[str]] = None,
    service_name: str = "app",
    use_entrypoint: bool = True,
    generate_docker_compose_file: bool = True,
    as_user: bool = True,
    print_docker_config: bool = False,
    use_bash: bool = False,
    skip_docker_image_compatibility_check: bool = False,
) -> str:
    """
    Get `docker-compose` run command.

    E.g.,
    ```
    IMAGE=*****..dkr.ecr.us-east-1.amazonaws.com/amp:dev \
        docker-compose \
        --file /amp/devops/compose/tmp.docker-compose.yml \
        --env-file devops/env/default.env \
        run \
        --rm \
        --name grisha.cmamp.app.cmamp1.20220317_232120 \
        --user $(id -u):$(id -g) \
        app \
        bash
    ```
    :param cmd: command to run inside Docker container
    :param extra_docker_run_opts: additional `docker-compose` run options
    :param service_name: service to use to run a command
    :param use_entrypoint: whether to use the `entrypoint.sh` or not
    :param generate_docker_compose_file: generate the Docker compose file or not
    :param as_user: pass the user / group id or not
    :param print_docker_config: print the docker config for debugging purposes
    :param use_bash: run command through a shell
    :param skip_docker_image_compatibility_check: if True, skip checking image architecture compatibility
    """
    _LOG.debug(hprint.func_signature_to_str())
    # - Get the base Docker command.
    docker_cmd_ = _get_docker_base_cmd(
        base_image,
        stage,
        version,
        service_name,
        generate_docker_compose_file,
        extra_env_vars,
        extra_docker_compose_files,
        skip_docker_image_compatibility_check,
    )
    # - Add the `config` command for debugging purposes.
    docker_config_cmd: List[str] = docker_cmd_[:]
    # TODO(gp): Use yaml approach like done for other parts of the code.
    docker_config_cmd.append(
        r"""
        config"""
    )
    # - Add the `run` command.
    docker_cmd_.append(
        r"""
        run \
        --rm"""
    )
    # - Add a name to the container.
    container_name = _get_container_name(service_name)
    docker_cmd_.append(
        rf"""
        --name {container_name}"""
    )
    # - Handle the user.
    as_user = _run_docker_as_user(as_user)
    if as_user:
        docker_cmd_.append(
            r"""
        --user $(id -u):$(id -g)"""
        )
    # - Handle the extra docker options.
    if extra_docker_run_opts:
        hdbg.dassert_isinstance(extra_docker_run_opts, list)
        extra_opts = " ".join(extra_docker_run_opts)
        docker_cmd_.append(
            rf"""
        {extra_opts}"""
        )
    # - Handle entrypoint.
    if use_entrypoint:
        docker_cmd_.append(
            rf"""
        {service_name}"""
        )
        if cmd:
            if use_bash:
                cmd = f"bash -c '{cmd}'"
            docker_cmd_.append(
                rf"""
        {cmd}"""
            )
    else:
        # No entrypoint.
        docker_cmd_.append(
            rf"""
        --entrypoint bash \
        {service_name}"""
        )
    # Print the config for debugging purpose.
    if print_docker_config:
        docker_config_cmd_as_str = hlitauti.to_multi_line_cmd(docker_config_cmd)
        _LOG.debug("docker_config_cmd=\n%s", docker_config_cmd_as_str)
        _LOG.debug(
            "docker_config=\n%s",
            hsystem.system_to_string(docker_config_cmd_as_str)[1],
        )
    # Print the config for debugging purpose.
    docker_cmd_: str = hlitauti.to_multi_line_cmd(docker_cmd_)
    return docker_cmd_


# ////////////////////////////////////////////////////////////////////////////////
# bash and cmd.
# ////////////////////////////////////////////////////////////////////////////////


def _docker_cmd(
    ctx: Any,
    docker_cmd_: str,
    *,
    skip_pull: bool = False,
    **ctx_run_kwargs: Any,
) -> Optional[int]:
    """
    Print and execute a Docker command.

    :param kwargs: kwargs for `ctx.run()`
    """
    if hserver.is_inside_ci():
        import helpers.hs3 as hs3

        # Generate files with the AWS settings that are missing when running
        # inside CI.
        hs3.generate_aws_files()
    docker_pull(ctx, skip_pull=skip_pull)
    _LOG.debug("cmd=%s", docker_cmd_)
    rc: Optional[int] = hlitauti.run(ctx, docker_cmd_, pty=True, **ctx_run_kwargs)
    return rc


@task
def docker_bash(  # type: ignore
    ctx,
    base_image="",
    stage="dev",
    version="",
    use_entrypoint=True,
    as_user=True,
    generate_docker_compose_file=True,
    container_dir_name=".",
    skip_pull=False,
    skip_docker_image_compatibility_check=False,
):
    """
    Start a bash shell inside the container corresponding to a stage.

    :param use_entrypoint: whether to use the `entrypoint.sh` or not
    :param as_user: pass the user / group id or not
    :param generate_docker_compose_file: generate the Docker compose file or not
    :param skip_pull: if True skip pulling the docker image
    """
    _LOG.debug(hprint.func_signature_to_str("ctx"))
    hlitauti.report_task(container_dir_name=container_dir_name)
    #
    cmd = "bash"
    docker_cmd_ = _get_docker_compose_cmd(
        base_image,
        stage,
        version,
        cmd,
        generate_docker_compose_file=generate_docker_compose_file,
        use_entrypoint=use_entrypoint,
        as_user=as_user,
        skip_docker_image_compatibility_check=skip_docker_image_compatibility_check,
    )
    _LOG.debug("docker_cmd_=%s", docker_cmd_)
    _docker_cmd(ctx, docker_cmd_, skip_pull=skip_pull)


@task
def docker_cmd(  # type: ignore
    ctx,
    base_image="",
    stage="dev",
    version="",
    cmd="",
    as_user=True,
    generate_docker_compose_file=True,
    use_bash=False,
    container_dir_name=".",
    skip_pull=False,
):
    """
    Execute the command `cmd` inside a container corresponding to a stage.

    :param as_user: pass the user / group id or not
    :param generate_docker_compose_file: generate or reuse the Docker
        compose file
    :param use_bash: run command through a shell
    """
    hlitauti.report_task(container_dir_name=container_dir_name)
    hdbg.dassert_ne(cmd, "")
    # TODO(gp): Do we need to overwrite the entrypoint?
    docker_cmd_ = _get_docker_compose_cmd(
        base_image,
        stage,
        version,
        cmd,
        generate_docker_compose_file=generate_docker_compose_file,
        as_user=as_user,
        use_bash=use_bash,
    )
    _docker_cmd(ctx, docker_cmd_, skip_pull=skip_pull)


# ////////////////////////////////////////////////////////////////////////////////
# Jupyter.
# ////////////////////////////////////////////////////////////////////////////////


def _get_docker_jupyter_cmd(
    base_image: str,
    stage: str,
    version: str,
    port: int,
    self_test: bool,
    *,
    use_entrypoint: bool = True,
    print_docker_config: bool = False,
) -> str:
    cmd = ""
    extra_env_vars = [f"PORT={port}"]
    extra_docker_run_opts = ["--service-ports"]
    service_name = "jupyter_server_test" if self_test else "jupyter_server"
    #
    docker_cmd_ = _get_docker_compose_cmd(
        base_image,
        stage,
        version,
        cmd,
        extra_env_vars=extra_env_vars,
        extra_docker_run_opts=extra_docker_run_opts,
        service_name=service_name,
        use_entrypoint=use_entrypoint,
        print_docker_config=print_docker_config,
    )
    return docker_cmd_


@task
def docker_jupyter(  # type: ignore
    ctx,
    stage="dev",
    version="",
    base_image="",
    auto_assign_port=True,
    use_entrypoint=True,
    port=None,
    self_test=False,
    container_dir_name=".",
    skip_pull=False,
):
    """
    Run Jupyter notebook server.

    :param auto_assign_port: use the UID of the user and the inferred
        number of the repo (e.g., 4 for `~/src/amp4`) to get a unique
        port
    :param skip_pull: if True skip pulling the docker image
    """
    hlitauti.report_task(container_dir_name=container_dir_name)
    if port is None:
        if auto_assign_port:
            uid = os.getuid()
            _LOG.debug("uid=%s", uid)
            git_repo_idx = hgit.get_project_dirname(only_index=True)
            git_repo_idx = int(git_repo_idx)
            _LOG.debug("git_repo_idx=%s", git_repo_idx)
            # We assume that there are no more than `max_idx_per_users` clients.
            max_idx_per_user = 10
            hdbg.dassert_lte(git_repo_idx, max_idx_per_user)
            port = (uid * max_idx_per_user) + git_repo_idx
        else:
            port = 9999
    _LOG.info("Assigned port is %s", port)
    #
    print_docker_config = False
    docker_cmd_ = _get_docker_jupyter_cmd(
        base_image,
        stage,
        version,
        port,
        self_test,
        use_entrypoint=use_entrypoint,
        print_docker_config=print_docker_config,
    )
    _docker_cmd(ctx, docker_cmd_, skip_pull=skip_pull)


def _get_docker_dash_app_cmd(
    base_image: str,
    stage: str,
    version: str,
    port: int,
    *,
    print_docker_config: bool = False,
) -> str:
    cmd = ""
    extra_env_vars = [f"PORT={port}"]
    extra_docker_run_opts = ["--service-ports"]
    service_name = "dash_app"
    #
    docker_cmd_ = _get_docker_compose_cmd(
        base_image,
        stage,
        version,
        cmd,
        extra_env_vars=extra_env_vars,
        extra_docker_run_opts=extra_docker_run_opts,
        service_name=service_name,
        print_docker_config=print_docker_config,
    )
    return docker_cmd_


@task
def docker_dash_app(  # type: ignore
    ctx,
    stage="dev",
    version="",
    base_image="",
    auto_assign_port=True,
    port=None,
    container_dir_name=".",
):
    """
    Run dash app.

    :param auto_assign_port: use the UID of the user and the inferred
        number of the repo (e.g., 4 for `~/src/amp4`) to get a unique
        port
    """
    hlitauti.report_task(container_dir_name=container_dir_name)
    if port is None:
        if auto_assign_port:
            uid = os.getuid()
            _LOG.debug("uid=%s", uid)
            git_repo_idx = hgit.get_project_dirname(only_index=True)
            git_repo_idx = int(git_repo_idx)
            _LOG.debug("git_repo_idx=%s", git_repo_idx)
            # We assume that there are no more than `max_idx_per_users` clients.
            max_idx_per_user = 10
            hdbg.dassert_lte(git_repo_idx, max_idx_per_user)
            port = (uid * max_idx_per_user) + git_repo_idx
        else:
            port = 9999
    #
    _LOG.info("Assigned port is %s", port)
    print_docker_config = False
    docker_cmd_ = _get_docker_dash_app_cmd(
        base_image,
        stage,
        version,
        port,
        print_docker_config=print_docker_config,
    )
    _docker_cmd(ctx, docker_cmd_)
