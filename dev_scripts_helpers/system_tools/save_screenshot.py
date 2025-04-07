#!/usr/bin/env python

"""
Take a screenshot and save it to a file.

The script should be run from the command line outside of a Docker
container.
"""

import argparse
import datetime
import logging
import os

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hserver as hserver
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("positional", nargs="*", help="...")
    parser.add_argument("--dst_dir", action="store", help="Destination directory")
    parser.add_argument("--filename", action="store", help="File name")
    parser.add_argument(
        "--override", action="store_true", help="Override if file exists"
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    #
    if args.filename:
        filename = args.filename
    else:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = "screenshot." + timestamp + ".png"
    if args.dst_dir:
        # E.g., notes/MSML610/tutorial_msml610/notebooks/figures
        filename = os.path.join(args.dst_dir, filename)
    _LOG.info("filename: %s", filename)
    if not args.override:
        hdbg.dassert_path_not_exists(filename)
    # Take a screenshot to the clipboard.
    _LOG.info("Take screenshot with Command (⌘) + Control + 4 ...")
    cmd = "screencapture -i -t png %s" % filename
    _LOG.info("cmd: %s", cmd)
    hsystem.system(cmd)
    # Print the info about the screenshot.
    txt = "![](%s)" % filename
    _LOG.info("%s", txt)
    # <img src="image.jpg" alt="A tree" width="300" title="This is a tree">
    if hserver.is_mac():
        _LOG.warning("Copied to clipboard")
        cmd = f"echo '{txt}' | pbcopy"
        hsystem.system(cmd)


if __name__ == "__main__":
    _main(_parse())
