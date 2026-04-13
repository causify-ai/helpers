#!/usr/bin/env python
"""
Run `pandoc` inside a Docker container.

This script builds the container dynamically if necessary.

> pandoc tmp.pandoc.no_spaces.txt \
    -t beamer --slide-level 4 -V theme:SimplePlus \
    --include-in-header=latex_abbrevs.sty \
    --toc --toc-depth 2 \
    -o tmp.pandoc.no_spaces.pdf
"""

import argparse
import logging

import helpers.hdbg as hdbg
import helpers.hdockerized_executables as hdocexec
import helpers.hio as hio
import helpers.hmarkdown_toc as hmarkdo
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hparser.add_dockerized_script_arg(parser)
    parser.add_argument("--input", action="store")
    parser.add_argument("--output", action="store", default="")
    parser.add_argument("--data_dir", action="store")
    parser.add_argument(
        "--container_type", action="store", default="pandoc_only"
    )
    parser.add_argument(
        "--remove_md_toc",
        action="store_true",
        default=False,
        help="Remove the markdown TOC block (<!-- toc --> ... <!-- tocstop -->) before converting",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    # Parse everything that can be parsed and returns the rest.
    args, cmd_opts = parser.parse_known_args()
    if not cmd_opts:
        cmd_opts = []
    hdbg.init_logger(
        verbosity=args.log_level, use_exec_path=True, force_white=False
    )
    _LOG.debug("cmd_opts: %s", cmd_opts)
    if not args.output:
        args.output = args.input
    # Optionally strip the markdown TOC block before converting.
    input_file = args.input
    if args.remove_md_toc:
        txt = hio.from_file(input_file)
        txt = hmarkdo.remove_table_of_contents(txt)
        input_file = "tmp.dockerized_pandoc.no_toc.md"
        hio.to_file(input_file, txt)
        _LOG.info("TOC removed; preprocessed input written to '%s'", input_file)
    cmd = f"pandoc {input_file} -o {args.output} {' '.join(cmd_opts)}"
    hdocexec.run_dockerized_pandoc(
        cmd,
        args.container_type,
        force_rebuild=args.dockerized_force_rebuild,
        use_sudo=args.dockerized_use_sudo,
    )
    _LOG.info("Output written to '%s'", args.output)


if __name__ == "__main__":
    _main(_parse())
