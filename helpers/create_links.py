"""
Import as:

import helpers.create_links as hcrelink
"""

import argparse
import filecmp
import logging
import os
from typing import List, Tuple

_LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def find_common_files(src_dir: str, dst_dir: str) -> List[Tuple[str, str]]:
    """
    Find files with the same name and content in both directories.

    The function iterates through all files in the `src_dir` and finds matching
    files in `dst_dir` based on their name and content. The matches are returned
    as the file paths from both directories.

    :param src_dir: The source directory containing the original files
    :param dst_dir: The destination directory to compare files against

    :return: paths of matching files from `src_dir` and `dst_dir`
    """
    common_files = []
    for root, _, files in os.walk(src_dir):
        for file in files:
            src_file = os.path.join(root, file)
            dst_file = os.path.join(dst_dir, os.path.relpath(src_file, src_dir))
            # Check if the file exists in the destination folder.
            if not os.path.exists(dst_file):
                _LOG.warning(
                    f"Warning: {dst_file} is missing in the destination directory."
                )
                continue
            # Compare file contents.
            if filecmp.cmp(src_file, dst_file, shallow=False):
                common_files.append((src_file, dst_file))
            else:
                _LOG.warning(
                    f"Warning: {dst_file} and {src_file} have different content."
                )
    return common_files


def replace_with_links(common_files: List[Tuple[str, str]]) -> None:
    """
    Replace matching files in the destination directory with symbolic links.

    For each pair of matching files, the file in `dst_dir` is replaced by a
    symbolic link pointing to the corresponding file in `src_dir`. The symbolic
    links are set to read-only to prevent accidental modifications.

    :param common_files: matching file paths from `src_dir` and `dst_dir`
    """
    for src_file, dst_file in common_files:
        # Ensure the destination directory exists.
        dst_dir = os.path.dirname(dst_file)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
            _LOG.info(f"Created destination directory: {dst_dir}")
        # Remove existing file or link in the destination path.
        if os.path.exists(dst_file) or os.path.islink(dst_file):
            try:
                os.remove(dst_file)
            except Exception as e:
                _LOG.error(f"Error removing {dst_file}: {e}")
                continue
        # Ensure src_file exists before creating a symlink.
        if not os.path.exists(src_file):
            _LOG.error(f"Error: Source file does not exist: {src_file}")
            continue
        # Create a symbolic link from the source to the destination.
        try:
            absolute_src_file = os.path.abspath(
                src_file
            )  # Use absolute path for src_file.
            os.symlink(absolute_src_file, dst_file)
            # Make the link read-only.
            os.chmod(dst_file, 0o444)
            _LOG.info(f"Created symlink: {dst_file} -> {absolute_src_file}")
        except Exception as e:
            _LOG.error(f"Error creating symlink for {dst_file}: {e}")


def main() -> None:
    """
    Entry point for the script to manage symbolic links between directories.

    Depending on the command-line arguments, this script either:

    - Replaces matching files in `dst_dir` with symbolic links to `src_dir`.
    - Stages all symbolic links in `dst_dir` for modification by replacing them
      with writable file copies.

    Usage:
    - `--replace_links`: Replace files with symbolic links
    - `--stage_links`: Replace symbolic links with writable file copies

    :return: None
    """
    parser = argparse.ArgumentParser(
        description="Manage symbolic links between src_dir and dst_dir."
    )
    parser.add_argument("--src_dir", required=True, help="Source directory.")
    parser.add_argument("--dst_dir", required=True, help="Destination directory.")
    parser.add_argument(
        "--replace_links",
        action="store_true",
        help="Replace files with symbolic links.",
    )
    args = parser.parse_args()
    if args.replace_links:
        common_files = find_common_files(args.src_dir, args.dst_dir)
        replace_with_links(common_files)
        _LOG.info(f"Replaced {len(common_files)} files with symbolic links.")


if __name__ == "__main__":
    main()


"""

Usage Example:

Step 1: Replace files in dst_dir with links from src_dir:

    - python3 create_links.py --src_dir /path/to/src --dst_dir /path/to/dst --replace_links

Step 2: Stage linked files for modification:

    - python3 stage_linked_file.py --src_dir /path/to/src --dst_dir /path/to/dst --stage_links

Step 3: After modification, restore the symbolic links:

    - python3 create_links.py --src_dir /path/to/src --dst_dir /path/to/dst --replace_links

"""
