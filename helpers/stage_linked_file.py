"""
Import as:

import helpers.stage_linked_file as hstlifil
"""

import argparse
import logging
import os
import shutil
from typing import List

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


def stage_links(symlinks: List[str]) -> None:
    """
    Replace symbolic links with writable copies of the linked files.

    :param symlinks: List of symbolic links to replace.
    """
    for link in symlinks:
        # Resolve the original file the symlink points to.
        target_file = os.readlink(link)
        if not os.path.exists(target_file):
            _LOG.warning(
                f"Warning: Target file does not exist for link {link} -> {target_file}"
            )
            continue
        # Replace the symlink with a writable copy of the target file.
        try:
            os.remove(link)
            # Copy file to the symlink location.
            shutil.copy2(target_file, link)
            # Make the file writable.
            os.chmod(link, 0o644)
            _LOG.info(f"Staged: {link} -> {target_file}")
        except Exception as e:
            _LOG.error(f"Error staging link {link}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Stage symbolic links for modification."
    )
    parser.add_argument("--dst_dir", required=True, help="Destination directory.")
    args = parser.parse_args()

    symlinks = find_symlinks(args.dst_dir)
    if not symlinks:
        _LOG.info("No symbolic links found to stage.")
        return
    stage_links(symlinks)
    _LOG.info(f"Staged {len(symlinks)} files for modification.")


if __name__ == "__main__":
    main()

"""
Usage

    - python3 stage_linked_file.py --dst_dir /path/to/dst

"""
