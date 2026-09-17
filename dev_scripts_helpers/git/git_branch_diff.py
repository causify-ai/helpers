#!/usr/bin/env python3

"""
Diff files of the current branch against a specified point in time.

# Usage Example

- Diff modified files against the branching point using vimdiff:
> git_branch_diff.py

- Diff against `origin/master`, only in a subdirectory, only Python files:
> git_branch_diff.py --target master --subdir helpers --file_types py

Import as:

import dev_scripts_helpers.git.git_branch_diff as dsggibrd
"""

import argparse
import logging
import os
from typing import Tuple

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


def _run_or_skip(cmd: str, dry_run: bool, **kwargs) -> None:  # type: ignore
    """
    Run `cmd` via `hsystem.system()`, or skip it (with a warning) when
    `dry_run` is True.

    :param cmd: command to run
    :param dry_run: if True, only log what would have run
    :param kwargs: forwarded to `hsystem.system()`
    """
    if dry_run:
        _LOG.warning("Skipping execution of '%s'", cmd)
        return
    hsystem.system(cmd, **kwargs)


# #############################################################################
# Diffing
# #############################################################################


def _git_diff_with_branch(
    hash_: str,
    tag: str,
    #
    dir_name: str,
    subdir: str,
    #
    diff_type: str,
    file_types: str,
    skip_file_types: str,
    files_filter: str,
    from_file_filter: str,
    #
    only_print_files: bool,
    dry_run: bool,
) -> None:
    """
    Diff files from this client against files in a branch using vimdiff.

    Same parameters as `_git_branch_diff()`.
    """
    _LOG.debug(
        hprint.to_str(
            "hash_ tag dir_name diff_type subdir file_types skip_file_types"
            " files_filter from_file_filter only_print_files dry_run"
        )
    )
    # Diff only works on non-master branches to avoid comparing with itself.
    curr_branch_name = hgit.get_branch_name()
    hdbg.dassert_ne(
        curr_branch_name,
        "master",
        "Cannot diff master branch against itself",
    )
    # Retrieve the list of changed files between current state and the given
    # hash.
    cmd = []
    cmd.append("git diff")
    if diff_type:
        cmd.append(f"--diff-filter={diff_type}")
    cmd.append(f"--name-only HEAD {hash_}")
    cmd = " ".join(cmd)
    files = hsystem.system_to_files(
        cmd, dir_name, remove_files_non_present=False
    )
    files = sorted(files)
    _LOG.debug("%s", "\n".join(files))
    # Filter by specific files if requested.
    if files_filter:
        _LOG.debug("Filter by files_filter")
        _LOG.info("Before filtering files=%s", len(files))
        filter_files = files_filter.split()
        files_tmp = []
        for f in files:
            if f in filter_files:
                files_tmp.append(f)
        hdbg.dassert_lt(
            0,
            len(files_tmp),
            "No files matching files_filter='%s' in\n%s",
            files_filter,
            "\n".join(files),
        )
        files = files_tmp
        _LOG.info("After filtering by files_filter: files=%s", len(files))
        _LOG.debug("%s", "\n".join(files))
    # Filter by file list if requested.
    if from_file_filter:
        _LOG.debug("Filter by from_file_filter")
        _LOG.info("Before filtering files=%s", len(files))
        with open(from_file_filter) as f:
            filter_files = [line.strip() for line in f if line.strip()]
        files_tmp = []
        for f in files:
            if f in filter_files:
                files_tmp.append(f)
        hdbg.dassert_lt(
            0,
            len(files_tmp),
            "No files matching from_file_filter='%s' in\n%s",
            from_file_filter,
            "\n".join(files),
        )
        files = files_tmp
        _LOG.info("After filtering by from_file_filter: files=%s", len(files))
        _LOG.debug("%s", "\n".join(files))
    # Keep only files with specified extensions (useful for focusing on code
    # vs docs).
    if file_types:
        _LOG.debug("# Filter by file_types")
        _LOG.debug("Before filtering files=%s", len(files))
        extensions_lst = file_types.split(",")
        _LOG.warning(
            "Keeping files with %d extensions: %s",
            len(extensions_lst),
            extensions_lst,
        )
        files_tmp = []
        for f in files:
            if any(f.endswith(ext) for ext in extensions_lst):
                files_tmp.append(f)
        files = files_tmp
        _LOG.info("After filtering by file_types: files=%s", len(files))
        _LOG.debug("%s", "\n".join(files))
    # Exclude files with specified extensions (useful for skipping config or
    # build files).
    if skip_file_types:
        _LOG.debug("# Filter by skip_file_types")
        _LOG.debug("Before filtering files=%s", len(files))
        extensions_lst = skip_file_types.split(",")
        _LOG.warning(
            "Skipping files with %d extensions: %s",
            len(extensions_lst),
            extensions_lst,
        )
        files_tmp = []
        for f in files:
            if not any(f.endswith(ext) for ext in extensions_lst):
                files_tmp.append(f)
        files = files_tmp
        _LOG.info("After filtering by skip_file_types: files=%s", len(files))
        _LOG.debug("%s", "\n".join(files))
    # Limit diff to files within a specific subdirectory.
    if subdir != "":
        _LOG.debug("# Filter by subdir")
        _LOG.debug("Before filtering files=%s", len(files))
        files_tmp = []
        for f in files:
            if f.startswith(subdir):
                files_tmp.append(f)
        files = files_tmp
        _LOG.info("After filtering by subdir: files=%s", len(files))
        _LOG.debug("%s", "\n".join(files))
    # Summary of what will be diffed.
    _LOG.info("\n" + hprint.frame(f"# files={len(files)}"))
    _LOG.info("\n" + "\n".join(files))
    if len(files) == 0:
        _LOG.warning("No files match the filter criteria: exiting")
        return
    if only_print_files:
        _LOG.warning("Exiting as per user request with --only-print-files")
        return
    # Create temporary directory to store base versions for comparison.
    root_dir = hgit.get_repo_full_name_from_client(super_module=True)
    # TODO(gp): We should get a temp dir.
    dst_dir = f"/tmp/{root_dir}/tmp.{tag}"
    hio.create_dir(dst_dir, incremental=False)
    # Build vimdiff commands for each file, retrieving base version from
    # source hash.
    script_txt = []
    for branch_file in files:
        _LOG.debug("\n%s", hprint.frame(f"branch_file={branch_file}"))
        # Use current file as right side (what the branch currently has).
        if os.path.exists(branch_file):
            right_file = branch_file
        else:
            # For deleted files, use /dev/null as the right side.
            right_file = "/dev/null"
        # Flatten directory structure to avoid naming conflicts in temp
        # directory.
        tmp_file = branch_file
        tmp_file = tmp_file.replace("/", "_")
        tmp_file = os.path.join(dst_dir, tmp_file)
        _LOG.debug(
            "Extracting base version of %s to %s",
            branch_file,
            tmp_file,
        )
        # Extract the base version from the specified hash/branch.
        cmd = f"git show {hash_}:{branch_file} >{tmp_file}"
        rc = hsystem.system(cmd, abort_on_error=False)
        if rc != 0:
            # File is new in the branch (didn't exist in base hash).
            _LOG.debug("File '%s' is new (doesn't exist in base)", branch_file)
            left_file = "/dev/null"
        else:
            left_file = tmp_file
        # Generate vimdiff command to compare base and current versions.
        cmd = f"vimdiff {left_file} {right_file}"
        _LOG.debug("-> %s", cmd)
        script_txt.append(cmd)
    script_txt = "\n".join(script_txt)
    # Display the diff commands that will be executed.
    _LOG.info("\n%s" % hprint.frame("Diffing script"))
    _LOG.info(script_txt)
    # Create executable script for easy manual re-running.
    script_file_name = f"./tmp.vimdiff_branch_with_{tag}.sh"
    msg = f"To diff against {tag} run"
    hio.create_executable_script(script_file_name, script_txt, msg=msg)
    if dry_run:
        _LOG.warning("Skipping execution of '%s'", script_file_name)
    else:
        # Use `os.system()`, not `hsystem.system()`, since the latter pipes
        # stdout and breaks `vimdiff`'s connection to the terminal.
        os.system(script_file_name)
    # Clean up temporary files.
    cmd = f"rm -rf {dst_dir}"
    _run_or_skip(cmd, dry_run)


def _git_diff_with_branch_wrapper(
    hash_: str,
    tag: str,
    #
    dir_name: str,
    subdir: str,
    include_submodules: bool,
    #
    diff_type: str,
    file_types: str,
    skip_file_types: str,
    files_filter: str,
    from_file_filter: str,
    #
    only_print_files: bool,
    dry_run: bool,
) -> None:
    """
    Wrapper for `_git_diff_with_branch()` that handles submodules.

    Delegates to `_git_diff_with_branch()`. If include_submodules is True,
    also runs the diff for the amp submodule if present.

    Parameters are the same as `_git_diff_with_branch` with the addition of:
    :param include_submodules: if True, also diff the amp submodule
    """
    hdbg.dassert_eq(dir_name, ".")
    # Diff files in the main repository.
    _git_diff_with_branch(
        hash_,
        tag,
        dir_name,
        subdir,
        diff_type,
        file_types,
        skip_file_types,
        files_filter,
        from_file_filter,
        only_print_files,
        dry_run,
    )
    # Also diff the amp submodule if it exists and was requested.
    if include_submodules:
        if hgit.is_amp_present():
            with hsystem.cd("amp"):
                _git_diff_with_branch(
                    hash_,
                    tag,
                    dir_name,
                    subdir,
                    diff_type,
                    file_types,
                    skip_file_types,
                    files_filter,
                    from_file_filter,
                    only_print_files,
                    dry_run,
                )


def _resolve_target(
    target: str, hash_value: str, last_commit: bool
) -> Tuple[str, str]:
    """
    Resolve `target` to a specific git hash/ref and a tag for the diff.

    :param target: what to diff against, see `_git_branch_diff()`
    :param hash_value: hash to use with `target="hash"`
    :param last_commit: if True, override `target` to "last_commit"
    :return: `(hash_value, tag)`
    """
    if last_commit:
        target = "last_commit"
    hdbg.dassert_in(
        target,
        ("base", "master", "head", "hash", "last_commit"),
        "Invalid target",
    )
    if target == "base":
        # Compare against the point where this branch diverged from master.
        hdbg.dassert_eq(
            hash_value,
            "",
            "Cannot specify hash_value when target is 'base'",
        )
        hash_value = hgit.get_branch_hash(dir_name=".")
        tag = "base"
    elif target == "master":
        # Compare against the current state of the remote master branch.
        hdbg.dassert_eq(
            hash_value,
            "",
            "Cannot specify hash_value when target is 'master'",
        )
        hash_value = "origin/master"
        tag = "origin_master"
    elif target == "head":
        # Compare working directory against HEAD (uncommitted changes).
        hdbg.dassert_eq(
            hash_value,
            "",
            "Cannot specify hash_value when target is 'head'",
        )
        hash_value = ""
        tag = "head"
    elif target == "last_commit":
        # Compare against the previous commit.
        hdbg.dassert_eq(
            hash_value,
            "",
            "Cannot specify hash_value when target is 'last_commit'",
        )
        hash_value = "HEAD^"
        tag = "last_commit"
    elif target == "hash":
        # Compare against a user-specified commit hash.
        hdbg.dassert_ne(
            hash_value,
            "",
            "Must provide hash_value when target is 'hash'",
        )
        tag = f"hash@{hash_value}"
    else:
        raise ValueError(f"Invalid target='{target}")
    return hash_value, tag


def _git_branch_diff(
    target: str = "base",
    hash_value: str = "",
    # File filtering options.
    files: str = "",
    from_file: str = "",
    last_commit: bool = False,
    # Where to diff.
    subdir: str = "",
    include_submodules: bool = False,
    # What files to diff.
    diff_type: str = "",
    file_types: str = "",
    skip_file_types: str = "",
    # What actions.
    only_print_files: bool = False,
    dry_run: bool = False,
) -> None:
    """
    Diff files of the current branch against a specified point in time.

    Same parameters as `invoke git_branch_diff`.
    """
    dir_name = "."
    hash_value, tag = _resolve_target(target, hash_value, last_commit)
    _git_diff_with_branch_wrapper(
        hash_value,
        tag,
        #
        dir_name,
        subdir,
        include_submodules,
        #
        diff_type,
        file_types,
        skip_file_types,
        files,
        from_file,
        #
        only_print_files,
        dry_run,
    )


# #############################################################################
# CLI
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    parser.add_argument(
        "--target",
        type=str,
        default="base",
        choices=["base", "master", "head", "hash", "last_commit"],
        help="What to diff against",
    )
    parser.add_argument(
        "--hash_value",
        type=str,
        default="",
        help="The hash to use with --target=hash",
    )
    parser.add_argument(
        "--files",
        type=str,
        default="",
        help="Specific files to diff (space-separated string)",
    )
    parser.add_argument(
        "--from_file",
        type=str,
        default="",
        help="Path to file containing file list (one per line)",
    )
    parser.add_argument(
        "--last_commit",
        action="store_true",
        help="Override --target to 'last_commit'",
    )
    parser.add_argument(
        "--subdir",
        type=str,
        default="",
        help="Subdir to consider for diffing, instead of '.'",
    )
    parser.add_argument(
        "--include_submodules",
        action="store_true",
        help="Run recursively on all submodules",
    )
    parser.add_argument(
        "--diff_type",
        type=str,
        default="",
        help="Files to diff using git --diff-filter options",
    )
    parser.add_argument(
        "--file_types",
        type=str,
        default="",
        help="Comma-separated list of extensions to keep, e.g., 'csv,py'",
    )
    parser.add_argument(
        "--skip_file_types",
        type=str,
        default="",
        help="Comma-separated list of extensions to skip, e.g., 'txt'",
    )
    parser.add_argument(
        "--only_print_files",
        action="store_true",
        help="Print files to diff and exit",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Do not execute the diffing script",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    _git_branch_diff(
        args.target,
        args.hash_value,
        args.files,
        args.from_file,
        args.last_commit,
        args.subdir,
        args.include_submodules,
        args.diff_type,
        args.file_types,
        args.skip_file_types,
        args.only_print_files,
        args.dry_run,
    )


if __name__ == "__main__":
    _main(_parse())
