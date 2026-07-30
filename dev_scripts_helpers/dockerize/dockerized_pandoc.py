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
import shutil

import helpers.hdbg as hdbg
import dev_scripts_helpers.dockerize.dockerized_utils as dshddut
import dev_scripts_helpers.dockerize.lib_pandoc as dshdlipa
import helpers.hio as hio
import helpers.hmarkdown_toc as hmartoc
import helpers.hdocker as hdocker
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# #############################################################################
# Backend selection
# #############################################################################

# TODO(ai_gp): Move all the non-CLI functions to
# dev_scripts_helpers.dockerize.lib_pandoc.py

# - `host`: run the host `pandoc` binary directly (fails if missing)
# - `dockerized`: always run pandoc inside a Docker container
# - `auto`: use the host `pandoc` if it's available, otherwise fall back to
#   `dockerized`
VALID_PANDOC_BACKENDS = ["auto", "dockerized", "host"]


def is_pandoc_on_path() -> bool:
    """
    Check if a `pandoc` binary is available on the host `PATH`.
    """
    return shutil.which("pandoc") is not None


def run_host_pandoc(cmd: str) -> str:
    """
    Run a `pandoc` command directly on the host (no Docker).

    :param cmd: full `pandoc` command line, e.g., `pandoc in.json -f json
        -t typst -o out.typ`
    :return: stdout of the command
    """
    hdbg.dassert(is_pandoc_on_path(), "No `pandoc` binary found on host PATH")
    _, result = hsystem.system_to_string(cmd)
    return result


def run_pandoc(
    cmd: str,
    container_type: str,
    pandoc_backend: str,
    *,
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> str:
    """
    Run a `pandoc` command using the selected backend.

    :param cmd: full `pandoc` command line (input file, options, `-o
        output_file`)
    :param container_type: Docker container flavor to use when running
        dockerized, e.g., `pandoc_only`, `pandoc_latex`, `pandoc_texlive`
    :param pandoc_backend: one of `VALID_PANDOC_BACKENDS` selecting how to
        run pandoc (see module docstring for the semantics of each value)
    :return: stdout of the pandoc invocation
    """
    hdbg.dassert_in(pandoc_backend, VALID_PANDOC_BACKENDS)
    if pandoc_backend == "auto":
        pandoc_backend = "host" if is_pandoc_on_path() else "dockerized"
    if pandoc_backend == "host":
        result = run_host_pandoc(cmd)
    else:
        result = dshdlipa.run_dockerized_pandoc(
            cmd,
            container_type,
            force_rebuild=force_rebuild,
            use_sudo=use_sudo,
        )
    return result


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hdocker.add_dockerized_script_arg(parser)
    parser.add_argument("-i", "--input", action="store")
    parser.add_argument("-o", "--output", action="store", default="")
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
    dshddut.add_open_arg(parser)
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
        txt = hmartoc.remove_table_of_contents(txt)
        input_file = "tmp.dockerized_pandoc.no_toc.md"
        hio.to_file(input_file, txt)
        _LOG.info("TOC removed; preprocessed input written to '%s'", input_file)
    cmd = f"pandoc {input_file} -o {args.output} {' '.join(cmd_opts)}"
    dshdlipa.run_dockerized_pandoc(
        cmd,
        args.container_type,
        force_rebuild=args.dockerized_force_rebuild,
        use_sudo=args.dockerized_use_sudo,
    )
    _LOG.info("Output written to '%s'", args.output)
    if args.open:
        dshddut.open_file_on_macos(args.output)


if __name__ == "__main__":
    _main(_parse())
