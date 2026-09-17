#!/usr/bin/env python3

"""
Create a zip file with modified and/or untracked files from the current
repository and optionally its submodules.

The zip file is created with a timestamp-based name in the specified backup
directory (default: $HOME/src/backups). Example:
`modified_files.helpers_root.20251119_130034.zip`

# Usage Example

- Back up all modified and untracked files, including submodules:
> git_backup.py

- Preview what would be backed up without creating the zip:
> git_backup.py --dry_run

Import as:

import dev_scripts_helpers.git.git_backup as dsggibac
"""

import argparse
import logging
import os
import zipfile
from typing import List, Optional, Tuple

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.lib_tasks.lib_tasks_git as hltltagi
import helpers.lib_tasks.lib_tasks_utils as hltltaut

_LOG = logging.getLogger(__name__)

# pylint: disable=protected-access


# #############################################################################
# File collection
# #############################################################################


def _collect_backup_files(
    file_mode: str, include_subrepos: bool
) -> List[Tuple[str, str]]:
    """
    Collect `(repo_path, file_path)` pairs to include in the backup zip.

    :param file_mode: which files to include: "all", "modified", or
        "untracked"
    :param include_subrepos: whether to also collect submodule files
    :return: list of `(repo_path, file_path)` pairs, `repo_path` being
        `"."` for the main repository
    """
    # Collect files from the main repository.
    _LOG.info("Collecting %s files from main repository...", file_mode)
    main_repo_files = hgit.get_modified_and_untracked_files(".", mode=file_mode)
    _LOG.info("Found %d files in main repository", len(main_repo_files))
    all_files = []
    for file_path in main_repo_files:
        all_files.append((".", file_path))
    # Also include submodule files if requested to ensure complete backup.
    if include_subrepos:
        submodule_paths = hltltagi._get_submodule_paths()
        if submodule_paths:
            _LOG.info(
                "Found %d submodule(s), collecting files...",
                len(submodule_paths),
            )
            for submodule_path in submodule_paths:
                hdbg.dassert_dir_exists(
                    submodule_path,
                    msg=f"Submodule path does not exist: {submodule_path}",
                )
                _LOG.info("Checking submodule: %s", submodule_path)
                submodule_files = hgit.get_modified_and_untracked_files(
                    submodule_path, mode=file_mode
                )
                _LOG.info(
                    "Found %d files in submodule %s",
                    len(submodule_files),
                    submodule_path,
                )
                for file_path in submodule_files:
                    all_files.append((submodule_path, file_path))
        else:
            _LOG.info("No submodules found")
    else:
        _LOG.info("Skipping submodules (include_subrepos=False)")
    return all_files


# #############################################################################
# Backup
# #############################################################################


def _create_backup(
    file_mode: str = "all",
    backup_dir: Optional[str] = None,
    include_subrepos: bool = True,
    dry_run: bool = False,
) -> None:
    """
    Create a zip file with modified and/or untracked files from the current
    repository and optionally its submodules.

    Same parameters as `invoke git_backup`.
    """
    # Validate backup scope to ensure user intent is clear.
    valid_modes = ["all", "modified", "untracked"]
    hdbg.dassert_in(
        file_mode,
        valid_modes,
        "Invalid file_mode '%s'; must be one of: %s",
        file_mode,
        ", ".join(valid_modes),
    )
    # Use default backup location if not specified.
    if backup_dir is None:
        backup_dir = os.path.join(os.path.expanduser("~"), "src", "backups")
    hio.create_dir(backup_dir, incremental=True)
    # Determine repository name for readable backup file naming.
    super_module = False
    git_client_root = hgit.get_client_root(super_module)
    # Include timestamp to avoid overwriting previous backups.
    timestamp = hltltaut.get_ET_timestamp()
    repo_name = os.path.basename(git_client_root)
    zip_file_name = f"modified_files.{repo_name}.{timestamp}.zip"
    # Collect files from the main repository and, optionally, submodules.
    all_files = _collect_backup_files(file_mode, include_subrepos)
    # Verify there's content to backup before proceeding.
    if not all_files:
        _LOG.warning("No %s files found. Nothing to zip.", file_mode)
        return
    # Display summary of what will be backed up.
    _LOG.info(
        "\n%s\nFound %d total files to include:\n%s",
        hprint.frame("Files to include in zip"),
        len(all_files),
        hprint.indent(
            "\n".join(
                [
                    (
                        os.path.join(repo_path, file_path)
                        if repo_path != "."
                        else file_path
                    )
                    for repo_path, file_path in all_files
                ]
            )
        ),
    )
    if dry_run:
        _LOG.warning("Dry-run mode: not creating zip file")
        return
    # Create zip file with all collected files.
    zip_file_path = os.path.join(backup_dir, zip_file_name)
    _LOG.info("Creating zip file: %s", zip_file_path)
    with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for repo_path, file_path in all_files:
            full_path = os.path.join(repo_path, file_path)
            # Maintain directory hierarchy in archive for easy restoration.
            arcname = (
                os.path.join(repo_path, file_path)
                if repo_path != "."
                else file_path
            )
            try:
                zipf.write(full_path, arcname=arcname)
                _LOG.debug("Added to zip: %s", arcname)
            except Exception as e:
                _LOG.warning("Failed to add %s to zip: %s", full_path, e)
    _LOG.info("Successfully created zip file: %s", zip_file_path)
    # Display location for easy access.
    abs_zip_path = os.path.abspath(zip_file_path)
    print(f"\nZip file created at: {abs_zip_path}")


# #############################################################################
# CLI
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    parser.add_argument(
        "--file_mode",
        type=str,
        default="all",
        choices=["all", "modified", "untracked"],
        help="Which files to include",
    )
    parser.add_argument(
        "--backup_dir",
        type=str,
        default=None,
        help="Directory where to save the zip file (default: "
        "$HOME/src/backups)",
    )
    parser.add_argument(
        "--no_include_subrepos",
        action="store_true",
        help="Do not include submodule files",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Only print the files that would be included without "
        "creating the zip",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    _create_backup(
        args.file_mode,
        args.backup_dir,
        not args.no_include_subrepos,
        args.dry_run,
    )


if __name__ == "__main__":
    _main(_parse())
