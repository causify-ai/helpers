"""
Import as:

import helpers.hgit as hgit
"""

import collections
import functools
import logging
import os
import random
import re
import string
from typing import List, Optional, Tuple

import helpers.hdbg as hdbg
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem
import helpers.repo_config_utils as hrecouti

# This module can depend only on:
# - Python standard modules
# - a few helpers as described in `helpers/dependencies.txt`


_LOG = logging.getLogger(__name__)

# We refer to "Git" when we talk about the control system (e.g., "in a Git
# repository") and `git` when we refer to implementation of Git as a program
# installed in a computer.

# TODO(gp): Check
#  https://git-scm.com/book/en/v2/Appendix-B%3A-Embedding-Git-in-your-Applications-Dulwich

# TODO(gp): Avoid "stuttering": the module is already called "git", so no need
#  to make reference to git again.

# TODO(gp): Add mem caching to some functions below. We assume that one doesn't
#  change dir (which is a horrible idea) and thus we can memoize.

# TODO(gp): Spell super_module and sub_module always in the same way in both
#  comments and code. For simplicity (e.g., instead of `super_module` in code and
#  `super-module` in comment) we might want to spell `supermodule` everywhere.

# #############################################################################
# Git branch functions
# #############################################################################


def extract_gh_issue_number_from_branch(branch_name: str) -> Optional[int]:
    """
    Extract the GitHub issue number from a branch name.

    Example:
    CmampTask10725_Add_more_tabs_to_orange_tmux -> 10725
    HelpersTask23_Add_more_tabs_to_orange_tmux -> 23.

    Works only if `invoke gh_branch_create` was used to create the branch.
    or the name was retrieved using `invoke gh_issue_title`.

    :param branch_name: the name of the branch
    :return: the issue number or None if it can't be extracted
    """
    match = re.match(r".*Task_?(\d+)(?:_\w+)?", branch_name)
    if match:
        # Return the captured number.
        return int(match.group(1))
    return None


@functools.lru_cache()
def get_branch_name(dir_name: str = ".") -> str:
    """
    Return the name of the Git branch including a certain dir.

    E.g., `master` or `AmpTask672_Add_script_to_check_and_merge_PR`
    """
    hdbg.dassert_path_exists(dir_name)
    # > git rev-parse --abbrev-ref HEAD
    # master
    cmd = f"cd {dir_name} && git rev-parse --abbrev-ref HEAD"
    data: Tuple[int, str] = hsystem.system_to_one_line(cmd)
    _, output = data
    return output


def get_branch_next_name(
    dir_name: str = ".",
    *,
    curr_branch_name: Optional[str] = None,
    log_verb: int = logging.DEBUG,
) -> str:
    """
    Return a name derived from the branch so that the branch doesn't exist.

    E.g., `AmpTask1903_Implemented_system_Portfolio` ->
    `AmpTask1903_Implemented_system_Portfolio_3`
    """
    if curr_branch_name is None:
        curr_branch_name = get_branch_name(dir_name=dir_name)
    hdbg.dassert_ne(curr_branch_name, "master")
    _LOG.log(log_verb, "curr_branch_name='%s'", curr_branch_name)
    #
    max_num_ids = 100
    for i in range(1, max_num_ids):
        new_branch_name = f"{curr_branch_name}_{i}"
        _LOG.info("Trying branch name '%s' ...", new_branch_name)
        mode = "all"
        exists = does_branch_exist(new_branch_name, mode, dir_name=dir_name)
        _LOG.log(log_verb, "-> exists=%s", exists)
        if not exists:
            _LOG.log(log_verb, "new_branch_name='%s'", new_branch_name)
            return new_branch_name
    raise ValueError(
        f"Can't find the next branch name for '{curr_branch_name}' within %s ids",
        max_num_ids,
    )


def get_branch_hash(dir_name: str = ".") -> str:
    """
    Return the hash of the commit right before the branch in `dir_name` was
    created.
    """
    curr_branch_name = get_branch_name(dir_name=dir_name)
    hdbg.dassert_ne(curr_branch_name, "master")
    _LOG.debug("curr_branch_name=%s", curr_branch_name)
    #
    cmd = f"cd {dir_name} && git merge-base master {curr_branch_name}"
    _, hash_ = hsystem.system_to_string(cmd)
    hash_ = hash_.rstrip("\n").lstrip("\n")
    hdbg.dassert_eq(len(hash_.split("\n")), 1)
    return hash_


# #############################################################################
# Git submodule functions
# #############################################################################


@functools.lru_cache()
def get_client_root(super_module: bool) -> str:
    """
    Return the full path of the root of the Git client.

    E.g., `/Users/saggese/src/.../amp`.

    :param super_module: if True use the root of the Git super_module,
        if we are in a submodule. Otherwise use the Git sub_module root
    """
    if super_module and is_inside_submodule():
        # https://stackoverflow.com/questions/957928
        # > cd /Users/saggese/src/.../amp
        # > git rev-parse --show-superproject-working-tree
        # /Users/saggese/src/...
        cmd = "git rev-parse --show-superproject-working-tree"
    else:
        # > git rev-parse --show-toplevel
        # /Users/saggese/src/.../amp
        cmd = "git rev-parse --show-toplevel"
    # TODO(gp): Use system_to_one_line().
    _, out = hsystem.system_to_string(cmd)
    out = out.rstrip("\n")
    hdbg.dassert_eq(len(out.split("\n")), 1, msg=f"Invalid out='{out}'")
    client_root: str = os.path.realpath(out)
    return client_root


# TODO(gp): Replace `get_client_root` with this.
# TODO(gp): -> get_client_root2() or get_outermost_supermodule_root()
def find_git_root(path: str = ".") -> str:
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
    import helpers.hio as hio

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


# #############################################################################


# TODO(gp): There are several functions doing the same work.
# helpers_root/helpers/hgit.py:827:def find_file_in_git_tree(
# helpers_root/helpers/hsystem.py:757:def find_file_in_repo(file_name: str, *, root_dir: Optional[str] = None) -> str:
def find_file(file_name: str, *, dir_path: Optional[str] = None) -> str:
    """
    Find the file under a directory.

    :param file_name: the name of the file to find
    :param dir_path: the directory to start the search from
    :return: the absolute path to the file
    """
    if dir_path is None:
        dir_path = find_git_root()
    _LOG.debug(hprint.to_str("dir_path"))
    cmd = (
        rf"find {dir_path} "
        + r"\( -path '*/.git' -o -path '*/.mypy_cache' \) -prune "
        + rf'-o -name "{file_name}" -print'
    )
    _LOG.debug(hprint.to_str("cmd"))
    _, res = hsystem.system_to_one_line(cmd)
    hdbg.dassert_ne(res, "Can't find file '%s' in '%s'", file_name, dir_path)
    return res


def find_helpers_root(dir_path: str = ".") -> str:
    """
    Find the root directory of the `helpers` repository.

    If the current directory is within the `helpers` repository, the root of the
    repository is returned. Otherwise, the function searches for the `helpers_root`
    directory starting from the root of the repository.

    :return: The absolute path to the `helpers_root` directory.
    """
    with hsystem.cd(dir_path):
        git_root = find_git_root()
        if is_helpers():
            # If we are in `//helpers`, then the helpers root is the root of the
            # repo.
            cmd = "git rev-parse --show-toplevel"
            _, helpers_root = hsystem.system_to_one_line(cmd)
        else:
            # We need to search for the `helpers_root` dir starting from the root
            # of the repo.
            helpers_root = find_file("helpers_root", dir_path=git_root)
        helpers_root = os.path.abspath(helpers_root)
        # Make sure the dir and that `helpers` subdir exists.
        hdbg.dassert_dir_exists(helpers_root)
        hdbg.dassert_dir_exists(os.path.join(helpers_root), "helpers")
    return helpers_root


# #############################################################################


def resolve_git_client_dir(git_client_name: str) -> str:
    """
    Resolve the absolute path of the Git client directory.

    :param git_client_name: the name of the Git client (e.g., "helpers1"
        or "/Users/saggese/src/helpers1")
    :return: the absolute path of the Git client directory
    """
    if not os.path.isabs(git_client_name):
        # If the Git client name is not absolute, assume it's in the home
        # directory (e.g., 'helpers1' -> '/Users/saggese/src/helpers1').
        git_client_dir = os.path.join(os.environ["HOME"], "src", git_client_name)
    else:
        # If the Git client name is absolute, use it as is.
        git_client_dir = git_client_name
    _LOG.debug(hprint.to_str("git_client_dir"))
    hdbg.dassert_dir_exists(git_client_dir)
    return git_client_dir


def project_file_name_in_git_client(
    file_name: str,
    git_src_dir: str,
    git_dst_dir: str,
    *,
    check_src_file_exists: bool = False,
    check_dst_file_exists: bool = False,
) -> str:
    """
    Find the file corresponding to `file_name` in `git_src_dir` for the client
    `git_dst_dir`.

    This is useful when we want to find the file in a destination Git client
    directory corresponding to a file in a source Git client directory.

    E.g., for:
    ```
    file_name = '/Users/saggese/src/helpers1/dev_scripts_helpers/system_tools/path.py'
    git_src_dir = '/Users/saggese/src/helpers1'
    git_dst_dir = '/Users/saggese/src/helpers2'
    ```
    the output is
    `/Users/saggese/src/helpers2/dev_scripts_helpers/system_tools/path.py`

    :param file_name: the name of the file to find (which is under `git_src_dir`)
    :param git_src_dir: the directory of the Git client from which `file_name` is
    :param git_dst_dir: the directory of the Git client to which find the
        corresponding file
    :param check_src_file_exists: if True, check that `file_name` exists in
        `git_src_dir`
    :param check_dst_file_exists: if True, check that the file in `git_dst_dir`
        exists
    :return: the absolute path of the file in `git_dst_dir`
    """
    if not os.path.isabs(file_name):
        file_name = os.path.abspath(file_name)
    if check_src_file_exists:
        hdbg.dassert_file_exists(file_name)
    if not os.path.isabs(git_src_dir):
        git_src_dir = os.path.abspath(git_src_dir)
    if not os.path.isabs(git_dst_dir):
        git_dst_dir = os.path.abspath(git_dst_dir)
    # Compute the relative path of the file in the source git client.
    hdbg.dassert_is_path_abs(file_name)
    hdbg.dassert_is_path_abs(git_src_dir)
    rel_path = os.path.relpath(file_name, git_src_dir)
    # Compute the absolute path of the file in the destination git client.
    hdbg.dassert_is_path_abs(git_dst_dir)
    dst_file_path = os.path.join(git_dst_dir, rel_path)
    dst_file_path = os.path.abspath(dst_file_path)
    if check_dst_file_exists:
        hdbg.dassert_file_exists(dst_file_path)
    return dst_file_path


def get_project_dirname(only_index: bool = False) -> str:
    """
    Return the name of the project name (e.g., `/Users/saggese/src/amp1` ->
    `amp1`).

    NOTE: this works properly only outside Docker, e.g., when calling from
    `invoke`. Inside Docker the result might be incorrect since the Git client
    is mapped on `/app`.

    :param only_index: return only the index of the client if possible, e.g.,
        E.g., for `/Users/saggese/src/amp1` it returns the string `1`
    """
    # git_dir = get_client_root(super_module=True)
    git_dir = find_git_root()
    _LOG.debug("git_dir=%s", git_dir)
    ret = os.path.basename(git_dir)
    if only_index:
        last_char = ret[-1]
        hdbg.dassert(
            last_char.isdigit(),
            "The last char `%s` of the git dir `%s` is not a digit",
            last_char,
            git_dir,
        )
        ret = last_char
    _LOG.debug("ret=%s", ret)
    return ret


# #############################################################################


@functools.lru_cache()
def is_inside_submodule(git_dir: str = ".") -> bool:
    """
    Return whether a dir is inside a Git submodule or a Git supermodule.

    We determine this checking if the current Git repo is included
    inside another Git repo.
    """
    cmd = []
    # - Find the git root of the current directory
    # - Check if the dir one level up is a valid Git repo
    # Go to the dir.
    cmd.append(f"cd {git_dir}")
    # > cd im/
    # > git rev-parse --show-toplevel
    # /Users/saggese/src/.../amp
    cmd.append('cd "$(git rev-parse --show-toplevel)/.."')
    # > git rev-parse --is-inside-work-tree
    # true
    cmd.append("(git rev-parse --is-inside-work-tree | grep -q true)")
    cmd_as_str = " && ".join(cmd)
    rc = hsystem.system(cmd_as_str, abort_on_error=False)
    ret: bool = rc == 0
    return ret


def _is_repo(repo_short_name: str) -> bool:
    """
    Return whether we are inside the module `repo_short_name`.
    """
    curr_repo_short_name = hrecouti.get_repo_config().get_repo_short_name()
    is_repo = bool(curr_repo_short_name == repo_short_name)
    return is_repo


def is_helpers() -> bool:
    """
    Return whether we are inside `helpers` repo.

    Either as super module, or a sub module depending on a current
    working directory.
    """
    return _is_repo("helpers")


def is_amp() -> bool:
    """
    Return whether we are inside `amp` repo.

    Either as super module or a sub module depending on a current
    working directory.
    """
    return _is_repo("amp") or _is_repo("cmamp") or _is_repo("sorr")


def is_in_helpers_as_supermodule() -> bool:
    """
    Return whether we are in the `helpers` repo and it's a super-module, i.e.,
    `helpers` by itself.
    """
    return is_helpers() and not is_inside_submodule(".")


# TODO(gp): Be consistent with submodule and sub-module in the code. Same for
#  supermodule.
def is_in_amp_as_submodule() -> bool:
    """
    Return whether we are in the `amp` repo and it's a sub-module, e.g., of
    `lm`.
    """
    return is_amp() and is_inside_submodule(".")


def is_in_amp_as_supermodule() -> bool:
    """
    Return whether we are in the `amp` repo and it's a super-module, i.e.,
    `amp` by itself.
    """
    return is_amp() and not is_inside_submodule(".")


def is_amp_present(*, dir_name: str = ".") -> bool:
    """
    Return whether the `amp` dir exists.

    This is a bit of an hacky way of knowing if there is the amp
    submodule.

    :param dir_name: path to the directory where we want to
      check the existence of `amp`.
    """
    amp_path = os.path.join(dir_name, "amp")
    return os.path.exists(amp_path)


# Using these functions is the last resort to skip / change the tests depending
# on the repo. We should control the tests through what functionalities they
# have, rather than the name of the repo.


def is_cmamp() -> bool:
    """
    Return whether we are inside `cmamp` repo.
    """
    return _is_repo("cmamp")


def is_lem() -> bool:
    """
    Return whether we are inside `lem` repo.
    """
    return _is_repo("lem")


def is_lime() -> bool:
    """
    Return whether we are inside `lime` repo.
    """
    return _is_repo("lime")


# #############################################################################


def _get_submodule_hash(dir_name: str) -> str:
    """
    Report the Git hash that a submodule (e.g., amp) is at from the point of
    view of a supermodule.

    > git ls-tree master | grep <dir_name>
    """
    hdbg.dassert_path_exists(dir_name)
    cmd = f"git ls-tree master | grep {dir_name}"
    data: Tuple[int, str] = hsystem.system_to_one_line(cmd)
    _, output = data
    # 160000 commit 0011776388b4c0582161eb2749b665fc45b87e7e  amp
    _LOG.debug("output=%s", output)
    data: List[str] = output.split()
    _LOG.debug("data=%s", data)
    git_hash = data[2]
    return git_hash


@functools.lru_cache()
def get_path_from_supermodule() -> Tuple[str, str]:
    """
    Return the path to the Git repo including the Git submodule for a
    submodule, and return empty for a supermodule. See AmpTask1017.

    E.g.,
    - for amp included in another repo returns 'amp'
    - for amp without supermodule returns ''
    """
    cmd = "git rev-parse --show-superproject-working-tree"
    # > cd /Users/saggese/src/.../lm/amp
    # > git rev-parse --show-superproject-working-tree
    # /Users/saggese/src/.../lm
    #
    # > cd /Users/saggese/src/.../lm
    # > git rev-parse --show-superproject-working-tree
    # (No result)
    superproject_path: str = hsystem.system_to_one_line(cmd)[1]
    _LOG.debug("superproject_path='%s'", superproject_path)
    #
    cmd = (
        f"git config --file {superproject_path}/.gitmodules --get-regexp path"
        '| grep $(basename "$(pwd)")'
        "| awk '{ print $2 }'"
    )
    # > git config --file /Users/saggese/src/.../.gitmodules --get-regexp path
    # submodule.amp.path amp
    submodule_path: str = hsystem.system_to_one_line(cmd)[1]
    _LOG.debug("submodule_path='%s'", submodule_path)
    return superproject_path, submodule_path


@functools.lru_cache()
def get_submodule_paths() -> List[str]:
    """
    Return the path of the submodules in this repo, e.g., `["amp"]` or `[]`.
    """
    # > git config --file .gitmodules --get-regexp path
    # submodule.amp.path amp
    cmd = "git config --file .gitmodules --get-regexp path | awk '{ print $2 }'"
    _, txt = hsystem.system_to_string(cmd)
    _LOG.debug("txt=%s", txt)
    files: List[str] = hsystem.text_to_list(txt)
    _LOG.debug("files=%s", files)
    return files


def has_submodules() -> bool:
    return len(get_submodule_paths()) > 0


# #############################################################################


def _get_hash(git_hash: str, short_hash: bool, num_digits: int = 8) -> str:
    hdbg.dassert_lte(1, num_digits)
    if short_hash:
        ret = git_hash[:num_digits]
    else:
        ret = git_hash
    return ret


def _group_hashes(head_hash: str, remh_hash: str, subm_hash: str) -> str:
    """
    head_hash: a
    remh_hash: b
    subm_hash: c
    """
    map_ = collections.OrderedDict()
    map_["head_hash"] = head_hash
    map_["remh_hash"] = remh_hash
    if subm_hash:
        map_["subm_hash"] = subm_hash
    #
    inv_map = collections.OrderedDict()
    for k, v in map_.items():
        if v not in inv_map:
            inv_map[v] = [k]
        else:
            inv_map[v].append(k)
    #
    txt = []
    for k, v in inv_map.items():
        # Transform:
        #   ('a2bfc704', ['head_hash', 'remh_hash'])
        # into
        #   'head_hash = remh_hash = a2bfc704'
        txt.append(f"{' = '.join(v)} = {k}")
    txt = "\n".join(txt)
    return txt


def report_submodule_status(dir_names: List[str], short_hash: bool) -> str:
    """
    Return a string representing the status of the repos in `dir_names`.
    """
    txt = []
    for dir_name in dir_names:
        txt.append(f"dir_name='{dir_name}'")
        txt.append(f"  is_inside_submodule: {is_inside_submodule(dir_name)}")
        #
        branch_name = get_branch_name(dir_name)
        if branch_name != "master":
            branch_name = f"!!! {branch_name} !!!"
        txt.append(f"  branch: {branch_name}")
        #
        head_hash = get_head_hash(dir_name)
        head_hash = _get_hash(head_hash, short_hash)
        txt.append(f"  head_hash: {head_hash}")
        #
        remh_hash = get_remote_head_hash(dir_name)
        remh_hash = _get_hash(remh_hash, short_hash)
        txt.append(f"  remh_hash: {remh_hash}")
        #
        if dir_name != ".":
            subm_hash = _get_submodule_hash(dir_name)
            subm_hash = _get_hash(subm_hash, short_hash)
            txt.append(f"  subm_hash: {subm_hash}")
    txt_as_str = "\n".join(txt)
    return txt_as_str


# #############################################################################
# GitHub repository name
# #############################################################################


# All functions should take as input `repo_short_name` and have a switch `mode`
# to distinguish full vs short repo name.

# TODO(gp): Maybe rename full -> long to keep it more symmetric "short vs long".


def _parse_github_repo_name(repo_name: str) -> Tuple[str, str]:
    """
    Parse a repo name from `git remote`.

    The supported formats are both SSH and HTTPS, e.g.,
    - `git@github.com:alphamatic/amp`
    - `https://github.com/alphamatic/amp`

    For both of these strings the function returns ("github.com", "alphamatic/amp").
    """
    # Try to parse the SSH format, e.g., `git@github.com:alphamatic/amp`
    m = re.match(r"^git@(\S+.com):(\S+)$", repo_name)
    if not m:
        # Try tp parse the HTTPS format, e.g., `https://github.com/alphamatic/amp`
        m = re.match(r"^https://(\S+.com)/(\S+)$", repo_name)
    hdbg.dassert(m, "Can't parse '%s'", repo_name)
    # The linter doesn't understand that `dassert` is equivalent to an
    # `assert`.
    assert m is not None
    host_name = m.group(1)
    repo_name = m.group(2)
    _LOG.debug("host_name=%s repo_name=%s", host_name, repo_name)
    # We expect something like "alphamatic/amp".
    m = re.match(r"^\S+/\S+$", repo_name)
    hdbg.dassert(m, "repo_name='%s'", repo_name)
    # The linter doesn't understand that `dassert` is equivalent to an
    # `assert`.
    assert m is not None
    # origin  git@github.com:.../ORG_....git (fetch)
    suffix_to_remove = ".git"
    if repo_name.endswith(suffix_to_remove):
        repo_name = repo_name[: -len(suffix_to_remove)]
    return host_name, repo_name


def get_repo_full_name_from_dirname(
    dir_name: str, include_host_name: bool
) -> str:
    """
    Return the full name of the repo in `git_dir`.

    E.g., "alphamatic/amp", "github.com/alphamatic/amp".

    This function relies on `git remote` to gather the required information.

    :param include_hostname: prepend also the GitHub hostname, e.g., returning
        "github.com/alphamatic/amp"
    :return: the full name of the repo in `git_dir`
        - E.g., "alphamatic/amp", "github.com/alphamatic/amp".
    """
    hdbg.dassert_path_exists(dir_name)
    #
    cmd = f"cd {dir_name}; (git remote -v | grep origin | grep fetch)"
    _, output = hsystem.system_to_string(cmd)
    # > git remote -v
    # origin  git@github.com:alphamatic/amp (fetch)
    # origin  git@github.com:alphamatic/amp (push)
    # TODO(gp): Make it more robust, by checking both fetch and push.
    #  "origin  git@github.com:alphamatic/amp (fetch)"
    data: List[str] = output.split()
    _LOG.debug("data=%s", data)
    hdbg.dassert_eq(len(data), 3, "data='%s'", str(data))
    # Extract the middle string, e.g., "git@github.com:alphamatic/amp"
    repo_name = data[1]
    # Parse the string.
    host_name, repo_name = _parse_github_repo_name(repo_name)
    if include_host_name:
        res = f"{host_name}/{repo_name}"
    else:
        res = repo_name
    return res


def get_repo_full_name_from_client(super_module: bool) -> str:
    """
    Return the full name of the repo (e.g., "alphamatic/amp") from a Git
    client.

    :param super_module: like in get_client_root()
    """
    # Get the Git remote in the dir containing the Git repo.
    git_dir = get_client_root(super_module)
    repo_name = get_repo_full_name_from_dirname(git_dir, include_host_name=False)
    return repo_name


def is_cwd_git_repo() -> bool:
    """
    Return whether the current working directory is a Git repo root.
    """
    return os.path.exists(".git")


# #############################################################################
# Git path
# #############################################################################


# TODO(gp): Use find_file
@functools.lru_cache()
def find_file_in_git_tree(
    file_name: str, super_module: bool = True, remove_tmp_base: bool = False
) -> str:
    """
    Find the path of a file in a Git tree.

    We get the Git root and then search for the file from there.
    """
    root_dir = get_client_root(super_module=super_module)
    cmd = rf"find {root_dir} -name '{file_name}' -not -path '*/.git/*'"
    if remove_tmp_base:
        cmd += r" -not -path '*/tmp\.base/*'"
    _, file_name_out = hsystem.system_to_one_line(cmd)
    _LOG.debug(hprint.to_str("file_name_out"))
    hdbg.dassert_ne(
        file_name_out,
        "",
        "Can't find file '%s' in dir '%s'",
        file_name,
        root_dir,
    )
    file_name_out: str = os.path.abspath(file_name_out)
    hdbg.dassert_path_exists(file_name_out)
    return file_name_out


def get_path_from_git_root(
    file_name: str,
    super_module: bool,
    *,
    git_root: Optional[str] = None,
) -> str:
    """
    Get the path of `file_name` from the root of the Git client.

    E.g., in Docker:
        - `super_module=True` -> git_root=/app
        - `super_module=False` -> git_root=/app/amp

    :param super_module: like get_client_root()
    """
    # Get the root of the Git client.
    if git_root is None:
        git_root = get_client_root(super_module)
    #
    git_root = os.path.normpath(git_root)
    _LOG.debug("git_root=%s", git_root)
    file_name = os.path.normpath(file_name)
    _LOG.debug("file_name=%s", file_name)
    if file_name.startswith(git_root):
        # Remove the `git_root` from file_name.
        ret = os.path.relpath(file_name, git_root)
    else:
        # If the file is not under the root, we can't normalize it.
        raise ValueError(
            f"Can't normalize file_name='{file_name}' for git_root='{git_root}'"
        )
    _LOG.debug(
        "file_name=%s, git_root=%s (super_module=%s) -> ret=%s",
        file_name,
        git_root,
        super_module,
        ret,
    )
    return ret


# TODO(gp): Rewrite this function in a better way.
@functools.lru_cache()
def get_amp_abs_path() -> str:
    """
    Return the absolute path of `amp` dir.
    """
    repo_sym_name = get_repo_full_name_from_client(super_module=False)
    _LOG.debug("repo_sym_name=%s", repo_sym_name)
    #
    repo_sym_names = ["alphamatic/amp"]
    extra_amp_repo_sym_name = (
        hrecouti.get_repo_config().get_extra_amp_repo_sym_name()
    )
    repo_sym_names.append(extra_amp_repo_sym_name)
    _LOG.debug("repo_sym_names=%s", repo_sym_names)
    #
    if repo_sym_name in repo_sym_names:
        # If we are in the amp repo, then the git client root is the amp
        # directory.
        git_root = get_client_root(super_module=False)
        amp_dir = git_root
    else:
        # If we are not in the amp repo, then look for the amp dir.
        amp_dir = find_file_in_git_tree(
            "amp", super_module=True, remove_tmp_base=True
        )
        git_root = get_client_root(super_module=True)
        amp_dir = os.path.join(git_root, amp_dir)
    amp_dir = os.path.abspath(amp_dir)
    # Sanity check.
    hdbg.dassert_dir_exists(amp_dir)
    return amp_dir


# TODO(gp): Is this needed?
def get_repo_dirs() -> List[str]:
    """
    Return the list of the repo repositories, e.g., `[".", "amp", "infra"]`.
    """
    dir_names = ["."]
    dirs = ["amp"]
    for dir_name in dirs:
        if os.path.exists(dir_name):
            dir_names.append(dir_name)
    return dir_names


# TODO(gp): It should go in hdocker?
# TODO(gp): There are functions in hdocker.py that might be more general than
# this.
def find_docker_file(
    file_name: str,
    *,
    root_dir: str = ".",
    dir_depth: int = -1,
    mode: str = "return_all_results",
    candidate_files: Optional[List[str]] = None,
) -> List[str]:
    """
    Convert a file or dir that was generated inside Docker to a file in the
    current Git client.

    This operation is best-effort since it might not be able to find the
    corresponding file in the current repo.

    E.g.,
    - A file like '/app/amp/core/dataflow_model/utils.py', in a Docker container
      with Git root in '/app' becomes 'amp/core/dataflow_model/utils.py'
    - For a file like '/app/amp/core/dataflow_model/utils.py' outside Docker, we
        look for the file 'dataflow_model/utils.py' in the current client and
        then normalize with respect to the

    :param dir_depth: same meaning as in `find_file_with_dir()`
    :param mode: same as `system_interaction.select_result_file_from_list()`
    :param candidate_files: list of results from the `find` command for unit
        test mocking
    :return: the best guess for the file name corresponding to `file_name`
    """
    _LOG.debug(hprint.func_signature_to_str())
    hdbg.dassert_isinstance(file_name, str)
    # Clean up file name.
    file_name = os.path.normpath(file_name)
    _LOG.debug("file_name=%s", file_name)
    # Find the file in the dir.
    file_names = hsystem.find_file_with_dir(
        file_name,
        root_dir=root_dir,
        dir_depth=dir_depth,
        mode=mode,
        candidate_files=candidate_files,
    )
    # Purify.
    _LOG.debug("Purifying file_names=%s", file_names)
    file_names = [
        os.path.relpath(file_name, root_dir) for file_name in file_names
    ]
    return file_names


# #############################################################################
# Git hash
# #############################################################################


def get_head_hash(dir_name: str = ".", short_hash: bool = False) -> str:
    """
    Report the hash that a Git repo is synced at.

    ```
    > git rev-parse HEAD
    4759b3685f903e6c669096e960b248ec31c63b69
    ```
    """
    hdbg.dassert_path_exists(dir_name)
    opts = "--short " if short_hash else " "
    cmd = f"cd {dir_name} && git rev-parse {opts}HEAD"
    data: Tuple[int, str] = hsystem.system_to_one_line(cmd)
    _, output = data
    # Check whether we are building an orange image. If the condition
    # is True, add './amp' hash to the tag as well.
    if is_amp_present(dir_name=dir_name):
        amp_hash = get_head_hash(os.path.join(dir_name, "amp"), short_hash=True)
        output = output + "-" + amp_hash
    else:
        random_string = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=3)
        )
        output = output + "-" + random_string
    return output


# TODO(gp): Use get_head_hash() and remove this.
def get_current_commit_hash(dir_name: str = ".") -> str:
    hdbg.dassert_path_exists(dir_name)
    cmd = f"cd {dir_name} && git rev-parse HEAD"
    data: Tuple[int, str] = hsystem.system_to_one_line(cmd)
    _, sha = data
    # 0011776388b4c0582161eb2749b665fc45b87e7e
    _LOG.debug("sha=%s", sha)
    return sha


def get_remote_head_hash(dir_name: str) -> str:
    """
    Report the hash that the remote Git repo is at.
    """
    hdbg.dassert_path_exists(dir_name)
    sym_name = get_repo_full_name_from_dirname(dir_name, include_host_name=False)
    cmd = f"git ls-remote git@github.com:{sym_name} HEAD 2>/dev/null"
    data: Tuple[int, str] = hsystem.system_to_one_line(cmd)
    _, output = data
    # > git ls-remote git@github.com:alphamatic/amp HEAD 2>/dev/null
    # 921676624f6a5f3f36ab507baed1b886227ac2e6        HEAD
    return output


# #############################################################################
# Modified files
# #############################################################################


def get_modified_files(
    dir_name: str = ".", remove_files_non_present: bool = True
) -> List[str]:
    """
    Return the files that are added and modified in the Git client.

    In other words the files that will be committed with a `git commit -am ...`.
    Equivalent to `dev_scripts/git_files.sh`

    :param dir_name: directory with Git client
    :param remove_files_non_present: remove the files that are not
        currently present in the client
    :return: list of files
    """
    # If the client status is:
    #   > git status -s
    #   AM dev_scripts/infra/ssh_tunnels.py
    #   M helpers/git.py
    #   ?? linter_warnings.txt
    #
    # The result is:
    #   > git diff --cached --name-only
    #   dev_scripts/infra/ssh_tunnels.py
    #
    #   > git ls-files -m
    #   dev_scripts/infra/ssh_tunnels.py
    #   helpers/git.py
    cmd = "(git diff --cached --name-only; git ls-files -m) | sort | uniq"
    files: List[str] = hsystem.system_to_files(
        cmd, dir_name, remove_files_non_present
    )
    return files


# TODO(gp): -> ...previously...
def get_previous_committed_files(
    dir_name: str = ".",
    num_commits: int = 1,
    remove_files_non_present: bool = True,
) -> List[str]:
    """
    Return files changed in the Git client in the last `num_commits` commits.

    Equivalent to `dev_scripts/git_previous_commit_files.sh`

    :param dir_name: directory with Git client
    :param num_commits: how many commits in the past to consider
    :param remove_files_non_present: remove the files that are not
        currently present in the client
    :return: list of files
    """
    cmd = []
    cmd.append('git show --pretty="" --name-only')
    cmd.append(f"$(git log --author $(git config user.name) -{num_commits}")
    cmd.append(r"""| \grep "^commit " | perl -pe 's/commit (.*)/$1/')""")
    cmd_as_str = " ".join(cmd)
    files: List[str] = hsystem.system_to_files(
        cmd_as_str, dir_name, remove_files_non_present
    )
    return files


def get_modified_files_in_branch(
    dst_branch: str, dir_name: str = ".", remove_files_non_present: bool = True
) -> List[str]:
    """
    Return files modified in the current branch with respect to `dst_branch`.

    Equivalent to `git diff --name-only master...`
    Please remember that there is a difference between `master` and `origin/master`.
    See https://stackoverflow.com/questions/18137175

    :param dir_name: directory with Git client
    :param dst_branch: branch to compare to, e.g., `master`, `HEAD`
    :param remove_files_non_present: remove the files that are not
        currently present in the client
    :return: list of files
    """
    if dst_branch == "HEAD":
        target = dst_branch
    else:
        target = f"{dst_branch}..."
    cmd = f"git diff --name-only {target}"
    files: List[str] = hsystem.system_to_files(
        cmd, dir_name, remove_files_non_present
    )
    return files


def get_summary_files_in_branch(
    dst_branch: str,
    *,
    dir_name: str = ".",
) -> str:
    """
    Report summary of files in the current branch with respect to `dst_branch'.

    Same interface as `get_modified_files_in_branch`.
    """
    # File types (from https://git-scm.com/docs/git-diff).
    file_types = [
        ("added", "A"),
        ("copied", "C"),
        ("deleted", "D"),
        ("modified", "M"),
        ("renamed", "R"),
        ("type changed", "T"),
        ("unmerged", "U"),
        ("unknown", "X"),
        ("broken pairing", "B"),
    ]
    res = ""
    for tag, diff_type in file_types:
        cmd = f"git diff --diff-filter={diff_type} --name-only {dst_branch}..."
        files = hsystem.system_to_files(
            cmd, dir_name, remove_files_non_present=False
        )
        _LOG.debug("files=%s", "\n".join(files))
        if files:
            res += f"# {tag}: {len(files)}\n"
            res += hprint.indent("\n".join(files)) + "\n"
    res = res.rstrip("\n")
    return res


# #############################################################################
# Git commands.
# #############################################################################


# TODO(gp): -> get_user_name()
@functools.lru_cache()
def get_git_name() -> str:
    """
    Return the git user name.
    """
    cmd = "git config --get user.name"
    # For some reason data is annotated as Any by mypy, instead of
    # Tuple[int, str] so we need to cast it to the right value.
    data: Tuple[int, str] = hsystem.system_to_one_line(cmd)
    _, output = data
    return output


def git_log(num_commits: int = 5, my_commits: bool = False) -> str:
    """
    Return the output of a pimped version of git log.

    :param num_commits: number of commits to report
    :param my_commits: True to report only the current user commits
    :return: string
    """
    cmd = []
    cmd.append("git log --date=local --oneline --graph --date-order --decorate")
    cmd.append(
        "--pretty=format:'%h %<(8)%aN%  %<(65)%s (%>(14)%ar) %ad %<(10)%d'"
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


def git_stash_push(
    prefix: str, msg: Optional[str] = None, log_level: int = logging.DEBUG
) -> Tuple[str, bool]:
    import helpers.hdatetime as hdateti

    user_name = hsystem.get_user_name()
    server_name = hsystem.get_server_name()
    timestamp = hdateti.get_current_timestamp_as_string("naive_ET")
    tag = f"{user_name}-{server_name}-{timestamp}"
    tag = prefix + "." + tag
    _LOG.debug("tag='%s'", tag)
    cmd = "git stash push"
    _LOG.debug("msg='%s'", msg)
    push_msg = tag[:]
    if msg:
        push_msg += ": " + msg
    cmd += f" -m '{push_msg}'"
    hsystem.system(cmd, suppress_output=False, log_level=log_level)
    # Check if we actually stashed anything.
    cmd = rf"git stash list | \grep '{tag}' | wc -l"
    _, output = hsystem.system_to_string(cmd)
    was_stashed = int(output) > 0
    if not was_stashed:
        msg = "Nothing was stashed"
        _LOG.warning(msg)
        # raise RuntimeError(msg)
    return tag, was_stashed


def git_stash_apply(mode: str, log_level: int = logging.DEBUG) -> None:
    _LOG.debug("# Checking stash head ...")
    cmd = "git stash list | head -3"
    hsystem.system(cmd, suppress_output=False, log_level=log_level)
    #
    _LOG.debug("# Restoring local changes...")
    if mode == "pop":
        cmd = "git stash pop --quiet"
    elif mode == "apply":
        cmd = "git stash apply --quiet"
    else:
        raise ValueError(f"mode='{mode}'")
    hsystem.system(cmd, suppress_output=False, log_level=log_level)


# TODO(gp): Consider using this everywhere. Maybe it can simplify handling issues
#  stemming from the super-module / sub-module repo.
def _get_git_cmd(super_module: bool) -> str:
    """
    Build the first part of a Git command line.
    """
    cmd = []
    cmd.append("git")
    client_root = get_client_root(super_module=super_module)
    # Set the path to the repository (".git" directory), avoiding Git to search for
    # it (from https://git-scm.com/docs/git)
    cmd.append(f"--git-dir='{client_root}/.git'")
    # Set the path to the working tree.
    cmd.append(f"--work-tree='{client_root}'")
    cmd = " ".join(cmd)
    return cmd


def git_tag(
    tag_name: str, super_module: bool = True, log_level: int = logging.DEBUG
) -> None:
    """
    Tag the Git tree with `tag_name` without pushing the tag to the remote.
    """
    _LOG.debug("# Tagging current commit ...")
    git_cmd = _get_git_cmd(super_module)
    cmd = f"{git_cmd} tag -f {tag_name}"
    _ = hsystem.system(cmd, suppress_output=False, log_level=log_level)


def git_push_tag(
    tag_name: str,
    remote: str = "origin",
    super_module: bool = True,
    log_level: int = logging.DEBUG,
) -> None:
    """
    Push the tag `tag_name` to the given remote.
    """
    _LOG.debug("# Pushing current commit ...")
    git_cmd = _get_git_cmd(super_module)
    cmd = f"{git_cmd} push {remote} {tag_name}"
    _ = hsystem.system(cmd, suppress_output=False, log_level=log_level)


def git_describe(
    match: Optional[str] = None, log_level: int = logging.DEBUG
) -> str:
    """
    Return the closest tag in the repo, e.g., 1.0.0.

    If there is no tag, this will return short commit hash.

    :param match: e.g., `cmamp-*`, only consider tags matching the given
        glob pattern
    """
    _LOG.debug("# Looking for version ...")
    cmd = "git describe --tags --always --abbrev=0"
    if match is not None:
        hdbg.dassert_isinstance(match, str)
        hdbg.dassert_ne(match, "")
        cmd = f"{cmd} --match '{match}'"
    num, tag = hsystem.system_to_one_line(cmd, log_level=log_level)
    _ = num
    return tag


def git_add_update(
    file_list: Optional[List[str]] = None, log_level: int = logging.DEBUG
) -> None:
    """
    Add list of files to hgit.

    If `file_list` is not specified, it adds all modified files.

    :param file_list: list of files to `git add`
    """
    _LOG.debug("# Adding all changed files to staging ...")
    cmd = f"git add {' '.join(file_list) if file_list is not None else '-u'}"
    hsystem.system(cmd, suppress_output=False, log_level=log_level)


def fetch_origin_master_if_needed() -> None:
    """
    If inside CI system, force fetching `master` branch from Git repo.

    When testing a branch, `master` is not always fetched, but it might
    be needed by tests.
    """
    if hserver.is_inside_ci():
        _LOG.warning("Running inside CI so fetching master")
        cmd = "git branch -a"
        _, txt = hsystem.system_to_string(cmd)
        _LOG.debug("%s=%s", cmd, txt)
        cmd = r'git branch -a | egrep "\s+master\s*$" | wc -l'
        # * (HEAD detached at pull/1337/merge)
        # master
        # remotes/origin/master
        # remotes/pull/1337/merge
        _, num = hsystem.system_to_one_line(cmd)
        num = int(num)
        _LOG.debug("num=%s", num)
        if num == 0:
            # See AmpTask1321 and AmpTask1338 for details.
            cmd = "git fetch origin master:refs/remotes/origin/master"
            hsystem.system(cmd)
            cmd = "git branch --track master origin/master"
            hsystem.system(cmd)


def is_client_clean(
    dir_name: str = ".",
    abort_if_not_clean: bool = False,
) -> bool:
    """
    Return whether there are files modified, added, or removed in `dir_name`.

    :param abort_if_not_clean: if True and the client is not clean,
        abort reporting the files modified
    """
    _LOG.debug(hprint.to_str("abort_if_not_clean"))
    files = get_modified_files(dir_name)
    # Remove "amp" from files.
    if "amp" in files:
        _LOG.warning("Skipping 'amp' in modified files")
        files = [f for f in files if "amp" != f]
    elif "helpers_root" in files:
        # Remove "helpers_root" from files.
        _LOG.warning("Skipping 'helpers_root' in modified files")
        files = [f for f in files if "helpers_root" != f]
    # A Git client is clean iff there are no files in the index.
    is_clean = len(files) == 0
    if abort_if_not_clean:
        hdbg.dassert(
            is_clean, "The Git client is not clean:\n%s", "\n".join(files)
        )
    return is_clean


@functools.lru_cache()
def _get_gh_pr_list() -> str:
    cmd = "gh pr list -s all --limit 1000"
    rc, txt = hsystem.system_to_string(cmd)
    _ = rc
    return txt


def does_branch_exist(
    branch_name: str,
    mode: str,
    *,
    dir_name: str = ".",
) -> bool:
    """
    Check if a branch with the given name exists in Git or GitHub.
    """
    _LOG.debug(hprint.to_str("branch_name mode dir_name"))
    # Handle the "all" case by recursion on all the possible modes.
    if mode == "all":
        exists = False
        for mode_tmp in ("git_local", "git_remote", "github"):
            exists_tmp = does_branch_exist(
                branch_name, mode_tmp, dir_name=dir_name
            )
            exists |= exists_tmp
        return exists
    #
    hdbg.dassert_in(mode, ("git_local", "git_remote", "github"))
    exists = False
    if mode in ("git_local", "git_remote"):
        # From https://stackoverflow.com/questions/35941566
        cmd = f"cd {dir_name} && git fetch --prune"
        hsystem.system(cmd, abort_on_error=False)
        # From https://stackoverflow.com/questions/5167957
        # > git rev-parse --verify LimeTask197_Get_familiar_with_CF2
        # f03bfa0b4577c2524afd6a1f24d06013f8aa9f1a
        # > git rev-parse --verify I_dont_exist
        # fatal: Needed a single revision
        git_branch_name = branch_name
        if mode == "git_remote":
            git_branch_name = f"origin/{git_branch_name}"
        cmd = f"cd {dir_name} && git rev-parse --verify {git_branch_name}"
        rc = hsystem.system(cmd, abort_on_error=False)
        exists = rc == 0
        _LOG.debug("branch_name='%s' on git: exists=%s", branch_name, exists)
    # Check on GitHub.
    if mode == "github":
        txt = _get_gh_pr_list()
        # ```
        # > gh pr list -s all --limit 10000 | grep AmpTask2163
        # 347     AmpTask2163_Implement_tiled_backtesting_1  AmpTask2163 ... MERGED
        # ```
        # The text is separated by tabs.
        #
        # If there are no issues on the GitHub repo, just return.
        # ```
        # > gh pr list -s all --limit 1000
        # no pull requests match your search in causify-ai/sports_analytics
        # ```
        if txt == "":
            return False
        for line in txt.split("\n"):
            # number, GH branch name, Git branch name, status.
            fields = line.split("\t")
            # fields=['179',
            #   'CmTask2914: Add end-to-end unit test for prod reconcile',
            #   'CmTask2914_Add_end_to_end_unit_test_around_the_prod_reconciliation',
            #   'DRAFT', '2022-09-27 19:56:50 +0000 UTC']
            hdbg.dassert_lte(4, len(fields), "fields=%s", fields)
            number, gh_branch_name, git_branch_name = fields[:3]
            _ = number, gh_branch_name
            if branch_name == git_branch_name:
                exists = True
                _LOG.debug(
                    "branch_name='%s' on github: exists=%s", branch_name, exists
                )
    return exists


def delete_branches(
    dir_name: str,
    mode: str,
    branches: List[str],
    confirm_delete: bool,
    abort_on_error: bool = True,
) -> None:
    """
    Delete local or remote branches.

    :param mode: local or remote
    :param branches: list of branches to delete
    :param confirm_delete: ask the user to confirm before deleting, or
        just do it
    """
    hdbg.dassert_isinstance(branches, list)
    delete_cmd = f"cd {dir_name} && "
    if mode == "local":
        delete_cmd += "git branch -d"
    elif mode == "remote":
        delete_cmd += "git push origin --delete"
    else:
        raise ValueError(f"Invalid mode='{mode}'")
    # Ask whether to continue.
    if confirm_delete:
        branches_as_str = " ".join(branches)
        msg = (
            hdbg.WARNING
            + f": Delete {len(branches)} {mode} branch(es) '{branches_as_str}'?"
        )
        hsystem.query_yes_no(msg, abort_on_no=True)
    for branch in branches:
        if mode == "remote":
            prefix = "origin/"
            hdbg.dassert(
                branch.startswith(prefix),
                "Remote branch '%s' needs to start with '%s'",
                branch,
                prefix,
            )
            branch = branch[len(prefix) :]
        cmd = f"{delete_cmd} {branch}"
        hsystem.system(
            cmd,
            suppress_output=False,
            log_level="echo",
            abort_on_error=abort_on_error,
        )
