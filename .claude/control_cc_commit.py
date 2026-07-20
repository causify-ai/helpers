#!/usr/bin/env python3
"""
Control git commit and git push permissions in .claude/settings.local.json.

Usage:
    control_cc_commit.py --enable   # Remove git commit/push from deny list
    control_cc_commit.py --disable  # Add git commit/push to deny list
"""

import argparse
import json
import logging
import os
from typing import Dict, List

import helpers.hdbg as hdbg

_LOG = logging.getLogger(__name__)

# #############################################################################
# Constants
# #############################################################################

# Git commit and push permissions to control.
_GIT_DENIALS = [
    "Bash(*git commit:*)",
    "Bash(*git commit -m *)",
    "Bash(*git push:*)",
]


# #############################################################################
# Helpers
# #############################################################################


# TODO(ai_gp): Allow .claude/settings.local.json to be specified through command
# line and it's .claude/settings.local.json by default. Do a dassert_file_exists
def _get_settings_path() -> str:
    """
    Get path to .claude/settings.local.json.

    Searches up from the current directory to find the project's .claude
    directory.

    :return: Absolute path to settings.local.json
    """
    # Start from current directory and search up.
    current_dir = os.getcwd()
    while current_dir != "/":
        claude_dir = os.path.join(current_dir, ".claude")
        if os.path.isdir(claude_dir):
            settings_file = os.path.join(claude_dir, "settings.local.json")
            return settings_file
        current_dir = os.path.dirname(current_dir)
    # Not found, use default path.
    hdbg.dfatal("Could not find .claude directory in parent directories")
    return ""


def _load_settings(settings_path: str) -> Dict:
    """
    Load settings from JSON file.

    :param settings_path: Path to settings.local.json
    :return: Parsed JSON settings dictionary
    """
    hdbg.dassert_file_exists(settings_path)
    with open(settings_path, "r") as f:
        settings = json.load(f)
    return settings


def _save_settings(settings_path: str, settings: Dict) -> None:
    """
    Save settings to JSON file.

    Writes settings with proper formatting (2-space indent).

    :param settings_path: Path to settings.local.json
    :param settings: Settings dictionary to save
    """
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)
    _LOG.info("Settings saved to '%s'", settings_path)


def _enable_git_commands(settings: Dict) -> bool:
    """
    Remove git commit/push denials from settings.

    :param settings: Settings dictionary to modify
    :return: True if any denials were removed, False otherwise
    """
    if "permissions" not in settings:
        settings["permissions"] = {}
    if "deny" not in settings["permissions"]:
        settings["permissions"]["deny"] = []
    deny_list: List[str] = settings["permissions"]["deny"]
    # Check if any denials need to be removed.
    initial_len = len(deny_list)
    deny_list = [d for d in deny_list if d not in _GIT_DENIALS]
    settings["permissions"]["deny"] = deny_list
    removed = initial_len != len(deny_list)
    if removed:
        _LOG.info("Removed %d git commit/push denials", initial_len - len(deny_list))
    else:
        _LOG.info("No git commit/push denials to remove")
    return removed


def _disable_git_commands(settings: Dict) -> bool:
    """
    Add git commit/push denials to settings.

    :param settings: Settings dictionary to modify
    :return: True if any denials were added, False otherwise
    """
    if "permissions" not in settings:
        settings["permissions"] = {}
    if "deny" not in settings["permissions"]:
        settings["permissions"]["deny"] = []
    deny_list: List[str] = settings["permissions"]["deny"]
    # Add denials that are not already present.
    initial_len = len(deny_list)
    for denial in _GIT_DENIALS:
        if denial not in deny_list:
            deny_list.append(denial)
    settings["permissions"]["deny"] = deny_list
    added = len(deny_list) != initial_len
    if added:
        _LOG.info("Added %d git commit/push denials", len(deny_list) - initial_len)
    else:
        _LOG.info("Git commit/push denials already present")
    return added


# #############################################################################
# CLI
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    """
    Parse command line arguments.

    :return: Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--enable",
        action="store_true",
        help="Enable git commit and git push commands (remove from deny list)",
    )
    group.add_argument(
        "--disable",
        action="store_true",
        help="Disable git commit and git push commands (add to deny list)",
    )
    return parser


def _main(args: argparse.Namespace) -> None:
    """
    Main entry point for the script.

    :param args: Parsed command line arguments
    """
    # Find and load settings.
    settings_path = _get_settings_path()
    _LOG.info("Using settings file: '%s'", settings_path)
    settings = _load_settings(settings_path)
    # Apply changes.
    changed = False
    if args.enable:
        changed = _enable_git_commands(settings)
    elif args.disable:
        changed = _disable_git_commands(settings)
    # Save if changed.
    if changed:
        _save_settings(settings_path, settings)
        _LOG.info("Git commit/push permissions: %s",
                  "ENABLED" if args.enable else "DISABLED")
    else:
        _LOG.info("No changes made to settings")


if __name__ == "__main__":
    parser = _parse()
    args = parser.parse_args()
    hdbg.init_logger(use_exec_path=True)
    _main(args)
