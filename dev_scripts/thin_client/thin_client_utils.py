import os

import helpers.hdbg as hdbg
import helpers.hsystem as hsystem


def get_git_root_dir() -> str:
    _, git_root_dir = hsystem.system_to_string("git rev-parse --show-toplevel")
    return git_root_dir


def get_home_dir() -> str:
    home_dir = os.environ['HOME']
    return home_dir


def get_thin_environment_dir() -> str:
    git_root_dir = get_git_root_dir()
    thin_environ_dir = f"{git_root_dir}/dev_scripts/thin_client"
    return thin_environ_dir


def get_venv_dir(dir_prefix: str) -> str:
    home_dir = get_home_dir()
    venv_dir = f"{home_dir}/src/venv/client_venv.{dir_prefix}"
    return venv_dir


def get_tmux_session() -> str:
    rc, tmux_session = hsystem.system_to_string("tmux display-message -p '#S'",
                                               abort_on_error=False)
    if rc != 0:
        tmux_session = ""
    return tmux_session


def inside_tmux() -> bool:
    return 'TMUX' in os.environ


def dassert_not_inside_tmux():
    hdbg.dassert(not inside_tmux())