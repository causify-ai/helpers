"""
Identify on which server we are running.

Import as:

import helpers.hserver as hserver
"""

import functools
import logging
import os
import shutil
import subprocess
from typing import Dict, List, Optional, Tuple

import helpers.hprint as hprint
import helpers.repo_config_utils as hrecouti

# This module should depend only on:
# - Python standard modules
# See `helpers/dependencies.txt` for more details

_LOG = logging.getLogger(__name__)

_WARNING = "\033[33mWARNING\033[0m"


def _print(msg: str) -> None:
    _ = msg
    # _LOG.info(msg)
    if False:
        print(msg)


# We can't use `hsystem` to avoid import cycles.
def _system_to_string(cmd: str) -> Tuple[int, str]:
    """
    Run a command and return the output and the return code.

    :param cmd: command to run
    :return: tuple of (return code, output)
    """
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        # Redirect stderr to stdout.
        stderr=subprocess.STDOUT,
        shell=True,
        text=True,
    )
    rc = result.returncode
    output = result.stdout
    output = output.strip()
    return rc, output


# #############################################################################
# Host
# #############################################################################


# We can't rely only on the name / version of the host to infer where we are
# running, since inside Docker the name of the host is like `01a7e34a82a5`. Of
# course, there is no way to know anything about the host for security reason,
# so we pass this value from the external environment to the container, through
# env vars (e.g., `CSFY_HOST_NAME`, `CSFY_HOST_OS_NAME`, `CSFY_HOST_OS_VERSION`).


# Sometimes we want to know if:
# - The processor is x86_64 or arm64
# - The host is Mac or Linux
# - We are running on a Causify machine or on an external machine
# - We are inside CI or not
# TODO(gp): Grep all the use cases in the codebase and use the right function.


def get_host_user_name() -> Optional[str]:
    """
    Return the name of the user running the host.
    """
    return os.environ.get("CSFY_HOST_USER_NAME", None)


def get_dev_csfy_host_names() -> List[str]:
    """
    Return the names of the Causify dev servers.
    """
    host_names = ("dev1", "dev2", "dev3")
    return host_names


def _get_host_name() -> str:
    """
    Return the name of the host (not the machine) on which we are running.

    If we are inside a Docker container, we use the name of the host passed
    through the `CSFY_HOST_NAME` env var.
    """
    if is_inside_docker():
        host_name = os.environ["CSFY_HOST_NAME"]
    else:
        # sysname='Linux'
        # nodename='dev1'
        # release='5.15.0-1081-aws'
        # version='#88~20.04.1-Ubuntu SMP Fri Mar 28 14:17:22 UTC 2025'
        # machine='x86_64'
        host_name = os.uname()[1]
    _LOG.debug("host_name=%s", host_name)
    return host_name


def _get_host_os_name() -> str:
    """
    Return the name of the OS on which we are running (e.g., "Linux",
    "Darwin").

    If we are inside a Docker container, we use the name of the OS passed
    through the `CSFY_HOST_OS_NAME` env var.
    """
    if is_inside_docker():
        host_os_name = os.environ["CSFY_HOST_OS_NAME"]
    else:
        # sysname='Linux'
        # nodename='dev1'
        # release='5.15.0-1081-aws'
        # version='#88~20.04.1-Ubuntu SMP Fri Mar 28 14:17:22 UTC 2025'
        # machine='x86_64'
        host_os_name = os.uname()[0]
    _LOG.debug("host_os_name=%s", host_os_name)
    return host_os_name


def _get_host_os_version() -> str:
    """
    Return the version of the OS on which we are running.

    If we are inside a Docker container, we use the version of the OS passed
    through the `CSFY_HOST_OS_VERSION` env var.
    """
    if is_inside_docker():
        host_os_version = os.environ["CSFY_HOST_OS_VERSION"]
    else:
        # sysname='Linux'
        # nodename='dev1'
        # release='5.15.0-1081-aws'
        # version='#88~20.04.1-Ubuntu SMP Fri Mar 28 14:17:22 UTC 2025'
        # machine='x86_64'
        host_os_version = os.uname()[2]
    _LOG.debug("host_os_version=%s", host_os_version)
    return host_os_version


def is_host_csfy_server() -> bool:
    """
    Return whether we are running on a Causify dev server.
    """
    host_name = _get_host_name()
    ret = host_name in get_dev_csfy_host_names()
    return ret


_MAC_OS_VERSION_MAPPING = {
    "Catalina": "19.",
    "Monterey": "21.",
    "Ventura": "22.",
    "Sequoia": "24.",
}


def is_host_mac() -> bool:
    """
    Return whether we are running on macOS.
    """
    host_os_name = _get_host_os_name()
    #
    ret = host_os_name == "Darwin"
    return ret


def get_host_mac_version() -> str:
    """
    Get the macOS version (e.g., "Catalina", "Monterey", "Ventura").
    """
    host_os_version = _get_host_os_version()
    for version, tag in _MAC_OS_VERSION_MAPPING.items():
        if tag in host_os_version:
            return version
    raise ValueError(f"Invalid host_os_version='{host_os_version}'")


def is_host_mac_version(version: str) -> bool:
    """
    Return whether we are running on a Mac with a specific version (e.g.,
    "Catalina", "Monterey", "Ventura").
    """
    assert version in _MAC_OS_VERSION_MAPPING, f"Invalid version='{version}'"
    host_mac_version = get_host_mac_version()
    ret = version.lower() == host_mac_version.lower()
    return ret


def is_host_gp_mac() -> bool:
    """
    Return whether we are running on a Mac owned by GP.

    This is used to check if we can use a specific feature before
    releasing it to all the users.
    """
    host_name = _get_host_name()
    ret = host_name.startswith("gpmac.")
    return ret


# #############################################################################
# Detect server.
# #############################################################################


def is_inside_ci() -> bool:
    """
    Return whether we are running inside the Continuous Integration flow.
    """
    if "CSFY_CI" not in os.environ:
        ret = False
    else:
        ret = os.environ["CSFY_CI"] != ""
    return ret


# TODO(gp): -> is_inside_docker_container()
def is_inside_docker() -> bool:
    """
    Return whether we are inside a container or not.
    """
    # From https://stackoverflow.com/questions/23513045
    ret = os.path.exists("/.dockerenv")
    return ret


def is_inside_unit_test() -> bool:
    """
    Return whether we are running code insider the regressions.
    """
    ret = "PYTEST_CURRENT_TEST" in os.environ
    return ret


# TODO(gp): Remove!
def is_dev_csfy() -> bool:
    # sysname='Linux'
    # nodename='dev1'
    # release='5.15.0-1081-aws',
    # version='#88~20.04.1-Ubuntu SMP Fri Mar 28 14:17:22 UTC 2025',
    # machine='x86_64'
    host_name = os.uname()[1]
    host_names = ("dev1", "dev2", "dev3")
    csfy_host_name = os.environ.get("CSFY_HOST_NAME", "")
    _LOG.debug("host_name=%s csfy_host_name=%s", host_name, csfy_host_name)
    is_dev_csfy_ = host_name in host_names or csfy_host_name in host_names
    return is_dev_csfy_


# TODO(gp): This is obsolete and should be removed.
def is_dev4() -> bool:
    """
    Return whether it's running on dev4.
    """
    host_name = os.uname()[1]
    csfy_host_name = os.environ.get("CSFY_HOST_NAME", None)
    dev4 = "cf-spm-dev4"
    _LOG.debug("host_name=%s csfy_host_name=%s", host_name, csfy_host_name)
    is_dev4_ = dev4 in (host_name, csfy_host_name)
    #
    if not is_dev4_:
        dev4 = "cf-spm-dev8"
        _LOG.debug("host_name=%s csfy_host_name=%s", host_name, csfy_host_name)
        is_dev4_ = dev4 in (host_name, csfy_host_name)
    return is_dev4_


def is_host_mac(*, version: Optional[str] = None) -> bool:
    """
    Return whether we are running on macOS and, optionally, on a specific
    version.

    :param version: check whether we are running on a certain macOS version (e.g.,
        `Catalina`, `Monterey`)
    """
    _LOG.debug("version=%s", version)
    host_os_name = os.uname()[0]
    _LOG.debug("os.uname()=%s", str(os.uname()))
    csfy_host_os_name = os.environ.get("CSFY_HOST_OS_NAME", None)
    _LOG.debug(
        "host_os_name=%s csfy_host_os_name=%s", host_os_name, csfy_host_os_name
    )
    is_mac_ = host_os_name == "Darwin" or csfy_host_os_name == "Darwin"
    if version is None:
        # The user didn't request a specific version, so we return whether we
        # are running on a Mac or not.
        _LOG.debug("is_mac_=%s", is_mac_)
        return is_mac_
    else:
        # The user specified a version: if we are not running on a Mac then we
        # return False, since we don't even have to check the macOS version.
        if not is_mac_:
            _LOG.debug("is_mac_=%s", is_mac_)
            return False
    # Check the macOS version we are running.
    if version == "Catalina":
        # Darwin gpmac.local 19.6.0 Darwin Kernel Version 19.6.0:
        # root:xnu-6153.141.2~1/RELEASE_X86_64 x86_64
        macos_tag = "19.6"
    elif version == "Monterey":
        # Darwin alpha.local 21.5.0 Darwin Kernel Version 21.5.0:
        # root:xnu-8020.121.3~4/RELEASE_ARM64_T6000 arm64
        macos_tag = "21."
    elif version == "Ventura":
        macos_tag = "22."
    elif version == "Sequoia":
        # Darwin gpmac.local 24.4.0 Darwin Kernel Version 24.4.0:
        # root:xnu-11417.101.15~1/RELEASE_ARM64_T8112 arm64
        macos_tag = "24."
    else:
        raise ValueError(f"Invalid version='{version}'")
    _LOG.debug("macos_tag=%s", macos_tag)
    host_os_version = os.uname()[2]
    # 'Darwin Kernel Version 19.6.0: Mon Aug 31 22:12:52 PDT 2020;
    #   root:xnu-6153.141.2~1/RELEASE_X86_64'
    csfy_host_os_version = os.environ.get("CSFY_HOST_VERSION", "")
    _LOG.debug(
        "host_os_version=%s csfy_host_os_version=%s",
        host_os_version,
        csfy_host_os_version,
    )
    is_mac_ = macos_tag in host_os_version or macos_tag in csfy_host_os_version
    _LOG.debug("is_mac_=%s", is_mac_)
    return is_mac_


def is_prod_csfy() -> bool:
    """
    Detect whether we are running in a Causify production container.

    This env var is set inside `devops/docker_build/prod.Dockerfile`.
    """
    # TODO(gp): CK -> CSFY
    return bool(os.environ.get("CK_IN_PROD_CMAMP_CONTAINER", False))


# TODO(gp): Obsolete.
def is_ig_prod() -> bool:
    """
    Detect whether we are running in an IG production container.

    This env var is set inside `//lime/devops_cf/setenv.sh`
    """
    # CF sets up `DOCKER_BUILD` so we can use it to determine if we are inside
    # a CF container or not.
    # print("os.environ\n", str(os.environ))
    return bool(os.environ.get("DOCKER_BUILD", False))


# TODO(Grisha): consider adding to `setup_to_str()`.
def is_inside_ecs_container() -> bool:
    """
    Detect whether we are running in an ECS container.
    """
    # When deploying jobs via ECS the container obtains credentials based
    # on passed task role specified in the ECS task-definition, refer to:
    # https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html
    ret = "AWS_CONTAINER_CREDENTIALS_RELATIVE_URI" in os.environ
    return ret


# #############################################################################


def is_external_linux() -> bool:
    """
    Detect whether we are running on a non-server/non-CI Linux machine.

    This returns true when we run on the machine of an intern, or a non-
    CSFY contributor.
    """
    if is_host_csfy_server() or is_inside_ci():
        # Dev servers and CI are not external Linux systems.
        ret = False
    else:
        # We need to check if the host is Linux.
        host_os_name = _get_host_os_name()
        ret = host_os_name == "Linux"
    return ret


def is_external_dev() -> bool:
    """
    Detect whether we are running on an system outside of Causify.

    E.g., a Linux / Mac contributor's laptop, an intern's laptop, a non-
    CSFY machine.
    """
    ret = is_host_mac() or is_external_linux()
    return ret


# #############################################################################
# Set up consistency.
# #############################################################################


# TODO(gp): Update this.
def _get_setup_signature() -> str:
    """
    Dump all the variables that are used to make a decision about the values of
    the functions in `_get_setup_settings()`.

    This function is used to mock the state of the system for testing
    purposes.
    """
    cmds = []
    # is_prod_csfy()
    cmds.append('os.environ.get("CK_IN_PROD_CMAMP_CONTAINER", "*undef*")')
    # is_dev4()
    # is_dev_csfy()
    # is_ig_prod()
    cmds.append('os.environ.get("CSFY_HOST_NAME", "*undef*")')
    # is_inside_ci()
    cmds.append('os.environ.get("CSFY_CI", "*undef*")')
    # is_mac()
    cmds.append("os.uname()[0]")
    cmds.append("os.uname()[2]")
    # is_external_linux()
    cmds.append('os.environ.get("CSFY_HOST_OS_NAME", "*undef*")')
    # Build an array of strings with the results of executing the commands.
    results = []
    for cmd in cmds:
        result_tmp = cmd + "=" + str(eval(cmd))
        results.append(result_tmp)
    # Join the results into a single string.
    result = "\n".join(results)
    return result


# The valid set ups are:
# - Running on a Causify server (e.g., `dev1`, `dev2`, `dev3`)
#   - Container
#   - Host
# - External Mac (GP, Paul, interns, contributors)
#   - Container
#   - Host
# - External Linux (interns, contributors)
#   - Container
#   - Host
# - Prod container on Linux
#   - Container
# - CI
#   - Container


def is_inside_docker_container_on_csfy_server() -> bool:
    """
    Return whether we are running on a Docker container on a Causify server.
    """
    ret = is_inside_docker() and is_host_csfy_server()
    return ret


def is_outside_docker_container_on_csfy_server() -> bool:
    """
    Return whether we are running outside a Docker container on a Causify
    server.
    """
    ret = not is_inside_docker() and is_host_csfy_server()
    return ret


def is_inside_docker_container_on_host_mac() -> bool:
    """
    Return whether we are running on a Docker container on a Mac host.
    """
    ret = is_inside_docker() and is_host_mac()
    return ret


def is_outside_docker_container_on_host_mac() -> bool:
    """
    Return whether we are running outside of a Docker container on a Mac host.
    """
    ret = not is_inside_docker() and is_host_mac()
    return ret


def is_inside_docker_container_on_external_linux() -> bool:
    """
    Return whether we are running on a Docker container on an external Linux.
    """
    ret = is_inside_docker() and is_external_linux()
    return ret


def is_outside_docker_container_on_external_linux() -> bool:
    """
    Return whether we are outside of a Docker container on an external Linux.
    """
    ret = not is_inside_docker() and is_external_linux()
    return ret


def _get_setup_settings() -> List[Tuple[str, bool]]:
    """
    Return a list of tuples with the name and value of the current server
    setup.
    """
    func_names = [
        "is_inside_docker_container_on_csfy_server",
        "is_outside_docker_container_on_csfy_server",
        #
        "is_inside_docker_container_on_host_mac",
        "is_outside_docker_container_on_host_mac",
        #
        "is_inside_docker_container_on_external_linux",
        "is_outside_docker_container_on_external_linux",
        #
        "is_dev4",
        "is_ig_prod",
        "is_prod_csfy",
        "is_inside_ci",
    ]
    # Store function name / value pairs as tuples.
    setups = []
    for func_name in func_names:
        val = eval(f"{func_name}()")
        setups.append((func_name, val))
    return setups


def _setup_to_str(setups: List[Tuple[str, bool]]) -> str:
    """
    Return a string representation of the current server setup configuration.

    :return: string with each setting on a new line, aligned with
        padding
    """
    # Find maximum length of setting names.
    max_len = max(len(name) for name, _ in setups) + 1
    # Format each line with computed padding.
    txt = []
    for name, value in setups:
        txt.append(f"{name:<{max_len}}{value}")
    return "\n".join(txt)


def _dassert_setup_consistency() -> None:
    """
    Check that one and only one setup configuration is true.

    This is used to ensure that the setup configuration is one of the
    expected ones and uniquely defined.
    """

    # We don't want to import `hprint` here because it will cause a circular
    # import.
    def _indent(txt: str, *, num_spaces: int = 2) -> str:
        """
        Add `num_spaces` spaces before each line of the passed string.
        """
        spaces = " " * num_spaces
        txt_out = []
        for curr_line in txt.split("\n"):
            if curr_line.lstrip().rstrip() == "":
                # Do not prepend any space to a line with only white characters.
                txt_out.append("")
                continue
            txt_out.append(spaces + curr_line)
        res = "\n".join(txt_out)
        return res

    setups = _get_setup_settings()
    # One and only one set-up should be true.
    sum_ = sum([value for _, value in setups])
    if sum_ != 1:
        msg = "One and only one set-up config should be true:\n"
        msg += _setup_to_str(setups) + "\n"
        msg += "_get_setup_signature() returns:\n"
        msg += _indent(_get_setup_signature())
        raise ValueError(msg)


# If the env var is not defined then we want to check. The only reason to skip
# it's if the env var is defined and equal to False.
check_repo = os.environ.get("CSFY_REPO_CONFIG_CHECK", "True") != "False"
_is_called = False
if check_repo:
    # The repo check is executed at import time, before the logger is initialized.
    # To debug the repo check, enable the following block.
    if False:
        import helpers.hdbg as hdbg

        hdbg.init_logger(verbosity=logging.DEBUG)
    # Compute and cache the result.
    if not _is_called:
        _dassert_setup_consistency()
        _is_called = True
else:
    _LOG.warning("Skipping repo check in %s", __file__)


# #############################################################################
# Detect Docker functionalities.
# #############################################################################


# Each function below should run without asserting. E.g., when we check if
# docker supports privileged mode, we should check if `docker` is available,
# and then if docker supports privileged mode, instead of asserting if `docker`
# doesn't exist on the system.


@functools.lru_cache()
def has_docker() -> bool:
    """
    Return whether we have Docker installed.
    """
    return shutil.which("docker") is not None


@functools.lru_cache()
def docker_needs_sudo() -> bool:
    """
    Return whether Docker commands need to be run with sudo.
    """
    if not has_docker():
        return False
    # Another way to check is to see if your user is in the docker group:
    # > groups | grep docker
    rc = os.system("docker run hello-world 2>&1 >/dev/null")
    if rc == 0:
        return False
    #
    rc = os.system("sudo docker run hello-world 2>&1 >/dev/null")
    if rc == 0:
        return True
    assert False, "Failed to run docker"


@functools.lru_cache()
def has_docker_privileged_mode() -> bool:
    """
    Return whether the current container supports privileged mode.

    Docker privileged mode gives containers nearly all the same capabilities as
    the host system's kernel.
    Privileged mode allows to:
    - run Docker-in-Docker
    - mount filesystems
    """
    cmd = "docker run --privileged hello-world 2>&1 >/dev/null"
    rc = os.system(cmd)
    _print("cmd=%s -> rc=%s" % (cmd, rc))
    has_privileged_mode = rc == 0
    return has_privileged_mode


def has_sibling_containers_support() -> bool:
    # We need to be inside a container to run sibling containers.
    if not is_inside_docker():
        return False
    # We assume that if the socket exists then we can run sibling containers.
    if os.path.exists("/var/run/docker.sock"):
        return True
    return False


def has_docker_dind_support() -> bool:
    """
    Return whether the current container supports Docker-in-Docker.
    """
    # We need to be inside a container to run docker-in-docker.
    if not is_inside_docker():
        return False
    # We assume that if we have privileged mode then we can run docker-in-docker.
    return has_docker_privileged_mode()


def get_docker_info() -> str:
    txt_tmp: List[str] = []
    #
    has_docker_ = has_docker()
    txt_tmp.append(f"has_docker={has_docker_}")
    #
    cmd = r"docker version --format '{{.Server.Version}}'"
    _, docker_version = _system_to_string(cmd)
    txt_tmp.append(f"docker_version='{docker_version}'")
    #
    docker_needs_sudo_ = docker_needs_sudo()
    txt_tmp.append(f"docker_needs_sudo={docker_needs_sudo_}")
    #
    has_privileged_mode_ = has_docker_privileged_mode()
    txt_tmp.append(f"has_privileged_mode={has_privileged_mode_}")
    #
    is_inside_docker_ = is_inside_docker()
    txt_tmp.append(f"is_inside_docker={is_inside_docker_}")
    #
    if is_inside_docker_:
        has_sibling_containers_support_ = has_sibling_containers_support()
        has_docker_dind_support_ = has_docker_dind_support()
    else:
        has_sibling_containers_support_ = "*undef*"
        has_docker_dind_support_ = "*undef*"
    txt_tmp.append(
        f"has_sibling_containers_support={has_sibling_containers_support_}"
    )
    txt_tmp.append(f"has_docker_dind_support={has_docker_dind_support_}")
    #
    txt = hprint.to_info("Docker info", txt_tmp)
    return txt


# #############################################################################
# Detect Docker functionalities, based on the set-up.
# #############################################################################


# TODO(gp): These approach is sub-optimal. We deduce what we can do based on the
# name of the set-up. We should base our decisions on the actual capabilities of
# the system.


# TODO(gp): -> has_docker_privileged_mode
@functools.lru_cache()
def has_dind_support() -> bool:
    """
    Return whether the current container supports privileged mode.

    This is needed to use Docker-in-Docker.
    """
    _print("is_inside_docker()=%s" % is_inside_docker())
    if not is_inside_docker():
        # Outside Docker there is no privileged mode.
        _print("-> ret = False")
        return False
    # TODO(gp): Not sure this is really needed since we do this check
    #  after enable_privileged_mode controls if we have dind or not.
    if _is_mac_version_with_sibling_containers():
        return False
    # TODO(gp): This part is not multi-process friendly. When multiple
    # processes try to run this code they interfere. A solution is to run `ip
    # link` in the entrypoint and create a `has_docker_privileged_mode` file
    # which contains the value.
    # We rely on the approach from https://stackoverflow.com/questions/32144575
    # to check if there is support for privileged mode.
    # Sometimes there is some state left, so we need to clean it up.
    # TODO(Juraj): this is slow and inefficient, but works for now.
    cmd = "sudo docker run hello-world"
    rc = os.system(cmd)
    _print("cmd=%s -> rc=%s" % (cmd, rc))
    has_dind = rc == 0
    # dind is supported on both Mac and GH Actions.
    # TODO(Juraj): HelpersTask16.
    # if check_repo:
    #    if hserver.is_inside_ci():
    #        # Docker-in-docker is needed for GH actions. For all other builds is optional.
    #        assert has_dind, (
    #            f"Expected privileged mode: has_dind={has_dind}\n"
    #            + hserver.setup_to_str()
    #        )
    #    else:
    #        only_warning = True
    #        _raise_invalid_host(only_warning)
    #        return False
    # else:
    #    csfy_repo_config = os.environ.get("CSFY_REPO_CONFIG_CHECK", "True")
    #    print(
    #        _WARNING
    #        + ": Skip checking since CSFY_REPO_CONFIG_CHECK="
    #        + f"'{csfy_repo_config}'"
    #    )
    return has_dind


def _raise_invalid_host(only_warning: bool) -> None:
    host_os_name = os.uname()[0]
    am_host_os_name = os.environ.get("AM_HOST_OS_NAME", None)
    msg = (
        f"Don't recognize host: host_os_name={host_os_name}, "
        f"am_host_os_name={am_host_os_name}"
    )
    if only_warning:
        _LOG.warning(msg)
    else:
        raise ValueError(msg)


# TODO(gp): -> use_docker_in_docker_support
def enable_privileged_mode() -> bool:
    """
    Return whether a host supports privileged mode for its containers.
    """
    repo_name = hrecouti.get_repo_config().get_name()
    # TODO(gp): Remove this dependency from a repo.
    if repo_name in ("//dev_tools",):
        ret = False
    else:
        # Keep this in alphabetical order.
        if is_dev_csfy():
            ret = True
        elif is_inside_ci():
            ret = True
        elif is_host_mac(version="Catalina"):
            # Docker for macOS Catalina supports dind.
            ret = True
        elif (
            is_host_mac(version="Monterey")
            or is_host_mac(version="Ventura")
            or is_host_mac(version="Sequoia")
        ):
            # Docker doesn't seem to support dind for these versions of macOS.
            ret = False
        elif is_prod_csfy():
            ret = False
        else:
            ret = False
            only_warning = True
            _raise_invalid_host(only_warning)
    return ret


# TODO(gp): -> use_docker_sudo_in_commands
def has_docker_sudo() -> bool:
    """
    Return whether Docker commands should be run with `sudo` or not.
    """
    # Keep this in alphabetical order.
    if is_dev_csfy():
        ret = True
    elif is_external_linux():
        ret = True
    elif is_inside_ci():
        ret = False
    elif is_host_mac():
        # macOS runs Docker with sudo by default.
        # TODO(gp): This is not true.
        ret = True
    elif is_prod_csfy():
        ret = False
    else:
        ret = False
        only_warning = True
        _raise_invalid_host(only_warning)
    return ret


def _is_mac_version_with_sibling_containers() -> bool:
    return (
        is_host_mac(version="Monterey")
        or is_host_mac(version="Ventura")
        or is_host_mac(version="Sequoia")
    )


# TODO(gp): -> use_docker_sibling_container_support
def use_docker_sibling_containers() -> bool:
    """
    Return whether to use Docker sibling containers.

    Using sibling containers requires that all Docker containers in the
    same network so that they can communicate with each other.
    """
    val = is_dev4() or _is_mac_version_with_sibling_containers()
    return val


# TODO(gp): -> use_docker_main_network
def use_main_network() -> bool:
    # TODO(gp): Replace this.
    return use_docker_sibling_containers()


# TODO(gp): -> get_docker_shared_data_dir_map
def get_shared_data_dirs() -> Optional[Dict[str, str]]:
    """
    Get path of dir storing data shared between different users on the host and
    Docker.

    E.g., one can mount a central dir `/data/shared`, shared by multiple
    users, on a dir `/shared_data` in Docker.
    """
    # TODO(gp): Keep this in alphabetical order.
    if is_dev4():
        shared_data_dirs = {
            "/local/home/share/cache": "/cache",
            "/local/home/share/data": "/data",
        }
    elif is_dev_csfy():
        shared_data_dirs = {
            "/data/shared": "/shared_data",
            "/data/shared2": "/shared_data2",
        }
    elif is_external_dev() or is_inside_ci() or is_prod_csfy():
        shared_data_dirs = None
    else:
        shared_data_dirs = None
        only_warning = True
        _raise_invalid_host(only_warning)
    return shared_data_dirs


def use_docker_network_mode_host() -> bool:
    # TODO(gp): Not sure this is needed any more, since we typically run in
    # bridge mode.
    ret = is_host_mac() or is_dev_csfy()
    ret = False
    if ret:
        assert use_docker_sibling_containers()
    return ret


def use_docker_db_container_name_to_connect() -> bool:
    """
    Connect to containers running DBs just using the container name, instead of
    using port and localhost / hostname.
    """
    if _is_mac_version_with_sibling_containers():
        # New Macs don't seem to see containers unless we connect with them
        # directly with their name.
        ret = True
    else:
        ret = False
    if ret:
        # This implies that we are using Docker sibling containers.
        assert use_docker_sibling_containers()
    return ret


# TODO(gp): This seems redundant with use_docker_sudo_in_commands
def run_docker_as_root() -> bool:
    """
    Return whether Docker should be run with root user.

    I.e., adding `--user $(id -u):$(id -g)` to docker compose or not.
    """
    # Keep this in alphabetical order.
    if is_dev4() or is_ig_prod():
        # //lime runs on a system with Docker remap which assumes we don't
        # specify user credentials.
        ret = True
    elif is_dev_csfy():
        # On dev1 / dev2 we run as users specifying the user / group id as
        # outside.
        ret = False
    elif is_external_linux():
        ret = False
    elif is_inside_ci():
        # When running as user in GH action we get an error:
        # ```
        # /home/.config/gh/config.yml: permission denied
        # ```
        # see https://github.com/alphamatic/amp/issues/1864
        # So we run as root in GH actions.
        ret = True
    elif is_host_mac():
        ret = False
    elif is_prod_csfy():
        ret = False
    else:
        ret = False
        only_warning = True
        _raise_invalid_host(only_warning)
    return ret


# TODO(gp): Probably obsolete
def get_docker_user() -> str:
    """
    Return the user that runs Docker, if any.
    """
    if is_dev4():
        val = "spm-sasm"
    else:
        val = ""
    return val


# TODO(gp): Probably obsolete
def get_docker_shared_group() -> str:
    """
    Return the group of the user running Docker, if any.
    """
    if is_dev4():
        val = "sasm-fileshare"
    else:
        val = ""
    return val


# TODO(gp): -> repo_config.yaml
def skip_submodules_test() -> bool:
    """
    Return whether the tests in the submodules should be skipped.

    E.g. while running `i run_fast_tests`.
    """
    repo_name = hrecouti.get_repo_config().get_name()
    # TODO(gp): Why do we want to skip running tests?
    # TODO(gp): Remove this dependency from a repo.
    if repo_name in ("//dev_tools",):
        # Skip running `amp` tests from `dev_tools`.
        return True
    return False


# #############################################################################
# S3 buckets.
# #############################################################################


def is_AM_S3_available() -> bool:
    # AM bucket is always available.
    val = True
    _LOG.debug("val=%s", val)
    return val


def is_CK_S3_available() -> bool:
    val = True
    if is_inside_ci():
        repo_name = hrecouti.get_repo_config().get_name()
        # TODO(gp): Remove this dependency from a repo.
        if repo_name in ("//amp", "//dev_tools"):
            # No CK bucket.
            val = False
        # TODO(gp): We might want to enable CK tests also on lemonade.
        if repo_name in ("//lemonade",):
            # No CK bucket.
            val = False
    elif is_dev4():
        # CK bucket is not available on dev4.
        val = False
    _LOG.debug("val=%s", val)
    return val


# #############################################################################
# Functions.
# #############################################################################


# Copied from hprint to avoid import cycles.


def _indent(txt: str, *, num_spaces: int = 2) -> str:
    """
    Add `num_spaces` spaces before each line of the passed string.
    """
    spaces = " " * num_spaces
    txt_out = []
    for curr_line in txt.split("\n"):
        if curr_line.lstrip().rstrip() == "":
            # Do not prepend any space to a line with only white characters.
            txt_out.append("")
            continue
        txt_out.append(spaces + curr_line)
    res = "\n".join(txt_out)
    return res


# End copy.


def config_func_to_str() -> str:
    """
    Print the value of all the config functions.
    """
    ret: List[str] = []
    # Get the functions with:
    # grep "def " helpers/hserver.py | sort | awk '{ print $2 }' | perl -i -ne 'print "$1\n" if /^([^\(]+)/'
    function_names = [
        "enable_privileged_mode",
        "get_docker_shared_group",
        "get_docker_user",
        "get_host_user_name",
        "get_shared_data_dirs",
        "has_dind_support",
        "has_docker_sudo",
        "is_AM_S3_available",
        "is_CK_S3_available",
        "is_dev4",
        "is_dev_csfy",
        "is_external_linux",
        "is_host_mac",
        "is_ig_prod",
        "is_inside_ci",
        "is_inside_docker",
        "is_inside_ecs_container",
        "is_inside_unit_test",
        "is_prod_csfy",
        "run_docker_as_root",
        "skip_submodules_test",
        "use_docker_db_container_name_to_connect",
        "use_docker_network_mode_host",
        "use_docker_sibling_containers",
        "use_main_network",
    ]
    for func_name in sorted(function_names):
        try:
            _LOG.debug("func_name=%s", func_name)
            func_value = eval(f"{func_name}()")
        except NameError:
            func_value = "*undef*"
        msg = f"{func_name}='{func_value}'"
        ret.append(msg)
    # Package.
    ret = "\n".join(ret)
    return ret
