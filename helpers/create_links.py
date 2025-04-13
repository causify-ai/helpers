#!/usr/bin/env python

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


def _find_common_files(src_dir: str, dst_dir: str) -> List[Tuple[str, str]]:
    """
    Find common files in dst_dir and change to links.

    If a destination dir is not found, the functions makes a dest dir and copies
    all files from source to destination after users approval. All matching
    files are identified based on their name and content. The matches are
    returned as the file paths from both directories.

    :param src_dir: The source directory containing the original files
    :param dst_dir: The destination directory to compare files against
    :return: paths of matching files from `src_dir` and `dst_dir`
    """
    # # Ensure the destination directory exists; create it if it doesn't.
    # if not os.path.exists(dst_dir):
    #     user_input = input(
    #         "Destination directory %s does not exist. Would you like to create copy all files from source? (y/n): "
    #     )
    #     if user_input.lower() == "y":
    #         hio.create_dir(
    #             dir_name=dst_dir,
    #             incremental=True,
    #             abort_if_exists=True,
    #             ask_to_delete=False,
    #             backup_dir_if_exists=False,
    #         )
    #         _LOG.info("Created destination directory: %s", dst_dir)
    #         for root, _, files in os.walk(src_dir):
    #             for file in files:
    #                 src_file = os.path.join(root, file)
    #                 dst_file = os.path.join(
    #                     dst_dir, os.path.relpath(src_file, src_dir)
    #                 )
    #                 dst_file_dir = os.path.dirname(dst_file)
    #                 # Ensure the destination file directory exists.
    #                 if not os.path.exists(dst_file_dir):
    #                     os.makedirs(dst_file_dir)
    #                     _LOG.info("Created subdirectory: %s", dst_file_dir)
    #                 # Copy the file from source to destination.
    #                 shutil.copy2(src_file, dst_file)
    #                 _LOG.info("Copied file: %s -> %s", src_file, dst_file)
    #     else:
    #         _LOG.error(
    #             "Destination directory %s not created. Exiting function.",
    #             dst_dir,
    #         )
    #         return []
    # After copying files, continue with comparing files.
    common_files = []
    for root, _, files in os.walk(src_dir):
        for file in files:
            src_file = os.path.join(root, file)
            dst_file = os.path.join(dst_dir, os.path.relpath(src_file, src_dir))
            # Check if the file exists in the destination folder.
            if not os.path.exists(dst_file):
                _LOG.debug(
                    "File %s is missing in the destination directory",
                    dst_file,
                )
                continue
            # Check if the file is a symbolic link.
            if os.path.islink(dst_file):
                _LOG.debug(
                    "File %s is a symbolic link",
                    dst_file,
                )
                continue
            # Compare file contents.
            if filecmp.cmp(src_file, dst_file, shallow=False):
                _LOG.debug(
                    "Files src_file=%s, dst_file=%s are the same",
                    src_file,
                    dst_file,
                )
                common_files.append((src_file, dst_file))
            else:
                _LOG.debug(
                    "Files src_file=%s, dst_file=%s are not the same",
                    src_file,
                    dst_file,
                )
    return common_files


def _create_single_link(src_file: str, dst_file: str, use_relative_paths: bool, abort_on_first_error: bool) -> None:
    """
    Create a single symbolic link from dst_file to src_file.

    :param src_file: Source file path
    :param dst_file: Destination file path where symlink will be created
    :param use_relative_paths: If True, create relative symlinks; if False, use absolute paths
    :param abort_on_first_error: If True, abort on the first error; if False, continue processing
    """
    hdbg.dassert_file_exists(src_file)
    hdbg.dassert_file_exists(dst_file)
    # Remove the destination file.
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
        _LOG.debug("Created symlink: %s -> %s", dst_file, link_target)
    except Exception as e:
        msg = "Failed to create symlink %s -> %s with error %s" % (dst_file, link_target, str(e))
        if abort_on_first_error:
            raise RuntimeError(msg)
        else:
            _LOG.warning(msg)


def _replace_with_links(
    common_files: List[Tuple[str, str]],
    use_relative_paths: bool,
    *,
    abort_on_first_error: bool = False,
    dry_run: bool = False,
) -> None:
    """
    Replace matching files in the destination directory with symbolic links.

    :param common_files: Matching file paths from `src_dir` and `dst_dir`
    :param use_relative_paths: If True, create relative symlinks; if False, use
        absolute paths.
    :param abort_on_first_error: If True, abort on the first error; if False,
        continue processing
    :param dry_run: If True, print what will be done without actually doing it.
    """
    for src_file, dst_file in common_files:

        _create_single_link(src_file, dst_file, use_relative_paths, abort_on_first_error)


# #############################################################################


def _find_symlinks(dst_dir: str) -> List[str]:
    """
    Find all symbolic links in the destination directory.

    :param dst_dir: Directory to search for symbolic links
    :return: List of absolute paths to symbolic links
    """
    dst_dir = os.path.abspath(dst_dir)
    hdbg.dassert_dir_exists(dst_dir)
    symlinks = []
    for root, _, files in os.walk(dst_dir):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.islink(file_path):
                symlinks.append(file_path)
    return symlinks
        

def _stage_single_link(link: str, target_file: str, abort_on_first_error: bool, dry_run: bool) -> None:
    """
    Replace a single symlink with a writable copy of the linked file.

    :param link: The symlink to replace.
    :param target_file: The file to copy to the symlink location.
    :param abort_on_first_error: If True, abort on the first error; if False,
        continue processing
    :param dry_run: If True, print what will be done without actually doing it.
    """
    # Resolve the original file the symlink points to.
    target_file = os.readlink(link)
    if not os.path.exists(target_file):
        msg = "Target file does not exist for link %s -> %s" % (link, target_file)
        if abort_on_first_error:
            raise RuntimeError(msg)
        else:
            _LOG.warning(msg)
        return
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
        _LOG.debug("Staged: %s -> %s", link, target_file)
    except Exception as e:
        msg = "Error staging link %s: %s" % (link, str(e))
        if abort_on_first_error:
            raise RuntimeError(msg)
        else:
            _LOG.warning(msg)


def _stage_links(symlinks: List[str], abort_on_first_error: bool, dry_run: bool) -> None:
    """
    Replace symbolic links with writable copies of the linked files.

    :param symlinks: List of symbolic links to replace.
    """
    for link in symlinks:
        _stage_single_link(link, abort_on_first_error, dry_run)



# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--src_dir", required=True, help="Source directory.")
    parser.add_argument("--dst_dir", required=True, help="Destination directory.")
    parser.add_argument(
        "--replace_links",
        action="store_true",
        help="Replace equal files with symbolic links.",
    )
    parser.add_argument(
        "--stage_links",
        action="store_true",
        help="Replace symbolic links with writable copies.",
    )
    parser.add_argument(
        "--compare_files",
        action="store_true",
        help="Compare files in the directories.",
    )
    parser.add_argument(
        "--use_relative_paths",
        action="store_true",
        help="Use relative paths for symbolic links instead of absolute paths.",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Print what will be done without actually doing it.",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    hdbg.dassert_dir_exists(args.src_dir)
    hdbg.dassert_dir_exists(args.dst_dir)
    #
    hdbg.dassert_eq(sum([args.replace_links, args.stage_links, args.compare_files]), 1, "You must specify exactly one of --replace_links, --stage_links, or --compare_files.")
    if args.compare_files:
        # Compare files.
        common_files = _find_common_files(args.src_dir, args.dst_dir)
        _LOG.info("Found %d common files.", len(common_files))
    elif args.replace_links:
        # Replace with links.
        common_files = _find_common_files(args.src_dir, args.dst_dir)
        hdbg.dassert_ne(len(symlinks), 0, "No files found to replace.")
        _replace_with_links(
            common_files, use_relative_paths=args.use_relative_paths
        )
        _LOG.info("Replaced %d files with symbolic links.", len(common_files))
    elif args.stage_links:
        # Stage links for modification.
        symlinks = _find_symlinks(args.dst_dir)
        hdbg.dassert_ne(len(symlinks), 0, "No symbolic links found to stage.")
        _stage_links(symlinks)
        _LOG.info("Staged %d symbolic links for modification.", len(symlinks))
    else:
        raise RuntimeError("Internal error")


if __name__ == "__main__":
    _main(_parse())
