#!/usr/bin/env python3

r"""
Copy files or directories from one client directory to another.

Copies files and directories from `dir1` to `dir2`:
- If a source file doesn't exist, the destination file is deleted.
- For directories in the input list, rsync is used to sync them.
- For files in the input list, they are copied with cp.

Files and directories are interpreted as relative to `dir1` and `dir2`.

Examples:

Copy specific files:
> copy_across_clients.py \
    --dir1 /path/to/client1 \
    --dir2 /path/to/client2 \
    --files file1.txt file2.py

Copy files and directories from a list file:
> copy_across_clients.py \
    --dir1 /path/to/client1 \
    --dir2 /path/to/client2 \
    --from_file files.txt

Dry run to see what would be done:
> copy_across_clients.py \
    --dir1 /path/to/client1 \
    --dir2 /path/to/client2 \
    --files subdir1 file1.txt \
    --dry_run

Import as:

import dev_scripts_helpers.coding_tools.copy_across_clients as dscoac
"""

import argparse
import logging
import os
from typing import List

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# #############################################################################
# Helpers
# #############################################################################


def _get_files_to_copy(args: argparse.Namespace) -> List[str]:
    """
    Get the list of files to copy based on command line arguments.

    :param args: Parsed arguments
    :return: List of file paths relative to source directory
    """
    if args.files:
        # Files specified directly on command line.
        return args.files
    elif args.from_file:
        # Read files from a file.
        hdbg.dassert_path_exists(args.from_file)
        content = hio.from_file(args.from_file)
        files = [line.strip() for line in content.split("\n") if line.strip()]
        return files
    elif args.dir:
        # Copy entire directory.
        return ["."]
    else:
        # This should never happen since argparse enforces mutually_exclusive_group.
        raise ValueError("No files specified")


def _copy_files(
    src_dir: str,
    dst_dir: str,
    files: List[str],
    *,
    dry_run: bool = False,
) -> None:
    """
    Copy files from `src_dir` to `dst_dir`.

    If a source file doesn't exist, the destination file is deleted.
    Directories are synced using rsync.

    :param src_dir: Source directory
    :param dst_dir: Destination directory
    :param files: List of files to copy (relative paths)
    :param dry_run: If True, show what would be done without doing it
    """
    _LOG.debug(
        "Copying %d files from '%s' to '%s'", len(files), src_dir, dst_dir
    )
    for file_path in files:
        src_file = os.path.join(src_dir, file_path)
        dst_file = os.path.join(dst_dir, file_path)
        # Handle source file that doesn't exist.
        if not os.path.exists(src_file):
            if os.path.exists(dst_file):
                # Delete destination file since source doesn't exist.
                action = f"rm '{dst_file}'"
                if dry_run:
                    _LOG.info("[DRY RUN] %s", action)
                else:
                    _LOG.info("Deleting: '%s'", dst_file)
                    os.remove(dst_file)
            else:
                _LOG.info("Skipping: source '%s' doesn't exist", src_file)
            continue
        # Handle directory with rsync.
        if os.path.isdir(src_file):
            # Ensure destination directory exists.
            hio.create_dir(dst_file, incremental=True)
            cmd_parts = ["rsync", "-av"]
            if dry_run:
                cmd_parts.append("--dry-run")
            cmd_parts.append(f"{src_file}/")
            cmd_parts.append(dst_file)
            cmd = " ".join(cmd_parts)
            if dry_run:
                _LOG.info("[DRY RUN] %s", cmd)
            else:
                _LOG.info("Running: %s", cmd)
                hsystem.system(cmd)
        # Copy file.
        elif os.path.isfile(src_file):
            # Create destination directory if needed.
            dst_file_dir = os.path.dirname(dst_file)
            if dry_run:
                _LOG.info("[DRY RUN] cp '%s' '%s'", src_file, dst_file)
            else:
                # TODO(gp): Maybe use the library for speed.
                hio.create_dir(dst_file_dir, incremental=True)
                cmd = f"cp '{src_file}' '{dst_file}'"
                hsystem.system(cmd)
                _LOG.info("Copied: '%s' -> '%s'", src_file, dst_file)
        else:
            _LOG.warning("Source is neither file nor directory: '%s'", src_file)


# #############################################################################
# Parser
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # Required arguments.
    parser.add_argument(
        "--dir1",
        action="store",
        required=True,
        help="First client directory",
    )
    parser.add_argument(
        "--dir2",
        action="store",
        required=True,
        help="Second client directory",
    )
    # Mutually exclusive group for what to copy.
    copy_group = parser.add_mutually_exclusive_group(required=True)
    copy_group.add_argument(
        "--files",
        nargs="+",
        help="List of files and/or directories to copy (relative paths)",
    )
    copy_group.add_argument(
        "--from_file",
        action="store",
        help="File containing list of file/directory paths to copy (one per line)",
    )
    copy_group.add_argument(
        "--dir",
        action="store_true",
        help="Copy entire directory from dir1 to dir2",
    )
    # Optional arguments.
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Show what would be done without doing it",
    )
    hparser.add_verbosity_arg(parser)
    return parser


# #############################################################################
# Main
# #############################################################################


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Validate directories exist.
    hdbg.dassert_dir_exists(args.dir1)
    hdbg.dassert_dir_exists(args.dir2)
    dir1 = os.path.abspath(args.dir1)
    dir2 = os.path.abspath(args.dir2)
    _LOG.info("Source directory: '%s'", dir1)
    _LOG.info("Destination directory: '%s'", dir2)
    # Copy files and directories.
    files = _get_files_to_copy(args)
    _LOG.info("Copying %d items", len(files))
    _copy_files(dir1, dir2, files, dry_run=args.dry_run)
    _LOG.info("Done")


if __name__ == "__main__":
    _main(_parse())
