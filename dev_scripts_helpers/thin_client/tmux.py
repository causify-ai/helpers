#!/usr/bin/env python3
"""
Check whether a tmux session exists and, if not, creates it.
"""

import logging
import os
import subprocess
import sys
from typing import Tuple

_LOG = logging.getLogger(__name__)


# We can't use `hsystem` as this is a bootstrapping script.
def _system_to_string(
    cmd: str, abort_on_error: bool = True, verbose: bool = False
) -> Tuple[int, str]:
    assert isinstance(cmd, str), "Type of '%s' is %s" % (str(cmd), type(cmd))
    if verbose:
        print(f"> {cmd}")
    stdout = subprocess.PIPE
    stderr = subprocess.STDOUT
    with subprocess.Popen(
        cmd, shell=True, executable="/bin/bash", stdout=stdout, stderr=stderr
    ) as p:
        output = ""
        while True:
            line = p.stdout.readline().decode("utf-8")  # type: ignore
            if not line:
                break
            # print((line.rstrip("\n")))
            output += line
        p.stdout.close()  # type: ignore
        rc = p.wait()
    if abort_on_error and rc != 0:
        msg = (
            "cmd='%s' failed with rc='%s'" % (cmd, rc)
        ) + "\nOutput of the failing command is:\n%s" % output
        _LOG.error(msg)
        sys.exit(-1)
    return rc, output


# We can't use `hgit` as this is a bootstrapping script.
def _get_git_root_dir() -> str:
    """
    Return the absolute path to the outermost Git repository root.

    If inside a Git submodule, this returns the parent (superproject)
    root. Otherwise, it returns the current repository's root.
    :return: absolute path to the outermost Git repository root
    """
    cmd = "git rev-parse --show-superproject-working-tree --show-toplevel | head -n1"
    _, git_root_dir = _system_to_string(cmd)
    git_root_dir = git_root_dir.strip()
    return git_root_dir


# We need to tweak `PYTHONPATH` directly since we are bootstrapping the system.
sys.path.append("helpers_root/dev_scripts_helpers/thin_client")
import thin_client_utils as tcu

sys.path.append("helpers_root/helpers")
import helpers.repo_config_utils as hrecouti

# Get the real file path rather than the symlink path.
current_file_path = os.path.realpath(__file__)
current_dir = os.path.dirname(current_file_path)
# Change to the repo directory so that it can find the repo config.
os.chdir(current_dir)

# Change to the outermost Git repository root.
git_root_dir = _get_git_root_dir()
os.chdir(git_root_dir)

if __name__ == "__main__":
    parser = tcu.create_parser(__doc__)
    dir_suffix = hrecouti.get_repo_config().get_dir_suffix()
    setenv_path = os.path.join(
        f"dev_scripts_{dir_suffix}", "thin_client", "setenv.sh"
    )
    script_path = os.path.abspath(__file__)
    tcu.create_tmux_session(parser, script_path, dir_suffix, setenv_path)
