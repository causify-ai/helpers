#!/usr/bin/env python3

"""
Create a patch file for the entire repo client from the base revision.

Accepts a list of files to package, if specified.

# Usage Example

- Create a diff patch of the modified files:
> git_patch_create.py --modified

- Create a tar ball with all the files changed since the branch point:
> git_patch_create.py --mode tar --branch

Import as:

import dev_scripts_helpers.git.git_patch_create as dsggipac
"""

import argparse
import logging
import os

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.lib_tasks.lib_tasks_utils as hltltaut

_LOG = logging.getLogger(__name__)


# #############################################################################
# Patch creation
# #############################################################################


def _create_patch(
    mode: str = "diff",
    files: str = "",
    from_file: str = "",
    modified: bool = False,
    branch: bool = False,
    last_commit: bool = False,
) -> None:
    """
    Create a patch file for the entire repo client from the base revision.

    Same parameters as `invoke git_patch_create`.

    :param mode: what kind of patch to create
        - "diff": (default) creates a patch with the diff of the files
        - "tar": creates a tar ball with all the files
    """
    # TODO(gp): Check that the current branch is up to date with master to
    #  avoid failures when we try to merge the patch.
    hdbg.dassert_in(
        mode,
        ("tar", "diff"),
        "Patch mode must be either 'tar' for archives or 'diff' for patches",
    )
    # Currently only handles the current submodule (not parent repos).
    # TODO(gp): Extend this to handle also nested repos.
    super_module = False
    git_client_root = hgit.get_client_root(super_module)
    hash_ = hgit.get_head_hash(git_client_root, short_hash=True)
    # Use timestamp and hash to ensure unique patch filenames across time.
    timestamp = hltltaut.get_ET_timestamp()
    tag = os.path.basename(git_client_root)
    dst_file = f"patch.{tag}.{hash_}.{timestamp}"
    if mode == "tar":
        dst_file += ".tgz"
    elif mode == "diff":
        dst_file += ".patch"
    else:
        hdbg.dfatal("Invalid code path")
    _LOG.debug("dst_file=%s", dst_file)
    # Show what changes will be included in the patch.
    _LOG.info(
        "Difference between HEAD and master:\n%s",
        hgit.get_summary_files_in_branch("master", dir_name="."),
    )
    # Determine which files to include in the patch.
    all_ = False
    # Allow optional user-specified file subset (can be combined with other
    # selectors).
    mutually_exclusive = False
    # Filter out directories; patches only work with files.
    remove_dirs = True
    files_as_list = hgit.get_files_to_process(
        files,
        from_file,
        modified,
        branch,
        last_commit,
        all_,
        mutually_exclusive=mutually_exclusive,
        remove_dirs=remove_dirs,
    )
    _LOG.info("Files to save:\n%s", hprint.indent("\n".join(files_as_list)))
    if not files_as_list:
        _LOG.warning("Nothing to patch: exiting")
        return
    files_as_str = " ".join(files_as_list)
    # Choose command based on patch format: archive vs diff.
    cmd = ""
    if mode == "tar":
        # Create compressed tar archive of the selected files.
        cmd = f"tar czvf {dst_file} {files_as_str}"
        cmd_inv = "tar xvzf"
    elif mode == "diff":
        # Generate diff against various targets for different merge
        # strategies.
        opts: str
        if modified:
            # Only uncommitted changes in working tree.
            opts = "HEAD"
        elif branch:
            # All changes since branch point (includes commits on current
            # branch).
            opts = "master..."
        elif last_commit:
            # Only changes in the most recent commit.
            opts = "HEAD^"
        else:
            raise ValueError(
                "You need to specify one among -modified, --branch, "
                "--last-commit"
            )
        cmd = f"git diff {opts} --binary {files_as_str} >{dst_file}"
        cmd_inv = "git apply"
    else:
        raise ValueError(f"Invalid cmd='{cmd}'")
    # Execute the patch creation command.
    _LOG.info("Creating the patch into %s", dst_file)
    hdbg.dassert_ne(
        cmd,
        "",
        "Patch creation command must not be empty",
    )
    _LOG.debug("cmd=%s", cmd)
    rc = hsystem.system(cmd, abort_on_error=False)
    if not rc:
        _LOG.warning("Command failed with rc=%d", rc)
    # Provide instructions for applying the patch on different environments.
    remote_file = os.path.basename(dst_file)
    abs_path_dst_file = os.path.abspath(dst_file)
    msg = f"""
    # To apply the patch and execute:
    > git checkout {hash_}
    > {cmd_inv} {abs_path_dst_file}

    # To apply the patch to a remote client:
    > export SERVER="server"
    > export CLIENT_PATH="~/src"
    > scp {dst_file} $SERVER:
    > ssh $SERVER 'cd $CLIENT_PATH && {cmd_inv} ~/{remote_file}'"
    """
    msg = hprint.dedent(msg)
    print(msg)


# #############################################################################
# CLI
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="diff",
        choices=["diff", "tar"],
        help="What kind of patch to create",
    )
    parser.add_argument(
        "--files",
        type=str,
        default="",
        help="Specific files to include (space-separated string)",
    )
    parser.add_argument(
        "--from_file",
        type=str,
        default="",
        help="Path to file containing list of files (one per line)",
    )
    parser.add_argument(
        "--modified",
        action="store_true",
        help="Only uncommitted changes in the working tree",
    )
    parser.add_argument(
        "--branch",
        action="store_true",
        help="All changes since the branch point",
    )
    parser.add_argument(
        "--last_commit",
        action="store_true",
        help="Only changes in the most recent commit",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    _create_patch(
        args.mode,
        args.files,
        args.from_file,
        args.modified,
        args.branch,
        args.last_commit,
    )


if __name__ == "__main__":
    _main(_parse())
