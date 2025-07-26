#!/usr/bin/env python

"""
Print the branch name for each git submodule directory.

This script checks all git submodules and prints the name of the branch each 
directory is currently on. If no submodules are found, it reports that.

Example usage:
```
# Print branches for all submodules
> dev_scripts_helpers/git/print_git_branches.py

# Example output:
submodule1: master
submodule2: feature/new-branch
submodule3: develop
```
"""

import argparse
import logging
import os
import subprocess

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _get_submodule_paths() -> list[str]:
    """
    Get list of submodule paths from .gitmodules file.
    
    Returns:
        List of submodule directory paths, empty if no submodules found.
    """
    gitmodules_path = ".gitmodules"
    if not os.path.exists(gitmodules_path):
        _LOG.info("No .gitmodules file found")
        return []
    
    try:
        # Use git config to list submodule paths
        cmd = "git config --file .gitmodules --get-regexp path"
        _, output = hsystem.system_to_string(cmd)
        
        submodule_paths = []
        for line in output.strip().split('\n'):
            if line:
                # Format: "submodule.<name>.path <path>"
                path = line.split(' ', 1)[1]
                submodule_paths.append(path)
        
        return submodule_paths
    except Exception as e:
        _LOG.warning(f"Error reading submodules: {e}")
        return []


def _get_branch_name(submodule_path: str) -> str:
    """
    Get the current branch name for a submodule.
    
    Args:
        submodule_path: Path to the submodule directory
        
    Returns:
        Branch name or error message
    """
    if not os.path.exists(submodule_path):
        return "ERROR: Directory not found"
    
    if not os.path.exists(os.path.join(submodule_path, ".git")):
        return "ERROR: Not a git repository"
    
    try:
        # Get current branch name
        cmd = f"cd {submodule_path} && git rev-parse --abbrev-ref HEAD"
        _, branch_name = hsystem.system_to_string(cmd)
        return branch_name.strip()
    except Exception as e:
        return f"ERROR: {str(e)}"


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    
    _LOG.info("Checking git submodules...")
    
    submodule_paths = _get_submodule_paths()
    
    if not submodule_paths:
        _LOG.info("No git submodules found in this repository")
        return
    
    _LOG.info(f"Found {len(submodule_paths)} submodule(s)")
    
    # Print header
    print("Submodule branches:")
    print("-" * 40)
    
    # Check each submodule
    for path in submodule_paths:
        branch_name = _get_branch_name(path)
        print(f"{path}: {branch_name}")


if __name__ == "__main__":
    _main(_parse())
