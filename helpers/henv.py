"""
Import as:

import helpers.henv as henv
"""

import logging
import os
import re
from typing import Any, Dict, List, Tuple, Union

import helpers.hdbg as hdbg
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem
import helpers.hversion as hversio
import helpers.repo_config_utils as hrecouti

# This module can depend only on:
# - Python standard modules
# - a few helpers as described in `helpers/dependencies.txt`


_LOG = logging.getLogger(__name__)


# #############################################################################


_WARNING = "\033[33mWARNING\033[0m"


# TODO(gp): Is this the right place for this function?
def has_module(module: str) -> bool:
    """
    Return whether a Python module can be imported or not.
    """
    if module == "gluonts" and hserver.is_mac():
        # Gluonts and mxnet modules are not properly supported on the ARM
        # architecture yet, see CmTask4886 for details.
        return False
    code = f"""
    try:
        import {module}
        has_module_ = True
    except ImportError as e:
        _LOG.warning("%s: %s", _WARNING, str(e))
        has_module_ = False
    """
    code = hprint.dedent(code)
    # To make the linter happy.
    has_module_ = True
    locals_: Dict[str, Any] = {}
    # Need to explicitly declare and pass `locals_`:
    # https://docs.python.org/3/library/functions.html#exec
    # `Pass an explicit locals dictionary if you need to see effects
    # of the code on locals after function exec() returns.`
    exec(code, globals(), locals_)
    has_module_ = locals_["has_module_"]
    return has_module_


# #############################################################################
# Utility functions.
# #############################################################################


# All printing functions should:
# - Return a string and not a list of strings
# - Add a newline at the end of the string (i.e., the string should end with
#   `\n`)


def _dassert_one_trailing_newline(txt: str) -> None:
    num_newlines = len(re.search(r'\n*$', txt).group())
    hdbg.dassert_eq(num_newlines, 0, "num_newlines='%s' txt='%s'", num_newlines, txt)


def _to_info(tag: str, txt: Union[str, List[str]]) -> str:
    hdbg.dassert_isinstance(tag, str)
    hdbg.dassert_isinstance(txt, (str, list))
    txt_tmp = ""
    txt_tmp += "# " + tag + "\n"
    # Indent the text.
    if not isinstance(txt, str):
        for t in txt:
            hdbg.dassert_isinstance(t, str)
        txt = "\n".join(txt)
    txt_tmp += hprint.indent(txt)
    # Ensure that there is a single trailing newline.
    txt_tmp = txt_tmp.rstrip("\n")
    # txt_tmp += "\n"
    # _dassert_one_trailing_newline(txt_tmp)
    _LOG.debug("'%s'", txt_tmp)
    return txt_tmp


# #############################################################################
# Print the env vars.
# #############################################################################


def get_env_var(
    env_name: str,
    *,
    as_bool: bool = False,
    default_value: Any = None,
    abort_on_missing: bool = True,
) -> Union[str, bool]:
    """
    Get an environment variable by name.

    :param env_name: name of the env var
    :param as_bool: convert the value into a Boolean
    :param default_value: the default value to use in case it's not
        defined
    :param abort_on_missing: if the env var is not defined aborts,
        otherwise use the default value
    :return: value of env var
    """
    if env_name not in os.environ:
        if abort_on_missing:
            hdbg.dassert_in(env_name, os.environ, f"Can't find env var '{env_name}' in '{str(os.environ)}'")
        else:
            return default_value
    value = os.environ[env_name]
    if as_bool:
        # Convert the value into a boolean.
        if value in ("0", "", "None", "False"):
            value = False
        else:
            value = True
    return value


# TODO(gp): Extract all the env vars that start with AM_, CK_, CSFY_ and make
# sure they have a description here.
def get_env_vars() -> List[str]:
    """
    Return all the env vars that are expected to be set in Docker.
    """
    # Keep in sync with `lib_tasks.py:_generate_compose_file()`.
    env_var_names = [
        # Force enabling Docker-in-Docker.
        "CSFY_ENABLE_DIND",
        # Enable forcing certain unit tests to fail to check that unit test
        # failures are caught.
        "CSFY_FORCE_TEST_FAIL",
        # The name of the host running Docker.
        "CSFY_HOST_NAME",
        # The OS of the host running Docker.
        "CSFY_HOST_OS_NAME",
        # The name of the user running the host.
        "CSFY_HOST_USER_NAME",
        # The version of the host running Docker.
        "CSFY_HOST_VERSION",
        # Whether to check if certain property of the repo are as expected or not.
        "CSFY_REPO_CONFIG_CHECK",
        # Path to use for `repo_config.py`. E.g., used when running `helpers`
        # container to avoid using the `repo_config.py` corresponding to the
        # container launching the linter.
        "CSFY_REPO_CONFIG_PATH",
        "GH_ACTION_ACCESS_TOKEN",
        # Whether we are running inside GH Actions.
        "CSFY_CI",
        # TODO(gp): Difference between amp and cmamp.
        # CK AWS credentials.
        "CSFY_AWS_ACCESS_KEY_ID",
        "CSFY_AWS_DEFAULT_REGION",
        "CSFY_AWS_SECRET_ACCESS_KEY",
        "CSFY_AWS_SESSION_TOKEN",
        # S3 bucket to use for CK.
        "CSFY_AWS_S3_BUCKET",
        # Path to the ECR for the Docker images for CK.
        "CSFY_ECR_BASE_PATH",
    ]
    # No duplicates.
    # TODO(gp): GFI. Use `hdbg.dassert_no_duplicates()` instead.
    hdbg.dassert_eq(len(set(env_var_names)),len(env_var_names), f"There are duplicates", str(env_var_names))
    # Sort.
    env_var_names = sorted(env_var_names)
    return env_var_names


def get_secret_env_vars() -> List[str]:
    """
    Return the list of env vars that are secrets.
    """
    secret_env_var_names = [
        # TODO(gp): Difference between amp and cmamp.
        "CSFY_AWS_ACCESS_KEY_ID",
        "CSFY_AWS_SECRET_ACCESS_KEY",
        "GH_ACTION_ACCESS_TOKEN",
    ]
    # No duplicates.
    # TODO(gp): GFI. Use `hdbg.dassert_no_duplicates()` instead.
    hdbg.dassert_eq(len(set(secret_env_var_names)), len(secret_env_var_names), f"There are duplicates", str(secret_env_var_names))
    # Secret env vars are a subset of the env vars.
    env_vars = get_env_vars()
    # TODO(gp): GFI. Use `hdbg.dassert_issubset()` instead.
    if not set(secret_env_var_names).issubset(set(env_vars)):
        diff = set(secret_env_var_names).difference(set(env_vars))
        cmd = f"Secret vars in `{str(diff)} are not in '{str(env_vars)}'"
        assert 0, cmd
    # Sort.
    secret_env_var_names = sorted(secret_env_var_names)
    return secret_env_var_names


def check_env_vars() -> None:
    """
    Make sure all the expected env vars are defined.
    """
    env_vars = get_env_vars()
    for env_var in env_vars:
        # TODO(gp): GFI. Use %s instead of str().
        hdbg.dassert_in(env_var, os.environ, f"env_var='{str(env_var)}' is not in env_vars='{str(os.environ.keys())}''")


def env_vars_to_string() -> str:
    """
    Return a string with the signature of all the expected env vars (including
    the secret ones).
    """
    msg = []
    # Get the expected env vars and the secret ones.
    env_vars = get_env_vars()
    secret_env_vars = get_secret_env_vars()
    # Print a signature.
    for env_name in env_vars:
        is_defined = env_name in os.environ
        is_empty = is_defined and os.environ[env_name] == ""
        if not is_defined:
            msg.append(f"{env_name}=undef")
        else:
            if env_name in secret_env_vars:
                # Secret env var: print if it's empty or not.
                if is_empty:
                    msg.append(f"{env_name}=empty")
                else:
                    msg.append(f"{env_name}=***")
            else:
                # Not a secret var: print the value.
                msg.append(f"{env_name}='{os.environ[env_name]}'")
    msg = "\n".join(msg)
    return msg


# #############################################################################
# Print the library versions.
# #############################################################################


def _get_library_version(lib_name: str) -> str:
    try:
        cmd = f"import {lib_name}"
        # pylint: disable=exec-used
        exec(cmd)
    except ImportError:
        version = "?"
    else:
        cmd = f"{lib_name}.__version__"
        version = eval(cmd)
    return version


# Copied from helpers.hgit to avoid circular dependencies.


def _git_log(num_commits: int = 5, my_commits: bool = False) -> str:
    """
    Return the output of a pimped version of git log.

    :param num_commits: number of commits to report
    :param my_commits: True to report only the current user commits
    :return: string
    """
    cmd = []
    cmd.append("git log --date=local --oneline --graph --date-order --decorate")
    cmd.append(
        "--pretty=format:" "'%h %<(8)%aN%  %<(65)%s (%>(14)%ar) %ad %<(10)%d'"
    )
    cmd.append(f"-{num_commits}")
    if my_commits:
        # This doesn't work in a container if the user relies on `~/.gitconfig` to
        # set the user name.
        # TODO(gp): We should use `get_git_name()`.
        cmd.append("--author $(git config user.name)")
    cmd = " ".join(cmd)
    data: Tuple[int, str] = hsystem.system_to_string(cmd)
    _, txt = data
    return txt


# End copy.


def _get_git_signature(git_commit_type: str = "all") -> str:
    """
    Get information about current branch and latest commits.
    """
    txt_tmp: List[str] = []
    # Get the branch name.
    cmd = "git branch --show-current"
    _, branch_name = hsystem.system_to_one_line(cmd)
    txt_tmp.append(f"branch_name='{branch_name}'")
    # Get the short Git hash of the current branch.
    cmd = "git rev-parse --short HEAD"
    _, hash_ = hsystem.system_to_one_line(cmd)
    txt_tmp.append(f"hash='{hash_}'")
    # Add info about the latest commits.
    num_commits = 3
    if git_commit_type == "all":
        txt_tmp.append("# Last commits:")
        log_txt = _git_log(num_commits=num_commits, my_commits=False)
        txt_tmp.append(hprint.indent(log_txt))
    elif git_commit_type == "mine":
        txt_tmp.append("# Your last commits:")
        log_txt = _git_log(num_commits=num_commits, my_commits=True)
        txt_tmp.append(hprint.indent(log_txt))
    elif git_commit_type == "none":
        pass
    else:
        raise ValueError(f"Invalid value='{git_commit_type}'")
    #
    txt_tmp = "\n".join(txt_tmp) + "\n"
    hdbg.dassert(txt_tmp.endswith("\n"), f"txt_tmp='%s'", txt_tmp)
    return txt_tmp


# def _get_submodule_signature(
#     partial_signature: List[str], *, git_commit_type: str = "all"
# ) -> str:
#     """
#     Add git signature for all submodules.

#     :paramp partial_signature: the signature to append to
#         :git_commit_type: the type of git commit to include in the
#         signature
#     :return: system signature enhanced by git submodule info
#     """
#     # TODO(Juraj): Think of a better generalisation rather listing all the options.
#     submodule_options = ["amp", "amp/helpers_root", "helpers_root"]
#     signature = partial_signature
#     prev_cwd = os.getcwd()
#     for submodule in submodule_options:
#         if os.path.exists(submodule):
#             try:
#                 # Temporarily descend into submodule.
#                 os.chdir(submodule)
#                 signature.append(f"# Git {submodule}")
#                 git_amp_sig = _get_git_signature(git_commit_type)
#                 signature = _append(signature, git_amp_sig)
#             # In case there is a runtime error we want to end up in a consistent
#             # state (the original path).
#             finally:
#                 os.chdir(prev_cwd)
#     hdbg.dassert(txt_tmp.endswith("\n"), f"txt_tmp='%s'", txt_tmp)
#     return signature

# #############################################################################
# Print the system info.
# #############################################################################


def _get_platform_info() -> str:
    """
    Get platform information as a list of strings.
    """
    import platform
    txt_tmp: List[str] = []
    uname = platform.uname()
    txt_tmp.append(f"system={uname.system}")
    txt_tmp.append(f"node name={uname.node}")
    txt_tmp.append(f"release={uname.release}")
    txt_tmp.append(f"version={uname.version}")
    txt_tmp.append(f"machine={uname.machine}")
    txt_tmp.append(f"processor={uname.processor}")
    #
    txt = _to_info("Platform info", txt_tmp)
    return txt
    

def _get_psutil_info() -> str:
    """
    Get system resource information using psutil.
    """
    try:
        import psutil
        has_psutil = True
    except ModuleNotFoundError as e:
        _LOG.warning("psutil is not installed: %s", str(e))
        has_psutil = False
    
    txt_tmp = []
    if has_psutil:
        txt_tmp.append(f"cpu count={psutil.cpu_count()}")
        txt_tmp.append(f"cpu freq={str(psutil.cpu_freq())}")
        # TODO(gp): Report in MB or GB.
        txt_tmp.append(f"memory={str(psutil.virtual_memory())}")
        txt_tmp.append(f"disk usage={str(psutil.disk_usage('/'))}")
    txt = _to_info("Psutils info", txt_tmp)
    return txt


# #############################################################################
# Print the package info.
# #############################################################################


def _get_package_info() -> Tuple[List[str], int]:
    """Get package version information.
    
    Returns:
        Tuple containing:
        - List of strings with package info
        - Number of failed imports
    """
    import platform

    txt_tmp = []
    packages = []
    packages.append(("python", platform.python_version()))
    # import sys
    # print(sys.version)
    libs = [
        "cvxopt",
        "cvxpy", 
        "gluonnlp",
        "gluonts",
        "joblib",
        "mxnet",
        "numpy",
        "pandas",
        "pyarrow",
        "scipy",
        "seaborn",
        "sklearn",
        "statsmodels",
    ]
    libs = sorted(libs)
    failed_imports = 0
    for lib in libs:
        # This is due to Cmamp4924:
        # WARNING: libarmpl_lp64_mp.so: cannot open shared object file: No such
        #  file or directory
        try:
            version = _get_library_version(lib)
        except OSError as e:
            print(_WARNING + ": " + str(e))
        if version.startswith("ERROR"):
            failed_imports += 1
        packages.append((lib, version))
    txt_tmp.extend([f"{l}: {v}" for (l, v) in packages])
    #
    txt = _to_info("Packages", txt_tmp)
    return txt, failed_imports


# #############################################################################
# Get container info.
# #############################################################################

    
def _get_container_version() -> str:
    txt_tmp: List[str] = []
    #
    container_version = str(hversio.get_container_version())
    txt_tmp.append(f"container_version='{container_version}'")
    #
    container_dir_name = "."
    changelog_version = str(hversio.get_changelog_version(container_dir_name))
    txt_tmp.append(f"changelog_version='{changelog_version}'")
    #
    txt_tmp = _to_info("Container version", txt_tmp)
    return txt_tmp


# #############################################################################
# Get the system signature.
# #############################################################################


def _get_git_info(git_commit_type: str) -> str:
    txt_tmp: List[str] = []
    try:
        txt_tmp.append(_get_git_signature(git_commit_type))
        # If there are any submodules, fetch their git signature.
        # txt_tmp.append(_get_submodule_signature(txt_tmp, git_commit_type))
    except RuntimeError as e:
        _LOG.error(str(e))
    txt = _to_info("Git info", txt_tmp)
    return txt


def _get_docker_info() -> str:
    txt_tmp: List[str] = []
    has_docker = hserver.has_docker()
    txt_tmp.append(f"docker installed={has_docker}")
    rc, docker_version = hsystem.system_to_string(r"docker version --format '{{.Server.Version}}'")
    txt_tmp.append(f"docker_version='{docker_version}'")
    return txt_tmp


def get_system_signature(git_commit_type: str = "all") -> Tuple[str, int]:
    """
    Return a string with the system signature.

    :param git_commit_type: the type of git commit to include in the
        signature
    :return: the system signature and the number of failed imports
    """
    txt: List[str] = []
    # Add container version.
    txt_tmp = _get_container_version()
    _dassert_one_trailing_newline(txt_tmp)
    txt.append(txt_tmp)
    # Add git signature.
    txt_tmp = _get_git_info(git_commit_type)
    _dassert_one_trailing_newline(txt_tmp)
    txt.append(txt_tmp)
    # Add platform info.
    txt_tmp = _get_platform_info()
    _dassert_one_trailing_newline(txt_tmp)
    txt.append(txt_tmp)
    # Add psutil info.
    txt_tmp = _get_psutil_info()
    _dassert_one_trailing_newline(txt_tmp)
    txt.append(txt_tmp)
    # Add package info.
    txt_tmp, failed_imports = _get_package_info()
    _dassert_one_trailing_newline(txt_tmp)
    txt.append(txt_tmp)
    #
    txt = _to_info("System signature", txt)
    return txt, failed_imports


# #############################################################################
# Package all the information into a string.
# #############################################################################


def env_to_str(
    repo_config: bool = True,
    server_config: bool = True,
    system_signature: bool = True,
    env_vars: bool = True) -> str:
    """
    Package all the information into a string.
    """
    #
    msg = ""
    #
    if repo_config:
        repo_config_str = hrecouti.get_repo_config().config_func_to_str()
        msg += _to_info("Repo config", repo_config_str) + "\n"
    #
    if server_config:
        server_config_str = hserver.config_func_to_str()
        msg += _to_info("Server config", server_config_str) + "\n"
    #
    if system_signature:
        msg += get_system_signature()[0] + "\n"
    #
    if env_vars:
        env_vars_str = env_vars_to_string()
        msg += _to_info("Env vars", env_vars_str) + "\n"
    return msg
