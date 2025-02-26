"""
Import as:

import helpers.repo_config_utils as hrecouti
"""

import functools
import logging
import os
import yaml
from typing import Any, Dict, List, Optional, Union

import helpers.hio as hio
import helpers.hdbg as hdbg

_LOG = logging.getLogger(__name__)

# #############################################################################

# Copied from hgit to avoid import cycles.


def _find_git_root(path: str = ".") -> str:
    """
    Find recursively the dir of the outermost super module.

    This function traverses the directory hierarchy upward from a specified
    starting path to find the root directory of a Git repository.
    It supports:
    - standard git repository: where a `.git` directory exists at the root
    - submodule: where repository is nested inside another, and the `.git` file contains
      a `gitdir:` reference to the submodule's actual Git directory
    - linked repositories: where the `.git` file points to a custom Git directory
      location, such as in Git worktrees or relocated `.git` directories

    :param path: starting file system path. Defaults to the current directory (".")
    :return: absolute path to the top-level Git repository directory
    """
    path = os.path.abspath(path)
    git_root_dir = None
    while True:
        git_dir = os.path.join(path, ".git")
        _LOG.debug("git_dir=%s", git_dir)
        # Check if `.git` is a directory which indicates a standard Git repository.
        if os.path.isdir(git_dir):
            # Found the Git root directory.
            git_root_dir = path
            break
        # Check if `.git` is a file which indicates submodules or linked setups.
        if os.path.isfile(git_dir):
            txt = hio.from_file(git_dir)
            lines = txt.split("\n")
            for line in lines:
                # Look for a `gitdir:` line that specifies the linked directory.
                # Example: `gitdir: ../.git/modules/helpers_root`.
                if line.startswith("gitdir:"):
                    git_dir_path = line.split(":", 1)[1].strip()
                    _LOG.debug("git_dir_path=%s", git_dir_path)
                    # Resolve the relative path to the absolute path of the Git directory.
                    abs_git_dir = os.path.abspath(
                        os.path.join(path, git_dir_path)
                    )
                    # Traverse up to find the top-level `.git` directory.
                    while True:
                        # Check if the current directory is a `.git` directory.
                        if os.path.basename(abs_git_dir) == ".git":
                            git_root_dir = os.path.dirname(abs_git_dir)
                            # Found the root.
                            break
                        # Move one level up in the directory structure.
                        parent = os.path.dirname(abs_git_dir)
                        # Reached the filesystem root without finding the `.git` directory.
                        hdbg.dassert_ne(
                            parent,
                            abs_git_dir,
                            "Top-level .git directory not found.",
                        )
                        # Continue traversing up.
                        abs_git_dir = parent
                    break
        # Exit the loop if the Git root directory is found.
        if git_root_dir is not None:
            break
        # Move up one level in the directory hierarchy.
        parent = os.path.dirname(path)
        # Reached the filesystem root without finding `.git`.
        hdbg.dassert_ne(
            parent,
            path,
            "No .git directory or file found in any parent directory.",
        )
        # Update the path to the parent directory for the next iteration.
        path = parent
    return git_root_dir


# End copy.

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
        repo_name = self._data["repo_info"]["repo_name"]
        github_repo_account = self._data["repo_info"]["github_repo_account"]
        repo_map = {repo_name: f"{github_repo_account}/{repo_name}"}
        return repo_map

    def get_extra_amp_repo_sym_name(self) -> str:
        repo_name = self._data["repo_info"]["repo_name"]
        github_repo_account = self._data["repo_info"]["github_repo_account"]
        return f"{github_repo_account}/{repo_name}"

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
        value = self._data["s3_bucket_info"]["html_bucket_name"]
        return value

    def get_html_dir_to_url_mapping(self) -> Dict[str, str]:
        """
        Return a mapping between directories mapped on URLs.

        This is used when we have web servers serving files from specific
        directories.
        """
        dir_to_url = {self.get_html_bucket_path(): self.get_html_ip()}
        return dir_to_url

    def config_func_to_str(self) -> str:
        """
        return the string representation of the config function.
        """
        ret: List[str] = []
        ret.append(f"get_name='{self.get_name()}'")
        ret.append(f"get_github_repo_account='{self.get_github_repo_account()}'")
        ret.append(f"get_repo_map='{self.get_repo_map()}'")
        ret.append(f"get_extra_amp_repo_sym_name='{self.get_extra_amp_repo_sym_name()}'")
        ret.append(f"get_host_name='{self.get_host_name()}'")
        ret.append(f"get_invalid_words='{self.get_invalid_words()}'")
        ret.append(f"get_docker_base_image_name='{self.get_docker_base_image_name()}'")
        ret.append(f"get_unit_test_bucket_path='{self.get_unit_test_bucket_path()}'")
        ret.append(f"get_html_bucket_path='{self.get_html_bucket_path()}'")
        ret.append(f"get_html_ip='{self.get_html_ip()}'")
        ret.append(f"get_html_dir_to_url_mapping='{self.get_html_dir_to_url_mapping()}'")
        return "# repo_config.config\n" + indent("\n".join(ret))

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

