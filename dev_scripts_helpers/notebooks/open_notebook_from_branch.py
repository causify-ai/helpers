#!/usr/bin/env python

r"""
Open a notebook from a git branch in a live Jupyter Lab, in a git worktree.

The current client is not touched. The script:
- fetches the branch from `origin`
- creates a git worktree for the branch, or reuses and fast-forwards the existing
  one
- finds the project dir (i.e., the closest dir above the notebook storing
  `docker_jupyter.sh`)
- builds the project Docker image with `docker_build.sh`
- starts Jupyter Lab with `docker_jupyter.sh`
- opens the notebook in the browser as soon as Jupyter Lab answers

Stop Jupyter Lab with Ctrl+C. The worktree is left in place, remove it with
`git worktree remove <worktree_dir>`.

# Usage Example

- Open a notebook from a branch:
> open_notebook_from_branch.py \
    -i research/Optimal_strategy_for_racket_sports/notebooks/racket_shot_probability.ipynb \
    --branch UmdTask788_Racket_sports_Change_color_of_heatmaps

- Print the commands that change the client or start containers without
  running them:
> open_notebook_from_branch.py -i <notebook> --branch <branch> --dry_run

- Skip the Docker build, since the image is already built:
> open_notebook_from_branch.py -i <notebook> --branch <branch> --no_build

- Use another port and stop the Jupyter container already running:
> open_notebook_from_branch.py -i <notebook> --branch <branch> --port 8889 \
    --kill_existing_jupyter

Import as:

import dev_scripts_helpers.notebooks.open_notebook_from_branch as dsnoonfb
"""

import argparse
import logging
import os
import shlex
import socket
import threading
import time
import urllib.parse
import webbrowser
from typing import Optional

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# Seconds to wait for Jupyter Lab to answer before giving up on opening the
# browser (the first run can take long to pull the image).
_JUPYTER_READY_TIMEOUT_IN_SECS = 600

# #############################################################################
# Git helpers
# #############################################################################


def _normalize_branch(branch: str) -> str:
    """
    Remove the `origin/` prefix from a branch name.

    :param branch: branch name, with or without the remote
        - E.g., `origin/UmdTask788_Racket_sports` or `UmdTask788_Racket_sports`
    :return: branch name without remote
        - E.g., `UmdTask788_Racket_sports`
    """
    prefix = "origin/"
    branch = branch.removeprefix(prefix)
    return branch


def _get_notebook_rel_path(notebook: str, git_root: str) -> str:
    """
    Get the path of the notebook relative to the git root.

    A path that exists locally (absolute or relative to the current dir) is
    converted to a path relative to the git root. Any other path is assumed to be
    already relative to the git root, since the notebook can exist only on the
    branch.

    :param notebook: path of the notebook
    :param git_root: absolute path of the git root
    :return: path relative to the git root
        - E.g., `research/Racket/notebooks/racket_shot_probability.ipynb`
    """
    if os.path.isabs(notebook) or os.path.exists(notebook):
        rel_path = os.path.relpath(os.path.abspath(notebook), git_root)
    else:
        rel_path = notebook
    hdbg.dassert(rel_path.endswith(".ipynb"), "'%s' is not a notebook", rel_path)
    hdbg.dassert(
        not rel_path.startswith(".."),
        "'%s' is outside the git root '%s'",
        rel_path,
        git_root,
    )
    return rel_path


def _fetch_branch(branch: str, *, git_root: str) -> None:
    """
    Fetch a branch from `origin`, falling back to the local remote-tracking ref.

    The fetch fails when the remote branch is deleted (e.g., after the PR is
    merged) or when offline. In this case the local `origin/<branch>` ref, if
    any, is used.

    :param branch: branch name without remote
    :param git_root: absolute path of the git root
    """
    git_cmd = f"git -C {shlex.quote(git_root)}"
    branch_arg = shlex.quote(branch)
    rc, _ = hsystem.system_to_string(
        f"{git_cmd} fetch origin {branch_arg}", abort_on_error=False
    )
    if rc != 0:
        # Check that the remote-tracking ref is known locally.
        ref = shlex.quote(f"origin/{branch}")
        rc, _ = hsystem.system_to_string(
            f"{git_cmd} rev-parse --verify --quiet {ref}", abort_on_error=False
        )
        hdbg.dassert_eq(
            rc,
            0,
            "Can't fetch branch 'origin/%s' and it is not known locally",
            branch,
        )
        _LOG.warning(
            "Can't fetch 'origin/%s' (e.g., offline or deleted after the "
            "merge): using the local copy",
            branch,
        )


def _exists_on_branch(branch: str, rel_path: str, *, git_root: str) -> bool:
    """
    Check if a path exists on the `origin/<branch>` tree.

    :param branch: branch name without remote
    :param rel_path: path relative to the git root
    :param git_root: absolute path of the git root
    :return: whether the path exists on the branch
    """
    obj = shlex.quote(f"origin/{branch}:{rel_path}")
    cmd = f"git -C {shlex.quote(git_root)} cat-file -e {obj}"
    rc, _ = hsystem.system_to_string(cmd, abort_on_error=False)
    exists = rc == 0
    return exists


def _find_project_dir(branch: str, rel_notebook: str, *, git_root: str) -> str:
    """
    Find the closest dir above the notebook that stores `docker_jupyter.sh`.

    :param branch: branch name without remote
    :param rel_notebook: path of the notebook relative to the git root
    :param git_root: absolute path of the git root
    :return: project dir relative to the git root (empty for the git root)
        - E.g., `research/Optimal_strategy_for_racket_sports`
    """
    dir_name = os.path.dirname(rel_notebook)
    project_dir: Optional[str] = None
    while project_dir is None:
        script = os.path.join(dir_name, "docker_jupyter.sh")
        if _exists_on_branch(branch, script, git_root=git_root):
            project_dir = dir_name
        else:
            hdbg.dassert_ne(
                dir_name,
                "",
                "No 'docker_jupyter.sh' found above '%s' on branch '%s'",
                rel_notebook,
                branch,
            )
            dir_name = os.path.dirname(dir_name)
    return project_dir


# #############################################################################
# Worktree
# #############################################################################


def _parse_worktree_list(txt: str, branch: str) -> Optional[str]:
    """
    Find the worktree that has a branch checked out.

    :param txt: output of `git worktree list --porcelain`
    :param branch: branch name without remote
    :return: dir of the worktree with the branch checked out, or `None`
    """
    worktree_dir: Optional[str] = None
    curr_dir: Optional[str] = None
    for line in txt.split("\n"):
        if line.startswith("worktree "):
            curr_dir = line[len("worktree ") :]
        elif line == f"branch refs/heads/{branch}":
            worktree_dir = curr_dir
    return worktree_dir


def _get_default_worktree_dir(branch: str, *, git_root: str) -> str:
    """
    Get the default dir of the worktree of a branch.

    The name follows the one built by `git_create_issue_and_branch.py`, i.e.,
    `<repo>_worktree_<issue_id>`.

    :param branch: branch name without remote
    :param git_root: absolute path of the git root
    :return: sibling dir of the git root
        - E.g., `/src/umd_classes1_worktree_788`
    """
    issue_id = hgit.extract_gh_issue_number_from_branch(branch)
    suffix = str(issue_id) if issue_id is not None else branch.replace("/", "_")
    repo_name = os.path.basename(git_root)
    parent_dir = os.path.dirname(git_root)
    worktree_dir = os.path.join(parent_dir, f"{repo_name}_worktree_{suffix}")
    return worktree_dir


def _run(cmd: str, *, dry_run: bool) -> None:
    """
    Run a command showing its output, or only report it in a dry run.

    :param cmd: command to run
    :param dry_run: report the command without running it
    """
    if dry_run:
        _LOG.warning("[DRY_RUN] Would run: %s", cmd)
    else:
        _LOG.info("Running: %s", cmd)
        hsystem.system(cmd, suppress_output=False)


def _create_worktree(
    branch: str, worktree_dir: str, *, git_root: str, dry_run: bool
) -> None:
    """
    Create the worktree of a branch and initialize the submodules.

    :param branch: branch name without remote
    :param worktree_dir: dir of the new worktree
    :param git_root: absolute path of the git root
    :param dry_run: report the commands without running them
    """
    hdbg.dassert_path_not_exists(
        worktree_dir,
        "The dir is not a worktree of the branch: use another dir with --worktree_dir",
    )
    git_cmd = f"git -C {shlex.quote(git_root)}"
    # Reuse the local branch, if it exists, otherwise create it to track the
    # remote one.
    ref = shlex.quote(f"refs/heads/{branch}")
    rc, _ = hsystem.system_to_string(
        f"{git_cmd} show-ref --verify --quiet {ref}", abort_on_error=False
    )
    has_local_branch = rc == 0
    dir_arg = shlex.quote(worktree_dir)
    branch_arg = shlex.quote(branch)
    if has_local_branch:
        cmd = f"{git_cmd} worktree add {dir_arg} {branch_arg}"
    else:
        cmd = (
            f"{git_cmd} worktree add --track -b {branch_arg} {dir_arg} "
            f"origin/{branch_arg}"
        )
    _run(cmd, dry_run=dry_run)
    if has_local_branch:
        # The local branch can be behind the remote one.
        cmd = f"git -C {dir_arg} merge --ff-only origin/{branch_arg}"
        _run(cmd, dry_run=dry_run)
    # A new worktree has empty submodule dirs.
    if _exists_on_branch(branch, ".gitmodules", git_root=git_root):
        cmd = f"git -C {dir_arg} submodule update --init --recursive"
        _run(cmd, dry_run=dry_run)


def _sync_worktree(branch: str, worktree_dir: str, *, dry_run: bool) -> None:
    """
    Fast-forward an existing worktree to the remote branch, if it is clean.

    :param branch: branch name without remote
    :param worktree_dir: dir of the existing worktree
    :param dry_run: report the commands without running them
    """
    if hgit.is_client_clean(dir_name=worktree_dir):
        cmd = (
            f"git -C {shlex.quote(worktree_dir)} merge --ff-only "
            f"origin/{shlex.quote(branch)}"
        )
        _run(cmd, dry_run=dry_run)
    else:
        _LOG.warning(
            "Worktree '%s' has local changes: not syncing it with 'origin/%s'",
            worktree_dir,
            branch,
        )


# #############################################################################
# Jupyter
# #############################################################################


def _is_port_in_use(port: int) -> bool:
    """
    Check if something is listening on a local port.

    :param port: port on the host
    :return: whether a connection to the port succeeds
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        in_use = sock.connect_ex(("localhost", port)) == 0
    return in_use


def _get_notebook_url(rel_notebook: str, port: int) -> str:
    """
    Get the URL of a notebook served by Jupyter Lab in the container.

    The git root is mounted at `/git_root` in the container.

    :param rel_notebook: path of the notebook relative to the git root
    :param port: port of Jupyter Lab on the host
    :return: URL of the notebook
        - E.g., `http://localhost:8888/lab/tree/git_root/dir/notebook.ipynb`
    """
    quoted_path = urllib.parse.quote(rel_notebook)
    url = f"http://localhost:{port}/lab/tree/git_root/{quoted_path}"
    return url


def _open_browser_when_ready(url: str, port: int) -> None:
    """
    Wait for Jupyter Lab to answer and open a URL in the browser.

    :param url: URL to open
    :param port: port of Jupyter Lab on the host
    """
    cmd = f"curl --silent --fail --max-time 2 http://localhost:{port}/api"
    start_time = time.time()
    is_ready = False
    while (
        not is_ready
        and time.time() - start_time < _JUPYTER_READY_TIMEOUT_IN_SECS
    ):
        rc, _ = hsystem.system_to_string(
            cmd, abort_on_error=False, print_command=False
        )
        is_ready = rc == 0
        if not is_ready:
            time.sleep(2)
    if is_ready:
        _LOG.info("Opening '%s'", url)
        webbrowser.open(url)
    else:
        _LOG.warning(
            "Jupyter Lab did not answer in %s secs: open '%s' by hand",
            _JUPYTER_READY_TIMEOUT_IN_SECS,
            url,
        )


def _start_jupyter(
    project_dir: str,
    url: str,
    *,
    port: int,
    kill_existing_jupyter: bool,
    open_browser: bool,
    dry_run: bool,
) -> None:
    """
    Start Jupyter Lab in the project container and open the notebook.

    The call blocks until Jupyter Lab is stopped.

    :param project_dir: absolute path of the dir storing `docker_jupyter.sh`
    :param url: URL of the notebook to open
    :param port: port of Jupyter Lab on the host
    :param kill_existing_jupyter: stop the Jupyter container already running
        for the project
    :param open_browser: open the notebook in the browser when Jupyter Lab is
        ready
    :param dry_run: report the command without running it
    """
    cmd = [
        f"cd {shlex.quote(project_dir)} &&",
        "./docker_jupyter.sh",
        f"-p {port}",
    ]
    if kill_existing_jupyter:
        cmd.append("-f")
    cmd = " ".join(cmd)
    if not dry_run:
        if not kill_existing_jupyter:
            hdbg.dassert(
                not _is_port_in_use(port),
                "Port %s is in use: use --port or --kill_existing_jupyter",
                port,
            )
        if open_browser:
            thread = threading.Thread(
                target=_open_browser_when_ready, args=(url, port), daemon=True
            )
            thread.start()
    _run(cmd, dry_run=dry_run)


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    hparser.add_input_file_arg(
        parser,
        help_=(
            "Path of the notebook, relative to the git root or to the current "
            "dir (it can exist only on the branch)"
        ),
    )
    parser.add_argument(
        "--branch",
        action="store",
        required=True,
        help="Git branch with the notebook, with or without the `origin/` prefix",
    )
    parser.add_argument(
        "--worktree_dir",
        action="store",
        default=None,
        help="Dir of the new worktree, if the branch has no worktree yet "
        "(by default a sibling of the git root named `<repo>_worktree_<issue>`)",
    )
    parser.add_argument(
        "--port",
        action="store",
        type=int,
        default=8888,
        help="Host port for Jupyter Lab",
    )
    parser.add_argument(
        "--kill_existing_jupyter",
        action="store_true",
        help="Stop the Jupyter container already running for the project",
    )
    hparser.add_bool_arg(
        parser,
        "build",
        default_value=True,
        help_="Build the Docker image with `docker_build.sh` before starting",
    )
    hparser.add_bool_arg(
        parser,
        "open_browser",
        default_value=True,
        help_="Open the notebook in the browser when Jupyter Lab is ready",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Show what would be done without actually doing it",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    dry_run = args.dry_run
    branch = _normalize_branch(args.branch)
    git_root = hgit.find_git_root()
    rel_notebook = _get_notebook_rel_path(args.input, git_root)
    # Get the branch. The fetch only updates the remote-tracking ref, so it is
    # run also in a dry run to be able to inspect the branch.
    _fetch_branch(branch, git_root=git_root)
    hdbg.dassert(
        _exists_on_branch(branch, rel_notebook, git_root=git_root),
        "Notebook '%s' not found on branch 'origin/%s'",
        rel_notebook,
        branch,
    )
    project_dir = _find_project_dir(branch, rel_notebook, git_root=git_root)
    _LOG.info("Project dir: '%s'", project_dir)
    # Get a worktree synced with the branch.
    cmd = f"git -C {shlex.quote(git_root)} worktree list --porcelain"
    _, txt = hsystem.system_to_string(cmd)
    worktree_dir = _parse_worktree_list(txt, branch)
    if worktree_dir is None:
        worktree_dir = args.worktree_dir or _get_default_worktree_dir(
            branch, git_root=git_root
        )
        worktree_dir = os.path.abspath(worktree_dir)
        _create_worktree(
            branch, worktree_dir, git_root=git_root, dry_run=dry_run
        )
    else:
        _LOG.info("Reusing worktree '%s' of branch '%s'", worktree_dir, branch)
        if args.worktree_dir:
            _LOG.warning("Ignoring --worktree_dir, since the worktree exists")
        _sync_worktree(branch, worktree_dir, dry_run=dry_run)
    # Build the image and start Jupyter Lab from the project dir.
    abs_project_dir = os.path.join(worktree_dir, project_dir)
    if args.build:
        cmd = f"cd {shlex.quote(abs_project_dir)} && ./docker_build.sh"
        _run(cmd, dry_run=dry_run)
    url = _get_notebook_url(rel_notebook, args.port)
    _LOG.info("Notebook URL: %s", url)
    _LOG.info(
        "Stop with Ctrl+C. Remove the worktree with: git worktree remove '%s'",
        worktree_dir,
    )
    _start_jupyter(
        abs_project_dir,
        url,
        port=args.port,
        kill_existing_jupyter=args.kill_existing_jupyter,
        open_browser=args.open_browser,
        dry_run=dry_run,
    )


if __name__ == "__main__":
    _main(_parse())
