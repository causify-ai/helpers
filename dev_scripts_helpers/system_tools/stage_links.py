"""
Stage symbolic links for modification.

# Usage Example

- Stage all symbolic links under a destination directory for modification:
> stage_links.py --dst_dir /path/to/dst

- Use `--dry_run` to only report which symlinks would be staged, without
  touching the filesystem:
> stage_links.py --dst_dir /path/to/dst --dry_run
"""

import argparse
import logging
import os
import shutil
from typing import List, Tuple

import helpers.hparser as hparser
import helpers.htable as htable

_LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def find_symlinks(dst_dir: str) -> List[str]:
    """
    Find all symbolic links in the destination directory.

    :param dst_dir: Directory to search for symbolic links.
    :return: List of paths to symbolic links.
    """
    symlinks = []
    for root, _, files in os.walk(dst_dir):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.islink(file_path):
                symlinks.append(file_path)
    return symlinks


def _classify_symlinks(symlinks: List[str]) -> List[Tuple[str, str, str]]:
    """
    Classify each symlink by whether its target file exists.

    :param symlinks: list of symbolic links to classify
    :return: list of `(link, target_file, current_state)`, where
        `current_state` is "link" (the target exists, ready to be staged) or
        "missing" (the target file does not exist, cannot be staged)
    """
    rows = []
    for link in symlinks:
        target_file = os.readlink(link)
        current_state = "link" if os.path.exists(target_file) else "missing"
        rows.append((link, target_file, current_state))
    return rows


def build_status_table(symlinks: List[str]) -> htable.Table:
    """
    Build a table summarizing what staging would do to each symlink.

    :param symlinks: list of symbolic links to stage
    :return: table with columns `link`, `target_file`, `current_state`,
        `target_state` (`target_state` is "copy" for a link that would be
        staged, "-" if its target is missing)
    """
    column_names = ["link", "target_file", "current_state", "target_state"]
    rows = []
    for link, target_file, current_state in _classify_symlinks(symlinks):
        target_state = "copy" if current_state == "link" else "-"
        rows.append([link, target_file, current_state, target_state])
    return htable.Table(rows, column_names)


def stage_links(symlinks: List[str], *, dry_run: bool = False) -> None:
    """
    Replace symbolic links with writable copies of the linked files.

    :param symlinks: List of symbolic links to replace.
    :param dry_run: If True, only report which symlinks would be staged
        without touching the filesystem
    """
    for link in symlinks:
        # Resolve the original file the symlink points to.
        target_file = os.readlink(link)
        if not os.path.exists(target_file):
            _LOG.warning(
                "'%s' is missing (target of link '%s')", target_file, link
            )
            continue
        if dry_run:
            _LOG.info("DRY_RUN: Would stage '%s' -> '%s'", link, target_file)
            continue
        # Replace the symlink with a writable copy of the target file.
        try:
            os.remove(link)
            # Copy file to the symlink location.
            shutil.copy2(target_file, link)
            # Make the file writable.
            os.chmod(link, 0o644)
            _LOG.info("Staged: %s -> %s", link, target_file)
        except Exception as e:
            _LOG.error("Error staging link %s: %s", link, e)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    parser.add_argument(
        "--dst_dir", required=True, help="Destination directory."
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Report what would be done without touching the filesystem.",
    )
    args = parser.parse_args()
    symlinks = find_symlinks(args.dst_dir)
    if not symlinks:
        _LOG.info("No symbolic links found to stage")
        return
    table = build_status_table(symlinks)
    _LOG.info("\n%s", str(table))
    stage_links(symlinks, dry_run=args.dry_run)
    action_verb = "DRY_RUN: Would stage" if args.dry_run else "Staged"
    _LOG.info("%s %s files for modification", action_verb, len(symlinks))


if __name__ == "__main__":
    main()
