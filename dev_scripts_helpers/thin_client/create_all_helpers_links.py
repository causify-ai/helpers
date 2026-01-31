#!/usr/bin/env python

"""
Create symbolic links from the current repository to helpers_root files.

This script creates symbolic links for configuration files and directories from
helpers_root to the current repository, enabling thin client repositories to
share common configuration.

Example usage:
# Create all missing links
> create_all_helpers_links.py

# Force recreate all links (even if they exist)
> create_all_helpers_links.py --force

# Preview what would be done without making changes
> create_all_helpers_links.py --dry_run

Import as:

import dev_scripts_helpers.thin_client.create_all_helpers_links as dstcrcahl
"""

import argparse
import logging
import os
from typing import List

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# #############################################################################


# Files and directories to link from helpers_root.
_FILES_TO_LINK = [
    ".claude",
    ".coveragerc",
    ".gitignore",
    ".gitleaksignore",
    ".isort.cfg",
    ".pre-commit-config.yaml",
    "CLAUDE.md",
    "conftest.py",
    "invoke.yaml",
    "linters2/",
    "pyproject.toml",
    "pytest.ini",
]


def _get_helpers_root_path() -> str:
    """
    Get the absolute path to the helpers_root directory.

    :return: absolute path to helpers_root
    """
    helpers_root = hgit.find_helpers_root()
    hdbg.dassert_dir_exists(helpers_root)
    _LOG.info("Found helpers_root at: %s", helpers_root)
    return helpers_root


def _get_current_repo_root() -> str:
    """
    Get the absolute path to the current repository root.

    :return: absolute path to current repo root
    """
    repo_root = hgit.get_client_root(".")
    hdbg.dassert_dir_exists(repo_root)
    _LOG.info("Current repository root: %s", repo_root)
    return repo_root


def _is_broken_link(path: str) -> bool:
    """
    Check if the path is a broken symbolic link.

    :param path: path to check
    :return: True if the path is a broken symlink, False otherwise
    """
    is_broken = os.path.islink(path) and not os.path.exists(path)
    return is_broken


def _should_create_link(
    target_path: str,
    *,
    force: bool,
) -> bool:
    """
    Determine if a symbolic link should be created.

    :param target_path: path where the link would be created
    :param force: if True, link should be created even if file exists
    :return: True if link should be created, False otherwise
    """
    if not os.path.exists(target_path):
        _LOG.debug("Target does not exist: %s", target_path)
        return True
    if _is_broken_link(target_path):
        _LOG.info("Broken link detected, will recreate: %s", target_path)
        return True
    if force:
        _LOG.info("Force mode: will recreate existing link: %s", target_path)
        return True
    # Warn if the file exists but is not a symbolic link.
    if os.path.exists(target_path) and not os.path.islink(target_path):
        _LOG.warning(
            "Target exists but is not a symbolic link: %s", target_path
        )
    _LOG.debug("Target already exists and is not broken: %s", target_path)
    return False


def _create_symbolic_link(
    source_path: str,
    target_path: str,
    *,
    force: bool,
    dry_run: bool,
) -> None:
    """
    Create a symbolic link from target to source.

    :param source_path: the file/directory to link to (in helpers_root)
    :param target_path: where to create the link (in current repo)
    :param force: if True, remove existing file/link before creating
    :param dry_run: if True, only show what would be done without doing it
    """
    # Check if we should create the link.
    if not _should_create_link(target_path, force=force):
        # Print the target for existing links.
        if os.path.islink(target_path):
            link_target = os.readlink(target_path)
            _LOG.info("Skipping existing link: %s -> %s", target_path, link_target)
        else:
            _LOG.info("Skipping existing link: %s", target_path)
        return
    # Remove existing file/link if in force mode or if it's broken.
    if os.path.exists(target_path) or os.path.islink(target_path):
        if dry_run:
            _LOG.info(
                "[DRY RUN] Would remove existing file/link: %s", target_path
            )
        else:
            _LOG.info("Removing existing file/link: %s", target_path)
            if os.path.isdir(target_path) and not os.path.islink(target_path):
                hsystem.system(f"rm -rf {target_path}")
            else:
                os.remove(target_path)
    # Compute relative path from target to source.
    target_dir = os.path.dirname(target_path)
    relative_source_path = os.path.relpath(source_path, target_dir)
    # Create the symbolic link.
    if dry_run:
        _LOG.info(
            "[DRY RUN] Would create link: %s -> %s", target_path, relative_source_path
        )
    else:
        _LOG.info("Creating link: %s -> %s", target_path, relative_source_path)
        os.symlink(relative_source_path, target_path)


def _analyze_links(
    files_to_link: List[str],
) -> None:
    """
    Analyze and report existing symbolic links.

    :param files_to_link: list of files/directories to analyze
    """
    # Get paths.
    helpers_root = _get_helpers_root_path()
    repo_root = _get_current_repo_root()
    # Analyze links.
    _LOG.info("Analyzing symbolic links for %d items", len(files_to_link))
    for item in files_to_link:
        # Remove trailing slash for directories.
        item_clean = item.rstrip("/")
        # Build full paths.
        source_path = os.path.join(helpers_root, item_clean)
        target_path = os.path.join(repo_root, item_clean)
        # Check if target exists.
        if not os.path.exists(target_path) and not os.path.islink(target_path):
            _LOG.info("Link does not exist: %s", target_path)
            continue
        # Check if it's a symbolic link.
        if not os.path.islink(target_path):
            _LOG.info("Not a symbolic link: %s", target_path)
            continue
        # Read the link target.
        link_target = os.readlink(target_path)
        # Resolve to absolute path for checking.
        target_dir = os.path.dirname(target_path)
        resolved_path = os.path.normpath(
            os.path.join(target_dir, link_target)
        )
        # Check if the resolved path exists.
        if not os.path.exists(resolved_path):
            _LOG.info(
                "Broken link: %s -> %s (resolved: %s)",
                target_path,
                link_target,
                resolved_path,
            )
            continue
        # Determine if it's a file or directory.
        if os.path.isfile(resolved_path):
            item_type = "file"
        elif os.path.isdir(resolved_path):
            item_type = "directory"
        else:
            item_type = "unknown"
        # Report the link.
        _LOG.info(
            "Link: %s -> %s (type: %s)", target_path, link_target, item_type
        )
    _LOG.info("Finished analyzing symbolic links")


def _create_all_links(
    files_to_link: List[str],
    *,
    force: bool,
    dry_run: bool,
) -> None:
    """
    Create all symbolic links from helpers_root to current repository.

    :param files_to_link: list of files/directories to link
    :param force: if True, recreate links even if they exist
    :param dry_run: if True, only show what would be done without doing it
    """
    # Get paths.
    helpers_root = _get_helpers_root_path()
    repo_root = _get_current_repo_root()
    # Create links.
    if dry_run:
        _LOG.info(
            "[DRY RUN] Would create symbolic links for %d items",
            len(files_to_link),
        )
    else:
        _LOG.info("Creating symbolic links for %d items", len(files_to_link))
    for item in files_to_link:
        # Remove trailing slash for directories.
        item_clean = item.rstrip("/")
        # Build full paths.
        source_path = os.path.join(helpers_root, item_clean)
        target_path = os.path.join(repo_root, item_clean)
        # Verify source exists.
        if not os.path.exists(source_path):
            _LOG.warning("Source does not exist, skipping: %s", source_path)
            continue
        # Create the link.
        _create_symbolic_link(
            source_path, target_path, force=force, dry_run=dry_run
        )
    if dry_run:
        _LOG.info("[DRY RUN] Finished preview of symbolic links")
    else:
        _LOG.info("Finished creating symbolic links")


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze and report existing links instead of creating them",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force recreate links even if they exist",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Show what would be done without actually doing it",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Analyze or create symbolic links.
    if args.analyze:
        _analyze_links(_FILES_TO_LINK)
    else:
        _create_all_links(_FILES_TO_LINK, force=args.force, dry_run=args.dry_run)


if __name__ == "__main__":
    _main(_parse())
