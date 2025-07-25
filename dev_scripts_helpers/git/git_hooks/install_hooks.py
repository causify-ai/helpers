#!/usr/bin/env python
"""
Manage custom git pre-commit hooks.

# Install hooks as links to the repo:
> install_hooks.py --action install

# Remove hooks:
> install_hooks.py --action remove

# Check hook status:
> install_hooks.py --action status

Import as:

import dev_scripts_helpers.git.git_hooks.install_hooks as dsgghinho
"""

import argparse
import logging
import os
import sys

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# #############################################################################

# Phases to install.
_GIT_PHASE_HOOKS = ["pre-commit", "commit-msg"]
# _GIT_PHASE_HOOKS = ["pre-commit"]


def _main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--action",
        required=True,
        choices=["install", "remove", "status"],
        action="store",
    )
    hparser.add_verbosity_arg(parser)
    #
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level)
    # Get the dir with the Git hooks to install.
    helpers_root = hgit.find_helpers_root()
    src_dir = os.path.join(helpers_root, "dev_scripts_helpers/git/git_hooks")
    _LOG.info("src_dir=%s", src_dir)
    hdbg.dassert_dir_exists(src_dir)
    # Find the location to install the Git hooks.
    # In a super-module:
    # > git rev-parse --git-path hooks
    # .git/hooks
    # In a sub-module:
    # > git rev-parse --git-path hooks
    # /Users/saggese/src/.../.git/modules/amp/hooks
    cmd = "git rev-parse --git-path hooks"
    rc, target_dir = hsystem.system_to_one_line(cmd)
    _ = rc
    _LOG.info("target_dir=%s", target_dir)
    hdbg.dassert_dir_exists(target_dir)
    #
    if args.action == "install":
        _LOG.info("Installing hooks into '%s'", target_dir)
    elif args.action == "remove":
        _LOG.info("Removing hooks from '%s'", target_dir)
    elif args.action == "status":
        _LOG.info("Checking status of hooks in the repo '%s'", src_dir)
        cmd = f"ls -l {src_dir}"
        hsystem.system(cmd, suppress_output=False, log_level=logging.DEBUG)
        #
        _LOG.info("Checking status of hooks in '%s'", target_dir)
        cmd = f"ls -l {target_dir}"
        hsystem.system(cmd, suppress_output=False, log_level=logging.DEBUG)
        sys.exit(0)
    else:
        hdbg.dfatal(f"Invalid action='{args.action}'")
    # Scan the hooks.
    for hook in _GIT_PHASE_HOOKS:
        # Target location for the hooks.
        target_file = os.path.join(target_dir, hook)
        _LOG.debug("target_file=%s", target_file)
        if args.action == "install":
            # The name of the script hook is the same as the hook phase.
            hook_file = os.path.join(src_dir, hook) + ".py"
            hook_file = os.path.abspath(hook_file)
            hdbg.dassert_file_exists(hook_file)
            _LOG.info("Creating %s -> %s", hook_file, target_file)
            # Create link.
            cmd = f"ln -sf {hook_file} {target_file}"
            hsystem.system(cmd, log_level=logging.DEBUG)
            # Make the scripts executable.
            cmd = f"chmod +x {hook_file}"
            hsystem.system(cmd, log_level=logging.DEBUG)
            cmd = f"chmod +x {target_file}"
            hsystem.system(cmd, log_level=logging.DEBUG)
        elif args.action == "remove":
            _LOG.info("Remove hook '%s'", target_file)
            if os.path.exists(target_file):
                cmd = f"unlink {target_file}"
                hsystem.system(cmd, log_level=logging.DEBUG)
            else:
                _LOG.warning(
                    "Nothing to do since '%s' doesn't exist", target_file
                )
        else:
            hdbg.dfatal(f"Invalid action='{args.action}'")


if __name__ == "__main__":
    _main()
