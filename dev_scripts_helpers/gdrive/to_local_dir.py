#!/usr/bin/env python3

"""
Convert Google Drive document links to local directory paths.

This script takes a Google Drive document URL (for Docs, Sheets, or Drive files)
and converts it to the corresponding local directory path under one of the
configured Google Drive accounts.

The script supports three Google Drive accounts:
- causify: /Users/saggese/Library/CloudStorage/GoogleDrive-gp@causify.ai
- gmail: /Users/saggese/Library/CloudStorage/GoogleDrive-saggese@gmail.com
- umd: /Users/saggese/Library/CloudStorage/GoogleDrive-gsaggese@umd.edu

Usage examples:

# Automatic account detection
> to_local_dir.py --url "https://docs.google.com/document/d/1DK-ZWp4EhY-EpdfH66SOsdZcWkM1VE9o/edit"

# Specify account explicitly
> to_local_dir.py --url "https://docs.google.com/document/d/1DK-ZWp4EhY-EpdfH66SOsdZcWkM1VE9o/edit" --account causify

# Using file name instead of URL
> to_local_dir.py --file_name "My Document" --account gmail

Import as:

import dev_scripts_helpers.gdrive.to_local_dir as dscgdtld
"""

import argparse
import logging
import os
from typing import Dict, List, Optional

import helpers.hdbg as hdbg
import helpers.hgoogle_drive_api as hgodrapi
import helpers.hio as hio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

# #############################################################################
# Google Drive account mappings
# #############################################################################

GOOGLE_DRIVE_ACCOUNTS: Dict[str, str] = {
    "causify": "/Users/saggese/Library/CloudStorage/GoogleDrive-gp@causify.ai",
    "gmail": "/Users/saggese/Library/CloudStorage/GoogleDrive-saggese@gmail.com",
    "umd": "/Users/saggese/Library/CloudStorage/GoogleDrive-gsaggese@umd.edu",
}


def _get_valid_accounts() -> List[str]:
    """
    Get list of valid account names.

    :return: List of account names
    """
    return list(GOOGLE_DRIVE_ACCOUNTS.keys())


def _get_local_gdrive_path(account: str) -> str:
    """
    Get the local Google Drive path for a specific account.

    :param account: Account name (causify, gmail, umd)
    :return: Local file system path to the Google Drive directory
    """
    hdbg.dassert_in(
        account,
        GOOGLE_DRIVE_ACCOUNTS,
        "Invalid account '%s'. Valid accounts are: %s",
        account,
        list(GOOGLE_DRIVE_ACCOUNTS.keys()),
    )
    base_path = GOOGLE_DRIVE_ACCOUNTS[account]
    # Verify that the base path exists
    if not os.path.exists(base_path):
        _LOG.warning(
            "Google Drive path for account '%s' does not exist: %s",
            account,
            base_path,
        )
    return base_path


def _find_file_in_account(
    file_name: str,
    account: str,
) -> Optional[str]:
    """
    Find a file by name in a specific Google Drive account.

    :param file_name: Name of the file to search for
    :param account: Account name (causify, gmail, umd)
    :return: Full path to the file if found, None otherwise
    """
    base_path = _get_local_gdrive_path(account)
    if not os.path.exists(base_path):
        _LOG.warning(
            "Cannot search in account '%s' - path does not exist: %s",
            account,
            base_path,
        )
        return None
    _LOG.debug("Searching for '%s' in account '%s'", file_name, account)
    # Walk through the directory tree to find the file
    for root, dirs, files in os.walk(base_path):
        if file_name in files:
            full_path = os.path.join(root, file_name)
            _LOG.info("Found file: %s", full_path)
            return full_path
    _LOG.debug("File '%s' not found in account '%s'", file_name, account)
    return None


def _auto_detect_account(file_name: str) -> Optional[str]:
    """
    Auto-detect which Google Drive account contains the file.

    :param file_name: Name of the file to search for
    :return: Account name if found, None otherwise
    """
    _LOG.info("Auto-detecting account for file: %s", file_name)
    for account in GOOGLE_DRIVE_ACCOUNTS.keys():
        file_path = _find_file_in_account(file_name, account)
        if file_path:
            _LOG.info("File found in account: %s", account)
            return account
    _LOG.warning("File '%s' not found in any account", file_name)
    return None


def _convert_google_path_to_local_path(
    google_path_list: List[str],
    file_name: str,
    account: str,
) -> str:
    """
    Convert Google Drive path list to local file system path.

    :param google_path_list: List of folder names from Google Drive
    :param file_name: Name of the file
    :param account: Account name (causify, gmail, umd)
    :return: Local file system path
    """
    base_path = _get_local_gdrive_path(account)
    # Skip "My Drive" if it's in the path
    filtered_path = [p for p in google_path_list if p not in ["My Drive", "Shared drives"]]
    # Construct the full path
    local_path = os.path.join(base_path, *filtered_path, file_name)
    return local_path


def convert_url_to_local_path(
    url: str,
    *,
    account: Optional[str] = None,
    credentials: Optional["goasea.Credentials"] = None,
) -> str:
    """
    Convert a Google Drive URL to a local file system path.

    :param url: Google Drive URL (Docs, Sheets, or Drive)
    :param account: Account name (causify, gmail, umd), or None for auto-detection
    :param credentials: Google credentials object (optional)
    :return: Local file system path
    """
    # Get credentials if not provided
    if credentials is None:
        credentials = hgodrapi.get_credentials()
    # Get the file name from the URL
    try:
        file_name = hgodrapi.get_tab_name_from_url(credentials, url)
    except Exception as e:
        _LOG.warning("Could not get file name from URL: %s", e)
        # Try to extract file ID and use it as fallback
        file_id = hgodrapi._extract_file_id_from_url(url)
        file_name = f"file_{file_id}"
    _LOG.info("File name: %s", file_name)
    # Get the Google Drive path
    google_path_list = hgodrapi.get_google_path_from_url(credentials, url)
    _LOG.info("Google path: %s", google_path_list)
    # Auto-detect account if not specified
    if account is None or account == "auto":
        account = _auto_detect_account(file_name)
        if account is None:
            _LOG.warning(
                "Could not auto-detect account. Using 'causify' as default."
            )
            account = "causify"
    # Convert to local path
    local_path = _convert_google_path_to_local_path(
        google_path_list, file_name, account
    )
    return local_path


def convert_file_name_to_local_path(
    file_name: str,
    *,
    account: Optional[str] = None,
) -> str:
    """
    Convert a file name to a local file system path by searching in Google Drive accounts.

    :param file_name: Name of the file to search for
    :param account: Account name (causify, gmail, umd), or None for auto-detection
    :return: Local file system path
    """
    # Auto-detect account if not specified
    if account is None or account == "auto":
        account = _auto_detect_account(file_name)
        if account is None:
            raise ValueError(f"File '{file_name}' not found in any account")
    # Find the file in the specified account
    file_path = _find_file_in_account(file_name, account)
    if file_path is None:
        raise ValueError(
            f"File '{file_name}' not found in account '{account}'"
        )
    return file_path


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # Either URL or file_name must be provided
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--url",
        action="store",
        help="Google Drive URL (Docs, Sheets, or Drive)",
    )
    group.add_argument(
        "--file_name",
        action="store",
        help="Name of the file to search for",
    )
    parser.add_argument(
        "--account",
        action="store",
        choices=["auto", "causify", "gmail", "umd"],
        default="auto",
        help="Google Drive account to use (default: auto-detect)",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    try:
        if args.url:
            # Convert URL to local path
            local_path = convert_url_to_local_path(
                args.url,
                account=args.account,
            )
        else:
            # Convert file name to local path
            local_path = convert_file_name_to_local_path(
                args.file_name,
                account=args.account,
            )
        # Check if the path exists
        if os.path.exists(local_path):
            _LOG.info("File found at: %s", local_path)
            print(local_path)
        else:
            _LOG.warning(
                "Local path does not exist: %s",
                local_path,
            )
            print(f"Expected path (does not exist): {local_path}")
    except Exception as e:
        _LOG.error("Error: %s", e)
        raise


if __name__ == "__main__":
    _main(_parse())
