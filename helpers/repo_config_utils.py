"""
Import as:

import helpers.repo_config_utils as hrecouti
"""

import functools
import logging
import os
import yaml
from typing import Any, Dict, List, Optional, Union

_LOG = logging.getLogger(__name__)


# ######


def _get_env_var(
        env_name: str,
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
            assert 0, f"Can't find env var '{env_name}' in '{str(os.environ)}'"
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


def _find_git_root(path: str = ".") -> str:
    """
    Find the dir of the outermost Git super module.

    This function looks for `.git` dirs in the path and its parents until it
    finds one. This is a different approach than asking Git directly.
    Pros:
    - it doesn't require to call `git` through a system call.
    Cons:
    - it relies on `git` internal structure, which might change in the future.
    """
    path = os.path.abspath(path)
    while not os.path.isdir(os.path.join(path, ".git")):
        git_dir_file = os.path.join(path, ".git")
        if os.path.isfile(git_dir_file):
            with open(git_dir_file, "r") as f:
                for line in f:
                    if line.startswith("gitdir:"):
                        git_dir = line.split(":", 1)[1].strip()
                        return os.path.abspath(
                            os.path.join(path, git_dir, "..", "..")
                        )
        parent = os.path.dirname(path)
        assert parent != path, f"Can't find the Git root starting from {path}"
        path = parent
    return path


# End copy


class RepoConfig:

    def __init__(self, data: Dict) -> None:
        """
        Set the data to be used by the module.
        """
        self._data = data

    def set_repo_config_data(self, data: Dict) -> None:
        self._data = data

    @classmethod
    def from_file(cls, file_name: Optional[str] = None) -> "RepoConfig":
        """
        Return the text of the code stored in `repo_config.py`.
        """
        if file_name is None:
            file_name = RepoConfig._get_repo_config_file()
        assert os.path.exists(file_name), f"File '{file_name}' doesn't exist"
        _LOG.debug("Reading file_name='%s'", file_name)
        try:
            with open(file_name, "r") as file:
                # Use `safe_load()` to avoid executing arbitrary code.
                data = yaml.safe_load(file)
                assert isinstance(data, dict), ("data=\n%s\nis not a dict but %s",
                       str(data), type(data))
        except Exception as e:
            raise f"Error reading YAML file {file_name}: {e}"
        return cls(data)

    # TODO(gp): -> get_repo_name
    def get_name(self) -> str:
        value = self._data["repo_info"]["repo_name"]
        return f"//{value}"

    def get_github_repo_account(self) -> str:
        value = self._data["repo_info"]["github_repo_account"]
        return value

    def get_repo_map(self) -> Dict[str, str]:
        """
        Return a mapping of short repo name -> long repo name.
        """
        repo_name = self.get_name()
        github_repo_account = self.get_github_repo_account()
        repo_map = {repo_name: f"{github_repo_account}/{repo_name}"}
        return repo_map

    # def get_extra_amp_repo_sym_name() -> str:
    #     return f"{_GITHUB_REPO_ACCOUNT}/{_REPO_NAME}"

    # TODO(gp): -> get_github_host_name
    def get_host_name(self) -> str:
        value = self._data["repo_info"]["github_host_name"]
        return value

    def get_invalid_words(self) -> List[str]:
        return []

    def get_docker_base_image_name(self) -> str:
        """
        Return a base name for docker image.
        """
        value = self._data["docker_info"]["docker_image_name"]
        return value

    def get_unit_test_bucket_path(self) -> str:
        """
        Return the path to the unit test bucket.
        """
        value = self._data["s3_bucket_info"]["unit_test_bucket_name"]
        return value

    def get_html_bucket_path(self) -> str:
        """
        Return the path to the bucket where published HTMLs are stored.
        """
        value = self._data["s3_bucket_info"]["html_bucket_name"]
        return value

    def get_html_ip(self) -> str:
        """
        Return the IP of the bucket where published HTMLs are stored.
        """
        value = self.data["s3_bucket_info"]["html_bucket_name"]
        return value

    def get_html_dir_to_url_mapping(self) -> Dict[str, str]:
        """
        Return a mapping between directories mapped on URLs.

        This is used when we have web servers serving files from specific
        directories.
        """
        dir_to_url = {self.get_html_bucket_path(): self.get_html_ip()}
        return dir_to_url

    @staticmethod
    def _get_repo_config_file() -> str:
        """
        Return the absolute path to `repo_config.py` that should be used.

        The `repo_config.py` is determined based on an overriding env var or
        based on the root of the Git path.
        """
        env_var = "AM_REPO_CONFIG_PATH"
        file_name = _get_env_var(env_var, abort_on_missing=False)
        if file_name:
            _LOG.warning("Using value '%s' for %s from env var", file_name, env_var)
        else:
            client_root = _find_git_root()
            _LOG.debug("Reading file_name='%s'", file_name)
            file_name = os.path.join(client_root, "repo_config.yaml")
            file_name = os.path.abspath(file_name)
        return file_name


_repo_config = None


def get_repo_config() -> RepoConfig:
    """
    Return the repo config object.
    """
    global _repo_config
    if _repo_config is None:
        _repo_config = RepoConfig.from_file()
    return _repo_config

# # #############################################################################
#
#
# def assert_setup(
#     self_: Any, exp_enable_privileged_mode: bool, exp_has_dind_support: bool
# ) -> None:
#     signature = henv.env_to_str(add_system_signature=False)
#     _LOG.debug("env_to_str=%s", signature)
#     #
#     act_enable_privileged_mode = henv.execute_repo_config_code(
#         "enable_privileged_mode()"
#     )
#     self_.assertEqual(act_enable_privileged_mode, exp_enable_privileged_mode)
#     #
#     act_has_dind_support = henv.execute_repo_config_code("has_dind_support()")
#     self_.assertEqual(act_has_dind_support, exp_has_dind_support)
#
#
# def _dassert_setup_consistency() -> None:
#     """
#     Check that one and only one set up config should be true.
#     """
#     # Use the settings from the `repo_config` corresponding to this container.
#     enable_privileged_mode = henv.execute_repo_config_code(
#         "enable_privileged_mode()"
#     )
#     use_docker_sibling_containers = henv.execute_repo_config_code(
#         "use_docker_sibling_containers()"
#     )
#     use_docker_network_mode_host = henv.execute_repo_config_code(
#         "use_docker_network_mode_host()"
#     )
#     use_main_network = henv.execute_repo_config_code("use_main_network()")
#     _LOG.debug(
#         hprint.to_str(
#             "enable_privileged_mode use_docker_sibling_containers "
#             "use_docker_network_mode_host use_main_network"
#         )
#     )
#     # It's not possible to have dind and sibling containers together.
#     hdbg.dassert(
#         not (use_docker_sibling_containers and enable_privileged_mode),
#         "use_docker_sibling_containers=%s enable_privileged_mode=%s",
#         use_docker_sibling_containers,
#         enable_privileged_mode,
#     )
#     # To run sibling containers they need to be in the same main network.
#     if use_docker_sibling_containers:
#         hdbg.dassert(use_main_network, "use_main_network=%s", use_main_network)
#     # It's not possible to have both host and main network (which implies
#     # bridge mode).
#     hdbg.dassert(
#         not (use_docker_network_mode_host and use_main_network),
#         "use_docker_network_mode_host=%s use_main_network=%s",
#         use_docker_network_mode_host,
#         use_main_network,
#     )
#
#
# # If the env var is not defined then we want to check. The only reason to skip
# # it's if the env var is defined and equal to False.
# check_repo = os.environ.get("AM_REPO_CONFIG_CHECK", "True") != "False"
# _is_called = False
# if check_repo:
#     if not _is_called:
#         _dassert_setup_consistency()
#         _is_called = True
# else:
#     _LOG.warning(f"Skipping repo check in {__file__}")
