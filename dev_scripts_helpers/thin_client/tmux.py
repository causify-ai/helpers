#!/usr/bin/env python3
"""
Check whether a tmux session exists and, if not, creates it.
"""

import logging
import os
import sys

_LOG = logging.getLogger(__name__)

# We need to tweak `PYTHONPATH` directly since we are bootstrapping the system.
sys.path.append("helpers_root/dev_scripts_helpers/thin_client")
import thin_client_utils as tcu

sys.path.append("helpers_root/helpers")
import helpers.repo_config_utils as hrecouti

_HAS_SUBREPO = hrecouti.get_repo_config().use_helpers_as_nested_module()
_SCRIPT_PATH = os.path.abspath(__file__)
if _HAS_SUBREPO:
    # Change the directory to the real directory if we are in a symlink.
    dir_name = os.path.dirname(os.path.realpath(_SCRIPT_PATH)) + "/../.."
    # print(dir_name)
    os.chdir(dir_name)

if __name__ == "__main__":
    parser = tcu.create_parser(__doc__)
    dir_suffix = hrecouti.get_repo_config().get_dir_suffix()
    setenv_path = os.path.join(
        f"dev_scripts_{dir_suffix}", "thin_client", "setenv.sh"
    )
    tcu.create_tmux_session(
        parser, _SCRIPT_PATH, dir_suffix, setenv_path, _HAS_SUBREPO
    )
