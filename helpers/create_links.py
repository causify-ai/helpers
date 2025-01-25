"""
Usage Example:

- Using absolute links

    Step 1: Replace files in dst_dir with links from src_dir:

        > create_links.py --src_dir /path/to/src --dst_dir /path/to/dst --replace_links

    Step 2: Stage linked files for modification:

        > create_links.py --src_dir /path/to/src --dst_dir /path/to/dst --stage_links

    Step 3: After modification, restore the symbolic links:

        > create_links.py --src_dir /path/to/src --dst_dir /path/to/dst --replace_links

- Using relative links

    > create_links.py --src_dir /path/to/src --dst_dir /path/to/dst --replace_links --use_relative_paths

    - Other steps remain same.

Import as:

import helpers.create_links as hcrelink
"""

import argparse
import filecmp
import logging
import os
import shutil
import stat
from typing import List, Tuple

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

# #############################################################################


def _main(parser: argparse.ArgumentParser) -> None:
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
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    if args.replace_links:
        common_files = _find_common_files(args.src_dir, args.dst_dir)
        _replace_with_links(
            common_files, use_relative_paths=args.use_relative_paths
        )
        _LOG.info("Replaced %d files with symbolic links.", len(common_files))
    elif args.stage_links:
        symlinks = _find_symlinks(args.dst_dir)
        if not symlinks:
            _LOG.info("No symbolic links found to stage.")
        _stage_links(symlinks)
        _LOG.info("Staged %d symbolic links for modification.", len(symlinks))
    else:
        _LOG.error("You must specify either --replace_links or --stage_links.")


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments.

    :return: Argument parser object.
    """
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--src_dir", required=True, help="Source directory.")
    parser.add_argument("--dst_dir", required=True, help="Destination directory.")
    parser.add_argument(
        "--replace_links",
        action="store_true",
        help="Replace files with symbolic links.",
    )
    parser.add_argument(
        "--stage_links",
        action="store_true",
        help="Replace symbolic links with writable copies.",
    )
    parser.add_argument(
        "--use_relative_paths",
        action="store_true",
        help="Use relative paths for symbolic links instead of absolute paths.",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _find_common_files(src_dir: str, dst_dir: str) -> List[Tuple[str, str]]:
    """
    Find common files in dst_dir and change to links.

    If a destination dir is not found, the functions makes a dest dir and copies all files from
    source to destination after users approval. All matching files are identified based on their
    name and content. The matches are returned as the file paths from both directories.

    :param src_dir: The source directory containing the original files
    :param dst_dir: The destination directory to compare files against
    :return: paths of matching files from `src_dir` and `dst_dir`
    """
    # Ensure the destination directory exists; create it if it doesn't.
    if not os.path.exists(dst_dir):
        user_input = input(
            "Destination directory %s does not exist. Would you like to create copy all files from source? (y/n): "
        )
        if user_input.lower() == "y":
            hio.create_dir(
                dir_name=dst_dir,
                incremental=True,
                abort_if_exists=True,
                ask_to_delete=False,
                backup_dir_if_exists=False,
            )
            _LOG.info("Created destination directory: %s", dst_dir)
            for root, _, files in os.walk(src_dir):
                for file in files:
                    src_file = os.path.join(root, file)
                    dst_file = os.path.join(
                        dst_dir, os.path.relpath(src_file, src_dir)
                    )
                    dst_file_dir = os.path.dirname(dst_file)
                    # Ensure the destination file directory exists.
                    if not os.path.exists(dst_file_dir):
                        os.makedirs(dst_file_dir)
                        _LOG.info("Created subdirectory: %s", dst_file_dir)
                    # Copy the file from source to destination.
                    shutil.copy2(src_file, dst_file)
                    _LOG.info("Copied file: %s -> %s", src_file, dst_file)
        else:
            _LOG.error(
                "Destination directory %s not created. Exiting function.",
                dst_dir,
            )
            return []
    # After copying files, continue with comparing files.
    common_files = []
    for root, _, files in os.walk(src_dir):
        for file in files:
            src_file = os.path.join(root, file)
            dst_file = os.path.join(dst_dir, os.path.relpath(src_file, src_dir))
            # Check if the file exists in the destination folder.
            # Certain files do not need to be copied, so we skip them.
            if not os.path.exists(dst_file):
                _LOG.warning(
                    "Warning: %s is missing in the destination directory.",
                    dst_file,
                )
                continue
            # Compare file contents after copying.
            if filecmp.cmp(src_file, dst_file, shallow=False):
                _LOG.info(
                    "Files are the same and will be replaced: %s -> %s",
                    src_file,
                    dst_file,
                )
                common_files.append((src_file, dst_file))
            else:
                _LOG.warning(
                    "Warning: %s and %s have different content.",
                    dst_file,
                    src_file,
                )
    return common_files


def _replace_with_links(
    common_files: List[Tuple[str, str]],
    use_relative_paths: bool,
    *,
    abort_on_first_error: bool = False,
) -> None:
    """
    Replace matching files in the destination directory with symbolic links.

    :param common_files: Matching file paths from `src_dir` and `dst_dir`
    :param use_relative_paths: If True, create relative symlinks; if False, use absolute paths.
    :param abort_on_first_error: If True, abort on the first error; if False, continue processing
    """
    for src_file, dst_file in common_files:
        try:
            hdbg.dassert_file_exists(src_file)
        except FileNotFoundError as e:
            _LOG.error("Error: %s", str(e))
            if abort_on_first_error:
                _LOG.error("Aborting: Source file %s doesn't exist.", src_file)
            continue
        if os.path.exists(dst_file):
            os.remove(dst_file)
        try:
            if use_relative_paths:
                link_target = os.path.relpath(src_file, os.path.dirname(dst_file))
            else:
                link_target = os.path.abspath(src_file)
            os.symlink(link_target, dst_file)
            # Remove write permissions from the file to prevent accidental
            # modifications.
            current_permissions = os.stat(dst_file).st_mode
            new_permissions = (
                current_permissions
                & ~stat.S_IWUSR
                & ~stat.S_IWGRP
                & ~stat.S_IWOTH
            )
            os.chmod(dst_file, new_permissions)
            _LOG.info("Created symlink: %s -> %s", dst_file, link_target)
        except Exception as e:
            _LOG.error("Error creating symlink for %s: %s", dst_file, e)
            if abort_on_first_error:
                _LOG.warning(
                    "Aborting: Failed to create symlink for %s.", dst_file
                )
            continue


def _find_symlinks(dst_dir: str) -> List[str]:
    """
    Find all symbolic links in the destination directory.

    :param dst_dir: Directory to search for symbolic links
    :return: List of paths to symbolic links
    """
    symlinks = []
    for root, _, files in os.walk(dst_dir):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.islink(file_path):
                symlinks.append(file_path)
    return symlinks


def _stage_links(symlinks: List[str]) -> None:
    """
    Replace symbolic links with writable copies of the linked files.

    :param symlinks: List of symbolic links to replace.
    """
    for link in symlinks:
        # Resolve the original file the symlink points to.
        target_file = os.readlink(link)
        if not os.path.exists(target_file):
            _LOG.warning(
                "Warning: Target file does not exist for link %s -> %s",
                link,
                target_file,
            )
            continue
        # Replace the symlink with a writable copy of the target file.
        try:
            os.remove(link)
            # Copy file to the symlink location.
            shutil.copy2(target_file, link)
            # Make the file writable to allow for modifications.
            current_permissions = os.stat(link).st_mode
            new_permissions = (
                current_permissions | stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH
            )
            os.chmod(link, new_permissions)
            _LOG.info("Staged: %s -> %s", link, target_file)
        except Exception as e:
            _LOG.error("Error staging link %s: %s", link, e)


if __name__ == "__main__":
    _main(_parse())
