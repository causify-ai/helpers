#!/usr/bin/env python3

"""
Create a new branch in a different directory with a subset of files.

# Usage Example

- Copy the files listed in `files.txt` into a fresh branch under
  `~/src/other_client`:
> git_branch_subset_copy.py --from_file files.txt --dst_dir ~/src/other_client

Import as:

import dev_scripts_helpers.git.git_branch_subset_copy as dsggibsc
"""

import argparse
import logging
import os

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# #############################################################################
# Branch subset copy
# #############################################################################


def _copy_branch_subset(
    from_file: str = "",
    pr: int = 0,
    method: str = "auto",
    dst_dir: str = "",
    dry_run: bool = False,
) -> None:
    """
    Create a new branch in a different directory with a subset of files.

    Same parameters as `invoke git_branch_subset_copy`.
    """
    # Validate inputs.
    if pr > 0:
        hdbg.dassert_eq(from_file, "")
        # Use PR-based file list.
        from_file = f"pr{pr}.files.txt"
    hdbg.dassert_ne(
        from_file,
        "",
        "from_file or --pr must be provided",
    )
    hdbg.dassert_ne(
        dst_dir,
        "",
        "dst_dir must be provided",
    )
    hdbg.dassert_file_exists(from_file)
    hdbg.dassert_dir_exists(dst_dir)
    # Get next branch name.
    branch_name = hgit.get_branch_next_name(method=method)
    _LOG.info("branch_name='%s'", branch_name)
    hdbg.dassert_ne(
        branch_name,
        None,
        "Branch name must not be None after generation",
    )
    # Allow scratch branches to bypass naming convention.
    check_branch_name = not branch_name.startswith("gp_scratch")
    # Navigate to destination directory and create branch.
    original_dir = os.getcwd()
    try:
        os.chdir(dst_dir)
        if dry_run:
            _LOG.warning(
                "Skipping branch '%s' creation and file copy into '%s' "
                "(dry run)",
                branch_name,
                dst_dir,
            )
            return
        hsystem.system("git checkout master", suppress_output=False)
        #
        cmd = f"invoke git_branch_create --branch-name '{branch_name}'"
        if not check_branch_name:
            cmd += " --no-check-branch-name"
        hsystem.system(cmd, suppress_output=False)
        # Copy files from current directory to destination directory.
        with open(from_file) as f:
            files_to_copy = [line.strip() for line in f if line.strip()]
        _LOG.info("Copying %d files to destination", len(files_to_copy))
        cmd = (
            f"copy_across_clients.py --dir1 {original_dir} --dir2 {dst_dir} "
            f"--from_file {from_file}"
        )
        hsystem.system(cmd)
        # Copy pytest script if using PR mode.
        if pr > 0:
            pytest_src = os.path.join(original_dir, f"pr{pr}.pytest.sh")
            hdbg.dassert_file_exists(pytest_src)
            pytest_dst = os.path.join(dst_dir, f"pr{pr}.pytest.sh")
            _LOG.info("Copying %s to %s", pytest_src, pytest_dst)
            hsystem.system(f"cp {pytest_src} {pytest_dst}")
    finally:
        os.chdir(original_dir)


# #############################################################################
# CLI
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    parser.add_argument(
        "--from_file",
        type=str,
        default="",
        help="Path to file containing list of files to copy",
    )
    parser.add_argument(
        "--pr",
        type=int,
        default=0,
        help="PR number to use files from pr<NUM>.files.txt and copy "
        "pr<NUM>.pytest.sh",
    )
    parser.add_argument(
        "--method",
        type=str,
        default="auto",
        choices=["auto", "github_api", "linear_scan"],
        help="Method to use for generating branch name",
    )
    parser.add_argument(
        "--dst_dir",
        type=str,
        default="",
        help="Destination directory where new branch will be created",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Log the actions without creating the branch or copying files",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    _copy_branch_subset(
        args.from_file,
        args.pr,
        args.method,
        args.dst_dir,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    _main(_parse())
