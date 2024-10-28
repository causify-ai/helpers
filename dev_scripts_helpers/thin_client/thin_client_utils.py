import argparse
import logging
import os
import sys

# We need to tweak `PYTHONPATH` directly since we are bootstrapping the system.
# sys.path.append("helpers_root")
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# #############################################################################
# General
# #############################################################################


def get_git_root_dir() -> str:
    _, git_root_dir = hsystem.system_to_string("git rev-parse --show-toplevel")
    return git_root_dir


def get_home_dir() -> str:
    home_dir = os.environ["HOME"]
    return home_dir


def get_thin_environment_dir(dir_prefix: str) -> str:
    git_root_dir = get_git_root_dir()
    thin_environ_dir = f"{git_root_dir}/dev_scripts_{dir_prefix}/thin_client"
    return thin_environ_dir


def get_venv_dir(dir_prefix: str) -> str:
    home_dir = get_home_dir()
    venv_dir = f"{home_dir}/src/venv/client_venv.{dir_prefix}"
    return venv_dir


def get_tmux_session() -> str:
    rc, tmux_session = hsystem.system_to_string(
        "tmux display-message -p '#S'", abort_on_error=False
    )
    if rc != 0:
        tmux_session = ""
    return tmux_session


def inside_tmux() -> bool:
    return "TMUX" in os.environ


def dassert_not_inside_tmux():
    hdbg.dassert(not inside_tmux())


def system(cmd: str) -> None:
    print(hprint.frame(cmd))
    hsystem.system(cmd, suppress_output=False)


# #############################################################################
# Tmux
# #############################################################################


def create_parser(docstring: str) -> argparse.ArgumentParser:
    # Create the parser.
    parser = argparse.ArgumentParser(
        description=docstring,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hparser.add_verbosity_arg(parser)
    parser.add_argument(
        "--do_not_confirm",
        action="store_true",
        help="Do not ask for user confirmation",
        required=False,
    )
    parser.add_argument(
        "--index",
        type=int,
        help="Index of the client (e.g., 1, 2, 3)",
        required=False,
    )
    parser.add_argument(
        "--force_restart",
        action="store_true",
        help="Destroy the existing tmux session and start a new one",
        required=False,
    )
    parser.add_argument(
        "--create_global_link",
        action="store_true",
        help="Create the link go_*.sh to this script in the home dir and exit",
        required=False,
    )
    return parser


# /////////////////////////////////////////////////////////////////////////////


def _create_new_window(window: str, color: str, dir_name: str, tmux_cmd: str) -> None:
    cmd = f"tmux new-window -n '{window}'"
    hsystem.system(cmd)
    cmd = f"tmux send-keys '{color}; cd {dir_name} && {tmux_cmd}' C-m C-m"
    hsystem.system(cmd)


def _create_repo_windows(git_root_dir: str, setenv_path: str, tmux_name: str) -> None:
    cmd = f"tmux new-session -d -s {tmux_name} -n '---{tmux_name}---'"
    hsystem.system(cmd)
    # Create the first window.
    tmux_cmd = f"source {setenv_path}"
    hdbg.dassert_file_exists(setenv_path)
    cmd = f"tmux send-keys 'white; cd {git_root_dir} && {tmux_cmd}' C-m C-m"
    hsystem.system(cmd)
    # Create the remaining windows.
    windows = ["dbash", "regr", "jupyter"]
    for window in windows:
        _create_new_window(window, "green", git_root_dir, tmux_cmd)


def _go_to_first_window(tmux_name: str) -> None:
    hsystem.system(f"tmux select-window -t {tmux_name}:0")
    hsystem.system(f"tmux -2 attach-session -t {tmux_name}")


# /////////////////////////////////////////////////////////////////////////////


def _create_helpers_tmux(
    git_root_dir: str, setenv_path: str, tmux_name: str
) -> None:
    _create_repo_windows(git_root_dir, setenv_path, tmux_name)
    _go_to_first_window(tmux_name)


def _create_helpers_tmux_with_subrepo(
    git_root_dir: str, setenv_path: str, tmux_name: str
) -> None:
    # - Create the windows for the current repo.
    _create_repo_windows(git_root_dir, setenv_path, tmux_name)
    # - Create the windows for helpers (the sub-repo).
    # Create the first window.
    window = "---HELPERS---"
    git_subrepo_dir = os.path.join(git_root_dir, "helpers_root")
    setenv_path = "dev_scripts_helpers/thin_client/setenv.sh"
    tmux_cmd = f"source {setenv_path}"
    hdbg.dassert_file_exists(os.path.join(git_subrepo_dir, setenv_path))
    _create_new_window(window, "white", git_subrepo_dir, tmux_cmd)
    # Create the remaining windows.
    windows = ["dbash", "regr", "jupyter"]
    for window in windows:
        _create_new_window(window, "green", git_subrepo_dir, tmux_cmd)
    #
    _go_to_first_window(tmux_name)


# /////////////////////////////////////////////////////////////////////////////


def create_tmux_session(
    parser: argparse.ArgumentParser,
    script_path: str,
    dir_prefix: str,
    setenv_path: str,
    has_subrepo: bool,
) -> None:
    """
    Creates a new tmux session or attaches to an existing one.

    This function checks if a tmux session with the given name (derived from
    `dir_prefix` and `index` argument) already exists. If it does, the function
    either attaches to the existing session or destroys it and creates a new
    one, based on the `force_restart` argument. If the session does not exist, a
    new one is created.

    The tmux session is configured based on the shell script specified by
    `setenv_path`.

    :param parser: Argument parser object.
    :param script_path: Path to the script file.
    :param dir_prefix: Prefix for the directory and tmux session name.
    :param setenv_path: Path to the shell script for setting up the environment.
    :param has_subrepo: Flag indicating if the project has a subrepository.
    """
    print(f"##> {script_path}")
    # Parse the args.
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    #
    if args.create_global_link:
        _LOG.info("Creating the global link")
        hdbg.dassert_file_exists(script_path)
        cmd = f"ln -sf {script_path} ~/go_{dir_prefix}.py"
        system(cmd)
        _LOG.info("Link created: exiting")
        sys.exit(0)
    #
    hdbg.dassert_is_not(args.index, None, "Need to specify --index")
    idx = int(args.index)
    tmux_name = f"{dir_prefix}{idx}"
    _LOG.info("tmux_name=%s", tmux_name)
    #
    _LOG.debug("Checking if the tmux session '%s' already exists", tmux_name)
    _, tmux_session_str = hsystem.system_to_string(
        "tmux list-sessions", 
        abort_on_error=False
    )
    _LOG.debug("tmux_session_str=\n%s", tmux_session_str)
    # E.g.,
    # ```
    # cmamp1: 4 windows (created Sun Aug  4 09:54:53 2024) (attached)
    # ...
    # ```
    tmux_sessions = [l.split(":")[0] for l in tmux_session_str.splitlines()]
    tmux_exists = tmux_name in tmux_sessions
    _LOG.debug("tmux_exists=%s", tmux_exists)
    if tmux_exists:
        # The tmux session exists.
        if args.force_restart:
            # Destroy the tmux session.
            _LOG.warning("The tmux session already exists: destroying it ...")
            current_tmux = get_tmux_session()
            system(f"tmux kill-session -t {current_tmux}")
        else:
            _LOG.info("The tmux session already exists: attaching it ...")
            # Make sure we are outside a tmux session.
            dassert_not_inside_tmux()
            # Attach the existing tmux session.
            system(f"tmux attach-session -t {tmux_name}")
            sys.exit(0)
    _LOG.info("The tmux session doesn't exist, creating it")
    # Make sure we are outside a tmux session.
    dassert_not_inside_tmux()
    os_name = hsystem.get_os_name()
    user_name = hsystem.get_user_name()
    if os_name == "Darwin":
        _LOG.info("Inferred MacOS setup")
        home_dir = get_home_dir()
    elif os_name == "Linux":
        _LOG.info("Inferred server setup")
        server_name = hsystem.get_server_name()
        hdbg.dassert_in(server_name, ["dev1", "dev2", "dev3"])
        home_dir = f"/data/{user_name}"
    hdbg.dassert_ne(home_dir, "")
    _LOG.info("home_dir=%s", home_dir)
    git_root_dir = os.path.join(home_dir, "src", tmux_name)
    _LOG.info("git_root_dir=%s", git_root_dir)
    # Create the tmux session.
    setenv_path = os.path.join(git_root_dir, setenv_path)
    _LOG.info("Checking if setenv_path=%s exists", setenv_path)
    hdbg.dassert_file_exists(setenv_path)
    if has_subrepo:
        _create_helpers_tmux_with_subrepo(git_root_dir, setenv_path, tmux_name)
    else:
        _create_helpers_tmux(git_root_dir, setenv_path, tmux_name)
