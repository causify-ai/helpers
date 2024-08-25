#!/usr/bin/env python3
"""
Check whether a tmux session exists and, if not, creates it.
"""

import logging
import os
import sys

# We need to tweak `PYTHONPATH` directly since we are bootstrapping the system.
sys.path.append("helpers_root/dev_scripts/thin_client")
import thin_client_utils as tcu

#sys.path.append("helpers_root/helpers")
import helpers.hdbg as hdbg

_LOG = logging.getLogger(__name__)

SCRIPT_PATH = os.path.abspath(__file__)


if __name__ == "__main__":
    parser = tcu.create_parser(__doc__)
    has_subrepo = False
    if has_subrepo:
        dir_prefix = "xyz"
    else:
        # `helpers` has no super-repo.
        dir_prefix = "helpers"
    setenv_path = os.path.join(f"dev_scripts_{dir_prefix}", "thin_client",
                               "setenv.sh")
    tcu.create_tmux_session(
        parser, SCRIPT_PATH, dir_prefix, setenv_path, has_subrepo
    )