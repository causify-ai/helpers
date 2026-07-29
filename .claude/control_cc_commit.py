#!/usr/bin/env python3
"""
Control git commit and git push permissions in .claude/settings.local.json.

Usage:
# Remove git commit/push from deny list:
> control_cc_commit.py --enable   

# Restore git commit/push to deny list:
> control_cc_commit.py --disable  
"""

import argparse
import json
import logging
import os
from typing import Dict, List, Tuple

import helpers.hdbg as hdbg

_LOG = logging.getLogger(__name__)

# #############################################################################
# Helpers
# #############################################################################


def _load_settings(settings_path: str) -> Dict:
    """
    Load settings from JSON file.

    :param settings_path: Path to settings.local.json
    :return: Parsed JSON settings dictionary
    """
    hdbg.dassert_file_exists(settings_path)
    # TODO(ai_gp): Is there a function in json in the helpers we can use?
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
    # TODO(ai_gp): Is there a function in json in the helpers we can use?
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)
    _LOG.info("Settings saved to '%s'", settings_path)


def _save_backup(backup_path: str, removed_denials: List[str]) -> None:
    """
    Save removed denials to backup file.

    :param backup_path: Path to backup file
    :param removed_denials: List of denials that were removed
    """
    with open(backup_path, "w") as f:
        json.dump(removed_denials, f, indent=2)
    _LOG.info("Backup saved to '%s'", backup_path)


def _load_backup(backup_path: str) -> List[str]:
    """
    Load removed denials from backup file.

    :param backup_path: Path to backup file
    :return: List of denials from backup
    """
    hdbg.dassert_file_exists(backup_path)
    with open(backup_path, "r") as f:
        backup_data = json.load(f)
    return backup_data


def _enable_git_commands(settings: Dict) -> Tuple[List[str], Dict]:
    """
    Remove git commit/push denials from settings.

    Removes all denials that contain "git commit" or "git push".

    :param settings: Settings dictionary to modify
    :return: Tuple of (removed denials, modified settings)
    """
    if "permissions" not in settings:
        settings["permissions"] = {}
    if "deny" not in settings["permissions"]:
        settings["permissions"]["deny"] = []
    deny_list: List[str] = settings["permissions"]["deny"]
    # Find denials containing "git commit" or "git push".
    removed_denials = [
        d for d in deny_list if "git commit" in d or "git push" in d
    ]
    # Update deny list.
    settings["permissions"]["deny"] = [
        d for d in deny_list if "git commit" not in d and "git push" not in d
    ]
    if removed_denials:
        _LOG.info(
            "Removed %d git commit/push denials", len(removed_denials)
        )
    else:
        _LOG.info("No git commit/push denials to remove")
    return removed_denials, settings


def _restore_from_backup(
    settings: Dict, backup_path: str
) -> Tuple[bool, Dict]:
    """
    Restore git commit/push denials from backup file.

    :param settings: Settings dictionary to modify
    :param backup_path: Path to backup file
    :return: Tuple of (whether restored, modified settings)
    """
    hdbg.dassert_file_exists(
        backup_path,
        msg=f"Backup file not found: {backup_path}. "
        "Run with --enable first to create a backup.",
    )
    backup_denials = _load_backup(backup_path)
    if "permissions" not in settings:
        settings["permissions"] = {}
    if "deny" not in settings["permissions"]:
        settings["permissions"]["deny"] = []
    deny_list: List[str] = settings["permissions"]["deny"]
    # Add back all denials from backup that are not already present.
    initial_len = len(deny_list)
    for denial in backup_denials:
        if denial not in deny_list:
            deny_list.append(denial)
    settings["permissions"]["deny"] = deny_list
    restored = len(deny_list) != initial_len
    if restored:
        _LOG.info(
            "Restored %d git commit/push denials", len(deny_list) - initial_len
        )
    else:
        _LOG.info("All denials already present")
    # Delete backup file after successful restore.
    os.remove(backup_path)
    _LOG.info("Backup file deleted: '%s'", backup_path)
    return restored, settings


# #############################################################################
# CLI
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    """
    Parse command line arguments.

    :return: Configured argument parser
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__,
    )
    parser.add_argument(
        "--settings",
        type=str,
        default=".claude/settings.local.json",
        help="Path to CC settings.local.json",
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
        help="Disable git commit and git push commands (restore from backup)",
    )
    return parser


def _main(args: argparse.Namespace) -> None:
    """
    Main entry point for the script.

    :param args: Parsed command line arguments
    """
    # Find and load settings.
    settings_path = args.settings
    backup_path = settings_path + ".backup"
    _LOG.info("Using settings file: '%s'", settings_path)
    _LOG.info("Using backup file: '%s'", backup_path)
    hdbg.dassert_file_exists(settings_path)
    settings = _load_settings(settings_path)
    # Apply changes.
    if args.enable:
        removed_denials, settings = _enable_git_commands(settings)
        hdbg.dassert(
            removed_denials,
            msg="No git commit/push denials to remove. "
            "Already enabled or denials not present in settings.",
        )
        _save_settings(settings_path, settings)
        _save_backup(backup_path, removed_denials)
        _LOG.info("Git commit/push permissions: ENABLED")
    elif args.disable:
        _, settings = _restore_from_backup(settings, backup_path)
        _save_settings(settings_path, settings)
        _LOG.info("Git commit/push permissions: DISABLED")


if __name__ == "__main__":
    parser = _parse()
    args = parser.parse_args()
    hdbg.init_logger(use_exec_path=True)
    _main(args)
