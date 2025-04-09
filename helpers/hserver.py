"""
Identify on which server we are running.

Import as:

import helpers.hserver as hserver
"""

import functools
import logging
import os
from typing import Dict, List, Optional, Tuple

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


def is_inside_docker() -> bool:
    """
    Return whether we are inside a container or not.
    """
    # From https://stackoverflow.com/questions/23513045
    return os.path.exists("/.dockerenv")


def is_inside_unit_test() -> bool:
    """
    Return whether we are running code insider the regressions.
    """
    return "PYTEST_CURRENT_TEST" in os.environ


# We can't rely only on the name of the host to infer where we are running,
# since inside Docker the name of the host is like `01a7e34a82a5`. Of course,
# there is no way to know anything about the host for security reason, so we
# pass this value from the external environment to the container, through env
# vars (e.g., `CSFY_HOST_NAME`, `CSFY_HOST_OS_NAME`).

# TODO(gp): The confusion is that we want to determine on which "setup" we are
# running. We do this both inside container and outside container.
#
# Sometimes we want to know if:
# - the processor is x86_64 or arm64
# - the host is Mac or Linux
# - we are running on a Causify machine or on an external machine
# - we are inside CI or not
# We should grep all the use cases in the codebase and use the right function.

# TODO(gp): The confusion is that we want to determine on which "setup" we are
# running. We do this both inside container and outside container.
#
# Sometimes we want to know if:
# - the processor is x86_64 or arm64
# - the host is Mac or Linux
# - we are running on a Causify machine or on an external machine
# - we are inside CI or not
# We should grep all the use cases in the codebase and use the right function.


def is_dev_csfy() -> bool:
    # TODO(gp): Update to use dev1 values.
    # sysname='Darwin'
    # nodename='gpmac.lan'
    # release='19.6.0'
    # version='Darwin Kernel Version 19.6.0: Mon Aug 31 22:12:52 PDT 2020;
    #   root:xnu-6153.141.2~1/RELEASE_X86_64'
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


def _get_macos_tag(version: str) -> str:
    """
    Get the macOS version tag based on the version name.

    :param version: macOS version name (e.g. "Catalina", "Monterey",
        "Ventura")
    :return: Version tag string
    """
    if version == "Catalina":
        # Darwin gpmac.fios-router.home 19.6.0 Darwin Kernel Version 19.6.0:
        # Mon Aug 31 22:12:52 PDT 2020; root:xnu-6153.141.2~1/RELEASE_X86_64 x86_64
        macos_tag = "19.6"
    elif version == "Monterey":
        # Darwin alpha.local 21.5.0 Darwin Kernel Version 21.5.0:
        # Tue Apr 26 21:08:37 PDT 2022;
        #   root:xnu-8020.121.3~4/RELEASE_ARM64_T6000 arm64```
        macos_tag = "21."
    elif version == "Ventura":
        # Darwin alpha.local 21.5.0 Darwin Kernel Version 21.5.0:
        # Tue Apr 26 21:08:37 PDT 2022;
        #   root:xnu-8020.121.3~4/RELEASE_ARM64_T6000 arm64```
        macos_tag = "22."
    else:
        raise ValueError(f"Invalid version='{version}'")
    _LOG.debug("macos_tag=%s", macos_tag)
    return macos_tag


def is_mac(*, version: Optional[str] = None) -> bool:
    """
    Return whether we are running on macOS and, optionally, on a specific
    version.

    :param version: check whether we are running on a certain macOS version (e.g.,
        `Catalina`, `Monterey`)
    """
    if is_inside_docker():
        return False
    _LOG.debug("version=%s", version)
    #
    host_os_name = os.uname()[0]
    _LOG.debug("host_os_name=%s", host_os_name)
    #
    is_mac_ = host_os_name == "Darwin"
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
    macos_tag = _get_macos_tag(version)
    host_os_version = os.uname()[2]
    _LOG.debug("host_os_version=%s", host_os_version)
    is_mac_ = macos_tag in host_os_version
    _LOG.debug("  -> is_mac_=%s", is_mac_)
    return is_mac_


def is_host_mac(*, version: Optional[str] = None) -> bool:
    """
    Return whether the host on which we are running a container is macOS.

    :param version: check whether we are running on a certain macOS version (e.g.,
        `Catalina`, `Monterey`)
    """
    assert (
        is_inside_docker()
    ), "You can call `is_host_mac()` only from inside a container"
    _LOG.debug("version=%s", version)
    #
    csfy_host_os_name = os.environ.get("CSFY_HOST_OS_NAME", None)
    _LOG.debug("csfy_host_os_name=%s", csfy_host_os_name)
    #
    is_mac_ = csfy_host_os_name == "Darwin"
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
    macos_tag = _get_macos_tag(version)
    # 'Darwin Kernel Version 19.6.0: Mon Aug 31 22:12:52 PDT 2020;
    #   root:xnu-6153.141.2~1/RELEASE_X86_64'
    csfy_host_os_version = os.environ.get("CSFY_HOST_VERSION", "")
    _LOG.debug(
        "csfy_host_os_version=%s",
        csfy_host_os_version,
    )
    is_mac_ = macos_tag in csfy_host_os_version
    _LOG.debug("  -> is_mac_=%s", is_mac_)
    return is_mac_


# TODO(gp): -> is_not_dev_csfy_linux: are we running on a host which is not a
# Causify machine?
def is_external_linux() -> bool:
    """
    Detect whether we are running on a non-server/non-CI Linux machine.

    This is true when we run on the machine of an intern, a student, or
    a non-CSFY contributor.
    """
    if is_dev_csfy() or is_inside_ci():
        # CI and dev servers are not considered external Linux systems.
        res = False
    elif is_inside_docker():
        # If we are inside a Docker container, we need to check the host OS.
        csfy_host_os_name = os.environ.get("CSFY_HOST_OS_NAME", None)
        res = csfy_host_os_name == "Linux"
    else:
        # If we are not inside a Docker container, we can check the host OS
        # directly.
        host_os_name = os.uname()[0]
        res = host_os_name == "Linux"
    _LOG.debug("  -> is_external_linux=%s", res)
    return res


def is_csfy_or_external_container() -> bool:
    """
    Detect whether we are running on a container in a CSFY or external system.

    This is true for dockerized executables.
    """
    res = False
    if is_inside_ci():
        # CI servers are not considered external or CSFY systems.
        res = False
    elif not is_inside_docker():
        # Outside Docker there is no container.
        res = False
    else:
        res = is_inside_docker()
    _LOG.debug("  -> is_csfy_or_external_container=%s", res)
    return res


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

    When deploying jobs via ECS the container obtains credentials based
    on passed task role specified in the ECS task-definition, refer to:
    https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html.
    """
    ret = "AWS_CONTAINER_CREDENTIALS_RELATIVE_URI" in os.environ
    return ret


# #############################################################################


def _get_setup_signature() -> str:
    """
    Dump all the variables that are used to make a decision about the values of
    the functions in `_get_setup_settings()`.
    """
    cmds = []
    # is_prod_csfy()
    cmds = 'os.environ.get("CK_IN_PROD_CMAMP_CONTAINER", "undef")'
    # is_dev4()
    # is_dev_ck()
    # is_ig_prod()
    cmds.append('os.environ.get("CSFY_HOST_NAME", "undef")')
    # is_inside_ci()
    cmds.append('os.environ.get("CSFY_CI", "undef")')
    # is_mac()
    cmds.append("os.uname()[0]")
    cmds.append("os.uname()[2]")
    # is_external_linux()
    cmds.append('os.environ.get("CSFY_HOST_OS_NAME", "undef")')
    # is_csfy_or_external_container()
    # Build an array of strings with the results of executing the commands.
    results = []
    for cmd in cmds:
        result_tmp = cmd + "=" + str(eval(cmd))
        results.append(result_tmp)
    # Join the results into a single string.
    result = "\n".join(results)
    return result


def _get_setup_settings() -> List[Tuple[str, bool]]:
    # Store name-value pairs as tuples.
    setups = [
        ("is_prod_csfy", is_prod_csfy()),
        ("is_dev4", is_dev4()),
        ("is_dev_ck", is_dev_ck()),
        ("is_ig_prod", is_ig_prod()),
        ("is_inside_ci", is_inside_ci()),
        ("is_mac", is_mac()),
        ("is_external_linux", is_external_linux()),
        ("is_csfy_or_external_container", is_csfy_or_external_container()),
    ]
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
    Check that one and only one server config is true.
    """
    setups = _get_setup_settings()
    # One and only one set-up should be true.
    sum_ = sum([value for _, value in setups])
    if sum_ != 1:
        msg = "One and only one set-up config should be true:\n" + _setup_to_str(
            setups
        )
        msg += "_get_setup_signature() returns:\n" + _get_setup_signature()
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
# Docker
# #############################################################################


# TODO(gp): -> has_docker_privileged_mode
@functools.lru_cache()
def has_dind_support() -> bool:
    """
    Return whether the current container supports privileged mode.

    This is need to use Docker-in-Docker.
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
        elif is_mac(version="Catalina"):
            # Docker for macOS Catalina supports dind.
            ret = True
        elif is_mac(version="Monterey") or is_mac(version="Ventura"):
            # Docker for macOS Monterey doesn't seem to support dind.
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
    elif is_inside_ci():
        ret = False
    elif is_mac():
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
    return is_mac(version="Monterey") or is_mac(version="Ventura")


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
    elif is_mac() or is_inside_ci() or is_prod_csfy():
        shared_data_dirs = None
    else:
        shared_data_dirs = None
        only_warning = True
        _raise_invalid_host(only_warning)
    return shared_data_dirs


def use_docker_network_mode_host() -> bool:
    # TODO(gp): Not sure this is needed any more, since we typically run in
    # bridge mode.
    ret = is_mac() or is_dev_csfy()
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
    elif is_inside_ci():
        # When running as user in GH action we get an error:
        # ```
        # /home/.config/gh/config.yml: permission denied
        # ```
        # see https://github.com/alphamatic/amp/issues/1864
        # So we run as root in GH actions.
        ret = True
    elif is_mac():
        ret = False
    elif is_prod_csfy():
        ret = False
    else:
        ret = False
        only_warning = True
        _raise_invalid_host(only_warning)
    return ret


def get_docker_user() -> str:
    """
    Return the user that runs Docker, if any.
    """
    if is_dev4():
        val = "spm-sasm"
    else:
        val = ""
    return val


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


# TODO(gp): Remove this comment.
# # This function can't be in `helpers.hserver` since it creates circular import
# # and `helpers.hserver` should not depend on anything.
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
# S3 buckets.
# #############################################################################


def is_AM_S3_available() -> bool:
    # AM bucket is always available.
    val = True
    _LOG.debug("val=%s", val)
    return val


def get_host_user_name() -> Optional[str]:
    return os.environ.get("CSFY_HOST_USER_NAME", None)


# #############################################################################
# Functions.
# #############################################################################


# Copied from hprint to avoid import cycles.


def indent(txt: str, *, num_spaces: int = 2) -> str:
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


# grep "def " helpers/hserver.py | sort
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
        "is_csfy_or_external_container",
        "is_dev4",
        "is_dev_ck",
        "is_external_linux",
        "is_host_mac",
        "is_ig_prod",
        "is_inside_ci",
        "is_inside_docker",
        "is_inside_ecs_container",
        "is_inside_unit_test",
        "is_mac",
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
            func_value = eval(func_name + "()")
        except NameError:
            func_value = "*undef*"
        msg = f"{func_name}='{func_value}'"
        ret.append(msg)
    # Package.
    ret: str = "# hserver.config\n" + indent("\n".join(ret))
    return ret
