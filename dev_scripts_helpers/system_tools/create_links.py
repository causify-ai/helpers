#!/usr/bin/env python3
"""
This tool allows to handle sets of links to files that are shared across many
dirs.

A detailed description is:

> docs/tools/dev_system/all.replace_common_files_with_script_links.md

# Usage Example

- Step 1: Replace files in `dst_dir` with links from `src_dir`:
> create_links.py --src_dir $SRC_DIR --dst_dir $DST_DIR --replace_links

- Step 2: Stage linked files for modification (e.g., make a copy of all the
  links so that they can be modified in place):
> create_links.py --src_dir $SRC_DIR --stage_links

- Step 3: After modification, restore the symbolic links:
> create_links.py --src_dir $SRC_DIR --dst_dir $DST_DIR --replace_links

- Links can be absolute or relative (using `--replace_links --link_type
  absolute`)

- Use `--dry_run` to only report which files would be replaced or staged,
  without touching the filesystem

- Example: `msml610/tutorials/L12_reinforcement_learning` was copied from
  `class_project/project_template`:
> create_links.py --src_dir class_project/project_template --dst_dir msml610/tutorials/L12_reinforcement_learning --replace_links

- Example: find files in `msml610/tutorials/L03_knowledge_representation` that
  are the same as in `class_project/project_template`, without modifying
  anything:
> create_links.py --src_dir class_project/project_template --dst_dir msml610/tutorials/L03_knowledge_representation --replace_links --dry_run

Import as:

import helpers.create_links as hcrelink
"""

import argparse
import filecmp
import logging
import os
import shutil
import stat
from typing import List, Set, Tuple

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.htable as htable

_LOG = logging.getLogger(__name__)


def _classify_files(src_dir: str, dst_dir: str) -> List[Tuple[str, str, str]]:
    """
    Classify every file under `src_dir` and `dst_dir` by content.

    :param src_dir: source directory
    :param dst_dir: destination directory
    :return: list of `(src_file, dst_file, current_state)`, where
        `current_state` is one of:
        - "link": `dst_file` is already a symlink pointing to `src_file`
        - "copy": the file is identical in both directories, but `dst_file`
          is a regular file (not yet a symlink to `src_file`)
        - "diff": the file exists in both directories with different content
        - "missing": the file exists only in `src_dir`
        - "extra": the file exists only in `dst_dir`
        `src_file`/`dst_file` are always the joined paths (i.e., they are
        reported even when the file does not exist on that side)
    """

    def _list_rel_paths(dir_name: str) -> Set[str]:
        rel_paths: Set[str] = set()
        for root, _, files in os.walk(dir_name):
            for file_name in files:
                path = os.path.join(root, file_name)
                rel_paths.add(os.path.relpath(path, dir_name))
        return rel_paths

    src_rel_paths = _list_rel_paths(src_dir)
    dst_rel_paths = _list_rel_paths(dst_dir)
    rows: List[Tuple[str, str, str]] = []
    for rel_path in sorted(src_rel_paths | dst_rel_paths):
        src_file = os.path.join(src_dir, rel_path)
        dst_file = os.path.join(dst_dir, rel_path)
        if rel_path in src_rel_paths and rel_path in dst_rel_paths:
            if os.path.islink(dst_file) and os.path.realpath(
                dst_file
            ) == os.path.realpath(src_file):
                # `dst_file` is already a symlink to `src_file`: nothing to
                # do.
                current_state = "link"
            elif filecmp.cmp(src_file, dst_file, shallow=False):
                current_state = "copy"
            else:
                current_state = "diff"
        elif rel_path in src_rel_paths:
            current_state = "missing"
        else:
            current_state = "extra"
        rows.append((src_file, dst_file, current_state))
    return rows


def _build_status_table(src_dir: str, dst_dir: str) -> htable.Table:
    """
    Build a table summarizing what `--replace_links` would do.

    :param src_dir: source directory
    :param dst_dir: destination directory
    :return: table with columns `src_file`, `dst_file`, `current_state`,
        `target_state` (`target_state` is "link" for a file that would be
        turned into a symlink, "-" otherwise); `src_file`/`dst_file` report
        only the basename, since the caller prints the shared `src_dir`/
        `dst_dir` prefix once above the table
    """
    column_names = ["src_file", "dst_file", "current_state", "target_state"]
    rows = []
    for src_file, dst_file, current_state in _classify_files(src_dir, dst_dir):
        target_state = "link" if current_state == "copy" else "-"
        if current_state == "missing":
            src_file = os.path.basename(src_file)
            dst_file = "-"
        elif current_state == "extra":
            src_file = "-"
            dst_file = os.path.basename(dst_file)
        else:
            src_file = os.path.basename(src_file)
            dst_file = os.path.basename(dst_file)
        rows.append([src_file, dst_file, current_state, target_state])
    return htable.Table(rows, column_names)


def _find_common_files(
    src_dir: str, dst_dir: str, *, dry_run: bool = False
) -> List[Tuple[str, str]]:
    """
    Find common files in dst_dir and change to links.

    If a destination dir is not found, the functions makes a dest dir and copies all files from
    source to destination after users approval. All matching files are identified based on their
    name and content. The matches are returned as the file paths from both directories.

    :param src_dir: The source directory containing the original files
    :param dst_dir: The destination directory to compare files against
    :param dry_run: If True, only report what would be done without
        creating `dst_dir` or copying any file
    :return: paths of matching files from `src_dir` and `dst_dir`
    """
    # Ensure the destination directory exists; create it if it doesn't.
    if not os.path.exists(dst_dir):
        if dry_run:
            _LOG.warning(
                "DRY_RUN: '%s' does not exist, skipping",
                dst_dir,
            )
            return []
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
    common_files: List[Tuple[str, str]] = []
    for src_file, dst_file, current_state in _classify_files(src_dir, dst_dir):
        if current_state == "copy":
            _LOG.debug("'%s' matches '%s'", src_file, dst_file)
            common_files.append((src_file, dst_file))
        elif current_state == "diff":
            _LOG.warning(
                "'%s' and '%s' have different content", dst_file, src_file
            )
        elif current_state == "missing":
            _LOG.warning(
                "'%s' is missing in the destination directory", dst_file
            )
        # "extra": file only in `dst_dir`, nothing to do for `--replace_links`.
    return common_files


def _replace_with_links(
    common_files: List[Tuple[str, str]],
    link_type: str,
    *,
    dry_run: bool = False,
    abort_on_first_error: bool = False,
) -> None:
    """
    Replace matching files in the destination directory with symbolic links.

    :param common_files: Matching file paths from `src_dir` and `dst_dir`
    :param link_type: Type of symlink paths: "absolute" or "relative"
    :param dry_run: If True, only report which files would be replaced with
        symlinks without touching the filesystem
    :param abort_on_first_error: If True, abort on the first error; if False, continue processing
    """
    hdbg.dassert_in(link_type, ("relative", "absolute"))
    for src_file, dst_file in common_files:
        try:
            hdbg.dassert_file_exists(src_file)
        except FileNotFoundError as e:
            _LOG.error("Error: %s", str(e))
            if abort_on_first_error:
                _LOG.error("Aborting: Source file %s doesn't exist.", src_file)
            continue
        if link_type == "relative":
            link_target = os.path.relpath(src_file, os.path.dirname(dst_file))
        else:
            link_target = os.path.abspath(src_file)
        if dry_run:
            _LOG.info(
                "DRY_RUN: Would create symlink '%s' -> '%s'",
                dst_file,
                link_target,
            )
            continue
        if os.path.exists(dst_file):
            os.remove(dst_file)
        try:
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


def _find_symlinks(dir_name: str) -> List[str]:
    """
    Find all symbolic links under the given directory.

    :param dir_name: directory to search for symbolic links
    :return: List of paths to symbolic links
    """
    symlinks = []
    for root, _, files in os.walk(dir_name):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.islink(file_path):
                symlinks.append(file_path)
    return symlinks


def _build_stage_status_table(symlinks: List[str]) -> htable.Table:
    """
    Build a table summarizing what `--stage_links` would do.

    :param symlinks: list of symbolic links to stage
    :return: table with columns `link`, `target_file`, `current_state`,
        `target_state` (`target_state` is "copy" for a link that would be
        staged, "-" if its target is missing); `link`/`target_file` report
        only the basename, since the caller prints the shared `dst_dir`
        prefix once above the table
    """
    column_names = ["link", "target_file", "current_state", "target_state"]
    rows = []
    for link in symlinks:
        target_file = os.readlink(link)
        if not os.path.isabs(target_file):
            target_file = os.path.join(os.path.dirname(link), target_file)
        if os.path.exists(target_file):
            current_state = "link"
            target_state = "copy"
        else:
            current_state = "missing"
            target_state = "-"
        rows.append(
            [
                os.path.basename(link),
                os.path.basename(target_file),
                current_state,
                target_state,
            ]
        )
    return htable.Table(rows, column_names)


def _stage_links(symlinks: List[str], *, dry_run: bool = False) -> None:
    """
    Replace symbolic links with writable copies of the linked files.

    :param symlinks: List of symbolic links to replace.
    :param dry_run: If True, only report which symlinks would be staged without
        touching the filesystem
    """
    for link in symlinks:
        # Resolve the original file the symlink points to.
        target_file = os.readlink(link)
        if not os.path.isabs(target_file):
            target_file = os.path.join(os.path.dirname(link), target_file)
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
            # Make the file writable to allow for modifications.
            current_permissions = os.stat(link).st_mode
            new_permissions = (
                current_permissions | stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH
            )
            os.chmod(link, new_permissions)
            _LOG.info("Staged: %s -> %s", link, target_file)
        except Exception as e:
            _LOG.error("Error staging link %s: %s", link, e)


# #############################################################################


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Entry point for the script to manage symbolic links between directories.

    Depending on the command-line arguments, this script either:

    - Replaces matching files in `dst_dir` with symbolic links to `src_dir`.
    - Stages all symbolic links under `src_dir` for modification by replacing
      them with writable file copies.

    Usage:
    - `--replace_links`: Replace files with symbolic links
    - `--stage_links`: Replace symbolic links with writable file copies
    - `--dry_run`: Report what would be done without touching the filesystem
    :return: None
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    if args.replace_links:
        # `--replace_links` turns files common to `src_dir` and `dst_dir`
        # into symlinks, so both directories are needed.
        hdbg.dassert_ne(
            args.dst_dir, "", "Must specify --dst_dir for --replace_links"
        )
        common_files = _find_common_files(
            args.src_dir, args.dst_dir, dry_run=args.dry_run
        )
        table = _build_status_table(args.src_dir, args.dst_dir)
        _LOG.info(
            "\nsrc_dir=%s\ndst_dir=%s\n\n%s",
            args.src_dir,
            args.dst_dir,
            str(table),
        )
        _replace_with_links(
            common_files, link_type=args.link_type, dry_run=args.dry_run
        )
        action_verb = "DRY_RUN: Would replace" if args.dry_run else "Replaced"
        _LOG.info(
            "%s %d files with symbolic links", action_verb, len(common_files)
        )
    elif args.stage_links:
        # `--stage_links` only stages the symlinks under `src_dir` (no
        # `dst_dir` involved), replacing them with writable copies.
        symlinks = _find_symlinks(args.src_dir)
        if not symlinks:
            _LOG.info("No symbolic links found to stage")
        else:
            table = _build_stage_status_table(symlinks)
            _LOG.info("\nsrc_dir=%s\n\n%s", args.src_dir, str(table))
        _stage_links(symlinks, dry_run=args.dry_run)
        action_verb = "DRY_RUN: Would stage" if args.dry_run else "Staged"
        _LOG.info(
            "%s %d symbolic links for modification", action_verb, len(symlinks)
        )
    else:
        _LOG.error("You must specify either --replace_links or --stage_links")


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments.

    :return: Argument parser object.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    parser.add_argument("--src_dir", required=True, help="Source directory.")
    parser.add_argument(
        "--dst_dir",
        default="",
        help="Destination directory (required for --replace_links).",
    )
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
        "--link_type",
        choices=["absolute", "relative"],
        default="relative",
        help='Type of symbolic link paths: "absolute" or "relative"',
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Report what would be done without touching the filesystem.",
    )
    hparser.add_verbosity_arg(parser)
    return parser


if __name__ == "__main__":
    _main(_parse())
