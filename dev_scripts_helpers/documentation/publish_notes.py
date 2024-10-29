#!/usr/bin/env python

"""
# Publish all notes:

> publish_notes.py publish

# Publish all the notes from scratch:
> publish_notes.py ls rm publish

Import as:

import documentation_devto.scripts.publish_notes as ddscpuno
"""

# TODO(gp): Add a unit test.

import argparse
import glob
import logging
import os

from tqdm.autonotebook import tqdm

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.old.tunnels as holdtunn

_LOG = logging.getLogger(__name__)


# #############################################################################


_DST_DIR = "/http/docs"


def _clean_doc_dir() -> None:
    server = holdtunn.get_server_ip("Doc server")
    hsystem.query_yes_no(
        f"Are you sure to delete the remote doc dir '{_DST_DIR}' on "
        f"server '{server}'",
        abort_on_no=True,
    )
    _LOG.warning("Cleaning %s on server %s", _DST_DIR, server)
    cmd = f"cd {_DST_DIR} && rm *.pdf *.html"
    cmd = f"ssh {server} '{cmd}'"
    hsystem.system(cmd, suppress_output=False)


def _list_doc_dir() -> None:
    server = holdtunn.get_server_ip("Doc server")
    _LOG.info("List %s on server %s", _DST_DIR, server)
    cmd = f"cd {_DST_DIR} && ls -lh *.pdf *.html"
    cmd = f"ssh {server} '{cmd}'"
    hsystem.system(cmd, suppress_output=False)


def _publish_file(args: argparse.Namespace, file_name: str, action: str) -> None:
    exec_path = hgit.find_file_in_git_tree("pandoc.py")
    hdbg.dassert_path_exists(exec_path)
    #
    tmp_dir = args.tmp_dir
    hio.create_dir(tmp_dir, incremental=False)
    out_file = f"{os.path.basename(file_name).replace('.md', '')}.{action}"
    out_file = os.path.join(tmp_dir, out_file)
    cmd = []
    cmd.append(exec_path)
    cmd.append(f"-a {action}")
    cmd.append(f"--input {file_name}")
    cmd.append(f"--output {out_file}")
    cmd.append(f"--tmp_dir {tmp_dir}")
    cmd.append("--no_open")
    # cmd.append("--gdrive_dir %s" % args.dst_dir)
    cmd = " ".join(cmd)
    hsystem.system(cmd)
    # Copy to doc server.
    server = holdtunn.get_server_ip("Doc server")
    cmd = f"scp {out_file} {server}:{_DST_DIR}"
    hsystem.system(cmd)


def _publish_all_files(args: argparse.Namespace) -> None:
    git_dir = hgit.get_client_root(super_module=True)
    _LOG.debug("git_dir=%s", git_dir)
    dir_name = os.path.join(git_dir, "amp/docs/notes/*.md")
    _LOG.debug("dir_name=%s", dir_name)
    file_names = glob.glob(dir_name)
    _LOG.info(
        "Found %d files\n%s",
        len(file_names),
        hprint.indent("\n".join(file_names)),
    )
    hdbg.dassert_lte(1, len(file_names))
    # targets = ["html", "pdf"]
    # if args.only_html:
    #    targets = ["html"]
    targets = ["html"]
    _LOG.info("targets=%s", targets)
    workload = []
    for target in targets:
        for f in file_names:
            workload.append((target, f))
    for target, f in tqdm(workload):
        _LOG.debug(hprint.frame(f"action={target} file_name={f}"))
        _publish_file(args, f, target)
    _LOG.info("\n%s", hprint.frame("SUCCESS"))


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("positional", nargs="*", choices=["rm", "ls", "publish"])
    parser.add_argument("--no_incremental", action="store_true")
    # parser.add_argument("--only_html", action="store_true")
    tmp_dir = "./tmp.publish_all_notes"
    parser.add_argument(
        "--tmp_dir",
        action="store",
        type=str,
        default=tmp_dir,
        help="Directory where to save artifacts",
    )
    dst_dir = "/Users/saggese/GoogleDrive.../Tech/Docs"
    parser.add_argument(
        "--dst_dir",
        action="store_true",
        default=dst_dir,
        help="Directory where to save the output",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    #
    actions = args.positional
    for action in actions:
        if action == "rm":
            _clean_doc_dir()
        elif action == "ls":
            _list_doc_dir()
        elif action == "publish":
            _publish_all_files(args)
        else:
            raise ValueError(f"Invalid action='{action}'")


if __name__ == "__main__":
    _main(_parse())
