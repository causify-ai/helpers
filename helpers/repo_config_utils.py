"""
Import as:

import helpers.repo_config_utils as hrecouti
"""

import logging
import os
from typing import Any, Dict, List, Optional, Union

import yaml

_LOG = logging.getLogger(__name__)

# #############################################################################

# Copied from hprint to avoid import cycles.


# TODO(gp): It should use *.
def indent(txt: str, num_spaces: int = 2) -> str:
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


def _find_config_file(file_name: str) -> str:
    """
    Find recursively the dir of config file.

    This function traverses the directory hierarchy upward from a
    specified starting path to find the directory that contains the
    config file.

    :param file_name: name of the file to find
    :return: path to the file
    """
    curr_dir = os.getcwd()
    while True:
        path = os.path.join(curr_dir, file_name)
        if os.path.exists(path):
            break
        parent = os.path.dirname(curr_dir)
        if parent == curr_dir:
            # We cannot use helpers since it creates circular import.
            raise FileNotFoundError(
                "Could not find '%s' in current directory or any parent directories"
                % file_name
            )
        curr_dir = parent
    return path


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


# #############################################################################
# RepoConfig
# #############################################################################


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
                assert isinstance(data, dict), (
                    "data=\n%s\nis not a dict but %s",
                    str(data),
                    type(data),
                )
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
        repo_name = self._data["repo_info"]["repo_name"]
        github_repo_account = self._data["repo_info"]["github_repo_account"]
        repo_map = {repo_name: f"{github_repo_account}/{repo_name}"}
        return repo_map

    def get_extra_amp_repo_sym_name(self) -> str:
        github_repo_account = self._data["repo_info"]["github_repo_account"]
        repo_name = self._data["repo_info"]["repo_name"]
        if repo_name in ["orange", "lemonade"]:
            # TODO(Grisha): it should return cmamp name, not the current
            return f"{github_repo_account}/cmamp"
        else:
            return f"{github_repo_account}/{repo_name}"

    # TODO(gp): -> get_github_host_name
    def get_host_name(self) -> str:
        value = self._data["repo_info"]["github_host_name"]
        return value

    def get_invalid_words(self) -> List[str]:
        values = self._data["repo_info"]["invalid_words"]
        if values is None:
            invalid_words = []
        else:
            invalid_words = values.split(",")
        return invalid_words

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

    def get_html_bucket_path_v2(self) -> str:
        """
        Return the path to the bucket with published HTMLs.

        "v2" version allows for the published HTMLs to be browsed.
        """
        html_bucket = self.get_html_bucket_path()
        html_bucket_path = os.path.join(html_bucket, "v2")
        return html_bucket_path

    def get_html_ip(self) -> str:
        """
        Return the IP of the bucket where published HTMLs are stored.
        """
        value = self._data["s3_bucket_info"]["html_ip"]
        return value

    def get_html_ip_v2(self) -> str:
        """
        Return the IP of the bucket with published HTMLs.

        "v2" version allows for the published HTMLs to be browsed.
        """
        ip = self.get_html_ip()
        ip_v2 = f"{ip}/v2"
        return ip_v2

    def get_html_dir_to_url_mapping(self) -> Dict[str, str]:
        """
        Return a mapping between directories mapped on URLs.

        This is used when we have web servers serving files from
        specific directories.
        """
        dir_to_url = {
            self.get_html_bucket_path(): self.get_html_ip(),
            self.get_html_bucket_path_v2(): self.get_html_ip_v2(),
        }
        return dir_to_url

    def config_func_to_str(self) -> str:
        """
        Return the string representation of the config function.
        """
        ret: List[str] = []
        ret.append(f"get_host_name='{self.get_host_name()}'")
        ret.append(
            f"get_html_dir_to_url_mapping='{self.get_html_dir_to_url_mapping()}'"
        )
        ret.append(f"get_invalid_words='{self.get_invalid_words()}'")
        ret.append(
            f"get_docker_base_image_name='{self.get_docker_base_image_name()}'"
        )
        return "# repo_config.config\n" + indent("\n".join(ret))

    @staticmethod
    def _get_repo_config_file() -> str:
        """
        Return the absolute path to `repo_config.yml` that should be used.

        The `repo_config.yml` is determined based on an overriding env var or
        based on the root of the Git path.
        """
        env_var = "CSFY_REPO_CONFIG_PATH"
        file_path = _get_env_var(env_var, abort_on_missing=False)
        if file_path:
            _LOG.warning(
                "Using value '%s' for %s from env var", file_path, env_var
            )
        else:
            # client_root = _find_git_root()
            # We cannot use git root here because the config file doesn't always
            # reside in the root of the repo (e.g., it can be in subdir such as
            # //cmamp/ck.infra for runnable dir).
            file_path = _find_config_file("repo_config.yaml")
            file_path = os.path.abspath(file_path)
            _LOG.debug("Reading file_name='%s'", file_path)
        # Check if path exists.
        # We can't use helpers since it creates circular import.
        if not os.path.exists(file_path):
            raise FileNotFoundError("File '%s' doesn't exist" % file_path)
        return file_path


_repo_config = None


def get_repo_config() -> RepoConfig:
    """
    Return the repo config object.
    """
    global _repo_config
    if _repo_config is None:
        _repo_config = RepoConfig.from_file()
    return _repo_config
