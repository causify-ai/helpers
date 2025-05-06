#!/usr/bin/env python3
"""
Check whether a tmux session exists and, if not, creates it.
"""

import logging
import os

# This can be imported because this module is in the same dir as the script
# being executed.
import thin_client_utils as tcu  # noqa: E402

# The `tcu` module adds root of helpers (or `helpers_root` when used in as
# module) to the path, thus allowing imports from helpers.
import helpers.hgit as hgit
import helpers.repo_config_utils as hrecouti

_LOG = logging.getLogger(__name__)

# Get the real file path rather than the symlink path.
current_file_path = os.path.realpath(__file__)
current_dir = os.path.dirname(current_file_path)
# Change to the directory where the file is located so it can find its way to
# the Git root.
# This is necessary when the script is symlinked (e.g., `~/go_cmamp.py`) and
# executed from a different directory.
os.chdir(current_dir)

# Change to the outermost Git repository root so that it can find and use
# the correct repo config.
git_root_dir = hgit.find_git_root()
os.chdir(git_root_dir)

if __name__ == "__main__":
    parser = tcu.create_parser(__doc__)
    dir_suffix = hrecouti.get_repo_config().get_dir_suffix()
    setenv_path = os.path.join(
        f"dev_scripts_{dir_suffix}", "thin_client", "setenv.sh"
    )
    script_path = os.path.abspath(__file__)
    tcu.create_tmux_session(parser, script_path, dir_suffix, setenv_path)
